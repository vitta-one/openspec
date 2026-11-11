"""Reflex state for administrator professional and specialty management."""

from typing import Any, TypedDict
import asyncio
import unicodedata

import reflex as rx
from vitta_one.auth.local_qa import (
    LocalQaAccountError, admin_create_qa_receptionist, local_qa_enabled,
)

from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.state import AuthState
from vitta_one.professional_directory.application import (
    admin_create_professional,
    admin_create_specialty,
    admin_get_specialty,
    admin_register_medical_professional,
    admin_set_onboarding_email_status,
    admin_reissue_medical_access,
    admin_list_available_medical_accounts,
    admin_list_professionals,
    admin_list_specialties,
    admin_list_recent_professionals,
    admin_list_recent_specialties,
    admin_rename_specialty,
    admin_set_professional_active,
    admin_set_specialty_active,
    admin_update_professional,
)
from vitta_one.professional_directory.email_sender import (
    EmailDelivery, send_medical_welcome, is_resend_configured,
)
from vitta_one.professional_directory.service import (
    DirectoryConflictError,
    DirectoryNotFoundError,
    DirectoryValidationError,
    validate_professional_name,
    validate_professional_email,
)


class SpecialtyRow(TypedDict):
    id: int
    name: str
    is_active: bool
    status_label: str


class SpecialtyOption(TypedDict):
    id: int
    name: str
    is_active: bool
    selected: bool
    locked: bool


class DirectorySpecialtyFilterRow(TypedDict):
    value: str
    name: str


class MedicalAccountRow(TypedDict):
    id: int
    value: str
    email: str


class ProfessionalRow(TypedDict):
    id: int
    name: str
    registration_identifier: str
    is_active: bool
    status_label: str
    user_id: int
    user_email: str
    specialty_ids: list[int]
    specialty_names: str
    has_inactive_specialty: bool
    onboarding_email_status: str
    access_label: str
    can_reissue_access: bool
    reissue_action_label: str
    specialty_primary: str
    specialty_more_count: int


def _specialty_row(item) -> SpecialtyRow:
    return {
        "id": item.id,
        "name": item.name,
        "is_active": item.is_active,
        "status_label": "Ativa" if item.is_active else "Inativa",
    }


def _professional_row(item) -> ProfessionalRow:
    status = item.onboarding_email_status
    labels = {
        "PENDING": "Envio em processamento",
        "ACCEPTED": "Aceito pelo provedor",
        "FAILED": "Falha no envio",
        "UNKNOWN": "Envio não confirmado",
        "NOT_CONFIGURED": "Não enviado",
        "NOT_REQUIRED": "Conta vinculada",
    }
    access_label = (
        "Sem conta vinculada" if item.user_id is None
        else labels.get(status, "Situação não disponível")
    )
    return {
        "id": item.id,
        "name": item.name,
        "registration_identifier": item.registration_identifier,
        "is_active": item.is_active,
        "status_label": "Ativo" if item.is_active else "Inativo",
        "user_id": item.user_id or 0,
        "user_email": item.user_email or "Sem conta vinculada",
        "specialty_ids": [specialty.id for specialty in item.specialties],
        "specialty_names": ", ".join(
            specialty.name + (" (inativa)" if not specialty.is_active else "")
            for specialty in item.specialties
        ),
        "has_inactive_specialty": any(
            not specialty.is_active for specialty in item.specialties
        ),
        "onboarding_email_status": status,
        "access_label": access_label,
        "can_reissue_access": bool(item.user_id) and status in {
            "FAILED", "UNKNOWN", "NOT_CONFIGURED"
        },
        "reissue_action_label": (
            "Gerar novo acesso e enviar"
            if status == "NOT_CONFIGURED"
            else "Tentar enviar novo acesso"
        ),
        "specialty_primary": (
            item.specialties[0].name if item.specialties else "Não vinculada"
        ),
        "specialty_more_count": max(0, len(item.specialties) - 1),
    }


def _specialty_search_key(value: str) -> str:
    """Case/accent insensitive search without changing the domain uniqueness key."""
    return "".join(
        char for char in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(char)
    )


def filter_specialty_rows(
    rows: list[SpecialtyRow], search: str, status: str
) -> list[SpecialtyRow]:
    """Combine search and status against records actually loaded from the server."""
    term = _specialty_search_key(search.strip())
    return [
        item for item in rows
        if (not term or term in _specialty_search_key(item["name"]))
        and (status == "all" or item["is_active"] == (status == "active"))
    ]


class AdminDirectoryState(rx.State):
    """Administrator-only operational state for professionals and specialties."""

    specialties: list[SpecialtyRow] = []
    professionals: list[ProfessionalRow] = []
    recent_specialties: list[SpecialtyRow] = []
    recent_professionals: list[ProfessionalRow] = []

    specialty_search: str = ""
    specialty_status: str = "all"
    specialty_page: int = 1
    professional_search: str = ""
    professional_status: str = "all"
    professional_specialty_filter: str = "all"
    professional_page: int = 1
    directory_page_size: int = 10
    medical_accounts: list[MedicalAccountRow] = []
    specialty_options: list[SpecialtyOption] = []

    is_loading: bool = False
    directory_load_failed: bool = False
    is_submitting: bool = False
    error_message: str = ""
    success_message: str = ""
    qa_local_enabled: bool = False

    specialty_dialog_open: bool = False
    specialty_status_dialog_open: bool = False
    pending_specialty_id: int = 0
    pending_specialty_name: str = ""
    pending_specialty_is_active: bool = False
    professional_dialog_open: bool = False
    reissue_dialog_open: bool = False
    reissue_professional_id: int = 0
    reissue_is_unsent: bool = False
    status_dialog_open: bool = False
    status_professional_id: int = 0
    status_professional_name: str = ""
    status_professional_active: bool = False

    new_specialty_name: str = ""
    specialty_form_error: str = ""
    editing_specialty_id: int = 0
    editing_specialty_name: str = ""
    editing_specialty_original_name: str = ""

    editing_professional_id: int = 0
    professional_name: str = ""
    professional_email: str = ""
    professional_name_error: str = ""
    professional_email_error: str = ""
    registration_identifier: str = ""
    selected_medical_user: str = "__none__"

    @rx.var
    def has_recent_specialties(self) -> bool:
        return bool(self.recent_specialties)

    @rx.var
    def has_recent_professionals(self) -> bool:
        return bool(self.recent_professionals)

    @rx.var
    def has_specialties(self) -> bool:
        return bool(self.specialties)

    @rx.var
    def has_selectable_specialties(self) -> bool:
        return bool(self.specialty_options)

    @rx.var
    def has_professionals(self) -> bool:
        return bool(self.professionals)

    @rx.var
    def filtered_specialties(self) -> list[SpecialtyRow]:
        return filter_specialty_rows(
            self.specialties, self.specialty_search, self.specialty_status
        )

    @rx.var
    def has_active_specialty_filters(self) -> bool:
        return bool(self.specialty_search.strip()) or self.specialty_status != "all"

    @rx.var
    def specialty_result_count(self) -> int:
        return len(self.filtered_specialties)

    @rx.var
    def professional_specialty_filter_options(self) -> list[DirectorySpecialtyFilterRow]:
        """Keep inactive historical areas filterable in the full directory."""
        return [
            {"value": str(item["id"]), "name": item["name"]}
            for item in self.specialties
        ]

    @rx.var
    def filtered_professionals(self) -> list[ProfessionalRow]:
        term = self.professional_search.strip().casefold()
        return [
            item for item in self.professionals
            if (not term or term in item["name"].casefold()
                or term in item["user_email"].casefold())
            and (
                self.professional_status == "all"
                or item["is_active"] == (self.professional_status == "active")
            )
            and (
                self.professional_specialty_filter == "all"
                or self.professional_specialty_filter in [
                    str(specialty_id) for specialty_id in item["specialty_ids"]
                ]
            )
        ]

    @rx.var
    def has_filtered_specialties(self) -> bool:
        return bool(self.filtered_specialties)

    @rx.var
    def has_filtered_professionals(self) -> bool:
        return bool(self.filtered_professionals)

    @rx.var
    def specialty_page_count(self) -> int:
        return max(1, (len(self.filtered_specialties) + self.directory_page_size - 1)
                   // self.directory_page_size)

    @rx.var
    def professional_page_count(self) -> int:
        return max(1, (len(self.filtered_professionals) + self.directory_page_size - 1)
                   // self.directory_page_size)

    @rx.var
    def paged_specialties(self) -> list[SpecialtyRow]:
        start = (self.specialty_page - 1) * self.directory_page_size
        return self.filtered_specialties[start:start + self.directory_page_size]

    @rx.var
    def paged_professionals(self) -> list[ProfessionalRow]:
        start = (self.professional_page - 1) * self.directory_page_size
        return self.filtered_professionals[start:start + self.directory_page_size]

    @rx.var
    def professional_results_count(self) -> int:
        return len(self.filtered_professionals)

    @rx.var
    def professional_filters_active(self) -> bool:
        return bool(
            self.professional_search.strip()
            or self.professional_status != "all"
            or self.professional_specialty_filter != "all"
        )

    @rx.var
    def is_editing_professional(self) -> bool:
        return self.editing_professional_id > 0

    @rx.var
    def professional_form_title(self) -> str:
        return (
            "Editar profissional"
            if self.editing_professional_id > 0
            else "Novo profissional"
        )

    async def _token(self) -> str:
        auth = await self.get_state(AuthState)
        return auth.session_token

    def _clear_feedback(self) -> None:
        self.error_message = ""
        self.success_message = ""

    def _clear_sensitive_data(self) -> None:
        self.qa_local_enabled = False
        self.specialties = []
        self.professionals = []
        self.recent_specialties = []
        self.recent_professionals = []
        self.medical_accounts = []
        self.specialty_options = []
        self.specialty_dialog_open = False
        self._reset_specialty_status_change()
        self.professional_dialog_open = False
        self.reissue_dialog_open = False
        self.reissue_professional_id = 0
        self.reissue_is_unsent = False
        self.status_dialog_open = False
        self.status_professional_id = 0
        self.status_professional_name = ""
        self.status_professional_active = False
        self.new_specialty_name = ""
        self.specialty_form_error = ""
        self._reset_specialty_edit()
        self._reset_professional_form()

    def _reset_specialty_edit(self) -> None:
        self.editing_specialty_id = 0
        self.editing_specialty_name = ""
        self.editing_specialty_original_name = ""

    def _reset_specialty_status_change(self) -> None:
        self.specialty_status_dialog_open = False
        self.pending_specialty_id = 0
        self.pending_specialty_name = ""
        self.pending_specialty_is_active = False

    def _reset_professional_form(self) -> None:
        self.editing_professional_id = 0
        self.professional_name = ""
        self.professional_email = ""
        self.professional_name_error = ""
        self.professional_email_error = ""
        self.registration_identifier = ""
        self.selected_medical_user = "__none__"
        self.specialty_options = [
            {
                "id": item["id"],
                "name": item["name"],
                "is_active": item["is_active"],
                "selected": False,
                "locked": False,
            }
            for item in self.specialties
            if item["is_active"]
        ]

    def _set_medical_accounts(self, items) -> None:
        self.medical_accounts = [
            {"id": item.id, "value": str(item.id), "email": item.email}
            for item in items
        ]

    def _load_with_token(self, token: str) -> None:
        """Dashboard queries only its latest three rows; full pages load the directory."""
        self.qa_local_enabled = local_qa_enabled()
        is_dashboard = self.router.route_id == "/admin"
        with rx.session() as db:
            if is_dashboard:
                recent_specialty_items = admin_list_recent_specialties(db, token=token)
                recent_professional_items = admin_list_recent_professionals(db, token=token)
                specialty_items = []
                professional_items = []
            else:
                specialty_items = admin_list_specialties(db, token=token)
                professional_items = admin_list_professionals(db, token=token)
                recent_specialty_items = []
                recent_professional_items = []

        self.specialties = [_specialty_row(item) for item in specialty_items]
        self.specialty_page = min(self.specialty_page, self.specialty_page_count)
        self.professionals = [_professional_row(item) for item in professional_items]
        self.recent_specialties = [_specialty_row(item) for item in recent_specialty_items]
        self.recent_professionals = [_professional_row(item) for item in recent_professional_items]
        # Uma mutação pode remover o último resultado da página filtrada.
        self.professional_page = min(self.professional_page, self.professional_page_count)
        self.specialty_page = min(self.specialty_page, self.specialty_page_count)
        self.medical_accounts = []
        self.directory_load_failed = False
        if not self.editing_professional_id:
            self._reset_professional_form()

    async def _authorization_redirect(self, exc: Exception):
        self._clear_sensitive_data()
        if isinstance(exc, AuthenticationRequiredError):
            yield rx.redirect("/login")
        else:
            yield rx.redirect("/acesso-negado")

    def _selected_specialty_ids(self) -> list[int]:
        return [
            item["id"]
            for item in self.specialty_options
            if item["selected"]
        ]

    @rx.event
    async def load(self):
        self.is_loading = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            self._load_with_token(token)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self._clear_sensitive_data()
            self.directory_load_failed = True
            self.error_message = (
                "Não foi possível carregar o diretório agora. Tente novamente."
            )
        finally:
            self.is_loading = False
            yield

    @rx.event
    def update_specialty_search(self, value: str) -> None:
        self.specialty_search = value
        self.specialty_page = 1

    @rx.event
    def update_specialty_status(self, value: str) -> None:
        if value in {"all", "active", "inactive"}:
            self.specialty_status = value
            self.specialty_page = 1

    @rx.event
    def clear_specialty_filters(self) -> None:
        self.specialty_search = ""
        self.specialty_status = "all"
        self.specialty_page = 1

    @rx.event
    def move_specialty_page(self, delta: int) -> None:
        self.specialty_page = max(1, min(
            self.specialty_page + delta, self.specialty_page_count
        ))

    @rx.event
    def update_professional_search(self, value: str) -> None:
        self.professional_search = value
        self.professional_page = 1

    @rx.event
    def update_professional_status(self, value: str) -> None:
        if value in {"all", "active", "inactive"}:
            self.professional_status = value
            self.professional_page = 1

    @rx.event
    def update_professional_specialty_filter(self, value: str) -> None:
        if value == "all" or any(
            option["value"] == value for option in self.professional_specialty_filter_options
        ):
            self.professional_specialty_filter = value
            self.professional_page = 1

    @rx.event
    def clear_professional_filters(self) -> None:
        self.professional_search = ""
        self.professional_status = "all"
        self.professional_specialty_filter = "all"
        self.professional_page = 1

    @rx.event
    def move_professional_page(self, delta: int) -> None:
        self.professional_page = max(1, min(
            self.professional_page + delta, self.professional_page_count
        ))

    @rx.event
    def set_specialty_dialog_open(self, is_open: bool) -> None:
        if self.is_submitting and not is_open:
            return
        self.specialty_dialog_open = is_open
        if not is_open:
            self.new_specialty_name = ""
            self.specialty_form_error = ""
            self._reset_specialty_edit()

    @rx.event
    def start_new_specialty(self) -> None:
        if self.is_submitting:
            return
        self._clear_feedback()
        self.specialty_form_error = ""
        self.new_specialty_name = ""
        self.specialty_form_error = ""
        self._reset_specialty_edit()
        self.specialty_dialog_open = True

    @rx.event
    def cancel_specialty_dialog(self) -> None:
        if self.is_submitting:
            return
        self.new_specialty_name = ""
        self._reset_specialty_edit()
        self.specialty_dialog_open = False

    @rx.event
    def set_professional_dialog_open(self, is_open: bool) -> None:
        if self.is_submitting and not is_open:
            return
        self.professional_dialog_open = is_open
        if not is_open:
            self._reset_professional_form()

    @rx.event
    def cancel_professional_dialog(self) -> None:
        if self.is_submitting:
            return
        self._clear_feedback()
        self._reset_professional_form()
        self.professional_dialog_open = False

    @rx.event
    def set_medical_reissue_dialog_open(self, is_open: bool) -> None:
        if not is_open and not self.is_submitting:
            self.reissue_dialog_open = False
            self.reissue_professional_id = 0

    @rx.event
    def begin_medical_reissue(
        self, professional_id: int, onboarding_status: str = ""
    ) -> None:
        if self.is_submitting:
            return
        self._clear_feedback()
        self.reissue_professional_id = professional_id
        self.reissue_is_unsent = onboarding_status == "NOT_CONFIGURED"
        self.reissue_dialog_open = True

    @rx.event
    def cancel_medical_reissue(self) -> None:
        if self.is_submitting:
            return
        self.reissue_dialog_open = False
        self.reissue_professional_id = 0

    @rx.event
    async def confirm_medical_reissue(self):
        if self.is_submitting or not self.reissue_professional_id:
            return
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            if not is_resend_configured():
                raise DirectoryValidationError(
                    "Configure RESEND_API_KEY e RESEND_FROM_EMAIL no servidor antes de reenviar."
                )
            token = await self._token()
            with rx.session() as db:
                result = admin_reissue_medical_access(
                    db, token=token, professional_id=self.reissue_professional_id
                )
            try:
                delivery = await asyncio.to_thread(
                    send_medical_welcome,
                    name=result.name, email=result.email,
                    temporary_password=result.temporary_password,
                    professional_id=result.professional_id,
                    token=token,
                )
            except Exception:
                # O provedor pode ter recebido a requisição: nunca reenviar automaticamente.
                delivery = EmailDelivery(status="UNKNOWN")
            with rx.session() as db:
                admin_set_onboarding_email_status(
                    db, token=token, professional_id=result.professional_id,
                    status=delivery.status, message_id=delivery.message_id,
                )
            self.reissue_dialog_open = False
            self.reissue_professional_id = 0
            self._load_with_token(token)
            self.success_message = (
                "Nova senha temporária criada. E-mail aceito pelo provedor."
                if delivery.status == "ACCEPTED"
                else "Senha temporária substituída. Envio não confirmado; verifique o status."
            )
        except (DirectoryValidationError, DirectoryConflictError, DirectoryNotFoundError) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = (
                "Não foi possível concluir o reenvio. Consulte o status e tente novamente."
            )
        finally:
            self.is_submitting = False
            yield

    @rx.event
    def update_new_specialty_name(self, value: str) -> None:
        self.new_specialty_name = value
        self.specialty_form_error = ""

    @rx.event
    async def create_specialty(self, _form_data: dict[str, Any]):
        if self.is_submitting:
            return
        self.is_submitting = True
        self._clear_feedback()
        self.specialty_form_error = ""
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                admin_create_specialty(db, token=token, name=self.new_specialty_name)
            self.new_specialty_name = ""
            self.specialty_dialog_open = False
            self._load_with_token(token)
            self.specialty_page = 1
            yield rx.toast.success(
                "Especialidade cadastrada com sucesso.", position="top-right"
            )
        except (DirectoryValidationError, DirectoryConflictError) as exc:
            self.specialty_form_error = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.specialty_form_error = "Não foi possível cadastrar a especialidade agora."
        finally:
            self.is_submitting = False
            yield

    @rx.event
    async def begin_specialty_edit(self, specialty_id: int):
        if self.is_submitting:
            return
        self._clear_feedback()
        self.specialty_form_error = ""
        try:
            token = await self._token()
            with rx.session() as db:
                specialty = admin_get_specialty(
                    db, token=token, specialty_id=specialty_id
                )
            self.editing_specialty_id = specialty.id
            self.editing_specialty_name = specialty.name
            self.editing_specialty_original_name = specialty.name
            self.specialty_dialog_open = True
        except DirectoryNotFoundError as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível carregar a especialidade para edição."

    @rx.event
    def update_specialty_edit_name(self, value: str) -> None:
        self.editing_specialty_name = value
        self.specialty_form_error = ""

    @rx.event
    def cancel_specialty_edit(self) -> None:
        if self.is_submitting:
            return
        self.new_specialty_name = ""
        self.specialty_form_error = ""
        self._reset_specialty_edit()
        self.specialty_dialog_open = False

    @rx.event
    async def save_specialty_edit(self, _form_data: dict[str, Any]):
        if self.is_submitting:
            return
        self.is_submitting = True
        self._clear_feedback()
        self.specialty_form_error = ""
        yield
        try:
            if not self.editing_specialty_id:
                raise DirectoryNotFoundError("Selecione uma especialidade para editar.")
            token = await self._token()
            with rx.session() as db:
                admin_rename_specialty(
                    db,
                    token=token,
                    specialty_id=self.editing_specialty_id,
                    name=self.editing_specialty_name,
                    expected_name=self.editing_specialty_original_name,
                )
            self._reset_specialty_edit()
            self.specialty_dialog_open = False
            self._load_with_token(token)
            yield rx.toast.success(
                "Especialidade atualizada com sucesso.", position="top-right"
            )
        except (
            DirectoryValidationError,
            DirectoryConflictError,
            DirectoryNotFoundError,
        ) as exc:
            self.specialty_form_error = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.specialty_form_error = "Não foi possível atualizar a especialidade agora."
        finally:
            self.is_submitting = False
            yield

    @rx.event
    def begin_specialty_status_change(self, specialty_id: int) -> None:
        if self.is_submitting:
            return
        row = next(
            (item for item in self.specialties + self.recent_specialties
             if item["id"] == specialty_id),
            None,
        )
        if row is None:
            return
        self._clear_feedback()
        self.pending_specialty_id = row["id"]
        self.pending_specialty_name = row["name"]
        self.pending_specialty_is_active = row["is_active"]
        self.specialty_status_dialog_open = True

    @rx.event
    def set_specialty_status_dialog_open(self, is_open: bool) -> None:
        if self.is_submitting and not is_open:
            return
        if not is_open:
            self._reset_specialty_status_change()

    @rx.event
    def cancel_specialty_status_change(self) -> None:
        if not self.is_submitting:
            self._reset_specialty_status_change()

    @rx.event
    async def confirm_specialty_status_change(self):
        if self.is_submitting or not self.specialty_status_dialog_open or not self.pending_specialty_id:
            return
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                admin_set_specialty_active(
                    db,
                    token=token,
                    specialty_id=self.pending_specialty_id,
                    is_active=not self.pending_specialty_is_active,
                    expected_active=self.pending_specialty_is_active,
                )
            was_active = self.pending_specialty_is_active
            self._reset_specialty_status_change()
            self._load_with_token(token)
            self.specialty_page = 1
            yield rx.toast.success(
                "Especialidade desativada." if was_active
                else "Especialidade reativada.",
                position="top-right",
            )
        except (
            DirectoryValidationError, DirectoryConflictError, DirectoryNotFoundError
        ) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível alterar a especialidade agora."
        finally:
            self.is_submitting = False
            yield

    @rx.event
    async def prepare_new_professional_page(self):
        """Prepare the same medical form for a dedicated, authenticated route."""
        self.is_loading = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            self._load_with_token(token)
            with rx.session() as db:
                accounts = admin_list_available_medical_accounts(db, token=token)
            self._set_medical_accounts(accounts)
            self._reset_professional_form()
            self.professional_dialog_open = False
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self._clear_sensitive_data()
            self.error_message = "Não foi possível preparar o cadastro. Atualize a página."
        finally:
            self.is_loading = False
            yield

    @rx.event
    async def start_new_professional(self):
        self._clear_feedback()
        try:
            token = await self._token()
            with rx.session() as db:
                specialties = admin_list_specialties(db, token=token)
                accounts = admin_list_available_medical_accounts(db, token=token)
            self.specialties = [_specialty_row(item) for item in specialties]
            self._reset_professional_form()
            self._set_medical_accounts(accounts)
            self.professional_dialog_open = True
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível preparar o cadastro. Tente novamente."

    @rx.event
    async def begin_professional_edit(
        self,
        professional_id: int,
        name: str,
        registration_identifier: str,
        user_id: int,
        specialty_ids: list[int],
        user_email: str,
    ):
        self._clear_feedback()
        self.editing_professional_id = professional_id
        self.professional_name = name
        self.professional_email = user_email if user_id else ""
        self.registration_identifier = registration_identifier
        self.selected_medical_user = str(user_id) if user_id else "__none__"
        selected = set(specialty_ids)
        self.specialty_options = [
            {
                "id": item["id"],
                "name": item["name"],
                "is_active": item["is_active"],
                "selected": item["id"] in selected,
                "locked": (item["id"] in selected and not item["is_active"]),
            }
            for item in self.specialties
            if item["is_active"] or item["id"] in selected
        ]
        try:
            token = await self._token()
            with rx.session() as db:
                accounts = admin_list_available_medical_accounts(
                    db,
                    token=token,
                    professional_id=professional_id,
                )
            self._set_medical_accounts(accounts)
            self.professional_dialog_open = True
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível carregar as contas Médicas disponíveis."

    @rx.event
    def cancel_professional_edit(self) -> None:
        self._clear_feedback()
        self._reset_professional_form()
        self.professional_dialog_open = False

    @rx.event
    def update_professional_name(self, value: str) -> None:
        self.professional_name = value
        self.professional_name_error = ""

    @rx.event
    def update_professional_email(self, value: str) -> None:
        if not self.editing_professional_id:
            self.professional_email = value
            self.professional_email_error = ""

    @rx.event
    def update_registration_identifier(self, value: str) -> None:
        self.registration_identifier = value

    @rx.event
    def update_medical_user(self, value: str) -> None:
        self.selected_medical_user = value

    @rx.event
    def set_professional_specialty(self, specialty_id: int, selected: bool) -> None:
        """Apply the checkbox's explicit value, avoiding async toggle races."""
        updated: list[SpecialtyOption] = []
        for item in self.specialty_options:
            if item["id"] == specialty_id and item["is_active"] and not item["locked"]:
                updated.append({**item, "selected": bool(selected)})
            else:
                updated.append(item)
        self.specialty_options = updated

    @rx.event
    async def create_qa_receptionist(self, form_data: dict[str, Any]):
        if self.is_submitting:
            return
        self._clear_feedback()
        self.is_submitting = True
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                admin_create_qa_receptionist(
                    db, token=token,
                    email=str(form_data.get("email", "")),
                    password=str(form_data.get("password", "")),
                )
            self.success_message = "Recepcionista de QA criado. Entre com o e-mail e senha definidos."
        except (LocalQaAccountError, ValueError) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível criar o acesso de recepcionista."
        finally:
            self.is_submitting = False
            yield

    @rx.event
    async def save_professional(self, _form_data: dict[str, Any]):
        if self.is_submitting:
            return
        self.is_submitting = True
        self._clear_feedback()
        was_saved = False
        created_staff_user_id = 0
        yield
        try:
            self.professional_name_error = ""
            self.professional_email_error = ""
            try:
                validate_professional_name(self.professional_name)
            except DirectoryValidationError as exc:
                self.professional_name_error = str(exc)
            if not self.editing_professional_id:
                try:
                    validate_professional_email(self.professional_email)
                except DirectoryValidationError as exc:
                    self.professional_email_error = str(exc)
            if self.professional_name_error or self.professional_email_error:
                self.error_message = "Revise os campos destacados e tente novamente."
                return

            token = await self._token()
            specialty_ids = self._selected_specialty_ids()
            user_id = (
                None
                if self.selected_medical_user == "__none__"
                else int(self.selected_medical_user)
            )
            with rx.session() as db:
                if self.editing_professional_id:
                    admin_update_professional(
                        db,
                        token=token,
                        professional_id=self.editing_professional_id,
                        name=self.professional_name,
                        registration_identifier=self.registration_identifier,
                        specialty_ids=specialty_ids,
                        user_id=user_id,
                    )
                    message = "Profissional atualizado."
                else:
                    registration = admin_register_medical_professional(
                        db, token=token, name=self.professional_name,
                        email=self.professional_email, specialty_ids=specialty_ids,
                        local_qa_password=(
                            str(_form_data.get("qa_password", "")) or None
                        ),
                    )
                    created_staff_user_id = registration.user_id
                    message = (
                        "Médico de QA cadastrado. Use o e-mail e a senha definidos no login."
                        if str(_form_data.get("qa_password", "")) else "Profissional cadastrado."
                    )
            # Domain services commit before the external provider request.
            # Once committed, do not report an e-mail failure as a failed registration.
            was_saved = True
            if not self.editing_professional_id and registration.temporary_password:
                try:
                    delivery = await asyncio.to_thread(
                        send_medical_welcome,
                        name=registration.name,
                        email=registration.email,
                        temporary_password=registration.temporary_password,
                        professional_id=registration.professional_id,
                        token=token,
                    )
                except Exception:
                    # Treat unexpected transport/runtime errors as unknown, never
                    # automatically retry credentials that may already have arrived.
                    delivery = EmailDelivery(status="UNKNOWN")
                with rx.session() as db:
                    admin_set_onboarding_email_status(
                        db, token=token, professional_id=registration.professional_id,
                        status=delivery.status, message_id=delivery.message_id,
                    )
                if delivery.status == "ACCEPTED":
                    message = "Profissional cadastrado. E-mail aceito pelo provedor."
                elif delivery.status == "NOT_CONFIGURED":
                    message = "Profissional cadastrado. Resend não configurado; e-mail não enviado."
                else:
                    message = (
                        "Profissional cadastrado. Não foi possível confirmar o envio do e-mail. "
                        "Verifique a situação antes de reenviar o acesso."
                    )
            self._reset_professional_form()
            self.professional_dialog_open = False
            self._load_with_token(token)
            self.success_message = message
            yield rx.toast.success(message, position="top-right")
            if created_staff_user_id and self.router.route_id in {
                "/admin/funcionarios/novo", "/admin/funcionarios/medico"
            }:
                yield rx.redirect(f"/admin/funcionarios/{created_staff_user_id}")
        except (
            DirectoryValidationError,
            DirectoryConflictError,
            DirectoryNotFoundError,
        ) as exc:
            self.error_message = str(exc)
            yield rx.toast.error(self.error_message, position="top-right")
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            if was_saved:
                self.professional_dialog_open = False
                self.success_message = (
                    "Profissional salvo. Não foi possível atualizar ou confirmar o status do e-mail. "
                    "Atualize a página para verificar o cadastro antes de tentar novamente."
                )
            else:
                self.error_message = "Não foi possível salvar o profissional agora."
            yield rx.toast.error(self.error_message or self.success_message, position="top-right")
        finally:
            self.is_submitting = False
            yield

    @rx.event
    def begin_professional_status_change(
        self, professional_id: int, name: str, current_active: bool
    ) -> None:
        if self.is_submitting:
            return
        self._clear_feedback()
        self.status_professional_id = professional_id
        self.status_professional_name = name
        self.status_professional_active = current_active
        self.status_dialog_open = True

    @rx.event
    def set_professional_status_dialog_open(self, is_open: bool) -> None:
        if self.is_submitting and not is_open:
            return
        self.status_dialog_open = is_open
        if not is_open:
            self.status_professional_id = 0
            self.status_professional_name = ""

    @rx.event
    def cancel_professional_status_change(self) -> None:
        if self.is_submitting:
            return
        self.status_dialog_open = False
        self.status_professional_id = 0
        self.status_professional_name = ""

    @rx.event
    async def confirm_professional_status_change(self):
        if self.is_submitting or not self.status_professional_id:
            return
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                admin_set_professional_active(
                    db,
                    token=token,
                    professional_id=self.status_professional_id,
                    is_active=not self.status_professional_active,
                    expected_active=self.status_professional_active,
                )
            message = (
                "Profissional desativado."
                if self.status_professional_active
                else "Profissional reativado."
            )
            self.status_dialog_open = False
            self.status_professional_id = 0
            self.status_professional_name = ""
            self._load_with_token(token)
            self.success_message = message
            yield rx.toast.success(message, position="top-right")
        except (DirectoryNotFoundError, DirectoryConflictError) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível alterar o profissional agora."
        finally:
            self.is_submitting = False
            yield

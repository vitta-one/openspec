"""Reflex state for administrator professional and specialty management."""

from typing import Any, TypedDict

import reflex as rx

from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.state import AuthState
from vitta_one.professional_directory.application import (
    admin_create_professional,
    admin_create_specialty,
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
from vitta_one.professional_directory.service import (
    DirectoryConflictError,
    DirectoryNotFoundError,
    DirectoryValidationError,
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


def _specialty_row(item) -> SpecialtyRow:
    return {
        "id": item.id,
        "name": item.name,
        "is_active": item.is_active,
        "status_label": "Ativa" if item.is_active else "Inativa",
    }


def _professional_row(item) -> ProfessionalRow:
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
    }


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
    is_submitting: bool = False
    error_message: str = ""
    success_message: str = ""

    specialty_dialog_open: bool = False
    professional_dialog_open: bool = False

    new_specialty_name: str = ""
    editing_specialty_id: int = 0
    editing_specialty_name: str = ""

    editing_professional_id: int = 0
    professional_name: str = ""
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
    def has_professionals(self) -> bool:
        return bool(self.professionals)

    @rx.var
    def filtered_specialties(self) -> list[SpecialtyRow]:
        term = self.specialty_search.strip().casefold()
        return [
            item for item in self.specialties
            if (not term or term in item["name"].casefold())
            and (
                self.specialty_status == "all"
                or item["is_active"] == (self.specialty_status == "active")
            )
        ]

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
        self.specialties = []
        self.professionals = []
        self.recent_specialties = []
        self.recent_professionals = []
        self.medical_accounts = []
        self.specialty_options = []
        self.specialty_dialog_open = False
        self.professional_dialog_open = False
        self.new_specialty_name = ""
        self._reset_specialty_edit()
        self._reset_professional_form()

    def _reset_specialty_edit(self) -> None:
        self.editing_specialty_id = 0
        self.editing_specialty_name = ""

    def _reset_professional_form(self) -> None:
        self.editing_professional_id = 0
        self.professional_name = ""
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
        self.professionals = [_professional_row(item) for item in professional_items]
        self.recent_specialties = [_specialty_row(item) for item in recent_specialty_items]
        self.recent_professionals = [_professional_row(item) for item in recent_professional_items]
        self.medical_accounts = []
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
            self.error_message = (
                "Não foi possível carregar o diretório agora. Atualize a página e tente novamente."
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
            self._reset_specialty_edit()

    @rx.event
    def start_new_specialty(self) -> None:
        self._clear_feedback()
        self.new_specialty_name = ""
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
    def update_new_specialty_name(self, value: str) -> None:
        self.new_specialty_name = value

    @rx.event
    async def create_specialty(self, _form_data: dict[str, Any]):
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                admin_create_specialty(
                    db,
                    token=token,
                    name=self.new_specialty_name,
                )
            self.new_specialty_name = ""
            self.specialty_dialog_open = False
            self._load_with_token(token)
            self.success_message = "Especialidade cadastrada."
        except (DirectoryValidationError, DirectoryConflictError) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível cadastrar a especialidade agora."
        finally:
            self.is_submitting = False
            yield

    @rx.event
    def begin_specialty_edit(self, specialty_id: int, name: str) -> None:
        self._clear_feedback()
        self.editing_specialty_id = specialty_id
        self.editing_specialty_name = name
        self.specialty_dialog_open = True

    @rx.event
    def update_specialty_edit_name(self, value: str) -> None:
        self.editing_specialty_name = value

    @rx.event
    def cancel_specialty_edit(self) -> None:
        self._reset_specialty_edit()
        self.specialty_dialog_open = False

    @rx.event
    async def save_specialty_edit(self, _form_data: dict[str, Any]):
        self.is_submitting = True
        self._clear_feedback()
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
                )
            self._reset_specialty_edit()
            self.specialty_dialog_open = False
            self._load_with_token(token)
            self.success_message = "Especialidade atualizada."
        except (
            DirectoryValidationError,
            DirectoryConflictError,
            DirectoryNotFoundError,
        ) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível atualizar a especialidade agora."
        finally:
            self.is_submitting = False
            yield

    @rx.event
    async def toggle_specialty_active(self, specialty_id: int, current_active: bool):
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                admin_set_specialty_active(
                    db,
                    token=token,
                    specialty_id=specialty_id,
                    is_active=not current_active,
                )
            self._load_with_token(token)
            self.success_message = (
                "Especialidade desativada."
                if current_active
                else "Especialidade reativada."
            )
        except DirectoryNotFoundError as exc:
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
    ):
        self._clear_feedback()
        self.editing_professional_id = professional_id
        self.professional_name = name
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

    @rx.event
    def update_registration_identifier(self, value: str) -> None:
        self.registration_identifier = value

    @rx.event
    def update_medical_user(self, value: str) -> None:
        self.selected_medical_user = value

    @rx.event
    def toggle_professional_specialty(self, specialty_id: int) -> None:
        updated: list[SpecialtyOption] = []
        for item in self.specialty_options:
            if item["id"] == specialty_id and item["is_active"] and not item["locked"]:
                updated.append({**item, "selected": not item["selected"]})
            else:
                updated.append(item)
        self.specialty_options = updated

    @rx.event
    async def save_professional(self, _form_data: dict[str, Any]):
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
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
                    admin_create_professional(
                        db,
                        token=token,
                        name=self.professional_name,
                        registration_identifier=self.registration_identifier,
                        specialty_ids=specialty_ids,
                        user_id=user_id,
                    )
                    message = "Profissional cadastrado."
            self._reset_professional_form()
            self.professional_dialog_open = False
            self._load_with_token(token)
            self.success_message = message
        except (
            DirectoryValidationError,
            DirectoryConflictError,
            DirectoryNotFoundError,
        ) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível salvar o profissional agora."
        finally:
            self.is_submitting = False
            yield

    @rx.event
    async def toggle_professional_active(
        self, professional_id: int, current_active: bool
    ):
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                admin_set_professional_active(
                    db,
                    token=token,
                    professional_id=professional_id,
                    is_active=not current_active,
                )
            self._load_with_token(token)
            self.success_message = (
                "Profissional desativado."
                if current_active
                else "Profissional reativado."
            )
        except DirectoryNotFoundError as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível alterar o profissional agora."
        finally:
            self.is_submitting = False
            yield

"""Reflex state for administrator professional and specialty management."""

from typing import TypedDict

import reflex as rx

from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.state import AuthState
from vitta_one.professional_directory.application import (
    admin_create_professional,
    admin_create_specialty,
    admin_list_available_medical_accounts,
    admin_list_professionals,
    admin_list_specialties,
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


class MedicalAccountRow(TypedDict):
    id: int
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
    medical_accounts: list[MedicalAccountRow] = []
    specialty_options: list[SpecialtyOption] = []

    is_loading: bool = False
    is_submitting: bool = False
    error_message: str = ""
    success_message: str = ""

    editing_specialty_id: int = 0
    editing_specialty_name: str = ""

    editing_professional_id: int = 0
    professional_name: str = ""
    registration_identifier: str = ""
    selected_medical_user: str = "__none__"

    @rx.var
    def has_specialties(self) -> bool:
        return bool(self.specialties)

    @rx.var
    def has_professionals(self) -> bool:
        return bool(self.professionals)

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
        self.medical_accounts = []
        self.specialty_options = []
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
            {"id": item.id, "email": item.email}
            for item in items
        ]

    def _load_with_token(self, token: str) -> None:
        with rx.session() as db:
            specialty_items = admin_list_specialties(db, token=token)
            professional_items = admin_list_professionals(db, token=token)
            account_items = admin_list_available_medical_accounts(db, token=token)

        self.specialties = [_specialty_row(item) for item in specialty_items]
        self.professionals = [_professional_row(item) for item in professional_items]
        self._set_medical_accounts(account_items)
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
    async def create_specialty(self, form_data: dict[str, str]):
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                admin_create_specialty(
                    db,
                    token=token,
                    name=str(form_data.get("name", "")),
                )
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

    @rx.event
    def update_specialty_edit_name(self, value: str) -> None:
        self.editing_specialty_name = value

    @rx.event
    def cancel_specialty_edit(self) -> None:
        self._reset_specialty_edit()

    @rx.event
    async def save_specialty_edit(self):
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
        self._reset_professional_form()
        try:
            token = await self._token()
            with rx.session() as db:
                accounts = admin_list_available_medical_accounts(db, token=token)
            self._set_medical_accounts(accounts)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível carregar as contas Médicas disponíveis."

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
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível carregar as contas Médicas disponíveis."

    @rx.event
    def cancel_professional_edit(self) -> None:
        self._clear_feedback()
        self._reset_professional_form()

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
    async def save_professional(self):
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

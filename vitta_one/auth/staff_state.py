"""Administração: diretório autorizado e cadastro único de funcionários."""

import asyncio
from typing import TypedDict

import reflex as rx

from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.security import is_valid_email_identifier, normalize_email
from vitta_one.auth.staff_service import (
    create_receptionist,
    get_employee_detail,
    list_employee_directory,
    list_receptionists,
    filter_employee_directory,
)
from vitta_one.auth.state import AuthState
from vitta_one.professional_directory.application import (
    admin_register_medical_professional,
    admin_set_onboarding_email_status,
)
from vitta_one.professional_directory.email_sender import EmailDelivery, send_medical_welcome
from vitta_one.professional_directory.service import (
    DirectoryConflictError,
    DirectoryNotFoundError,
    DirectoryValidationError,
)
from vitta_one.professional_directory.state import AdminDirectoryState


class EmployeeRow(TypedDict):
    id: int
    email: str
    name: str
    role: str
    role_label: str
    href: str


_EMPTY_EMPLOYEE: EmployeeRow = {
    "id": 0, "email": "", "name": "", "role": "", "role_label": "", "href": "",
}

class EmployeeDetail(EmployeeRow):
    has_name: bool
    professional_identifier: str
    professional_status: str
    specialties: str


_EMPTY_EMPLOYEE_DETAIL: EmployeeDetail = {
    "id": 0, "email": "", "name": "", "role": "", "role_label": "", "href": "",
    "has_name": False, "professional_identifier": "", "professional_status": "",
    "specialties": "",
}

from vitta_one.auth.state import AuthState
from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.staff_service import (
    create_receptionist,
    get_employee_detail,
    list_employee_directory,
    list_receptionists,
    filter_employee_directory,
)


class AdminStaffState(rx.State):
    emails: list[str] = []
    employees: list[EmployeeRow] = []
    employee_detail: EmployeeDetail = _EMPTY_EMPLOYEE_DETAIL
    detail_status: str = "loading"
    employee_search: str = ""
    employee_role: str = "todos"
    is_loading: bool = True
    current_page: int = 1
    page_size: int = 10
    creation_profile: str = ""
    new_name: str = ""
    new_email: str = ""
    show_password: bool = False
    pending_profile: str = ""
    profile_change_dialog_open: bool = False
    cancel_dialog_open: bool = False

    name_error: str = ""
    email_error: str = ""
    profile_error: str = ""
    password_error: str = ""
    error: str = ""
    success: str = ""
    saving: bool = False

    @rx.var
    def filtered_employees(self) -> list[EmployeeRow]:
        return filter_employee_directory(
            self.employees, search=self.employee_search, role=self.employee_role,
        )

    @rx.var
    def detail_matches_route(self) -> bool:
        """Prevent displaying a prior employee while navigating between detail routes."""
        return (
            self.detail_status == "ready"
            and str(self.employee_detail["id"])
            == str(self.router.page.params.get("employee_id", ""))
        )

    @rx.var
    def has_employee_filters(self) -> bool:
        return bool(self.employee_search.strip()) or self.employee_role != "todos"

    @rx.var
    def total_pages(self) -> int:
        return max(1, (len(self.filtered_employees) + self.page_size - 1) // self.page_size)

    @rx.var
    def paged_employees(self) -> list[dict[str, str | int]]:
        start = (self.current_page - 1) * self.page_size
        return self.filtered_employees[start:start + self.page_size]

    @rx.var
    def page_label(self) -> str:
        return f"{self.current_page} de {self.total_pages}"

    def _clear_errors(self) -> None:
        self.name_error = ""
        self.email_error = ""
        self.profile_error = ""
        self.password_error = ""
        self.error = ""

    @rx.event
    def update_employee_search(self, value: str):
        self.employee_search = value
        self.current_page = 1

    @rx.event
    def update_employee_role(self, value: str):
        self.employee_role = value if value in ("todos", "MEDICO", "RECEPCIONISTA") else "todos"
        self.current_page = 1

    @rx.event
    def clear_employee_filters(self):
        self.employee_search = ""
        self.employee_role = "todos"
        self.current_page = 1

    @rx.event
    def move_employee_page(self, delta: int):
        self.current_page = max(1, min(self.current_page + delta, self.total_pages))

    @rx.event
    def update_new_name(self, value: str) -> None:
        self.new_name = value
        self.name_error = ""

    @rx.event
    def update_new_email(self, value: str) -> None:
        self.new_email = value
        self.email_error = ""

    @rx.event
    def toggle_password_visibility(self) -> None:
        self.show_password = not self.show_password

    async def _apply_profile(self, value: str) -> None:
        # O formulário conserva a identificação comum, mas descarta vínculos
        # profissionais ao sair do perfil médico.
        if self.creation_profile == "medico" and value != "medico":
            directory = await self.get_state(AdminDirectoryState)
            directory.specialty_options = [
                {**option, "selected": False} for option in directory.specialty_options
            ]
        self.creation_profile = value
        self.pending_profile = ""
        self.show_password = False
        self._clear_errors()

    @rx.event
    async def select_creation_profile(self, value: str):
        if self.saving:
            return
        next_profile = value if value in ("medico", "recepcionista") else ""
        if next_profile == self.creation_profile:
            return
        has_specific_data = self.creation_profile in ("medico", "recepcionista")
        if has_specific_data:
            self.pending_profile = next_profile
            self.profile_change_dialog_open = True
            return
        await self._apply_profile(next_profile)

    @rx.event
    async def confirm_profile_change(self):
        await self._apply_profile(self.pending_profile)
        self.profile_change_dialog_open = False

    @rx.event
    def set_profile_change_dialog_open(self, is_open: bool) -> None:
        self.profile_change_dialog_open = is_open
        if not is_open:
            self.pending_profile = ""

    @rx.event
    def dismiss_profile_change(self) -> None:
        self.pending_profile = ""
        self.profile_change_dialog_open = False

    @rx.event
    def request_cancel(self):
        if self.new_name.strip() or self.new_email.strip() or self.creation_profile:
            self.cancel_dialog_open = True
        else:
            return rx.redirect("/admin/funcionarios")

    @rx.event
    def set_cancel_dialog_open(self, is_open: bool) -> None:
        self.cancel_dialog_open = is_open

    @rx.event
    def dismiss_cancel(self) -> None:
        self.cancel_dialog_open = False

    @rx.event
    def confirm_cancel(self):
        self.cancel_dialog_open = False
        self.new_name = ""
        self.new_email = ""
        self.creation_profile = ""
        return rx.redirect("/admin/funcionarios")

    async def _token(self):
        auth = await self.get_state(AuthState)
        return auth.session_token

    @rx.event
    async def prepare_creation(self):
        self.creation_profile = ""
        self.new_name = ""
        self.new_email = ""
        self.show_password = False
        self.pending_profile = ""
        self.profile_change_dialog_open = False
        self.cancel_dialog_open = False
        self.success = ""
        self._clear_errors()
        try:
            token = await self._token()
            with rx.session() as db:
                # Revalidar autorização antes de habilitar qualquer operação.
                list_employee_directory(db, token=token)
        except AuthenticationRequiredError:
            yield rx.redirect("/login")
        except RoleForbiddenError:
            yield rx.redirect("/acesso-negado")
        except Exception:
            self.error = "Não foi possível preparar o cadastro. Atualize a página."

    @rx.event
    async def load(self):
        self._clear_errors()
        self.success = ""
        if self.router.route_id == "/admin/funcionarios/recepcionista":
            self.creation_profile = "recepcionista"
        self.is_loading = True
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                self.emails = list_receptionists(db, token=token)
                self.employees = list_employee_directory(db, token=token)
        except AuthenticationRequiredError:
            self.emails = []
            self.employees = []
            yield rx.redirect("/login")
        except RoleForbiddenError:
            self.emails = []
            self.employees = []
            yield rx.redirect("/acesso-negado")
        except Exception:
            self.emails = []
            self.employees = []
            self.error = "Não foi possível carregar os funcionários."
        finally:
            self.is_loading = False

    @rx.event
    async def load_detail(self):
        self.employee_detail = _EMPTY_EMPLOYEE_DETAIL.copy()
        self.detail_status = "loading"
        try:
            raw_id = self.router.page.params.get("employee_id", "")
            if not str(raw_id).isdigit() or int(raw_id) <= 0:
                self.detail_status = "not_found"
                return
            token = await self._token()
            with rx.session() as db:
                record = get_employee_detail(db, token=token, employee_id=int(raw_id))
            if record is None:
                self.detail_status = "not_found"
                return
            self.employee_detail = record
            self.detail_status = "ready"
        except AuthenticationRequiredError:
            self.detail_status = "denied"
            yield rx.redirect("/login")
        except RoleForbiddenError:
            self.detail_status = "denied"
            yield rx.redirect("/acesso-negado")
        except Exception:
            self.detail_status = "error"

    @rx.event
    async def create(self, form_data: dict):
        if self.saving:
            return
        self._clear_errors()
        self.success = ""
        self.saving = True
        yield
        created_id = 0
        try:
            # Dados do formulário são validados novamente no serviço e no banco.
            name = " ".join(str(form_data.get("name", "")).split())
            email = normalize_email(str(form_data.get("email", "")))
            if not 2 <= len(name) <= 160:
                self.name_error = "Informe o nome completo (2 a 160 caracteres)."
            if not is_valid_email_identifier(email):
                self.email_error = "Informe um e-mail de acesso válido."
            if self.creation_profile not in ("medico", "recepcionista"):
                self.profile_error = "Selecione um perfil válido."
            if self.creation_profile == "recepcionista":
                password = str(form_data.get("password", ""))
                if not 12 <= len(password) <= 128:
                    self.password_error = "A senha precisa ter entre 12 e 128 caracteres."
            elif self.creation_profile == "medico":
                directory = await self.get_state(AdminDirectoryState)
                qa_password = str(form_data.get("qa_password", ""))
                if directory.qa_local_enabled and not 12 <= len(qa_password) <= 128:
                    self.password_error = "No QA local, informe uma senha de 12 a 128 caracteres."
                elif qa_password and not 12 <= len(qa_password) <= 128:
                    self.password_error = "A senha de QA precisa ter entre 12 e 128 caracteres."
            if any((self.name_error, self.email_error, self.profile_error, self.password_error)):
                self.error = "Revise os campos indicados para concluir o cadastro."
                return

            token = await self._token()
            if self.creation_profile == "recepcionista":
                with rx.session() as db:
                    created = create_receptionist(
                        db, token=token, name=name, email=email,
                        password=str(form_data.get("password", "")),
                    )
                    created_id = created.id or 0
                message = "Recepcionista cadastrado. O acesso utiliza a senha inicial definida."
            else:
                directory = await self.get_state(AdminDirectoryState)
                specialty_ids = [
                    option["id"] for option in directory.specialty_options
                    if option["selected"]
                ]
                with rx.session() as db:
                    registration = admin_register_medical_professional(
                        db, token=token, name=name, email=email,
                        specialty_ids=specialty_ids,
                        local_qa_password=(str(form_data.get("qa_password", "")) or None),
                    )
                    created_id = registration.user_id
                message = (
                    "Médico cadastrado em QA. Use o e-mail e a senha inicial definida."
                    if str(form_data.get("qa_password", ""))
                    else "Médico cadastrado."
                )
                if registration.temporary_password:
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
                        delivery = EmailDelivery(status="UNKNOWN")
                    with rx.session() as db:
                        admin_set_onboarding_email_status(
                            db, token=token, professional_id=registration.professional_id,
                            status=delivery.status, message_id=delivery.message_id,
                        )
                    if delivery.status == "ACCEPTED":
                        message = "Médico cadastrado. E-mail aceito pelo provedor (entrega não confirmada)."
                    elif delivery.status == "NOT_CONFIGURED":
                        message = "Médico cadastrado. Resend não configurado; acesso não enviado."
                    else:
                        message = (
                            "Médico cadastrado. O envio do acesso não foi confirmado; "
                            "verifique o cadastro antes de tentar reenviar."
                        )
            self.success = message
            self.new_name = ""
            self.new_email = ""
            yield rx.toast.success(message, position="top-right")
            yield rx.redirect(f"/admin/funcionarios/{created_id}")
        except (ValueError, DirectoryValidationError, DirectoryConflictError,
                DirectoryNotFoundError) as exc:
            if created_id:
                # O cadastro já foi persistido. Falha posterior no status do
                # provedor não deve incentivar nova criação do mesmo usuário.
                self.success = (
                    "Funcionário cadastrado, mas não foi possível confirmar o status "
                    "do primeiro acesso. Confira a ficha antes de tentar novamente."
                )
                yield rx.redirect(f"/admin/funcionarios/{created_id}")
            else:
                self.error = str(exc)
                if "e-mail" in self.error.lower() or "conta" in self.error.lower():
                    self.email_error = self.error
        except AuthenticationRequiredError:
            yield rx.redirect("/login")
        except RoleForbiddenError:
            yield rx.redirect("/acesso-negado")
        except Exception:
            if created_id:
                self.success = (
                    "Funcionário cadastrado, mas não foi possível confirmar o status "
                    "do primeiro acesso. Consulte a ficha antes de cadastrar novamente."
                )
                yield rx.redirect(f"/admin/funcionarios/{created_id}")
            else:
                self.error = "Não foi possível concluir o cadastro. Tente novamente."
        finally:
            self.saving = False
            yield

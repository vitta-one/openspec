"""Administration state for a paginated employee directory and staff onboarding."""
import reflex as rx
from typing import TypedDict


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
    creation_profile: str = "__none__"
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
    def select_creation_profile(self, value: str):
        self.creation_profile = value if value in ("medico", "recepcionista") else "__none__"

    async def _token(self):
        auth = await self.get_state(AuthState)
        return auth.session_token

    @rx.event
    async def load(self):
        self.error = ""
        self.success = ""
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
        self.saving = True
        self.error = ""
        self.success = ""
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                created = create_receptionist(
                    db, token=token, email=str(form_data.get("email", "")),
                    name=str(form_data.get("name", "")),
                    password=str(form_data.get("password", "")),
                )
                self.emails = list_receptionists(db, token=token)
                self.employees = list_employee_directory(db, token=token)
            self.success = "Funcionário cadastrado com sucesso."
            yield rx.toast.success(self.success, position="top-right")
            yield rx.redirect(f"/admin/funcionarios/{created.id}")
        except ValueError:
            self.error = "Não foi possível concluir o cadastro com os dados informados."
            yield rx.toast.error(self.error, position="top-right")
        except AuthenticationRequiredError:
            yield rx.redirect("/login")
        except RoleForbiddenError:
            yield rx.redirect("/acesso-negado")
        except Exception:
            self.error = "Não foi possível criar o acesso."
            yield rx.toast.error(self.error, position="top-right")
        finally:
            self.saving = False
            yield

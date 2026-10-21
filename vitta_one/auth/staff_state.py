"""Admin staff access state."""
import reflex as rx
from vitta_one.auth.state import AuthState
from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.staff_service import create_receptionist, list_receptionists

class AdminStaffState(rx.State):
    emails: list[str] = []
    error: str = ""
    success: str = ""
    saving: bool = False

    async def _token(self):
        auth = await self.get_state(AuthState)
        return auth.session_token

    @rx.event
    async def load(self):
        self.error = ""
        self.success = ""
        try:
            token = await self._token()
            with rx.session() as db:
                self.emails = list_receptionists(db, token=token)
        except AuthenticationRequiredError:
            self.emails = []
            yield rx.redirect("/login")
        except RoleForbiddenError:
            self.emails = []
            yield rx.redirect("/acesso-negado")
        except Exception:
            self.emails = []
            self.error = "Não foi possível carregar os recepcionistas."

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
                create_receptionist(db, token=token, email=str(form_data.get("email", "")),
                                    password=str(form_data.get("password", "")))
                self.emails = list_receptionists(db, token=token)
            self.success = "Recepcionista cadastrado. Já pode entrar com o e-mail e a senha informados."
        except ValueError as exc:
            self.error = str(exc)
        except AuthenticationRequiredError:
            yield rx.redirect("/login")
        except RoleForbiddenError:
            yield rx.redirect("/acesso-negado")
        except Exception:
            self.error = "Não foi possível criar o acesso."
        finally:
            self.saving = False
            yield

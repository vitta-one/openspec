"""Reflex authentication state, session restoration, logout, and route authorization."""

from typing import TypedDict

import reflex as rx

from vitta_one.auth.authorization import (
    AuthenticationRequiredError,
    RoleForbiddenError,
    PasswordChangeRequiredError,
    require_authenticated,
    require_role,
)
from vitta_one.auth.roles import Role
from vitta_one.auth.service import (
    authenticate_user, create_session, revoke_session,
    temporary_password_is_expired, complete_temporary_password_change,
    TemporaryPasswordError,
)
from vitta_one.auth.settings import (
    SESSION_COOKIE_NAME,
    local_admin_preview_enabled,
    secure_cookie_enabled,
    session_ttl,
    session_ttl_seconds,
)
from vitta_one.auth.security import is_valid_email_identifier, normalize_email

_INVALID_CREDENTIALS = "E-mail ou senha inválidos. Verifique os dados e tente novamente."
_LOGIN_REQUIRED = "Preencha o e-mail e a senha para continuar."
_SYSTEM_LOGIN_ERROR = "Não foi possível concluir o acesso agora. Tente novamente."
_LOGOUT_ERROR = "Não foi possível encerrar a sessão agora. Tente novamente."

_ROLE_BY_ROUTE = {
    **{role.dashboard_path: role for role in Role},
    "/admin/especialidades": Role.ADMINISTRADOR,
    "/admin/profissionais": Role.ADMINISTRADOR,
    "/recepcao/agenda": Role.RECEPCIONISTA,
    "/recepcao/pacientes": Role.RECEPCIONISTA,
    "/recepcao/fila": Role.RECEPCIONISTA,
    "/medico/agenda": Role.MEDICO,
    "/medico/pacientes": Role.MEDICO,
}
_ADMIN_PREVIEW_ROUTES = frozenset(
    {
        "/admin/recepcao",
        "/admin/agenda",
        "/admin/atendimento",
        "/admin/pacientes",
        "/admin/financeiro",
    }
)


class LoginFormData(TypedDict):
    """Expected login form fields submitted by the Reflex form."""

    email: str
    password: str


class AuthState(rx.State):
    """Own the authenticated browser session and sanitized identity context."""

    session_token: str = rx.Cookie(
        "",
        name=SESSION_COOKIE_NAME,
        path="/",
        max_age=session_ttl_seconds(),
        secure=secure_cookie_enabled(),
        same_site="strict",
    )

    current_email: str = ""
    current_role: str = ""
    verified_path: str = ""
    auth_checked: bool = False
    is_submitting: bool = False
    show_password: bool = False
    login_error: str = ""
    first_access_error: str = ""
    shell_error: str = ""
    local_admin_preview: bool = local_admin_preview_enabled()

    def _set_identity(self, *, email: str, role: Role, verified_path: str = "") -> None:
        self.current_email = email
        self.current_role = role.value
        self.verified_path = verified_path

    def _clear_identity(self) -> None:
        self.current_email = ""
        self.current_role = ""
        self.verified_path = ""

    async def _clear_sensitive_states(self) -> None:
        """Remove role-scoped patient and clinical projections from browser state."""
        from vitta_one.admin_preview.state import AdminPreviewState
        from vitta_one.clinical_prescription.state import PrintPrescriptionState
        from vitta_one.doctor_workspace.state import DoctorWorkspaceState
        from vitta_one.patient_portal.state import PatientPortalState
        from vitta_one.patient_queue.state import DoctorQueueState, ReceptionQueueState

        queue = await self.get_state(ReceptionQueueState)
        queue._clear_sensitive_view()
        doctor = await self.get_state(DoctorQueueState)
        doctor._clear_active()
        workspace = await self.get_state(DoctorWorkspaceState)
        workspace._clear()
        portal = await self.get_state(PatientPortalState)
        portal._clear()
        portal.error_message = ""
        prescriptions = await self.get_state(PrintPrescriptionState)
        prescriptions._clear()
        preview = await self.get_state(AdminPreviewState)
        preview._clear()

    @rx.var
    def role_label(self) -> str:
        """Return the localized current role label without trusting client input."""
        try:
            return Role(self.current_role).label
        except ValueError:
            return ""

    @rx.var
    def dashboard_path(self) -> str:
        """Return the current user's role dashboard destination."""
        try:
            return Role(self.current_role).dashboard_path
        except ValueError:
            return "/login"

    @rx.event
    def toggle_password_visibility(self) -> None:
        """Toggle only the presentation of the password field."""
        self.show_password = not self.show_password

    @rx.event
    async def prepare_login(self):
        """Restore a valid session on the login page or expose the login form."""
        self.auth_checked = False
        self.login_error = ""
        self.shell_error = ""
        yield

        if not self.session_token:
            await self._clear_sensitive_states()
            self._clear_identity()
            self.auth_checked = True
            yield
            return

        try:
            with rx.session() as db:
                identity = require_authenticated(db, self.session_token)
        except AuthenticationRequiredError:
            await self._clear_sensitive_states()
            self.session_token = ""
            self._clear_identity()
            self.auth_checked = True
            yield rx.remove_cookie(SESSION_COOKIE_NAME)
            return
        except Exception:
            await self._clear_sensitive_states()
            self._clear_identity()
            self.auth_checked = True
            self.login_error = _SYSTEM_LOGIN_ERROR
            yield
            return

        self._set_identity(email=identity.email, role=identity.role)
        self.auth_checked = True
        yield rx.redirect(
            "/primeiro-acesso" if identity.must_change_password
            else identity.role.dashboard_path
        )

    @rx.event
    async def login(self, form_data: LoginFormData):
        """Authenticate credentials, create the opaque server session, and route by role."""
        self.login_error = ""
        self.shell_error = ""
        self.is_submitting = True
        yield

        email = str(form_data.get("email", ""))
        password = str(form_data.get("password", ""))
        normalized_email = normalize_email(email)

        if not is_valid_email_identifier(normalized_email) or not password:
            self.login_error = _LOGIN_REQUIRED
            self.is_submitting = False
            yield
            return

        try:
            with rx.session() as db:
                user = authenticate_user(db, normalized_email, password)
                if user is None or user.id is None:
                    self.login_error = _INVALID_CREDENTIALS
                    self.is_submitting = False
                    yield
                    return

                if user.must_change_password and temporary_password_is_expired(user):
                    self.login_error = (
                        "Sua senha inicial expirou. Solicite novo acesso à administração."
                    )
                    self.is_submitting = False
                    yield
                    return
                requires_initial_change = user.must_change_password
                role = Role(user.role)
                authenticated_email = user.email
                authenticated_user_id = user.id
                token = create_session(
                    db,
                    user_id=authenticated_user_id,
                    ttl=session_ttl(),
                )
        except Exception:
            self.login_error = _SYSTEM_LOGIN_ERROR
            self.is_submitting = False
            yield
            return

        await self._clear_sensitive_states()
        self.session_token = token
        self._set_identity(email=authenticated_email, role=role)
        self.auth_checked = True
        self.is_submitting = False
        yield
        yield rx.redirect(
            "/primeiro-acesso" if requires_initial_change
            else role.dashboard_path
        )

    @rx.event
    async def route_from_root(self):
        """Route the app root to login or the authenticated role dashboard."""
        self.auth_checked = False
        self.shell_error = ""
        yield

        if not self.session_token:
            await self._clear_sensitive_states()
            self._clear_identity()
            self.auth_checked = True
            yield rx.redirect("/login")
            return

        try:
            with rx.session() as db:
                identity = require_authenticated(db, self.session_token)
        except AuthenticationRequiredError:
            await self._clear_sensitive_states()
            self.session_token = ""
            self._clear_identity()
            self.auth_checked = True
            yield rx.remove_cookie(SESSION_COOKIE_NAME)
            yield rx.redirect("/login")
            return
        except Exception:
            await self._clear_sensitive_states()
            self._clear_identity()
            self.auth_checked = True
            yield rx.redirect("/login")
            return

        self._set_identity(email=identity.email, role=identity.role)
        self.auth_checked = True
        yield rx.redirect(
            "/primeiro-acesso" if identity.must_change_password
            else identity.role.dashboard_path
        )

    @rx.event
    async def load_protected(self):
        """Revalidate session and derive the required role from the server-observed route."""
        self.auth_checked = False
        self.shell_error = ""
        yield

        required_role = _ROLE_BY_ROUTE.get(self.router.route_id)
        if required_role is None:
            self._clear_identity()
            self.auth_checked = True
            yield rx.redirect("/login")
            return

        try:
            with rx.session() as db:
                identity = require_role(db, self.session_token, required_role)
        except AuthenticationRequiredError:
            await self._clear_sensitive_states()
            self.session_token = ""
            self._clear_identity()
            self.auth_checked = True
            yield rx.remove_cookie(SESSION_COOKIE_NAME)
            yield rx.redirect("/login")
            return
        except RoleForbiddenError as exc:
            await self._clear_sensitive_states()
            self._set_identity(email=exc.identity.email, role=exc.identity.role)
            self.auth_checked = True
            yield rx.redirect("/acesso-negado")
            return
        except PasswordChangeRequiredError:
            await self._clear_sensitive_states()
            self._clear_identity()
            self.auth_checked = True
            yield rx.redirect("/primeiro-acesso")
            return
        except Exception:
            await self._clear_sensitive_states()
            self._clear_identity()
            self.auth_checked = True
            yield rx.redirect("/login")
            return

        self._set_identity(
            email=identity.email,
            role=identity.role,
            verified_path=self.router.route_id,
        )
        self.auth_checked = True
        yield

    @rx.event
    def load_admin_preview(self):
        """Authorize a read-only local Administrator QA route without widening production RBAC."""
        self.auth_checked = False
        self.shell_error = ""
        yield

        requested_path = self.router.route_id
        if not self.local_admin_preview or requested_path not in _ADMIN_PREVIEW_ROUTES:
            self.auth_checked = True
            yield rx.redirect(Role.ADMINISTRADOR.dashboard_path)
            return

        try:
            with rx.session() as db:
                identity = require_role(
                    db,
                    self.session_token,
                    Role.ADMINISTRADOR,
                )
        except AuthenticationRequiredError:
            self.session_token = ""
            self._clear_identity()
            self.auth_checked = True
            yield rx.remove_cookie(SESSION_COOKIE_NAME)
            yield rx.redirect("/login")
            return
        except RoleForbiddenError as exc:
            self._set_identity(email=exc.identity.email, role=exc.identity.role)
            self.auth_checked = True
            yield rx.redirect("/acesso-negado")
            return
        except Exception:
            self._clear_identity()
            self.auth_checked = True
            yield rx.redirect("/login")
            return

        self._set_identity(
            email=identity.email,
            role=identity.role,
            verified_path=requested_path,
        )
        self.auth_checked = True
        yield

    @rx.event
    async def prepare_forbidden(self):
        """Keep the forbidden page available only to an authenticated identity."""
        self.auth_checked = False
        self.shell_error = ""
        yield

        try:
            with rx.session() as db:
                identity = require_authenticated(db, self.session_token)
        except AuthenticationRequiredError:
            await self._clear_sensitive_states()
            self.session_token = ""
            self._clear_identity()
            self.auth_checked = True
            yield rx.remove_cookie(SESSION_COOKIE_NAME)
            yield rx.redirect("/login")
            return
        except Exception:
            await self._clear_sensitive_states()
            self._clear_identity()
            self.auth_checked = True
            yield rx.redirect("/login")
            return

        self._set_identity(email=identity.email, role=identity.role)
        self.auth_checked = True
        yield

    @rx.event
    async def load_first_access(self):
        """Allow only provisional Medical accounts to reach password rotation."""
        self.auth_checked = False
        self.first_access_error = ""
        yield
        try:
            with rx.session() as db:
                identity = require_authenticated(db, self.session_token)
        except AuthenticationRequiredError:
            await self._clear_sensitive_states()
            self.session_token = ""
            self._clear_identity()
            self.auth_checked = True
            yield rx.remove_cookie(SESSION_COOKIE_NAME)
            yield rx.redirect("/login")
            return
        except Exception:
            await self._clear_sensitive_states()
            self._clear_identity()
            self.auth_checked = True
            yield rx.redirect("/login")
            return
        if identity.role is not Role.MEDICO or not identity.must_change_password:
            self._clear_identity()
            self.auth_checked = True
            yield rx.redirect(identity.role.dashboard_path)
            return
        self._set_identity(
            email=identity.email, role=identity.role,
            verified_path="/primeiro-acesso",
        )
        self.auth_checked = True
        yield

    @rx.event
    def save_first_access(self, form_data: dict):
        """Never store current/new password in Reflex State; submit directly to service."""
        self.is_submitting = True
        self.first_access_error = ""
        yield
        old = str(form_data.get("current_password", ""))
        new = str(form_data.get("new_password", ""))
        confirm = str(form_data.get("confirm_password", ""))
        if not old or not new or new != confirm:
            self.first_access_error = "Preencha as senhas e confirme a nova senha corretamente."
            self.is_submitting = False
            yield
            return
        try:
            with rx.session() as db:
                complete_temporary_password_change(
                    db, token=self.session_token,
                    current_password=old, new_password=new,
                )
        except TemporaryPasswordError as exc:
            self.first_access_error = str(exc)
            self.is_submitting = False
            yield
            return
        except AuthenticationRequiredError:
            self.session_token = ""
            self._clear_identity()
            self.is_submitting = False
            yield rx.remove_cookie(SESSION_COOKIE_NAME)
            yield rx.redirect("/login")
            return
        except Exception:
            self.first_access_error = "Não foi possível atualizar a senha agora."
            self.is_submitting = False
            yield
            return
        self.is_submitting = False
        self.verified_path = ""
        yield rx.redirect(Role.MEDICO.dashboard_path)

    @rx.event
    def go_to_dashboard(self):
        """Revalidate the current session before returning to its authorized dashboard."""
        try:
            with rx.session() as db:
                identity = require_authenticated(db, self.session_token)
        except AuthenticationRequiredError:
            self.session_token = ""
            self._clear_identity()
            yield rx.remove_cookie(SESSION_COOKIE_NAME)
            yield rx.redirect("/login")
            return
        except Exception:
            self._clear_identity()
            yield rx.redirect("/login")
            return

        self._set_identity(email=identity.email, role=identity.role)
        yield rx.redirect(
            "/primeiro-acesso" if identity.must_change_password
            else identity.role.dashboard_path
        )

    @rx.event
    async def logout(self):
        """Revoke the session and clear sensitive role state before leaving the app."""
        self.shell_error = ""
        token = self.session_token

        if token:
            try:
                with rx.session() as db:
                    revoke_session(db, token)
            except Exception:
                self.shell_error = _LOGOUT_ERROR
                yield
                return

        # Clear clinical/read-only QA projections held by sibling states before
        # removing the authenticated browser context.
        await self._clear_sensitive_states()

        self.session_token = ""
        self._clear_identity()
        self.auth_checked = True
        yield rx.remove_cookie(SESSION_COOKIE_NAME)
        yield rx.redirect("/login")

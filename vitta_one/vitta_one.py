"""Vitta-One Reflex application entry point."""

import reflex as rx

from vitta_one.admin_preview.state import AdminPreviewState
from vitta_one.appointment_scheduling.state import AdminAvailabilityState, ReceptionAgendaState
from vitta_one.doctor_workspace.state import DoctorWorkspaceState
from vitta_one.auth.roles import Role
from vitta_one.auth.state import AuthState
from vitta_one.auth.staff_state import AdminStaffState
from vitta_one.clinical_prescription.state import PrintPrescriptionState
from vitta_one.models import (
    AuthSession,
    ClinicalCareRecord,
    Consultation,
    ConsultationScheduleChange,
    Patient,
    PatientPortalInvitation,
    Prescription,
    PrescriptionItem,
    Professional,
    ProfessionalAvailabilitySlot,
    ProfessionalWeeklySchedule,
    ProfessionalSpecialty,
    QueueEntry,
    Specialty,
    User,
)
from vitta_one.patient_portal.activation_api import activation_api
from vitta_one.patient_portal.state import AdminClinicConfigurationState, PatientPortalState
from vitta_one.patient_portal.booking_state import PatientBookingState
from vitta_one.patient_queue.state import DoctorQueueState, ReceptionQueueState
from vitta_one.professional_directory.state import AdminDirectoryState
from vitta_one.reception.dashboard.state import ReceptionDashboardState
from vitta_one.ui.pages import (
    admin_agenda_preview_page,
    admin_clinical_preview_page,
    admin_finance_preview_page,
    admin_page,
    admin_staff_types_page,
    admin_medical_staff_page,
    admin_receptionist_staff_page,
    admin_hours_page,
    admin_clinic_settings_page,
    admin_specialties_page,
    admin_professionals_page,
    admin_patients_preview_page,
    admin_reception_preview_page,
    doctor_page,
    doctor_agenda_page,
    doctor_patients_page,
    finance_page,
    forbidden_page,
    login_page,
    first_access_page,
    patient_activation_page,
    patient_portal_page,
    patient_booking_page,
    prescription_print_page,
    reception_page,
    reception_agenda_page,
    reception_patients_page,
    reception_queue_page,
    root_page,
)

# Keep persistent models imported from the application module so Reflex/Alembic
# can discover their metadata when generating migrations.
_PERSISTENT_MODELS = (
    User,
    AuthSession,
    Patient,
    QueueEntry,
    Specialty,
    Professional,
    ProfessionalAvailabilitySlot,
    ProfessionalWeeklySchedule,
    ProfessionalSpecialty,
    Consultation,
    ClinicalCareRecord,
    Prescription,
    PrescriptionItem,
    ConsultationScheduleChange,
    PatientPortalInvitation,
)

app = rx.App(
    api_transformer=activation_api,
    theme=rx.theme(
        appearance="light",
        accent_color="teal",
        gray_color="slate",
        radius="large",
    ),
    stylesheets=["/styles.css"],
)

app.add_page(
    root_page,
    route="/",
    title="Vitta-One",
    on_load=AuthState.route_from_root,
)
app.add_page(
    login_page,
    route="/login",
    title="Entrar | Vitta-One",
    on_load=AuthState.prepare_login,
)
app.add_page(
    first_access_page,
    route="/primeiro-acesso",
    title="Primeiro acesso | Vitta-One",
    on_load=AuthState.load_first_access,
)
app.add_page(
    patient_activation_page,
    route="/ativar-paciente",
    title="Ative seu portal | Vitta-One",
)
app.add_page(
    admin_page,
    route=Role.ADMINISTRADOR.dashboard_path,
    title="Painel administrativo | Vitta-One",
    on_load=AuthState.load_protected,
)
app.add_page(
    admin_staff_types_page,
    route="/admin/funcionarios",
    title="Criar funcionário | Vitta-One",
    on_load=AuthState.load_protected,
)
app.add_page(
    admin_medical_staff_page,
    route="/admin/funcionarios/medico",
    title="Cadastrar médico | Vitta-One",
    on_load=[AuthState.load_protected, AdminDirectoryState.prepare_new_professional_page],
)
app.add_page(
    admin_receptionist_staff_page,
    route="/admin/funcionarios/recepcionista",
    title="Cadastrar recepcionista | Vitta-One",
    on_load=[AuthState.load_protected, AdminStaffState.load],
)
app.add_page(
    admin_hours_page,
    route="/admin/horarios",
    title="Horários de atendimento | Vitta-One",
    on_load=[AuthState.load_protected, AdminAvailabilityState.load],
)
app.add_page(
    admin_clinic_settings_page,
    route="/admin/configuracoes",
    title="Configurações da clínica | Vitta-One",
    on_load=[AuthState.load_protected, AdminClinicConfigurationState.load],
)
app.add_page(
    admin_specialties_page,
    route="/admin/especialidades",
    title="Especialidades | Vitta-One",
    on_load=[AuthState.load_protected, AdminDirectoryState.load],
)
app.add_page(
    admin_professionals_page,
    route="/admin/profissionais",
    title="Profissionais | Vitta-One",
    on_load=[AuthState.load_protected, AdminDirectoryState.load],
)
app.add_page(
    admin_reception_preview_page,
    route="/admin/recepcao",
    title="Recepção · Preview local | Vitta-One",
    on_load=[AuthState.load_admin_preview, AdminPreviewState.load],
)
app.add_page(
    admin_agenda_preview_page,
    route="/admin/agenda",
    title="Agenda · Preview local | Vitta-One",
    on_load=[AuthState.load_admin_preview, AdminPreviewState.load],
)
app.add_page(
    admin_clinical_preview_page,
    route="/admin/atendimento",
    title="Atendimento · Preview local | Vitta-One",
    on_load=[AuthState.load_admin_preview, AdminPreviewState.load],
)
app.add_page(
    admin_patients_preview_page,
    route="/admin/pacientes",
    title="Pacientes · Preview local | Vitta-One",
    on_load=[AuthState.load_admin_preview, AdminPreviewState.load],
)
app.add_page(
    admin_finance_preview_page,
    route="/admin/financeiro",
    title="Financeiro · Preview local | Vitta-One",
    on_load=[AuthState.load_admin_preview, AdminPreviewState.load],
)

app.add_page(
    reception_page,
    route=Role.RECEPCIONISTA.dashboard_path,
    title="Painel de recepção | Vitta-One",
    on_load=[AuthState.load_protected, ReceptionDashboardState.load],
)
app.add_page(
    reception_agenda_page,
    route="/recepcao/agenda",
    title="Agenda e check-in | Vitta-One",
    on_load=[AuthState.load_protected, ReceptionAgendaState.load],
)
app.add_page(
    reception_patients_page,
    route="/recepcao/pacientes",
    title="Pacientes | Vitta-One",
    on_load=[AuthState.load_protected, ReceptionQueueState.load],
)
app.add_page(
    reception_queue_page,
    route="/recepcao/fila",
    title="Fila de espera | Vitta-One",
    on_load=[AuthState.load_protected, ReceptionQueueState.load],
)
app.add_page(
    doctor_page,
    route=Role.MEDICO.dashboard_path,
    title="Painel médico | Vitta-One",
    on_load=[AuthState.load_protected, DoctorQueueState.load],
)
app.add_page(
    doctor_agenda_page,
    route="/medico/agenda",
    title="Agenda médica | Vitta-One",
    on_load=[AuthState.load_protected, DoctorWorkspaceState.load],
)
app.add_page(
    doctor_patients_page,
    route="/medico/pacientes",
    title="Pacientes vinculados | Vitta-One",
    on_load=[AuthState.load_protected, DoctorWorkspaceState.load],
)
app.add_page(
    patient_portal_page,
    route=Role.PACIENTE.dashboard_path,
    title="Minhas consultas | Vitta-One",
    on_load=[AuthState.load_protected, PatientPortalState.load],
)
app.add_page(
    patient_booking_page,
    route="/paciente/agendar",
    title="Agendar consulta | Vitta-One",
    on_load=[AuthState.load_protected, PatientBookingState.load],
)
app.add_page(
    finance_page,
    route=Role.FINANCEIRO.dashboard_path,
    title="Painel financeiro | Vitta-One",
    on_load=AuthState.load_protected,
)
app.add_page(
    prescription_print_page,
    route="/medico/prescricao/[prescription_id]",
    title="Prescrição | Vitta-One",
    on_load=PrintPrescriptionState.load,
)
app.add_page(
    forbidden_page,
    route="/acesso-negado",
    title="Acesso não autorizado | Vitta-One",
    on_load=AuthState.prepare_forbidden,
)

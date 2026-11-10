"""Add clinical attachments, prescription signatures and financial billing.

Revision ID: f4a9c2d7e610
Revises: e9d3a8c2b170
Create Date: 2026-11-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4a9c2d7e610"
down_revision: Union[str, Sequence[str], None] = "e9d3a8c2b170"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clinical_attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("consultation_id", sa.Integer(), nullable=True),
        sa.Column("clinical_care_record_id", sa.Integer(), nullable=True),
        sa.Column("uploaded_by_user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("exam_date", sa.Date(), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("cloud_asset_id", sa.String(length=255), nullable=False),
        sa.Column("cloud_public_id", sa.String(length=255), nullable=False),
        sa.Column("cloud_version", sa.Integer(), nullable=False),
        sa.Column("cloud_resource_type", sa.String(length=20), nullable=False),
        sa.Column("cloud_format", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("patient_visible", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("byte_size > 0", name="ck_clinical_attachments_byte_size"),
        sa.CheckConstraint("status IN ('ACTIVE', 'DELETION_FAILED', 'REMOVED')", name="ck_clinical_attachments_status"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["consultation_id"], ["consultations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["clinical_care_record_id"], ["clinical_care_records.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["auth_users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cloud_asset_id"),
        sa.UniqueConstraint("cloud_public_id"),
    )
    for name, columns in (
        ("ix_clinical_attachments_patient_id", ["patient_id"]),
        ("ix_clinical_attachments_consultation_id", ["consultation_id"]),
        ("ix_clinical_attachments_clinical_care_record_id", ["clinical_care_record_id"]),
        ("ix_clinical_attachments_uploaded_by_user_id", ["uploaded_by_user_id"]),
        ("ix_clinical_attachments_category", ["category"]),
        ("ix_clinical_attachments_cloud_asset_id", ["cloud_asset_id"]),
        ("ix_clinical_attachments_cloud_public_id", ["cloud_public_id"]),
        ("ix_clinical_attachments_status", ["status"]),
        ("ix_clinical_attachments_patient_visible", ["patient_visible"]),
        ("ix_clinical_attachments_created_at", ["created_at"]),
        ("ix_clinical_attachments_patient_created", ["patient_id", "created_at"]),
        ("ix_clinical_attachments_record_created", ["clinical_care_record_id", "created_at"]),
    ):
        op.create_index(name, "clinical_attachments", columns)

    op.create_table(
        "clinical_attachment_audits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("attachment_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("outcome", sa.String(length=24), nullable=False),
        sa.Column("detail_code", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["attachment_id"], ["clinical_attachments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["auth_users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_clinical_attachment_audits_attachment_id", "clinical_attachment_audits", ["attachment_id"])
    op.create_index("ix_clinical_attachment_audits_actor_user_id", "clinical_attachment_audits", ["actor_user_id"])
    op.create_index("ix_clinical_attachment_audits_created_at", "clinical_attachment_audits", ["created_at"])
    op.create_index("ix_clinical_attachment_audits_attachment_created", "clinical_attachment_audits", ["attachment_id", "created_at"])

    op.create_table(
        "prescription_signature_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("prescription_id", sa.Integer(), nullable=False),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=False),
        sa.Column("request_key", sa.String(length=64), nullable=False),
        sa.Column("external_id", sa.String(length=80), nullable=False),
        sa.Column("provider_document_token", sa.String(length=128), nullable=True),
        sa.Column("provider_signer_token", sa.String(length=128), nullable=True),
        sa.Column("signer_email", sa.String(length=320), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("status_detail_code", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_provider_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('CREATING', 'PENDING', 'SIGNED', 'REFUSED', 'EXPIRED', 'CANCELLED', 'RECONCILIATION_REQUIRED', 'FAILED')",
            name="ck_prescription_signature_requests_status",
        ),
        sa.ForeignKeyConstraint(["prescription_id"], ["prescriptions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["auth_users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("prescription_id"),
        sa.UniqueConstraint("request_key"),
        sa.UniqueConstraint("external_id"),
        sa.UniqueConstraint("provider_document_token"),
    )
    for column in ("prescription_id", "requested_by_user_id", "request_key", "external_id", "provider_document_token", "status", "created_at"):
        op.create_index(f"ix_prescription_signature_requests_{column}", "prescription_signature_requests", [column])
    op.create_index("ix_prescription_signature_status_updated", "prescription_signature_requests", ["status", "updated_at"])

    op.create_table(
        "signature_webhook_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=160), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("provider_document_token", sa.String(length=128), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )
    for column in ("event_id", "event_type", "provider_document_token", "received_at"):
        op.create_index(f"ix_signature_webhook_events_{column}", "signature_webhook_events", [column])

    op.create_table(
        "financial_services",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("unit_price_cents > 0", name="ck_financial_services_price"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["auth_users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["auth_users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_financial_services_name", "financial_services", ["name"])
    op.create_index("ix_financial_services_active", "financial_services", ["active"])

    op.create_table(
        "patient_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("consultation_id", sa.Integer(), nullable=True),
        sa.Column("issued_by_user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("total_cents", sa.Integer(), nullable=False),
        sa.Column("paid_cents", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("total_cents >= 0", name="ck_patient_accounts_total"),
        sa.CheckConstraint("paid_cents >= 0 AND paid_cents <= total_cents", name="ck_patient_accounts_paid"),
        sa.CheckConstraint("status IN ('OPEN', 'PARTIALLY_PAID', 'PAID', 'CANCELLED')", name="ck_patient_accounts_status"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["consultation_id"], ["consultations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["issued_by_user_id"], ["auth_users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("patient_id", "consultation_id", "issued_by_user_id", "status", "due_date", "created_at"):
        op.create_index(f"ix_patient_accounts_{column}", "patient_accounts", [column])
    op.create_index("ix_patient_accounts_patient_created", "patient_accounts", ["patient_id", "created_at"])

    op.create_table(
        "patient_account_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=True),
        sa.Column("description_snapshot", sa.String(length=300), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False),
        sa.Column("total_cents", sa.Integer(), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_patient_account_items_quantity"),
        sa.CheckConstraint("unit_price_cents > 0", name="ck_patient_account_items_unit_price"),
        sa.CheckConstraint("total_cents = quantity * unit_price_cents", name="ck_patient_account_items_total"),
        sa.ForeignKeyConstraint(["account_id"], ["patient_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["service_id"], ["financial_services.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_patient_account_items_account_id", "patient_account_items", ["account_id"])
    op.create_index("ix_patient_account_items_account", "patient_account_items", ["account_id", "id"])

    op.create_table(
        "billing_customers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("provider_customer_id", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("patient_id"),
        sa.UniqueConstraint("provider_customer_id"),
    )
    op.create_index("ix_billing_customers_patient_id", "billing_customers", ["patient_id"])
    op.create_index("ix_billing_customers_provider_customer_id", "billing_customers", ["provider_customer_id"])

    op.create_table(
        "billing_charges",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("request_key", sa.String(length=64), nullable=False),
        sa.Column("external_reference", sa.String(length=80), nullable=False),
        sa.Column("provider_charge_id", sa.String(length=80), nullable=True),
        sa.Column("billing_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("value_cents", sa.Integer(), nullable=False),
        sa.Column("invoice_url", sa.String(length=1000), nullable=True),
        sa.Column("status_detail_code", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_provider_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("value_cents > 0", name="ck_billing_charges_value"),
        sa.CheckConstraint("billing_type IN ('UNDEFINED', 'BOLETO', 'PIX', 'CREDIT_CARD')", name="ck_billing_charges_type"),
        sa.CheckConstraint("status IN ('CREATING', 'PENDING', 'RECEIVED', 'CONFIRMED', 'OVERDUE', 'CANCELLED', 'REFUNDED', 'RECONCILIATION_REQUIRED', 'FAILED')", name="ck_billing_charges_status"),
        sa.ForeignKeyConstraint(["account_id"], ["patient_accounts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_key"),
        sa.UniqueConstraint("external_reference"),
        sa.UniqueConstraint("provider_charge_id"),
    )
    for column in ("account_id", "request_key", "external_reference", "provider_charge_id", "status", "due_date", "created_at"):
        op.create_index(f"ix_billing_charges_{column}", "billing_charges", [column])
    op.create_index("ix_billing_charges_account_created", "billing_charges", ["account_id", "created_at"])

    op.create_table(
        "billing_webhook_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=160), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("provider_charge_id", sa.String(length=80), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )
    for column in ("event_id", "event_type", "provider_charge_id", "received_at"):
        op.create_index(f"ix_billing_webhook_events_{column}", "billing_webhook_events", [column])

    op.create_table(
        "payment_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("charge_id", sa.Integer(), nullable=False),
        sa.Column("provider_payment_id", sa.String(length=80), nullable=False),
        sa.Column("provider_event_id", sa.String(length=160), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount_cents > 0", name="ck_payment_records_amount"),
        sa.CheckConstraint("status IN ('RECEIVED', 'CONFIRMED', 'REFUNDED', 'CHARGEBACK')", name="ck_payment_records_status"),
        sa.ForeignKeyConstraint(["charge_id"], ["billing_charges.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_payment_id", name="uq_payment_provider_payment_id"),
    )
    for column in ("charge_id", "provider_payment_id", "provider_event_id", "status", "created_at"):
        op.create_index(f"ix_payment_records_{column}", "payment_records", [column])

    op.create_table(
        "financial_audits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("resource_type", sa.String(length=40), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("outcome", sa.String(length=24), nullable=False),
        sa.Column("detail_code", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["auth_users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_financial_audits_actor_user_id", "financial_audits", ["actor_user_id"])
    op.create_index("ix_financial_audits_created_at", "financial_audits", ["created_at"])
    op.create_index("ix_financial_audits_resource_created", "financial_audits", ["resource_type", "resource_id", "created_at"])


def downgrade() -> None:
    # Destructive only in an explicitly disposable QA database.
    for table in (
        "financial_audits", "payment_records", "billing_webhook_events", "billing_charges",
        "billing_customers", "patient_account_items", "patient_accounts", "financial_services",
        "signature_webhook_events", "prescription_signature_requests",
        "clinical_attachment_audits", "clinical_attachments",
    ):
        op.drop_table(table)

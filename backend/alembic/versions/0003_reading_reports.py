"""Persist baseline reports generated from reading snapshots."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reading_reports",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("reading_id", sa.Uuid(), sa.ForeignKey("readings.id", ondelete="SET NULL")),
        sa.Column(
            "account_id",
            sa.Uuid(),
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("request_key", sa.String(72), nullable=False),
        sa.Column("template", sa.String(16), nullable=False),
        sa.Column("title", sa.String(48), nullable=False),
        sa.Column("category", sa.String(16), nullable=False),
        sa.Column("source", JSONB(), nullable=False),
        sa.Column("sections", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("account_id", "request_key", name="uq_report_request"),
    )
    op.create_index(
        "ix_reports_account_created", "reading_reports", ["account_id", "created_at", "id"]
    )


def downgrade() -> None:
    op.drop_table("reading_reports")

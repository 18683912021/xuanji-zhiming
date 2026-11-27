"""Store account details, reading notes and public share snapshots."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("accounts", sa.Column("details", JSONB(), nullable=False, server_default="{}"))
    op.add_column(
        "birth_profiles", sa.Column("details", JSONB(), nullable=False, server_default="{}")
    )
    op.add_column("readings", sa.Column("note", sa.Text(), nullable=False, server_default=""))
    op.create_table(
        "reading_shares",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "reading_id",
            sa.Uuid(),
            sa.ForeignKey("readings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "account_id",
            sa.Uuid(),
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(48), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_reading_shares_account_id", "reading_shares", ["account_id"])
    op.create_index("ix_reading_shares_reading_id", "reading_shares", ["reading_id"])


def downgrade() -> None:
    op.drop_table("reading_shares")
    op.drop_column("readings", "note")
    op.drop_column("birth_profiles", "details")
    op.drop_column("accounts", "details")

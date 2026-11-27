"""Persist expiring email codes and login throttling."""

import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("accounts", sa.Column("wechat_app_id", sa.String(32)))
    op.add_column("accounts", sa.Column("wechat_open_id", sa.String(128)))
    op.create_unique_constraint(
        "uq_account_wechat", "accounts", ["wechat_app_id", "wechat_open_id"]
    )
    op.create_table(
        "email_challenges",
        sa.Column("email", sa.String(254), primary_key=True),
        sa.Column("purpose", sa.String(20), primary_key=True),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("nonce", sa.Uuid(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resend_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_email_challenges_expires_at", "email_challenges", ["expires_at"])
    op.create_table(
        "password_attempts",
        sa.Column("email", sa.String(254), primary_key=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_password_attempts_expires_at", "password_attempts", ["expires_at"])


def downgrade() -> None:
    op.drop_table("password_attempts")
    op.drop_table("email_challenges")
    op.drop_constraint("uq_account_wechat", "accounts", type_="unique")
    op.drop_column("accounts", "wechat_open_id")
    op.drop_column("accounts", "wechat_app_id")

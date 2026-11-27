"""Mark the local administrator account independently of member accounts."""

import sqlalchemy as sa

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column("is_development_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM login_sessions WHERE account_id IN "
        "(SELECT id FROM accounts WHERE is_development_admin)"
    )
    op.execute("UPDATE accounts SET password_hash = NULL WHERE is_development_admin")
    op.drop_column("accounts", "is_development_admin")

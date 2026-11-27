"""Enable password accounts with a username and optional email."""

import sqlalchemy as sa

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("accounts", sa.Column("username", sa.String(24)))
    op.create_unique_constraint("uq_account_username", "accounts", ["username"])
    op.alter_column("password_attempts", "email", new_column_name="identifier")
    op.execute("""
        UPDATE password_attempts AS attempts
        SET identifier = 'account:' || accounts.id::text
        FROM accounts WHERE attempts.identifier = accounts.email
    """)


def downgrade() -> None:
    op.execute(
        "DELETE FROM password_attempts WHERE identifier LIKE 'account:%' OR identifier LIKE 'unknown:%'"
    )
    op.alter_column("password_attempts", "identifier", new_column_name="email")
    op.drop_constraint("uq_account_username", "accounts", type_="unique")
    op.drop_column("accounts", "username")

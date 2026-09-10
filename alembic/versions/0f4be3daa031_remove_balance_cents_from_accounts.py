"""remove balance_cents from accounts

Revision ID: 0f4be3daa031
Revises: 7af7709706ad
Create Date: 2026-09-10 00:00:00.000000

O saldo passa a ser calculado a partir da soma das transações da conta
(event sourcing) em vez de ser uma coluna mutável em ``accounts``.

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0f4be3daa031"
down_revision: str | None = "7af7709706ad"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("accounts", schema=None) as batch_op:
        batch_op.drop_constraint("ck_accounts_balance_non_negative", type_="check")
        batch_op.drop_column("balance_cents")


def downgrade() -> None:
    # O saldo histórico não é recuperável a partir daqui — a coluna volta
    # zerada para todas as contas existentes.
    with op.batch_alter_table("accounts", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("balance_cents", sa.Integer(), nullable=False, server_default="0")
        )
        batch_op.create_check_constraint(
            "ck_accounts_balance_non_negative", "balance_cents >= 0"
        )

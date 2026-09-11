"""fix linked account plaid ids and misc constraints

Revision ID: fb4fa4f2cd12
Revises: b31d9fda54f8
Create Date: 2026-09-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb4fa4f2cd12'
down_revision: Union[str, Sequence[str], None] = 'b31d9fda54f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # plaid_item_id is shared by every account under the same Plaid Item,
    # so it can no longer be unique on its own.
    op.drop_index(
        op.f('ix_linked_accounts_plaid_item_id'),
        table_name='linked_accounts',
    )
    op.create_index(
        op.f('ix_linked_accounts_plaid_item_id'),
        'linked_accounts',
        ['plaid_item_id'],
        unique=False,
    )

    # Each individual Plaid account gets its own globally-unique account_id.
    op.add_column(
        'linked_accounts',
        sa.Column('plaid_account_id', sa.String(length=255), nullable=True),
    )
    op.create_index(
        op.f('ix_linked_accounts_plaid_account_id'),
        'linked_accounts',
        ['plaid_account_id'],
        unique=True,
    )

    # Every user currently goes through /auth/register, which always sets
    # a hashed password.
    op.alter_column(
        'users',
        'hashed_password',
        existing_type=sa.String(length=255),
        nullable=False,
    )

    # created_at shouldn't move on update; give transfer_rules a real
    # updated_at column instead.
    op.add_column(
        'transfer_rules',
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('now()'),
        ),
    )
    op.alter_column('transfer_rules', 'updated_at', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('transfer_rules', 'updated_at')

    op.alter_column(
        'users',
        'hashed_password',
        existing_type=sa.String(length=255),
        nullable=True,
    )

    op.drop_index(
        op.f('ix_linked_accounts_plaid_account_id'),
        table_name='linked_accounts',
    )
    op.drop_column('linked_accounts', 'plaid_account_id')

    op.drop_index(
        op.f('ix_linked_accounts_plaid_item_id'),
        table_name='linked_accounts',
    )
    op.create_index(
        op.f('ix_linked_accounts_plaid_item_id'),
        'linked_accounts',
        ['plaid_item_id'],
        unique=True,
    )

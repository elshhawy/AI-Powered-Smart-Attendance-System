# migrations/versions/d4e5f6a7b8c9_add_org_id_to_users.py
"""add organization_id to users

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-16 00:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('organization_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'users_organization_id_fkey',
        'users', 'organizations',
        ['organization_id'], ['id'],
        ondelete='SET NULL',
    )
    op.create_index(
        op.f('ix_users_organization_id'),
        'users', ['organization_id'], unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_users_organization_id'), table_name='users')
    op.drop_constraint('users_organization_id_fkey', 'users', type_='foreignkey')
    op.drop_column('users', 'organization_id')
"""add cascade delete to attendance student_id

Revision ID: a1b2c3d4e5f6
Revises: d6a0fb05a3e2
Create Date: 2026-04-04 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'd6a0fb05a3e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the old FK constraint (without CASCADE)
    op.drop_constraint(
        'attendance_student_id_fkey',
        'attendance',
        type_='foreignkey'
    )
    # Re-create it with ON DELETE CASCADE
    op.create_foreign_key(
        'attendance_student_id_fkey',
        'attendance', 'students',
        ['student_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    op.drop_constraint(
        'attendance_student_id_fkey',
        'attendance',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'attendance_student_id_fkey',
        'attendance', 'students',
        ['student_id'], ['id'],
    )
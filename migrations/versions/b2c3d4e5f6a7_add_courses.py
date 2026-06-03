"""add courses and course_sessions tables

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Create courses table ──────────────────────────────────
    op.create_table(
        'courses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_courses_id'), 'courses', ['id'], unique=False)
    op.create_index(op.f('ix_courses_organization_id'), 'courses', ['organization_id'], unique=False)

    # ── Create course_sessions table ──────────────────────────
    op.create_table(
        'course_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('session_type', sa.String(length=50), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('late_after_minutes', sa.Integer(), nullable=False, server_default='15'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_course_sessions_id'), 'course_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_course_sessions_course_id'), 'course_sessions', ['course_id'], unique=False)

    # ── Add course_session_id to attendance ───────────────────
    op.add_column(
        'attendance',
        sa.Column('course_session_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'attendance_course_session_id_fkey',
        'attendance', 'course_sessions',
        ['course_session_id'], ['id'],
        ondelete='SET NULL',
    )
    op.create_index(
        op.f('ix_attendance_course_session_id'),
        'attendance', ['course_session_id'], unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_attendance_course_session_id'), table_name='attendance')
    op.drop_constraint('attendance_course_session_id_fkey', 'attendance', type_='foreignkey')
    op.drop_column('attendance', 'course_session_id')

    op.drop_index(op.f('ix_course_sessions_course_id'), table_name='course_sessions')
    op.drop_index(op.f('ix_course_sessions_id'), table_name='course_sessions')
    op.drop_table('course_sessions')

    op.drop_index(op.f('ix_courses_organization_id'), table_name='courses')
    op.drop_index(op.f('ix_courses_id'), table_name='courses')
    op.drop_table('courses')
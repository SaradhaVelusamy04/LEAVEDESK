"""create leave and wfh tables

Revision ID: 0002_leave_wfh
Revises: 0001_users
Create Date: 2026-11-18 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_leave_wfh'
down_revision: Union[str, None] = '0001_users'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. leave_requests table
    op.create_table(
        'leave_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('leave_type', sa.String(length=20), nullable=False),
        sa.Column('duration_type', sa.String(length=20), nullable=False),
        sa.Column('half', sa.String(length=20), nullable=True),
        sa.Column('hours', sa.Integer(), nullable=True),
        sa.Column('days_counted', sa.Float(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('decided_by', sa.Integer(), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decision_comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['decided_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_leave_requests_id'), 'leave_requests', ['id'], unique=False)
    op.create_index(op.f('ix_leave_requests_user_id'), 'leave_requests', ['user_id'], unique=False)
    op.create_index(op.f('ix_leave_requests_date'), 'leave_requests', ['date'], unique=False)
    op.create_index(op.f('ix_leave_requests_status'), 'leave_requests', ['status'], unique=False)

    # 2. wfh_requests table
    op.create_table(
        'wfh_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('working_days_count', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('decided_by', sa.Integer(), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decision_comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['decided_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wfh_requests_id'), 'wfh_requests', ['id'], unique=False)
    op.create_index(op.f('ix_wfh_requests_user_id'), 'wfh_requests', ['user_id'], unique=False)
    op.create_index(op.f('ix_wfh_requests_start_date'), 'wfh_requests', ['start_date'], unique=False)
    op.create_index(op.f('ix_wfh_requests_end_date'), 'wfh_requests', ['end_date'], unique=False)
    op.create_index(op.f('ix_wfh_requests_status'), 'wfh_requests', ['status'], unique=False)


def downgrade() -> None:
    op.drop_table('wfh_requests')
    op.drop_table('leave_requests')

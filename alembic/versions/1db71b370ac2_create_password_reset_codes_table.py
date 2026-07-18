"""create password_reset_codes table

Revision ID: 1db71b370ac2
Revises: 19520b00c582
Create Date: 2026-07-18 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1db71b370ac2'
down_revision: Union[str, Sequence[str], None] = '19520b00c582'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('password_reset_codes',
    sa.Column('uuid', sa.Uuid(), nullable=False),
    sa.Column('user_uuid', sa.Uuid(), nullable=False),
    sa.Column('code', sa.String(length=6), nullable=False),
    sa.Column('attempts_used', sa.Integer(), nullable=False),
    sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_uuid'], ['users.uuid']),
    sa.PrimaryKeyConstraint('uuid')
    )
    op.create_index(
        op.f('ix_password_reset_codes_user_uuid'),
        'password_reset_codes',
        ['user_uuid'],
    )
    op.create_index(
        op.f('ix_password_reset_codes_code'), 'password_reset_codes', ['code']
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f('ix_password_reset_codes_code'), table_name='password_reset_codes'
    )
    op.drop_index(
        op.f('ix_password_reset_codes_user_uuid'), table_name='password_reset_codes'
    )
    op.drop_table('password_reset_codes')

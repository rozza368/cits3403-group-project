"""Made email unique and non-nullable in User

Revision ID: 81174eeaf49d
Revises: cbe995dcf42c
Create Date: 2025-05-16 15:56:06.728348

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '81174eeaf49d'
down_revision = 'cbe995dcf42c'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('email',
               existing_type=sa.VARCHAR(length=120),
               nullable=False)
        batch_op.create_unique_constraint('uq_users_email', ['email'])


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('uq_users_email', type_='unique')
        batch_op.alter_column('email',
               existing_type=sa.VARCHAR(length=120),
               nullable=True)

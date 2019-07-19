"""add box end timestamp

Revision ID: 24da70e9c2c2
Revises: 3f63f2913228
Create Date: 2019-07-16 08:53:20.382985

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.types import TIMESTAMP

# revision identifiers, used by Alembic.
revision = '24da70e9c2c2'
down_revision = '3f63f2913228'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("box", sa.Column("session_end_time", TIMESTAMP, nullable=True))
    pass


def downgrade():
    op.drop_column("box", "session_end_time")
    pass

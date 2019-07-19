"""baseline

Revision ID: c8493c83258e
Revises: 
Create Date: 2018-09-05 15:53:19.622321

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c8493c83258e"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # docker exec userland_db_1 createdb -U postgres userland_development
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=64), nullable=True),
        sa.Column("password_hash", sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)
    op.create_table(
        "config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("reserved", sa.BOOLEAN, nullable=False),
        sa.Column("in_use", sa.BOOLEAN, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_config_name"), "config", ["name"], unique=True)
    op.create_table(
        "box",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("box_server", sa.String(length=64), nullable=False),
        sa.Column("box_ssh_port", sa.Integer(), nullable=False),
        sa.Column("box_connection_port", sa.Integer(), nullable=False),
        sa.Column("config_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("config_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["config_id"], ["config.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_box_id"), "box", ["id"], unique=True)
    pass


def downgrade():
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")
    op.drop_index(op.f("ix_box_id"), table_name="box")
    op.drop_table("box")
    op.drop_index(op.f("ix_config_name"), table_name="config")
    op.drop_table("config")
    pass

"""baseline

Revision ID: c8493c83258e
Revises: 
Create Date: 2018-09-05 15:53:19.622321

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

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
        sa.Column("confirmed", sa.Boolean(), nullable=True),
        sa.Column("email", sa.String(length=64), nullable=True),
        sa.Column("password_hash", sa.String(length=128), nullable=True),
        sa.Column("uuid", UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("plan_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)
    op.create_table(
        "config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_config_name"), "config", ["name"], unique=True)
    op.create_table(
        "box",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("config_id", sa.Integer(), nullable=True),
        sa.Column("ssh_port", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(length=64), nullable=True),
        sa.Column("ip_address", sa.String(length=32)),
        sa.Column("session_end_time", sa.types.TIMESTAMP, nullable=True),
        sa.ForeignKeyConstraint(["config_id"], ["config.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_box_id"), "box", ["id"], unique=True)

    op.create_table(
        "plan",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("box_count", sa.Integer(), nullable=True),
        sa.Column("bandwidth", sa.Integer(), nullable=True),
        sa.Column("forwards", sa.Integer(), nullable=True),
        sa.Column("reserved_config", sa.Integer(), nullable=True),
        sa.Column("cost", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("stripe_id", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_plan_name"), "plan", ["name"], unique=True)
    op.create_index(op.f("ix_plan_stripe_id"), "plan", ["stripe_id"], unique=True)
    op.create_foreign_key("user_plan_fk", "user", "plan", ["plan_id"], ["id"])
    pass


def downgrade():
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")
    op.drop_index(op.f("ix_box_id"), table_name="box")
    op.drop_table("box")
    op.drop_index(op.f("ix_config_name"), table_name="config")
    op.drop_table("config")
    op.drop_index(op.f("ix_plan_name"), "plan", ["name"], unique=True)
    op.drop_index(op.f("ix_plan_stripe_id"), "plan", ["stripe_id"], unique=True)
    op.drop_table("plan")
    op.drop_foreign_key("user_plan_fk", "user", "plan", ["plan_id"], ["id"])
    pass

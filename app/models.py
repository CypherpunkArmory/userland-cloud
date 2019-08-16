from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import types, DateTime
from werkzeug import check_password_hash, generate_password_hash
from app import db
from sqlalchemy.dialects.postgresql import UUID
from typing import NamedTuple


class UserLimit(NamedTuple):
    box_count: int
    bandwidth: int
    time_limit: int
    forwards: int
    reserved_config: int


class Config(db.Model):  # type: ignore
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", back_populates="configs", lazy="joined")

    def __repr__(self):
        return "<Config {}>".format(self.name)


class Plan(db.Model):  # type: ignore
    id = db.Column(db.Integer, primary_key=True)
    box_count = db.Column(db.Integer)
    bandwidth = db.Column(db.Integer)
    forwards = db.Column(db.Integer)
    reserved_config = db.Column(db.Integer)
    cost = db.Column(db.Integer)
    name = db.Column(db.String, index=True, nullable=False, unique=True)
    stripe_id = db.Column(db.String, index=True, unique=True)
    users = db.relationship("User")

    @staticmethod
    def paid():
        return Plan.query.filter_by(name="paid").first()

    @staticmethod
    def free():
        return Plan.query.filter_by(name="free").first()

    @staticmethod
    def beta():
        return Plan.query.filter_by(name="beta").first()

    @staticmethod
    def waiting():
        return Plan.query.filter_by(name="waiting").first()

    def __repr__(self):
        return "<Plan {}>".format(self.name)

    def limits(self):
        return UserLimit(
            box_count=self.box_count,
            bandwidth=self.bandwidth,
            time_limit=1800,
            forwards=self.forwards,
            reserved_config=self.reserved_config,
        )


class User(db.Model):  # type: ignore
    id = db.Column(db.Integer, primary_key=True)
    confirmed = db.Column(db.Boolean)
    email = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    uuid = db.Column(UUID(as_uuid=True), nullable=False, unique=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("plan.id", name="user_plan_fk"))
    configs = db.relationship(
        "Config", back_populates="user", lazy="dynamic", cascade="all, delete"
    )
    boxes = db.relationship("Box", secondary="config", lazy="dynamic")
    plan = db.relationship("Plan", lazy="joined")

    def __repr__(self):
        return "<User {}>".format(self.email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def limits(self):
        return self.plan.limits()

    @property
    def tier(self):
        return self.plan.name


class Box(db.Model):  # type: ignore
    id = db.Column(db.Integer, primary_key=True)
    config_id = db.Column(db.Integer, db.ForeignKey("config.id"))
    ssh_port = db.Column(db.Integer)
    job_id = db.Column(db.String(64))
    ip_address = db.Column(db.String(32))
    config = db.relationship("Config", backref="box", lazy="joined")
    session_end_time = db.Column(DateTime())

    user = association_proxy("config", "user")

    def __repr__(self):
        return "<Box {} {}>".format(self.config, self.job_id)

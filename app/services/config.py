from app import db
from app.models import Config
from app.utils.errors import ConfigTaken

config_reserved_limits = {"free": 0, "paid": 5, "beta": 5}


class ConfigCreationService:
    def __init__(self, current_user, config_name=""):
        self.current_user = current_user
        self.config_name = config_name

    def create(self):
        config_exist = (
            db.session.query(Config.name).filter_by(name=self.config_name).scalar()
        )

        if config_exist:
            raise ConfigTaken("Requested Config is already reserved")

        config = Config(user_id=self.current_user.id, name=self.config_name)

        db.session.add(config)
        db.session.flush()

        return config


class ConfigDeletionService:
    def __init__(self, current_user, config):
        self.current_user = current_user
        self.config = config

    def release(self) -> None:

        db.session.delete(self.config)
        db.session.flush()

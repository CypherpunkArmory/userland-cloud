from app import db, momblish
from app.models import Config
from app.utils.errors import ConfigTaken, ConfigInUse, ConfigLimitReached

config_reserved_limits = {"free": 0, "paid": 5, "beta": 5}


class ConfigCreationService:
    def __init__(self, current_user, config_name=""):
        self.current_user = current_user
        self.config_name = config_name

    def over_config_limits(self):
        num_reserved_config = self.current_user.configs.filter_by(
            reserved=True
        ).count()
        if num_reserved_config >= self.current_user.limits().reserved_config:
            return True
        return False

    def get_unused_config(self):
        while True:
            self.config_name = momblish.word(10).lower()
            try:
                config = self.reserve(reserve=False)
                break
            except ConfigTaken:
                continue
        return config

    def reserve(self, reserve=True):
        if reserve:
            if self.over_config_limits():
                raise ConfigLimitReached(
                    "Maximum number of reserved configs reached"
                )
        config_exist = (
            db.session.query(Config.name)
            .filter_by(name=self.config_name)
            .scalar()
        )

        if config_exist:
            raise ConfigTaken("Requested Config is already reserved")

        config = Config(
            user_id=self.current_user.id,
            name=self.config_name,
            reserved=reserve,
            in_use=False,
        )

        db.session.add(config)
        db.session.flush()

        return config


class ConfigDeletionService:
    def __init__(self, current_user, config):
        self.current_user = current_user
        self.config = config

    def release(self) -> None:
        if self.config.in_use:
            raise ConfigInUse("Config is in use")
        db.session.delete(self.config)
        db.session.flush()

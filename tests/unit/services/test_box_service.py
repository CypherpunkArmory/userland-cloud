import pytest

from app.services.box import BoxCreationService
from app.models import UserLimit
from app.utils.errors import BoxLimitReached
from tests.factories.config import ConfigFactory
from unittest.mock import patch


class TestBoxCreationService(object):
    """Box creation service has correct business logic"""

    def test_create_box_user(self, current_free_user, session):
        """ Raises an exception when too many open boxes"""

        zero_limit = UserLimit(
            box_count=0, bandwidth=0, forwards=0, reserved_config=0
        )
        conf = ConfigFactory(user=current_free_user)
        session.add(conf)

        with patch.object(current_free_user, "limits", return_value=zero_limit):
            with pytest.raises(BoxLimitReached):
                BoxCreationService(
                    current_user=current_free_user,
                    config_id=conf.id,
                    port_type=["http"],
                    ssh_key="",
                ).create()

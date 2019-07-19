import pytest

from app.services.config import ConfigCreationService


class TestConfigCreationService(object):
    """Config creation service has correct business logic"""

    def test_create_reserve_config(self, current_free_user, current_user):
        """ Raises an exception when too many reserved configs"""
        with pytest.raises(Exception):
            ConfigCreationService(current_free_user, "subsub").reserve(True)
        for x in range(0, 5):
            ConfigCreationService(current_user, "subsub" + str(x)).reserve(True)
        with pytest.raises(Exception):
            ConfigCreationService(current_user, "subconf10").reserve(True)

    def test_create_unreserved_config(self, current_free_user, current_user):
        """ Does not raise an exception creating an unreserved config"""
        for x in range(0, 10):
            ConfigCreationService(current_free_user, "free" + str(x)).reserve(False)
        for x in range(0, 10):
            ConfigCreationService(current_user, "paid" + str(x)).reserve(False)
        # make sure unreserved configs were not counted
        ConfigCreationService(current_user, "subsub-paid-reserved").reserve(True)

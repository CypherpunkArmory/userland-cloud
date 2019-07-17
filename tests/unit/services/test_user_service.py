from tests.factories.user import UserFactory
from app.models import UserLimit


class TestUserLimits(object):
    """ Ensure user limits are reported correctly """

    def test_user_can_report_limts(self, session):
        user = UserFactory(email="user@gmail.com")
        session.add(user)
        session.flush()

        assert user.limits() == UserLimit(
            box_count=5, bandwidth=100000, forwards=9999, reserved_config=5
        )

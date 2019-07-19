from factory import Factory, SubFactory, fuzzy
from faker import Faker as RealFaker
from pytest_factoryboy import register

from app.models import Config
from tests.factories.user import UserFactory

fake = RealFaker()


@register
class ConfigFactory(Factory):
    class Meta:
        model = Config

    user = SubFactory(UserFactory)
    name = fuzzy.FuzzyText()
    id = fuzzy.FuzzyInteger(1, 213)

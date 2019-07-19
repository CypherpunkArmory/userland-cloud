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
    in_use = False
    reserved = False
    name = fuzzy.FuzzyText()
    id = fuzzy.FuzzyInteger(1, 213)


@register
class ReservedConfigFactory(ConfigFactory):
    reserved = True


@register
class InuseConfigFactory(ConfigFactory):
    in_use = True


@register
class InuseReservedConfigFactory(ConfigFactory):
    in_use = True
    reserved = True


@register
class InuseUnreservedConfigFactory(ConfigFactory):
    in_use = True
    reserved = False

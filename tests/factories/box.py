from random import randint

from faker import Faker as RealFaker

from app.models import Box
from factory import Factory, SubFactory
from pytest_factoryboy import register
from tests.factories.config import ConfigFactory

fake = RealFaker()


@register
class BoxFactory(Factory):
    class Meta:
        model = Box

    config = SubFactory(ConfigFactory)
    port = ["http"]
    ssh_port = randint(1000, 32678)
    job_id = f"ssh/dispatch-{randint(1000,3678)}"


@register
class HttpsBoxFactory(BoxFactory):
    port = ["https"]

from app.models import Config
from tests.factories import config, user
from tests.support.assertions import assert_valid_schema
from dpath.util import values
import json


class TestConfig(object):
    """Logged in Users can manage their configs"""

    def test_empty_config_index(self, client):
        """User can list all of their configs when empty"""
        res = client.get("/configs")
        assert_valid_schema(res.get_json(), "configs.json")

    def test_config_index(self, client, current_user):
        """User can list all of their configs"""

        conf = config.ConfigFactory.create(user=current_user)
        res3 = client.get("/configs")
        assert_valid_schema(res3.get_json(), "configs.json")
        assert str(conf.id) in values(res3.get_json(), "data/*/id")

    def test_config_get(self, client, current_user):
        """User can get a single config"""

        conf = config.ConfigFactory.create(user=current_user)
        res3 = client.get(f"/configs/{conf.id}")
        assert_valid_schema(res3.get_json(), "config.json")
        assert str(conf.id) in values(res3.get_json(), "data/id")

    def test_config_reserve(self, client, current_user):
        """User can reserve a config"""

        pre_config_count = Config.query.filter_by(user_id=current_user.id).count()

        res = client.post(
            "/configs",
            json={"data": {"type": "config", "attributes": {"name": "test"}}},
        )

        post_config_count = Config.query.filter_by(
            user_id=current_user.id
        ).count()

        assert_valid_schema(res.get_data(), "config.json")
        assert post_config_count > pre_config_count

    def test_config_reserve_owned(self, client, current_user, session):
        """User cant reserve an already reserved config"""

        conf = config.ReservedConfigFactory(name="substation")
        session.add(conf)
        session.flush()

        res = client.post(
            "/configs",
            json={"data": {"type": "config", "attributes": {"name": "substation"}}},
        )

        assert res.status_code == 400
        assert (
            res.json["data"]["attributes"]["detail"]
            == "Config has already been reserved"
        )

    def test_config_reserve_free_tier(self, free_client):
        """User cant reserve a config if they are free tier"""

        res = free_client.post(
            "/configs",
            json={"data": {"type": "config", "attributes": {"name": "test"}}},
        )

        assert res.status_code == 403

    def test_config_reserve_paid_over_limit(self, client, current_user, session):
        """User can't reserve more than 5 configs if they are paid tier"""

        conf1 = config.ReservedConfigFactory(user=current_user, name="sub")
        conf2 = config.ReservedConfigFactory(user=current_user, name="subtract")
        conf3 = config.ReservedConfigFactory(user=current_user, name="subwoofer")
        conf4 = config.ReservedConfigFactory(
            user=current_user, name="subconscious"
        )
        conf5 = config.ReservedConfigFactory(user=current_user, name="subreddit")
        session.add(conf1)
        session.add(conf2)
        session.add(conf3)
        session.add(conf4)
        session.add(conf5)
        session.flush()
        res = client.post(
            "/configs",
            json={"data": {"type": "config", "attributes": {"name": "test"}}},
        )

        assert res.status_code == 403

    def test_config_release_owned(self, client, current_user):
        """User can release a config they own"""

        conf = config.ReservedConfigFactory(user=current_user, name="domainiown")
        res = client.delete(f"/configs/{conf.id}")

        assert res.status_code == 204

    def test_config_release_phantom(self, client):
        """User cant release a config that doesn't exist"""

        res = client.delete(f"/configs/5")

        assert res.status_code == 404

    def test_config_release_unowned(self, client, session):
        """User cant release a config is owned by someone else"""

        conf = config.ReservedConfigFactory(name="domainyouown")
        session.add(conf)
        session.flush()

        res = client.delete(f"/configs/{conf.id}")

        assert res.status_code == 404

    def test_config_release_used(self, client, session, current_user):
        """User cannot release a config is being used"""

        conf = config.InuseConfigFactory(user=current_user, name="scrub")
        session.add(conf)
        session.flush()

        assert conf.in_use is True

        res = client.delete(f"/configs/{conf.id}")
        assert res.status_code == 403
        assert (
            res.json["data"]["attributes"]["detail"]
            == "Config is associated with a running box"
        )

    def test_config_filter(self, client, session, current_user):
        """Can filter a config using JSON-API compliant filters"""

        conf1 = config.ReservedConfigFactory(user=current_user, name="submarine")
        conf2 = config.ReservedConfigFactory(user=current_user, name="sublime")
        session.add(conf1, conf2)
        session.flush()

        res = client.get(f"/configs?filter[name]=submarine")

        assert_valid_schema(res.get_json(), "configs.json")
        assert str(conf1.id) in values(res.get_json(), "data/*/id")
        assert str(conf2.id) not in values(res.get_json(), "data/*/id")

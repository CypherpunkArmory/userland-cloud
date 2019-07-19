import pytest
from dpath.util import values
from nomad.api.exceptions import BaseNomadException
from app.models import Box
from app.services.box import BoxCreationService, BoxDeletionService
from app.utils.errors import BoxError
from tests.factories.user import UserFactory
from tests.factories import config, box
from tests.support.assertions import assert_valid_schema
from unittest import mock


class TestBoxes(object):
    """Logged in Users can manage their boxes"""

    def test_empty_box_index(self, client):
        """Correct response for empty box list"""
        res = client.get("/boxes")
        assert_valid_schema(res.get_json(), "boxes.json")

    def test_box_index(self, client, current_user, session):
        """User can list all of their boxes"""
        test_box = box.BoxFactory(config__user=current_user)
        session.add(test_box)
        session.flush()

        res3 = client.get("/boxes")
        assert_valid_schema(res3.get_json(), "boxes.json")
        assert str(test_box.id) in values(res3.get_json(), "data/*/id")

    def test_get_box(self, client, current_user, session):
        """User can get a single box"""
        test_box = box.BoxFactory(config__user=current_user)
        session.add(test_box)
        session.flush()

        res3 = client.get(f"/boxes/{test_box.id}")
        assert_valid_schema(res3.get_json(), "box.json")
        assert str(test_box.id) in values(res3.get_json(), "data/id")

    def test_get_box_unowned(self, client, current_user, session):
        """User cannot lookup box info that does not belong to them"""
        other_user = UserFactory(email="other_person@gmail.com")
        session.add(other_user)
        session.flush()

        test_box = box.BoxFactory(config__user=other_user)
        session.add(test_box)
        session.flush()

        res = client.get(f"/boxes/{test_box.id}")
        assert res.status_code == 404

    @pytest.mark.vcr()
    def test_box_open_without_config(self, client, current_user, session):
        """User can open a box without providing a config"""

        res = client.post(
            "/boxes",
            json={
                "data": {
                    "type": "box",
                    "attributes": {"sshKey": "i-am-lousy-public-key"},
                }
            },
        )

        assert res.status_code == 201
        assert_valid_schema(res.get_data(), "box.json")
        assert Box.query.filter_by(user=current_user).count() == 1

    @pytest.mark.vcr()
    def test_box_open_with_config(self, client, current_user, session):
        """User can open a box when providing a config they own"""

        conf = config.ConfigFactory(user=current_user)
        session.add(conf)
        session.flush()

        res = client.post(
            "/boxes",
            json={
                "data": {
                    "type": "box",
                    "attributes": {
                        "sshKey": "i-am-a-lousy-public-key",
                    },
                    "relationships": {
                        "config": {"data": {"type": "config", "id": str(conf.id)}}
                    },
                }
            },
        )

        assert res.status_code == 201
        assert len(values(res.get_json(), "data/id")) == 1
        assert_valid_schema(res.get_data(), "box.json")
        assert Box.query.filter_by(user=current_user).count() == 1

    def test_box_open_unowned_config(self, client, current_user, session):
        """User can not open a box if they dont own the config"""

        conf = config.ConfigFactory()
        session.add(conf)
        session.flush()

        res = client.post(
            "/boxes",
            json={
                "data": {
                    "type": "box",
                    "attributes": {"sshKey": "i-am-a-lousy-key"},
                    "relationships": {
                        "config": {"data": {"type": "config", "id": str(conf.id)}}
                    },
                }
            },
        )

        assert res.status_code == 403
        assert Box.query.filter_by(user=current_user).count() == 0

    @pytest.mark.vcr()
    def test_box_close_owned(self, client, session, current_user):
        """User can close a box"""

        conf = config.ConfigFactory(user=current_user)
        session.add(conf)
        session.flush()
        test_box = BoxCreationService(
            current_user, conf.id, "i-am-a-lousy-key"
        ).create()
        session.add(test_box)
        session.flush()

        res = client.delete("/boxes/" + str(test_box.id))
        assert res.status_code == 204

    def test_box_close_unowned(self, client):
        """User cant close a box they do not own"""

        # I mean hopefully we're not making 239M configs in the test run
        res = client.delete("/box/239402934")

        assert res.status_code == 404

    def test_box_filter_by_config_name(self, client, session, current_user):
        """Can filter a config using JSON-API compliant filters"""

        conf1 = config.ConfigFactory(
            user=current_user, name="sub-sandwich"
        )
        conf2 = config.ConfigFactory(
            user=current_user, name="subscription"
        )

        test_box1 = box.BoxFactory(config=conf1)
        test_box2 = box.BoxFactory(config=conf2)

        session.add(test_box1, test_box2)
        session.flush()

        res = client.get(f"/boxes?filter[config][name]=sub-sandwich")

        assert_valid_schema(res.get_json(), "boxes.json")
        assert str(test_box1.id) in values(res.get_json(), "data/*/id")
        assert str(test_box2.id) not in values(res.get_json(), "data/*/id")


class TestFailedBoxes(object):
    @mock.patch.object(
        BoxCreationService, "create_box_nomad", return_value=[1, []]
    )
    @mock.patch.object(
        BoxCreationService,
        "get_box_details",
        side_effect=BoxError(detail="Error"),
        autospec=True,
    )
    @mock.patch.object(BoxDeletionService, "delete")
    def test_box_delete_on_fail_deploy(
        self,
        mock_del_box,
        mock_box_details,
        mock_create_box,
        client,
        current_user,
    ):
        """Box delete is called when provisioning it fails"""
        res = client.post(
            "/boxes",
            json={
                "data": {
                    "type": "box",
                    "attributes": {"sshKey": "i-am-lousy-public-key"},
                }
            },
        )

        assert res.status_code == 500, res.get_json()
        assert mock_box_details.called
        assert mock_del_box.called

    @mock.patch.object(
        BoxCreationService,
        "create_box_nomad",
        side_effect=BoxError(detail="Error"),
        autospec=True,
    )
    @mock.patch.object(BoxCreationService, "get_box_details")
    @mock.patch.object(BoxDeletionService, "delete")
    @mock.patch("app.services.box.cleanup_old_nomad_box.queue")
    def test_box_not_delete_on_start_up_fail(
        self,
        mock_del_box_job,
        mock_del_box_from_db,
        mock_get_box_details,
        mock_create_box,
        client,
        current_user,
    ):
        """Box delete is not called when provisioning it fails"""
        res = client.post(
            "/boxes",
            json={
                "data": {
                    "type": "box",
                    "attributes": {"sshKey": "i-am-lousy-public-key"},
                }
            },
        )

        assert res.status_code == 500
        assert mock_create_box.called
        assert not mock_get_box_details.called
        assert not mock_del_box_from_db.called
        assert not mock_del_box_job.called

    @mock.patch.object(
        BoxCreationService, "create_box_nomad", return_value=("1", [])
    )
    @mock.patch.object(
        BoxCreationService,
        "get_box_details",
        side_effect=BoxError(detail="Error"),
        autospec=True,
    )
    @mock.patch.object(BoxDeletionService, "delete")
    @mock.patch("app.services.box.cleanup_old_nomad_box.queue")
    def test_box_delete_on_fail_deploy(
        self,
        mock_del_box_job,
        mock_del_box_from_db,
        mock_get_box_details,
        mock_create_box,
        client,
        current_user,
    ):
        """Box delete is called when provisioning it fails"""
        res = client.post(
            "/boxes",
            json={
                "data": {
                    "type": "box",
                    "attributes": {"sshKey": "i-am-lousy-public-key"},
                }
            },
        )

        assert res.status_code == 500, res.get_json()
        assert mock_get_box_details.called
        assert not mock_del_box_from_db.called
        assert mock_del_box_job.called

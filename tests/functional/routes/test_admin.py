from tests.factories import config
from app.services.box import BoxCreationService
import pytest


class TestAdmin(object):
    """Logged in Users can manage their tunnels"""

    def test_non_admin_404(self, client):
        """Correct response for empty tunnel list"""
        res = client.post("/admin/configs")
        assert res.status_code == 404

    @pytest.mark.vcr()
    def test_box_admin(self, admin_client, current_user, session):
        """Admin can delete a user's tunnel"""
        sub = config.ConfigFactory(
            id=2000, user=current_user, name="testtunnelsubdomain"
        )
        session.add(sub)
        session.flush()
        tun = BoxCreationService(current_user, sub.id, "i-am-a-lousy-key").create()
        session.add(tun)
        session.flush()

        res = admin_client.post(
            "/admin/boxes",
            json={
                "data": {
                    "type": "tunnel",
                    "attributes": {
                        "config_name": "testtunnelsubdomain",
                        "reason": "testing",
                    },
                }
            },
        )
        assert res.status_code == 204

"""
Provides CRUD operations for Tunnel Resources
"""

from flask import Blueprint, request, Response, make_response
from flask_jwt_extended import get_jwt_identity, jwt_required
from app import json_schema_manager, logger
from app.models import Box, User, Config
from app.serializers import ErrorSchema
from app.services.box import BoxDeletionService
from app.utils.errors import NotFoundError, BoxError, BadRequest
from app.utils.json import dig, json_api
from typing import Tuple
from jsonschema import ValidationError

admin_blueprint = Blueprint("admin", __name__)


@admin_blueprint.route("/admin/boxes", methods=["POST"])
@jwt_required
def tunnel_admin() -> Tuple[Response, int]:
    """
    Stop any currently running tunnel if you are an admin
    """
    current_user = User.query.filter_by(uuid=get_jwt_identity()).first_or_404()
    if current_user.tier != "admin":
        return json_api(NotFoundError, ErrorSchema), 404

    try:
        json_schema_manager.validate(request.json, "admin_tunnel.json")

        config_name = dig(request.json, "data/attributes/config_name")
        reason = dig(request.json, "data/attributes/reason")
    except ValidationError as e:
        return json_api(BadRequest(source=e.message), ErrorSchema), 400

    config = Config.query.filter_by(name=config_name).first_or_404()
    tunnel = Box.query.filter_by(config_id=config.id).first_or_404()
    try:
        BoxDeletionService(current_user, tunnel).delete()
        logger.info(
            "%s deleted Userland Cloud Box %s for reason %s",
            current_user.email,
            config_name,
            reason,
        )
        return make_response(""), 204
    except BoxError:
        return json_api(BoxError, ErrorSchema), 500

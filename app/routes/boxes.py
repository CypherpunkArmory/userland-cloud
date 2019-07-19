"""
Provides CRUD operations for Box Resources
"""

from flask import Blueprint, request, Response, make_response
from flask_jwt_extended import get_jwt_identity, jwt_required
from jsonschema import ValidationError
from sqlalchemy.orm.exc import NoResultFound

from app import json_schema_manager
from app.models import Box, User, Config
from app.serializers import ErrorSchema, BoxSchema
from app.services.box import BoxCreationService, BoxDeletionService
from app.utils.errors import (
    BadRequest,
    NotFoundError,
    AccessDenied,
    ConfigInUse,
    ConfigLimitReached,
    BoxError,
    BoxLimitReached,
)
from app.utils.json import dig, json_api
from typing import Tuple

import rollbar
import sys


box_blueprint = Blueprint("box", __name__)


@box_blueprint.route("/boxes", methods=["GET"])
@jwt_required
def box_index() -> Tuple[Response, int]:
    """
    Fetch index of a users current boxes
    """
    boxes = User.query.filter_by(uuid=get_jwt_identity()).first_or_404().boxes

    name = dig(request.query_params, "filter/config/name")
    if name:
        boxes = boxes.join(Config).filter(Config.name == name)

    return json_api(boxes, BoxSchema, many=True), 200


@box_blueprint.route("/boxes", methods=["POST"])
@jwt_required
def start_box() -> Tuple[Response, int]:
    try:
        json_schema_manager.validate(request.json, "box_create.json")

        config_id = dig(request.json, "data/relationships/config/data/id")
        ssh_key = dig(request.json, "data/attributes/sshKey")

        current_user = User.query.filter_by(uuid=get_jwt_identity()).first_or_404()
        try:
            box_info = BoxCreationService(
                current_user, config_id, ssh_key
            ).create()
        except ConfigLimitReached:
            return json_api(ConfigLimitReached, ErrorSchema), 403
        except BoxLimitReached:
            return json_api(BoxLimitReached, ErrorSchema), 403
        except BoxError:
            rollbar.report_exc_info(sys.exc_info())
            return json_api(BoxError, ErrorSchema), 500

        return json_api(box_info, BoxSchema), 201

    except ValidationError as e:
        return json_api(BadRequest(detail=e.message), ErrorSchema), 400

    except AccessDenied:
        return json_api(AccessDenied, ErrorSchema), 403

    except ConfigInUse:
        return json_api(ConfigInUse, ErrorSchema), 403


@box_blueprint.route("/boxes/<int:box_id>", methods=["DELETE"])
@jwt_required
def stop_box(box_id) -> Tuple[Response, int]:
    """
    Stop a currently running box
    """
    current_user = User.query.filter_by(uuid=get_jwt_identity()).first_or_404()
    box = Box.query.filter_by(user=current_user, id=box_id).first_or_404()

    try:
        BoxDeletionService(current_user, box).delete()
        return make_response(""), 204
    except BoxError:
        return json_api(BoxError, ErrorSchema), 500


@box_blueprint.route("/boxes/<int:box_id>", methods=["GET"])
@jwt_required
def get_box(box_id) -> Tuple[Response, int]:
    """
    Retrieve Box Resource
    """
    current_user = User.query.filter_by(uuid=get_jwt_identity()).first_or_404()
    box = Box.query.filter_by(user=current_user, id=box_id).first_or_404()

    return json_api(box, BoxSchema), 200

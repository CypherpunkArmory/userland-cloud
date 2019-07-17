from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from jsonschema import ValidationError

from app import json_schema_manager
from app.models import Config, User
from app.serializers import ErrorSchema, ConfigSchema
from app.services.config import ConfigCreationService, ConfigDeletionService
from app.utils.errors import (
    AccessDenied,
    BadRequest,
    ConfigError,
    ConfigTaken,
    ConfigInUse,
    ConfigLimitReached,
)
from app.utils.json import dig, json_api

config_blueprint = Blueprint("config", __name__)


@config_blueprint.route("/configs", methods=["GET"])
@jwt_required
def config_index():
    configs = User.query.filter_by(uuid=get_jwt_identity()).first_or_404().configs

    name = dig(request.query_params, "filter/name")
    if name:
        configs = configs.filter_by(name=name)

    if configs:
        return json_api(configs, ConfigSchema, many=True)


@config_blueprint.route("/configs", methods=["POST"])
@jwt_required
def config_reserve():
    try:
        json_schema_manager.validate(request.json, "config_create.json")
        current_user = User.query.filter_by(uuid=get_jwt_identity()).first_or_404()
        config = ConfigCreationService(
            current_user, dig(request.json, "data/attributes/name")
        ).reserve(True)

        return json_api(config, ConfigSchema), 200
    except ValidationError:
        return (
            json_api(BadRequest(detail="Request does not match schema."), ErrorSchema),
            400,
        )
    except ConfigLimitReached:
        return json_api(ConfigLimitReached, ErrorSchema), 403
    except ConfigTaken:
        return json_api(ConfigTaken, ErrorSchema), 400
    except ConfigError:
        return json_api(ConfigError, ErrorSchema), 500


@config_blueprint.route("/configs/<int:config_id>", methods=["DELETE"])
@jwt_required
def config_release(config_id):
    current_user = User.query.filter_by(uuid=get_jwt_identity()).first_or_404()
    config = Config.query.filter_by(
        user=current_user, id=config_id
    ).first_or_404()

    try:
        ConfigDeletionService(current_user, config).release()
        return "", 204
    except AccessDenied:
        return json_api(BadRequest, ErrorSchema), 403
    except ConfigInUse:
        return json_api(ConfigInUse, ErrorSchema), 403


@config_blueprint.route("/configs/<int:config_id>", methods=["GET"])
@jwt_required
def get_config(config_id):
    """
    Stop a currently running config
    """
    current_user = User.query.filter_by(uuid=get_jwt_identity()).first_or_404()
    config = Config.query.filter_by(
        user=current_user, id=config_id
    ).first_or_404()

    return json_api(config, ConfigSchema)

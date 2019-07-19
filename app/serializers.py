from marshmallow_jsonapi import Schema, fields
from functools import partial
import inflection

drinkingCamel = partial(inflection.camelize, uppercase_first_letter=False)


class BoxSchema(Schema):
    class Meta:
        type_ = "box"
        strict = True
        inflect = drinkingCamel

    id = fields.Str()
    port = fields.List(fields.Str())
    ssh_port = fields.Str()
    ip_address = fields.Str()

    config = fields.Relationship(
        "/configs/{config_id}",
        related_url_kwargs={"config_id": "<config_id>"},
        include_resource_linkage=True,
        type_="config",
    )


class ConfigSchema(Schema):
    class Meta:
        type_ = "config"
        strict = True
        inflect = drinkingCamel

    id = fields.Str()
    name = fields.Str()


class UserSchema(Schema):
    class Meta:
        type_ = "user"
        strict = True
        inflect = drinkingCamel

    id = fields.Str()
    email = fields.Str()
    tier = fields.Str()
    confirmed = fields.Boolean()


class ErrorSchema(Schema):
    class Meta:
        type_ = "error"
        strict = True
        inflect = drinkingCamel

    id = fields.Str()
    status = fields.Str()
    title = fields.Str()
    detail = fields.Str()
    source = fields.Str()
    code = fields.Str()
    backtrace = fields.List(fields.Str())

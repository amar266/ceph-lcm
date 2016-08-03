# -*- coding: utf-8 -*-
"""This module contains view for /v1/role API."""


import six

from cephlcm.api import auth
from cephlcm.api import exceptions as http_exceptions
from cephlcm.api import validators
from cephlcm.api.views import generic
from cephlcm.common import exceptions as base_exceptions
from cephlcm.common import log
from cephlcm.common.models import role


DATA_SCHEMA = {
    "name": {"$ref": "#/definitions/non_empty_string"},
    "permissions": {
        "type": "object",
        "additionalProperties": {
            "type": "array",
            "items": {"$ref": "#/definitions/non_empty_string"}
        }
    }
}
"""Schema for the payload."""

MODEL_SCHEMA = validators.create_model_schema("role", DATA_SCHEMA)
"""Schema for the model with optional data fields."""

POST_SCHEMA = validators.create_data_schema(DATA_SCHEMA, True)
"""Schema for the new model request."""

LOG = log.getLogger(__name__)
"""Logger."""


class RoleView(generic.VersionedCRUDView):
    """Implementation of view for /v1/role API."""

    decorators = [
        auth.require_authorization("api", "view_role"),
        auth.require_authentication
    ]

    NAME = "role"
    MODEL_NAME = "role"
    ENDPOINT = "/role/"
    PARAMETER_TYPE = "uuid"

    def get_all(self):
        return role.RoleModel.list_models(self.pagination)

    @validators.with_model(role.RoleModel)
    def get_item(self, item_id, item, *args):
        return item

    @auth.require_authorization("api", "view_role_versions")
    def get_versions(self, item_id):
        return role.RoleModel.list_versions(str(item_id), self.pagination)

    @auth.require_authorization("api", "view_role_versions")
    def get_version(self, item_id, version):
        model = role.RoleModel.find_version(str(item_id), int(version))

        if not model:
            LOG.info("Cannot find model with ID %s", item_id)
            raise http_exceptions.NotFound

        return model

    @auth.require_authorization("api", "edit_role")
    @validators.with_model(role.RoleModel)
    @validators.require_schema(MODEL_SCHEMA)
    @validators.no_updates_on_default_fields
    def put(self, item_id, item):
        for key, value in six.iteritems(self.request_json["data"]):
            setattr(item, key, value)
        item.initiator_id = self.initiator_id

        try:
            item.save()
        except base_exceptions.CannotUpdateDeletedModel:
            LOG.warning(
                "Cannot update deleted role %s (deleted at %s, "
                "version %s)",
                item_id, item.time_deleted, item.version
            )
            raise http_exceptions.CannotUpdateDeletedModel()
        except ValueError as exc:
            LOG.warning("Incorrect permissions for role %s: %s",
                        item_id, exc)
            raise http_exceptions.BadRequest

        LOG.info("Role %s was updated by %s", item_id, self.initiator_id)

        return item

    @auth.require_authorization("api", "create_role")
    @validators.require_schema(POST_SCHEMA)
    def post(self):
        try:
            role_model = role.RoleModel.make_role(
                self.request_json["name"],
                self.request_json["permissions"],
                initiator_id=self.initiator_id
            )
        except base_exceptions.UniqueConstraintViolationError:
            LOG.warning("Cannot create role %s (unique constraint violation)",
                        self.request_json["name"])
            raise http_exceptions.ImpossibleToCreateSuchModel()
        except ValueError as exc:
            LOG.warning("Incorrect permissions for role %s: %s",
                        self.request_json["name"], exc)
            raise http_exceptions.BadRequest

        LOG.info("Role %s (%s) created by %s",
                 self.request_json["name"], role_model.model_id,
                 self.initiator_id)

        return role_model

    @auth.require_authorization("api", "delete_role")
    @validators.with_model(role.RoleModel)
    def delete(self, item_id, item):
        try:
            item.delete()
        except base_exceptions.CannotUpdateDeletedModel:
            LOG.warning("Cannot delete deleted role %s", item_id)
            raise http_exceptions.CannotUpdateDeletedModel()
        except base_exceptions.CannotDeleteRoleWithActiveUsers:
            LOG.warning("Cannot delete role %s with active users", item_id)
            raise http_exceptions.CannotDeleteRoleWithActiveUsers()

        LOG.info("Role %s was deleted by %s", item_id, self.initiator_id)

        return item
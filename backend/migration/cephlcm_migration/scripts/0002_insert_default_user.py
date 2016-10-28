#!/usr/bin/env python3
"""
This migration applies default user 'root'
"""


from cephlcm_api import wsgi
from cephlcm_common.models import db
from cephlcm_common.models import generic
from cephlcm_common.models import role
from cephlcm_common.models import user


with wsgi.application.app_context():
    generic.configure_models(db.MongoDB())

    role_collection = role.RoleModel.collection()
    role_id = role_collection.find_one(
        {"name": "wheel"}, ["model_id"])["model_id"]
    role_model = role.RoleModel.find_by_model_id(role_id)

    user.UserModel.make_user(
        "root",
        "root",
        "noreply@example.com",
        "Root User",
        role_model
    )

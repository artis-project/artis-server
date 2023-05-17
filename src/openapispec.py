from typing import Tuple

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from flask import Blueprint
from flask_swagger_ui import get_swaggerui_blueprint


def openApiSpecConfig() -> Tuple[APISpec, Blueprint]:
    spec = APISpec(
        title="Artis-Project",
        version="1.0.0",
        openapi_version="3.0.3",
        plugins=[FlaskPlugin(), MarshmallowPlugin()],
    )

    ### SECURITY SCHEMES ###
    api_security_scheme_did = {"type": "apiKey", "in": "header", "name": "did"}
    api_security_scheme_signature = {
        "type": "apiKey",
        "in": "header",
        "name": "signature",
    }
    spec.components.security_scheme("DID", api_security_scheme_did)
    spec.components.security_scheme("Signature", api_security_scheme_signature)

    ### SCHEMAS ###
    spec.components.schema("ViolationError",)


    ### SWAGGER-UI ###
    swaggerui_blueprint = get_swaggerui_blueprint(
        "/api/docs",  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
        "/swagger",
        config={"app_name": "Test application"},  # Swagger UI config overrides
    )

    return spec, swaggerui_blueprint

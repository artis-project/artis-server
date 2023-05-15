from flask import Flask
from marshmallow import ValidationError
from web3.exceptions import ContractLogicError
from werkzeug.exceptions import Unauthorized


def validation_error(error: ValidationError):
    return {"error": error.__class__.__name__, "messages": error.messages}, 400


def unauthorized_error(error: Unauthorized):
    return {"error": error.__class__.__name__, "messages": error.description}, 401


def contract_logic_error(error: ContractLogicError):
    if error.args[0] == "Token does not exist":
        return {"error": error.__class__.__name__, "messages": error.args}, 404
    else:
        return {"error": error.__class__.__name__, "messages": error.args}, 403


def register_error_handlers(app: Flask):
    app.register_error_handler(ValidationError, validation_error)
    app.register_error_handler(Unauthorized, unauthorized_error)
    app.register_error_handler(ContractLogicError, contract_logic_error)

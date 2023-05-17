from flask import Flask
from marshmallow import ValidationError
from web3.exceptions import ContractLogicError
from werkzeug.exceptions import HTTPException, MethodNotAllowed, NotFound, Unauthorized


def validation_error(error: ValidationError):
    return {"error": error.__class__.__name__, "messages": error.messages}, 400


def contract_logic_error(error: ContractLogicError):
    if error.args[0] == "Token does not exist":
        return {"error": error.__class__.__name__, "messages": error.args}, 404
    else:
        return {"error": error.__class__.__name__, "messages": error.args}, 403


def werkzeug_errors(error: HTTPException):
    return {
        "error": error.__class__.__name__,
        "messages": error.description,
    }, int(error.code)


def register_error_handlers(app: Flask):
    ### Werkzeug errors ###
    app.register_error_handler(NotFound, werkzeug_errors)
    app.register_error_handler(Unauthorized, werkzeug_errors)
    app.register_error_handler(MethodNotAllowed, werkzeug_errors)
    ### other errors ###
    app.register_error_handler(ValidationError, validation_error)
    app.register_error_handler(ContractLogicError, contract_logic_error)

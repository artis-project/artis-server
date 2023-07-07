from flask import Flask
from marshmallow import ValidationError
from web3.exceptions import ContractLogicError
from werkzeug.exceptions import HTTPException


def validation_error(error: ValidationError):
    return {"error": error.__class__.__name__, "messages": error.messages}, 400


def contract_logic_error(error: ContractLogicError):
    # contract reverts with the appropriate status code as the last three characters of the error message
    status_code = (
        lambda: int(error.args[0][-3:]) if error.args[0][-3:].isdigit() else 400
    )
    return {"error": error.__class__.__name__, "messages": error.args}, status_code()


def werkzeug_errors(error: HTTPException):
    return {
        "error": error.__class__.__name__,
        "messages": error.description,
    }, int(error.code)


def register_error_handlers(app: Flask):
    ### Werkzeug errors ###
    app.register_error_handler(HTTPException, werkzeug_errors)
    ### other errors ###
    # app.register_error_handler(ValidationError, validation_error)
    # app.register_error_handler(ContractLogicError, contract_logic_error)

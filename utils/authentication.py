import binascii
from functools import wraps

from flask import g, request
from marshmallow import ValidationError
from web3.exceptions import ContractLogicError
from werkzeug.exceptions import Unauthorized

from src.models.Fields import DID, Signature
from src.smartcontracts.SmartContract import SmartContract
from utils.logging import logger


def auth_required(sc: SmartContract):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            authenticate(sc)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def authenticate(smartcontract: SmartContract):
    signature = request.headers.get("signature")
    did = request.headers.get("did")

    if not signature or not did:
        raise Unauthorized("missing signature or did header")
    try:
        DID._validate(did)
        Signature._validate(signature)
    except ValidationError as e:
        raise Unauthorized(e.messages)

    signature_as_bytes = bytes.fromhex(signature[2:])
    try:
        sender = smartcontract.verifySignature(did=did, signature=signature_as_bytes)
    except ContractLogicError as e:
        raise Unauthorized(e.args)

    g.sender = binascii.unhexlify(sender[2:])
    logger.info(sender=sender, gsender=g.sender)

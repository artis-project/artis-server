from flask import abort
from marshmallow import ValidationError
from werkzeug.exceptions import Unauthorized
from src.smartcontracts.SmartContract import SmartContract
from src.models.Fields import DID, Signature
from web3.exceptions import ContractLogicError


def verify_signature(did: str, signature: str, smartcontract: SmartContract):
    if not signature or not did:
        raise Unauthorized("missing signature or did header")
    try:
        DID._validate(did)
        Signature._validate(signature)
    except ValidationError as e:
        raise Unauthorized(e.messages)

    signature_as_bytes = bytes.fromhex(signature[2:])
    try:
        return smartcontract.verifySignature(did=did, signature=signature_as_bytes)
    except ContractLogicError as e:
        raise Unauthorized(e.args)

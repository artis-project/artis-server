import base64
import binascii
import datetime
import json
from functools import wraps

from eth_abi.abi import encode
from eth_account import Account
from flask import g, request
from marshmallow import ValidationError
from web3 import Web3
from web3.exceptions import ContractLogicError
from werkzeug.exceptions import BadRequest, Unauthorized

from src.models.Fields import DID, Signature
from src.smartcontracts.SmartContract import SmartContract
from utils.logging import logger


def encode_dict_base64(data: dict):
    return base64.b64encode(json.dumps(data).encode("utf-8")).decode("utf-8")


def issue_token(private_key: str):
    """issue a jwt token signed with the private key of the user"""
    if private_key is None:
        return BadRequest("missing private key")
    try:
        subject = Account.from_key(private_key)
    except Exception:
        raise BadRequest("invalid private key")

    payload = {
        "iss": "ARTIS-Project",
        "sub": f"did:ethr:{subject.address}",
        "aud": "ARTIS-API",
        "iat": (iat := datetime.datetime.now().timestamp()),
        "exp": iat + 3600,
    }
    header = {"alg": "ECDSA", "typ": "JWT"}

    base64_header = encode_dict_base64(header)
    base64_payload = encode_dict_base64(payload)

    signature_data = f"{base64_header}.{base64_payload}"

    encoded = encode(["string"], [signature_data])
    hashed = Web3.keccak(encoded)
    signature = subject.signHash(hashed).signature.hex()
    print(type(signature))
    signature = base64.b64encode(
        subject.signHash(hashed).signature.hex().encode("utf-8")
    ).decode("utf-8")

    token = ".".join([base64_header, base64_payload, signature])
    return payload.get("sub"), token


def verify_token(token: str) -> str:
    """verify a jwt token and return the did of the user"""
    token = token.replace("Bearer ", "")
    try:
        _, payload, signature = token.split(".")
    except ValueError:
        raise Unauthorized("invalid token format")

    signed_data = token[: token.rfind(".")]
    try:
        decoded_payload = json.loads(base64.b64decode(payload).decode("utf-8"))
    except Exception:
        raise Unauthorized("invalid token payload")

    did = decoded_payload.get("sub")
    if did is None:
        raise Unauthorized("missing sub in token payload")

    try:
        DID._validate(did)
    except ValidationError as e:
        raise Unauthorized("invalid did in token payload: " + ", ".join(e.messages))

    exp = decoded_payload.get("exp")
    if exp is None or exp < datetime.datetime.now().timestamp():
        raise Unauthorized("token expired")

    encoded = encode(["string"], [signed_data])
    keccak_hash = Web3.keccak(encoded)

    recovered_address = Account._recover_hash(
        keccak_hash, signature=base64.b64decode(signature).decode("utf-8")
    )

    if recovered_address != did[9:]:
        raise Unauthorized("invalid signature")
    return did


def auth_required(sc: SmartContract):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # authenticate(sc)
            g.sender = binascii.unhexlify(
                verify_token(request.headers.get("Authorization"))[11:]
            )
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

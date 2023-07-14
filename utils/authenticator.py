import base64
from web3.eth.base_eth import Account
from eth_account.messages import encode_defunct
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, cast
from utils.auth_types import (
    LoginOptions,
    LoginPayload,
    LoginPayloadData,
    VerifyOptions,
    AuthenticationOptions,
    AuthenticationPayloadData,
)
from uuid import uuid4
import pytz
import json
from functools import wraps
from flask import g, request
import binascii
from werkzeug.exceptions import BadRequest, Unauthorized


class Authenticator:
    def __init__(
        self,
        signing_key: str,
        timezone=pytz.timezone("Europe/Zurich"),
        timeformat="%Y-%m-%dT%H:%M:%S%z",
    ):
        self._signing_key = signing_key
        self.timezone = timezone
        self.timeformat = timeformat
        self.signing_account = Account.from_key(signing_key)

    def user(self, domain: str, token: str) -> dict | str:
        """
        checks if token is valid and returns the user address if invalid returns "null"
        method for auth/user route used in authentication flow
        """
        try:
            return {"address": self.authenticate(domain, token)}
        except Exception as e:
            return "null"

    def generate_client_auth_payload(self, address: str, chain_id: str):
        return {
            "payload": {
                "version": "1",
                "type": "evm",
                "domain": "artis-project",
                "address": address,
                "chain_id": chain_id,
                "nonce": str(uuid4()),
                "issued_at": datetime.now(self.timezone).strftime(self.timeformat),
                "expiration_time": (
                    datetime.now(self.timezone) + timedelta(hours=1)
                ).strftime(self.timeformat),
            }
        }

    def verify(
        self,
        domain: str,
        payload: LoginPayload,
        options: VerifyOptions = VerifyOptions(),
    ) -> str:
        """
        Server-side function to securely verify the address of the logged in client-side wallet
        by validating the provided client-side login request.

        :param domain: The domain of the application to verify the login request for
        :param payload: The login payload to verify
        :return: The address of the logged in wallet that signed the payload
        """

        # Check that the intended domain matches the domain of the payload
        if payload.payload.domain != domain:
            raise Unauthorized(
                f"Expected domain '{domain}' does not match domain on payload '{payload.payload.domain}'"
            )

        # Check that the payload hasn't expired
        current_time = datetime.utcnow()
        if current_time.replace(
            tzinfo=pytz.utc
        ) > payload.payload.expiration_time.replace(tzinfo=pytz.utc):
            raise Unauthorized(f"Login request has expired")

        # If chain ID is specified, check that it matches the chain ID of the signature
        if (
            options.chain_id is not None
            and options.chain_id != payload.payload.chain_id
        ):
            raise Unauthorized(
                f"Chain ID '{options.chain_id}' does not match payload chain ID '{payload.payload.chain_id}'"
            )

        # Check that the signing address is the claimed wallet address
        message = self._generate_message(payload.payload)
        user_address = self._recover_address(message, payload.signature)
        if user_address.lower() != payload.payload.address.lower():
            raise Unauthorized(
                f"The intended payload address '{payload.payload.address.lower()}' is not the payload signer"
            )

        return user_address

    def generate_auth_token(
        self,
        domain: str,
        payload: dict,
    ) -> str:
        """
        Server-side function that generates a JWT token from the provided login request that the
        client-side wallet can use to authenticate to the server-side application.

        :param domain: The domain of the application to authenticate to
        :param payload: The login payload to authenticate with
        :param options: Optional configuration options for the authentication token
        :return: An authentication token that can be used to make authenticated requests to the server
        """
        payload = LoginPayload.from_json(payload, self.timeformat)
        user_address = self.verify(domain, payload)
        payload_data = AuthenticationPayloadData(
            iss=self.signing_account.address,
            sub=user_address,
            aud=domain,
            nbf=int(datetime.now(self.timezone).timestamp()),
            exp=int(payload.payload.expiration_time.timestamp())
            if payload.payload.expiration_time is not None
            else int((datetime.now(self.timezone) + timedelta(hours=1)).timestamp()),
            iat=int(datetime.now(self.timezone).timestamp()),
            jti=str(uuid4()),
        )

        # Configure json.dumps to work exactly as JSON.stringify works for compatibility
        data = self._stringify(payload_data.__dict__)
        signature = self._sign_message(data)

        # Header used for JWT token specifying hash algorithm
        header = {
            # Specify ECDSA with SHA-256 for hashing algorithm
            "alg": "ES256",
            "typ": "JWT",
        }

        encoded_header = self._base64encode(self._stringify(header))
        encoded_data = self._base64encode(data)
        encoded_signature = self._base64encode(signature)

        # Generate a JWT token with base64 encoded header, payload, and signature
        token = f"{encoded_header}.{encoded_data}.{encoded_signature}"

        return token

    def authenticate(
        self,
        domain: str,
        token: str,
    ) -> str:
        """
        Server-side function that authenticates the provided JWT token. This function verifies that
        the provided authentication token is valid and returns the address of the authenticated wallet.

        :param domain: The domain of the application to authenticate the token to
        :param token: The authentication token to authenticate with
        :return: The address of the authenticated wallet
        """
        if token is None:
            raise Unauthorized("missing token")

        token = token.replace("Bearer ", "")
        try:
            _, payload, signature = token.split(".")
        except ValueError:
            raise Unauthorized("invalid token format")

        token = token.replace("Bearer ", "")
        encoded_payload = token.split(".")[1]
        encoded_signature = token.split(".")[2]
        payload_dict = json.loads(self._base64decode(encoded_payload))
        payload = AuthenticationPayloadData(**payload_dict)
        signature = self._base64decode(encoded_signature)

        # Check that the intended audience matches the domain
        if payload.aud != domain:
            raise Unauthorized(
                f"Expected token to be for the domain '{domain}', but found token with domain '{payload.aud}'"
            )

        # Check that the token is past the invalid before time
        current_time = datetime.now(self.timezone)
        if current_time < datetime.fromtimestamp(payload.nbf, self.timezone):
            raise Unauthorized(
                f"This token is invalid before epoch time '{payload.nbf}', current epoch time is '{int(current_time.timestamp())}'"
            )

        # Check that the token hasn't expired
        if current_time > datetime.fromtimestamp(payload.exp, self.timezone):
            raise Unauthorized(
                f"This token expired at epoch time '{payload.exp}', current epoch time is '{int(current_time.timestamp())}'"
            )

        # Check that the connected wallet matches the token issuer
        if self.signing_account.address.lower() != payload.iss.lower():
            raise Unauthorized(
                f"Expected the connected wallet address '{self.signing_account.address}' to match the token issuer address '{payload.iss}'"
            )

        # Check that the connected wallet signed the token
        admin_address = self._recover_address(
            self._stringify(payload.__dict__), signature
        )
        if admin_address.lower() != self.signing_account.address.lower():
            raise Unauthorized(
                f"The connected wallet address '{self.signing_account.address}' did not sign the token"
            )
        return payload.sub

    def _stringify(self, value: Any) -> str:
        """
        Configure json.dumps to work exactly as JSON.stringify works for compatibility
        """

        return json.dumps(value, separators=(",", ":"))

    def _generate_message(self, payload: LoginPayloadData) -> str:
        """
        Generates an EIP-4361 compliant message to sign based on the login payload
        """
        typeField = "Ethereum" if payload.type == "evm" else "Solana"
        header = f"{payload.domain} wants you to sign in with your {typeField} account:"
        prefix = f"{header}\n{payload.address}"
        if payload.statement:
            prefix += f"\n\n{payload.statement}\n"
        else:
            prefix += "\n\n"
        suffixArray = []
        versionField = f"Version: {payload.version}"
        suffixArray.append(versionField)
        if payload.chain_id:
            chainField = f"Chain ID: {payload.chain_id if payload.chain_id else str(1)}"
            suffixArray.append(chainField)
        nonceField = f"Nonce: {payload.nonce}"
        suffixArray.append(nonceField)
        time = payload.issued_at.strftime(self.timeformat)
        issuedAtField = f"Issued At: {time}"
        suffixArray.append(issuedAtField)
        time = payload.expiration_time.strftime(self.timeformat)
        expiryField = f"Expiration Time: {time}"
        suffixArray.append(expiryField)

        suffix = "\n".join(suffixArray)
        return f"{prefix}\n{suffix}"

    def _sign_message(self, message: str) -> str:
        """
        Sign a message with the admin wallet
        """

        message_hash = encode_defunct(text=message)
        sig = self.signing_account.sign_message(message_hash)
        return sig.signature.hex()

    @staticmethod
    def _recover_address(message: str, signature: str) -> str:
        """
        Recover the signing address from a signed message
        """

        message_hash = encode_defunct(text=message)
        address = Account.recover_message(message_hash, signature=signature)

        return address

    @staticmethod
    def _base64encode(message: str) -> str:
        """
        Encode a message in base64
        """

        return base64.b64encode(message.encode("utf-8")).decode("utf-8")

    @staticmethod
    def _base64decode(message: str) -> str:
        """
        Decode a message from base64
        """

        return base64.b64decode(message).decode("utf-8")


def auth_required(authenticator: Authenticator):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(token := request.headers.get("Authorization"))
            g.sender = authenticator.authenticate("artis-project", token)
            return func(*args, **kwargs)

        return wrapper

    return decorator

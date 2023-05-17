from marshmallow import ValidationError, fields


class Address(fields.String):
    @staticmethod
    def _serialize(value, attr, obj, **kwargs):
        if value == "0x0000000000000000000000000000000000000000":
            return None
        return value

    @staticmethod
    def _validate(value):
        if value is None:
            return
        messages = []
        if not isinstance(value, str):
            messages.append(f"Address must be a string not {type(value)}")
        elif not value.startswith("0x"):
            messages.append("Addresses must start with 0x")
        elif not (length := len(value)) == 42:
            messages.append(f"Addresses must be 42 characters long not {length}")
        elif not all(c in "0123456789abcdef" for c in value[2:].lower()):
            messages.append("Addresses must be hexadecimal")

        if messages:
            raise ValidationError(messages)


class DID(fields.String):
    @staticmethod
    def _validate(value):
        """Check if the did is of the format did:ethr:<0xwallet_address>"""
        prefix = "did:ethr:"
        if not isinstance(value, str):
            raise ValidationError("did must be of type str")
        if not value.startswith(prefix):
            raise ValidationError(
                "did is of wrong format, must be did:ethr:0x<wallet_address>"
            )
        try:
            Address._validate(value[len(prefix) :])
        except ValidationError as err:
            raise ValidationError(
                ["did must be of format did:ethr:0x<wallet_address>"] + err.messages
            )


class Signature(fields.String):
    @staticmethod
    def _validate(value):
        """Check if the signature is valid."""
        messages = []
        if not isinstance(value, str):
            messages.append("signature header must be of type str")
        elif not value.startswith("0x"):
            messages.append("signature header must start with 0x")
        elif not all(c in "0123456789abcdef" for c in value[2:].lower()):
            messages.append("signature header must be hexadecimal")

        if messages:
            raise ValidationError(messages)

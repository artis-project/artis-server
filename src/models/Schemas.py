from marshmallow import Schema, ValidationError, fields, validates

from src.models.Fields import Address


class ArtworkSchema(Schema):
    id = fields.Int()
    owner = Address()
    carrier = Address()
    logger = Address()
    recipient = Address()
    status = fields.String()
    violationTimestamp = fields.Int()

    @staticmethod
    @validates("carrier")
    @validates("logger")
    @validates("recipient")
    def validate_address(address: str):
        if not isinstance(address, str):
            raise ValidationError("Address must be a string")
        if not address.startswith("0x"):
            raise ValidationError("Addresses must start with 0x")
        if not len(address) == 42:
            raise ValidationError("Addresses must be 42 characters long")
        if not all(c in "0123456789abcdef" for c in address[2:].lower()):
            raise ValidationError("Addresses must be hexadecimal")

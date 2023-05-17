from marshmallow import Schema, fields

from src.models.Fields import Address


class ArtworkSchema(Schema):
    id = fields.Int()
    owner = Address()
    carrier = Address()
    logger = Address()
    recipient = Address()
    status = fields.String()
    violationTimestamp = fields.Int()

from marshmallow import Schema, fields

from src.models.Fields import Address


class ArtworkSchema(Schema):
    id = fields.Int()
    objectId = fields.String()
    owner = Address()
    carrier = Address()
    logger = Address()
    recipient = Address()
    status = fields.String()
    violationTimestamp = fields.Int()

class ArtworkMintSchema(Schema):
    owner = Address()
    objectId = fields.String(required=True)
    carrier = Address()
    logger = Address()
    recipient = Address()
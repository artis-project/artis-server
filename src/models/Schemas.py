from marshmallow import Schema, fields, pre_load

from src.models.Fields import Address

class StatusSchema(Schema):
    currentStatus = fields.String(
        validate=lambda s: s in ["TO_BE_DELIVERED", "IN_TRANSIT", "DELIVERED"],
    )
    requestedStatus = fields.String(
        validate=lambda s: s in ["TO_BE_DELIVERED", "IN_TRANSIT", "DELIVERED", "NONE"]
    )
    approvals = fields.Dict(
        keys=fields.String(
            validate=lambda s: s in ["owner", "carrier", "recipient"]
        ),
        values=fields.Boolean(),
    )

class ArtworkSchema(Schema):
    id = fields.Int()
    objectId = fields.String()
    owner = Address()
    carrier = Address()
    logger = Address()
    recipient = Address()
    status = fields.Nested(StatusSchema)
    violationTimestamp = fields.Int()

    @pre_load
    def nest_status_field(self, data: dict , **kwargs):
        nested_status_fields = {}
        if (key:="status") not in data:
            data.update({key: {"approvals": {}}})
        if (key:="currentStatus") in data:
            value = data.pop(key)
            data["status"][key] = value
        if (key:="requestedStatus") in data:
            value = data.pop(key)
            data["status"][key] = value
        if (key:="recipientApproval") in data:
            value = data.pop(key)
            data["status"]["approvals"]["recipient"] = value
        if (key:="ownerApproval") in data:
            value = data.pop(key)
            data["status"]["approvals"]["owner"] = value
        if (key:="carrierApproval") in data:
            value = data.pop(key)
            data["status"]["approvals"]["carrier"] = value
        print(data)
        return data


class ArtworkMintSchema(Schema):
    owner = Address()
    objectId = fields.String(required=True)
    carrier = Address()
    logger = Address()
    recipient = Address()

class ArtworkUpdateSchema(ArtworkSchema):   
    pass

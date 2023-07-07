from src.models.Schemas import ArtworkSchema, ArtworkMintSchema, ArtworkUpdateSchema

INITIAL_ADDRESS = "0x0000000000000000000000000000000000000000"
NO_CHANGE_ADDRESS = "0x0000000000000000000000000000000000000001"


class Artwork:
    def __init__(
        self,
        id: int = None,
        objectId: str = None,
        owner: str = None,
        carrier: str = None,
        logger: str = None,
        recipient: str = None,
        status: dict = None,
        violationTimestamp: int = None,
    ):
        self.id = id
        self.objectId = objectId
        self.owner = owner
        self.carrier = carrier
        self.logger = logger
        self.recipient = recipient
        self.status = status
        self.violationTimestamp = violationTimestamp

    @classmethod
    def load(cls, data: dict):
        return cls(**ArtworkSchema().load(data))

    @classmethod
    def load_from_mint(cls, data: dict):
        return cls(**ArtworkMintSchema().load(data))

    @classmethod
    def load_from_update(cls, data: dict):
        return cls(**ArtworkUpdateSchema().load(data))

    def dump(self) -> dict:
        return ArtworkSchema().dump(self.__dict__)

    def to_sc_mint(self) -> tuple:
        owner = self.owner if self.owner else None
        return owner, {
            "id": 0,
            "objectId": self.objectId,
            "carrier": self.carrier if self.carrier else INITIAL_ADDRESS,
            "logger": self.logger if self.logger else INITIAL_ADDRESS,
            "recipient": self.recipient if self.recipient else INITIAL_ADDRESS,
            "status": {
                "currentStatus": "MINTED",
                "requestedStatus": "None"
            },
            "violationTimestamp": 0,
        }

    def to_sc_update(self) -> dict:
        return {
            "id": self.id,
            "objectId": self.objectId if self.objectId else "",
            "owner": self.owner if self.owner else NO_CHANGE_ADDRESS,
            "carrier": self.carrier if self.carrier else NO_CHANGE_ADDRESS,
            "recipient": self.recipient if self.recipient else NO_CHANGE_ADDRESS,
            "logger": self.logger if self.logger else NO_CHANGE_ADDRESS,
            "status": {
                "currentStatus": self.status.get("currentStatus", ""),
                "requestedStatus": self.status.get("requestedStatus", "")
            },
            "violationTimestamp": self.violationTimestamp
            if self.violationTimestamp
            else 0,
        }

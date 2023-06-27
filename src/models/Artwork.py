from src.models.Schemas import ArtworkSchema, ArtworkMintSchema

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
ONE_ADDRESS = "0x0000000000000000000000000000000000000001"

class Artwork:
    def __init__(
        self,
        id: int = None,
        objectId: str = None,
        owner: str = None,
        carrier: str = None,
        logger: str = None,
        recipient: str = None,
        status: str = None,
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

    def dump(self) -> dict:
        return ArtworkSchema().dump(self.__dict__)
    
    def to_sc_mint(self) -> dict:
        owner = self.owner if self.owner else None
        return owner, {
            "id": 0,
            "objectId": self.objectId,
            "carrier": self.carrier if self.carrier else ZERO_ADDRESS,
            "logger": self.logger if self.logger else ZERO_ADDRESS,
            "recipient": self.recipient if self.recipient else ZERO_ADDRESS,
            "status": "MINTED",
            "violationTimestamp": 0,
        }
            

    def to_sc_update(self) -> dict:
        return {
            "id": self.id,
            "objectId": self.objectId if self.objectId else "",
            "owner": self.owner
            if self.owner
            else "0x0000000000000000000000000000000000000001",
            "carrier": self.carrier
            if self.carrier
            else "0x0000000000000000000000000000000000000001",
            "recipient": self.recipient
            if self.recipient
            else "0x0000000000000000000000000000000000000001",
            "logger": self.logger
            if self.logger
            else "0x0000000000000000000000000000000000000001",
            "status": self.status if self.status else "",
            "violationTimestamp": self.violationTimestamp
            if self.violationTimestamp
            else 0,
        }

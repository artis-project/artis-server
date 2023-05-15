from src.models.Schemas import ArtworkSchema


class Artwork:
    def __init__(
        self,
        id: int = None,
        owner: str = None,
        carrier: str = None,
        logger: str = None,
        recipient: str = None,
        status: str = None,
        violationTimestamp: int = None,
    ):
        self.id = id
        self.owner = owner
        self.carrier = carrier
        self.logger = logger
        self.recipient = recipient
        self.status = status
        self.violationTimestamp = violationTimestamp

    @classmethod
    def load(cls, data: dict):
        return cls(**ArtworkSchema().load(data))

    def dump(self) -> dict:
        return ArtworkSchema().dump(self.__dict__)

    def toSC(self) -> dict:
        return {
            "id": self.id,
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

import os
import signal
import sys
from types import FrameType

from dotenv import load_dotenv
from flask import Flask, g, request

from src.models.Artwork import Artwork
from src.smartcontracts.DefaultArtwork import DefaultArtwork
from utils.authentication import auth_required, issue_token
from utils.error_handlers import register_error_handlers
from utils.logging import logger

### SETUP ###
load_dotenv()
app = Flask(__name__)
app.app_context()
sc = DefaultArtwork(
    signing_private_key=os.environ.get("SMARTCONTRACT_ADMIN_PRIVATE_KEY"),
    http_provider_url=os.environ.get("HTTP_PROVIDER_URL"),
)


### ROUTES ###
@app.route("/")
@auth_required(sc)
def hello() -> str:
    return "Hello from Artis-Project!"


@app.post("/auth")
def token() -> str:
    data = request.get_json()
    private_key = data.get("private_key")

    did, token = issue_token(private_key)
    return {"did": did, "token": token}


@app.get("/artworks/<int:artwork_id>")
@auth_required(sc)
def get(artwork_id: str) -> str:
    return sc.getArtworkData(artwork_id, g.sender).dump()


@app.patch("/artworks/<int:artwork_id>")
@auth_required(sc)
def update(artwork_id: int) -> str:
    newArtworkData = Artwork.load(request.get_json() | {"id": artwork_id})
    return sc.updateArtworkData(newArtworkData, g.sender).dump()


@app.post("/artworks")
@auth_required(sc)
def mint() -> str:
    artworkData = Artwork.load_from_mint(request.get_json())
    return {"tokenId": sc.safeMint(to=g.sender, data=artworkData)}


### HANDLERS ###
register_error_handlers(app)


def shutdown_handler(signal_int: int, frame: FrameType) -> None:
    logger.info(f"Caught Signal {signal.strsignal(signal_int)}")

    from utils.logging import flush

    flush()

    # Safely exit program
    sys.exit(0)


if __name__ == "__main__":
    # Running application locally, outside of a Google Cloud Environment

    # handles Ctrl-C termination
    signal.signal(signal.SIGINT, shutdown_handler)

    app.run(host="localhost", port=8080, debug=True)
else:
    # handles Cloud Run container termination
    signal.signal(signal.SIGTERM, shutdown_handler)

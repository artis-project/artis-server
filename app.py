import os
import signal
import sys
from types import FrameType

from dotenv import load_dotenv
from flask import Flask, g, request
from flask_cors import CORS

from src.authentication.Authenticator import Authenticator, auth_required
from src.models.Artwork import Artwork
from src.smartcontract.ArtworkConnector import ArtworkConnector
from utils.error_handlers import register_error_handlers
from utils.logging import logger

### SETUP ###
load_dotenv()
app = Flask(__name__)
app.json.sort_keys = False
cors = CORS(app, supports_credentials=True)
sc = ArtworkConnector(
    signing_private_key=os.environ.get("SMARTCONTRACT_ADMIN_PRIVATE_KEY"),
    http_provider_url=os.environ.get("HTTP_PROVIDER_URL"),
)
authenticator = Authenticator(os.environ.get("SMARTCONTRACT_ADMIN_PRIVATE_KEY"))


### ROUTES ###
@app.route("/")
@auth_required(authenticator)
def hello() -> str:
    return "Hello from Artis-Project!"


@app.post("/auth/payload")
def payload() -> dict:
    data = request.get_json()
    return authenticator.generate_client_auth_payload(
        data.get("address"), data.get("chainId")
    )


@app.post("/auth/login")
def login() -> dict:
    data = request.get_json().get("payload")
    return {"token": authenticator.generate_auth_token("artis-project", data)}


@app.post("/auth/logout")
def logout() -> dict:
    g.sender = None
    return ("", 204)


@app.get("/auth/user")
def user() -> str | dict:
    return authenticator.user("artis-project", request.headers.get("Authorization"))


@app.get("/artworks/<int:artwork_id>")
@auth_required(authenticator)
def get(artwork_id: int) -> dict:
    return sc.getArtworkData(artwork_id, g.sender).dump()


@app.patch("/artworks/<int:artwork_id>")
@auth_required(authenticator)
def update(artwork_id: int) -> dict:
    newArtworkData = Artwork.load(request.get_json() | {"id": artwork_id})
    return sc.updateArtworkData(newArtworkData, g.sender).dump()


@app.get("/artworks")
@auth_required(authenticator)
def get_all() -> dict:
    return {"artworks": sc.getArtworkIdsByAddress(g.sender)}


@app.post("/artworks")
@auth_required(authenticator)
def mint() -> dict:
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
    signal.signal(signal.SIGINT, shutdown_handler)  # type: ignore

    app.run(host="localhost", port=8080, debug=True, load_dotenv=True)
else:
    # handles Cloud Run container termination
    signal.signal(signal.SIGTERM, shutdown_handler)  # type: ignore

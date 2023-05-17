import os
import signal
import sys
from types import FrameType

from dotenv import load_dotenv
from flask import Flask, g, request

from src.models.Artwork import Artwork
from src.openapispec import openApiSpecConfig
from src.smartcontracts.DefaultArtwork import DefaultArtwork
from utils.authentication import auth_required
from utils.error_handlers import register_error_handlers
from utils.logging import logger

### SETUP ###
load_dotenv()
app = Flask(__name__)
app.app_context()
sc = DefaultArtwork(
    signing_private_key=os.environ.get("DEFAULT_PRIVATE_KEY"),
    http_provider_url=os.environ.get("HTTP_PROVIDER_URL"),
)


### ROUTES ###
@app.route("/")
@auth_required(sc)
def hello() -> str:
    """Home Route
    ---
    get:
      description: Home route of artis project
      security:
        - DID: []
        - Signature: []
      responses:
        default:
            description: This is the default response
            content:
                text/plain:
                    type: string
                    example: Hello from Artis-Project!
    """
    print(request.headers)
    return "Hello from Artis-Project!"


@app.get("/artworks/<int:artwork_id>")
@auth_required(sc)
def get(artwork_id: str) -> str:
    """Home Route
    ---
    get:
        tags:
        - Artwork
        summary: Get Artwork Data by Id
        description: Retrieves the data of a specific artwork by its id
        parameters:
        - name: artwork_id
          in: path
          description: id of the artwork
          required: true
          schema:
            type: integer
        security:
            - DID: []
            - Signature: []
        responses:
            200:
                content:
                    application/json:
                        schema: ArtworkSchema
            400:
                content:
                    application/json:
                        schema: ErrorSchema
    """
    return sc.getArtworkData(artwork_id, g.sender).dump()


@app.patch("/artworks/<int:artwork_id>")
@auth_required(sc)
def update(artwork_id: int) -> str:
    newArtworkData = Artwork.load(request.get_json() | {"id": artwork_id})
    return sc.updateArtworkData(newArtworkData, g.sender).dump()


@app.post("/artworks")
@auth_required(sc)
def mint() -> str:
    return {"tokenId": sc.safeMint(to=g.sender)}


### HANDLERS ###
register_error_handlers(app)


def shutdown_handler(signal_int: int, frame: FrameType) -> None:
    logger.info(f"Caught Signal {signal.strsignal(signal_int)}")

    from utils.logging import flush

    flush()

    # Safely exit program
    sys.exit(0)


### OpenApiSpec ###
spec, swaggerui_blueprint = openApiSpecConfig()


@app.route("/swagger")
def specification() -> str:
    return spec.to_yaml()


app.register_blueprint(swaggerui_blueprint)

with app.app_context():
    spec.path(view=hello)
    spec.path(view=get)
    spec.path(view=update)
    spec.path(view=mint)


# Running application locally, outside of a Google Cloud Environment
if __name__ == "__main__":
    # handles Ctrl-C termination
    signal.signal(signal.SIGINT, shutdown_handler)

    app.run(host="localhost", port=8080, debug=True)
else:
    # handles Cloud Run container termination
    signal.signal(signal.SIGTERM, shutdown_handler)

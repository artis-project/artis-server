from utils.authenticator import Authenticator
from utils.auth_types import LoginPayload
import os
from dotenv import load_dotenv
load_dotenv()

authenticator = Authenticator(os.environ.get("SMARTCONTRACT_ADMIN_PRIVATE_KEY"))

def test_authenticator():
    payload = authenticator.generate_client_auth_payload("0xc768e721AEfC2be6e0E958DA43389B7e6f68BdAE", "11155111")
    print(payload)


    token = authenticator.generate_auth_token("artis-project", LoginPayload.from_json({
        "payload": {
            "address": "0xc768e721AEfC2be6e0E958DA43389B7e6f68BdAE",
            "chain_id": "11155111",
            "domain": "artis-project",
            "expiration_time": "1688311592.22481",
            "issued_at": "1688307992.224798",
            "nonce": 1,
            "type": "evm"
        },
		"signature": "0x3c53e014173d04d71815ff79915e124db9b0969a6805144eafedaa2fec4330035f5a0d3e6f3535ba7a6ee08ce89972f486acd89fa5fa48e499d247434e90513b1c"
	}))
    print(token)



if __name__ == "__main__":
    test_authenticator()
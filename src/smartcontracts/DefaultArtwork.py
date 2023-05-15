import json
import os

import requests
from hexbytes import HexBytes

from src.models.Artwork import Artwork
from src.models.Schemas import ArtworkSchema
from src.smartcontracts.SmartContract import SmartContract


class DefaultArtwork(SmartContract):
    def __init__(self, signing_private_key: str, http_provider_url: str):
        super().__init__(signing_private_key, http_provider_url)

    @property
    def smartcontractAdmin(self) -> str:
        return self._contract.functions.smartcontractAdmin().call()

    @smartcontractAdmin.setter
    def smartcontractAdmin(self, new_admin: str) -> None:
        ArtworkSchema.validate_address(new_admin)
        tx_hash = self._contract.functions.changeSmartContractAdmin(
            new_admin
        ).transact()

    def safeMint(self, to: bytes) -> int:
        """Invoking safeMint function of smartcontract"""
        tx_hash = self._contract.functions.safeMint(to).transact()
        event_args = self._handleEvent(tx_hash, "Transfer")
        return event_args.get("tokenId")

    def updateArtworkData(self, newArtworkData: Artwork, sender: bytes) -> Artwork:
        """Invoking updateArtworkData function of smartcontract"""
        tx_hash = self._contract.functions.updateArtworkData(
            newArtworkData.toSC(), sender
        ).transact()
        event_args = self._handleEvent(tx_hash, "Updated")
        return Artwork.load(event_args.get("newData"))

    def verifySignature(self, did: str, signature: bytes) -> bool:
        """Invoking verifySignature function of smartcontract"""
        return self._contract.functions.verifySignature(did, signature).call()

    def getArtworkData(self, artworkId: int, sender: str) -> Artwork:
        """Invoking getArtworkData function of smartcontract"""
        data = self._contract.functions.getArtworkData(artworkId, sender).call()
        return Artwork.load(data=dict(data._asdict()))

    def _handleEvent(self, tx_hash: HexBytes, event_name: str) -> dict:
        """Wait for the transaction to be mined and return the arguments of the emitted event"""
        tx_receipt = self._w3.eth.wait_for_transaction_receipt(tx_hash)
        logs = self._contract.events[event_name]().process_receipt(tx_receipt)
        return logs[0]["args"]

    def _getSmartContractAbi(self) -> dict:
        """Get the smart contract abi from etherscan.io api"""
        api_key = os.environ.get("ETHERSCAN_API_KEY")
        response = requests.get(
            f"https://api-sepolia.etherscan.io/api?module=contract&action=getabi&address={self.address}&apikey={api_key}"
        )
        return json.loads(response.json()["result"])

    def _getSmartContractAddress(self) -> str:
        """Get the smart contract address from github actions secrets"""
        access_token = os.environ.get("GITHUB_VARIABLES_ACCESS_TOKEN")
        org_name = os.environ.get("GITHUB_ORG_NAME")
        variable_name = os.environ.get("GITHUB_SC_ADDRESS_VARIABLE_NAME")
        url = (
            f"https://api.github.com/orgs/{org_name}/actions/variables/{variable_name}"
        )
        return (
            requests.get(url, headers={"Authorization": f"Bearer {access_token}"})
            .json()
            .get("value")
        )

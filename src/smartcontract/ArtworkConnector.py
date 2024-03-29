import json
import os

import requests
from hexbytes import HexBytes

from src.models.Artwork import Artwork
from src.models.Fields import Address
from src.smartcontract.SmartcontractConnector import SmartcontractConnector


class ArtworkConnector(SmartcontractConnector):
    def __init__(self, signing_private_key: str, http_provider_url: str):
        super().__init__(signing_private_key, http_provider_url)

    @property
    def smartcontractAdmin(self) -> str:
        return self._contract.functions.smartcontractAdmin().call()

    @smartcontractAdmin.setter
    def smartcontractAdmin(self, new_admin: str) -> None:
        Address._validate(new_admin)
        tx_hash = self._contract.functions.changeSmartContractAdmin(
            new_admin
        ).transact()

    def safeMint(self, to: bytes, data: Artwork) -> int:
        """Invoking safeMint function of smartcontract"""
        owner, mint_data = data.to_sc_mint()
        tx_hash = self._contract.functions.safeMint(
            to if not owner else owner, mint_data
        ).transact()
        event_args = self._handleEvent(tx_hash, "Transfer")
        return event_args.get("tokenId")

    def updateArtworkData(self, newArtworkData: Artwork, sender: bytes) -> Artwork:
        """Invoking updateArtworkData function of smartcontract"""
        tx_hash = self._contract.functions.updateArtworkData(
            newArtworkData.to_sc_update(), sender
        ).transact(transaction={})
        event_args = self._handleEvent(tx_hash, "Updated")
        new_data = event_args.get("newData")
        new_data = dict(new_data, **{"owner": event_args.get("owner")})
        new_data["status"] = dict(
            new_data["status"], **{"approvals": event_args.get("approvals")}
        )
        return Artwork.load(data=new_data)

    def getArtworkIdsByAddress(self, address: str) -> dict:
        """Invoking getArtworkIdsByAddress function of smartcontract"""
        artwork_ids = (
            self._contract.functions.getArtworkIdsByAddress(address).call()._asdict()
        )
        # incoming lists are zero padded to the total supply of tokens, they can safely be removed
        remove_zeros = lambda d: {
            k: list(filter(lambda x: x != 0, v)) for k, v in d.items()
        }
        return remove_zeros(artwork_ids)

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

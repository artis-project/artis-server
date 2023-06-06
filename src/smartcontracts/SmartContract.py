from abc import ABC, abstractmethod
from web3 import Web3
from web3.contract import Contract
from web3.middleware import construct_sign_and_send_raw_middleware


class SmartContract(ABC):
    def __init__(self, signing_private_key: str, http_provider_url: str):
        self._w3 = Web3(Web3.HTTPProvider(http_provider_url))
        default_account = self._w3.eth.account.from_key(signing_private_key)

        self._w3.eth.default_account = default_account.address
        self._w3.middleware_onion.add(
            construct_sign_and_send_raw_middleware(default_account)
        )

        self._address = self._getSmartContractAddress()
        self._abi = self._getSmartContractAbi()
        self._contract: Contract = self._w3.eth.contract(
            address=self._address, abi=self._abi, decode_tuples=True
        )

    @property
    def address(self) -> str:
        return self._address

    @property
    def abi(self) -> dict:
        return self._abi

    @abstractmethod
    def _getSmartContractAddress(self) -> str:
        pass

    @abstractmethod
    def _getSmartContractAbi(self, sc_address: str) -> str:
        pass

    @abstractmethod
    def verifySignature(self, did: str, signature: bytes) -> bool:
        pass

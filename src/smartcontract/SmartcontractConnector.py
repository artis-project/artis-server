from abc import ABC, abstractmethod

from web3 import Web3, middleware
from web3.contract import Contract
from web3.gas_strategies.rpc import rpc_gas_price_strategy


class SmartcontractConnector(ABC):
    def __init__(self, signing_private_key: str, http_provider_url: str):
        self._w3 = Web3(Web3.HTTPProvider(http_provider_url))
        default_account = self._w3.eth.account.from_key(signing_private_key)

        def aggressive_gas_strategy(web3, transaction_params=None):
            return Web3.to_wei(30, "gwei")

        self._w3.eth.set_gas_price_strategy(aggressive_gas_strategy)

        self._w3.eth.default_account = default_account.address
        self._w3.middleware_onion.add(
            middleware.construct_sign_and_send_raw_middleware(default_account)
        )
        self._w3.middleware_onion.add(middleware.time_based_cache_middleware)
        self._w3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
        self._w3.middleware_onion.add(middleware.simple_cache_middleware)

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

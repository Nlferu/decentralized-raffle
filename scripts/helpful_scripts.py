
from brownie import Contract, network, config, accounts, MockV3Aggregator, VRFCoordinatorV2Mock, LinkToken

LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]
FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork-dev"]

# Constructor arguments for MockV3Aggregator
DECIMALS = 8
INITIAL_PRICE = 200000000000 # 2,000 $

# Constructor arguments for VRFCoordinatorV2Mock
BASE_FEE = 250000000000000000 # 0.25 is this the premium in LINK?
GAS_PRICE_LINK = 1e9 # link per gas, is this the gas lane? // 0.000000001 LINK per gas
FUND_AMOUNT = 1e18 # 1 ETH / 1 LINK

# We have to map contract type
contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    "vrf_coordinator_v2": VRFCoordinatorV2Mock,
    "link_token": LinkToken
}

# Added for testing purposes
def main():
    deploy_mocks()
    print(f'{get_contract("eth_usd_price_feed").address}')
    print(f'{get_contract("vrf_coordinator_v2").address}')
    print(f'{get_contract("link_token").address}')


def get_account(index = None, id = None):
    # If index was passed we do below
    if index:
        return accounts[index]
    # If id was passed we do below
    if id:
        return accounts.load(id)
    # Shows networks in "development" tab or named "ganache-local"
    if(network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS or network.show_active() in FORKED_LOCAL_ENVIRONMENTS):
        return accounts[0]
    # Below will be our default, so if above won't be picked we will get below
    return accounts.add(config["wallets"]["from_key"])


def get_contract(contract_name):
    contract_type = contract_to_mock[contract_name]
    # Checking below if we are on a local blockchain
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        # Checking if one of above contracts are even deployed (if MockV3Aggregator.length > 0 this mean mockV3 has been deployed and its deploy counter is bigger than 0)
        if len(contract_type) <= 0:
            deploy_mocks()
        # Getting recently deployed mock contract address
        # If we do not give index, so call below as "contract_type" it will throw something like <brownie.network.contract.ContractContainer object at 0x000002577D7DA730>,
        # which is container "number", which contain that whole contract, so it's "address" and ABI with all details that contract has.
        contract = contract_type[-1]
    else:
        contract_address = config["networks"][network.show_active()][contract_name]
        # We need "address" and "ABI" (We will get "ABI" from MockV3Aggregator)
        # We will be getting Contract from it's ABI from package from brownie called "Contract"
        # MockV3Aggregator got attributes as "_name" and "abi"
        contract = Contract.from_abi(contract_type._name, contract_address, contract_type.abi)
    return contract


def deploy_mocks():
    print(f'The active network is {network.show_active()}')
    print("Deploying Mocks...")
    # This have "decimals" and "initial value" in constructor:
    if len(MockV3Aggregator) <= 0:
        MockV3Aggregator.deploy(DECIMALS, INITIAL_PRICE, {"from": get_account()})
    if len(LinkToken) <= 0:
        LinkToken.deploy({"from": get_account()})
    if len(VRFCoordinatorV2Mock) <= 0:
        VRFCoordinatorV2Mock.deploy(BASE_FEE, GAS_PRICE_LINK, {"from": get_account()})
    print("Mocks Deployed!")

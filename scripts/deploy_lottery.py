
from scripts.helpful_scripts import get_account, get_contract, FUND_AMOUNT
from brownie import LotteryV2, network, config
import time

# For local network mock will provide all necessary data
# For testnet we are providing data in "brownie-config.yaml"


def main():
    deploy_lottery()
    start_lottery()
    buy_ticket()
    pick_winner()


def deploy_lottery():
    account = get_account()
    lottery = LotteryV2.deploy(
        get_contract("eth_usd_price_feed").address,
        get_contract("vrf_coordinator_v2").address,
        config["networks"][network.show_active()]["gasLane"],
        config["networks"][network.show_active()]["subscriptionId"],
        config["networks"][network.show_active()]["callbackGasLimit"],
        {"from": account},
        publish_source = config["networks"][network.show_active()].get("verify", False),
    )
    print("Lottery Has Been Successfully Deployed!")
    return lottery


def start_lottery():
    account = get_account()
    lottery = LotteryV2[-1]
    starting_transaction = lottery.startLottery({"from": account})
    starting_transaction.wait(1)
    print("The Lottery Has Started!")


def buy_ticket():
    account = get_account()
    lottery = LotteryV2[-1]
    # Adding some wei for bufor
    entry_fee = lottery.getEntryFee() + 10 ** 8
    buying_ticket_tx = lottery.buyTicket({"from": account, "value": entry_fee})
    buying_ticket_tx.wait(1)
    print("You Have Successfully Bought Lottery Ticket!")


def pick_winner():
    account = get_account()
    lottery = LotteryV2[-1]
    # 1. Create subscription
    # 2. Get subscription ID
    # 3. Fund subscription with LINK
    # 4. Add contract created to subscription list
    vrfCoordinatorV2Mock = get_contract("vrf_coordinator_v2")
    create_sub_tx = vrfCoordinatorV2Mock.createSubscription()
    create_sub_tx.wait(1)
    transactionReturn = create_sub_tx.return_value
    print(f'SubscriptionId: {transactionReturn}')

    #subscriptionId = config["networks"][network.show_active()]["subscriptionId"]
    vrfCoordinatorV2Mock.getSubscription(transactionReturn)
    fund_sub_tx = vrfCoordinatorV2Mock.fundSubscription(transactionReturn, FUND_AMOUNT)
    fund_sub_tx.wait(1)
    add_consumer_tx = vrfCoordinatorV2Mock.addConsumer(transactionReturn, lottery)
    add_consumer_tx.wait(1)
    pick_winner_tx = lottery.pickWinner({"from": account})
    pick_winner_tx.wait(1)
    print("Winner Picked!")
    print(f'{lottery.recentWinner()} is the new winner!')


from brownie import network, convert, config, LotteryV2
from scripts.run_lottery import deploy_lottery
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, FUND_AMOUNT, get_account, get_contract
import pytest
import time


def test_can_pick_winner():
    # Arrange
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for TestNet")
    account = get_account()
    vrfCoordinatorV2Mock = get_contract("vrf_coordinator_v2")
    subId = config["networks"][network.show_active()]["subscriptionId"]
    
    # Act
    # Checking if we have any subscriptions created, if not create one
    if subId == 0:
        print("Creating Subscritpion...")
        create_sub_tx = vrfCoordinatorV2Mock.createSubscription({"from": account})
        time.sleep(60)
        subId = create_sub_tx.events["SubscriptionCreated"]["subId"]
        print("Subscription Created!")
        print(f'SubscriptionId: {subId}')
    
    # Checking subscription balance...
    balance, reqCount, owner, consumers = vrfCoordinatorV2Mock.getSubscription(subId)
    print(f'Your Subscription Current Balance Is: {balance}')
    
    # If balance is less than 1 LINK, fund subscription
    if balance < 1000000000000000000:
        link_token = get_contract("link_token")
        fund_sub_tx = link_token.transferAndCall(vrfCoordinatorV2Mock.address, FUND_AMOUNT, convert.to_bytes(subId), {"from": account})
        #fund_sub_tx = vrfCoordinatorV2Mock.fundSubscription(subId, link_amount, {"from": account})
        print("Funding Subscription...")
        fund_sub_tx.wait(1)
        balance_two, reqCount, owner, consumers = vrfCoordinatorV2Mock.getSubscription(subId)
        print(f'Your Subscription Balance Is: {balance_two}')
    
    # Deploying lottery...
    deploy_lottery()
    lottery = LotteryV2[-1]
    # Checking If Our Lottery Is Added To Consumer List
    # Adding Lottery Contract To Consumer List If It Is Not...
    bal, reqCount, owner, consumers = vrfCoordinatorV2Mock.getSubscription(subId)
    if lottery.address not in consumers:
        print(f'Adding Consumer...')
        add_consumer_tx = vrfCoordinatorV2Mock.addConsumer(subId, lottery.address, {"from": account})
        add_consumer_tx.wait(1)
        # We can add like looong sleep here to get below updated with our recent lottery.address
        print(f'Your Subscription Consumers: {consumers}')
    
    
    lottery.startLottery({"from": account})
    lottery.buyTicket({"from": account, "value": lottery.getEntryFee()})
    lottery.buyTicket({"from": account, "value": lottery.getEntryFee()})
    

    lottery.pickWinner({"from": account})
    time.sleep(180)
    
    # Assert
    assert lottery.winner() == account
    # <= 1 because we cannot withdraw everything, there will be always something left...
    assert lottery.balance() <= 1

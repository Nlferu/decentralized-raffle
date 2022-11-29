
from brownie import network, exceptions
from scripts.run_lottery import deploy_lottery_local
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, FUND_AMOUNT, get_account, get_contract
from web3 import Web3
import pytest


def test_get_entrance_fee_and_states():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only For Local Testing")
    account = get_account()
    subId = "0"
    lottery = deploy_lottery_local(subId)
    # Act
    lottery_closed = lottery.getLotteryState()
    lottery.startLottery({"from": account})
    lottery_opened = lottery.getLotteryState()
    """
    2000 ETH/USD
    usdEntryFee is 50$
    2000/1 == 50/x == 0.025
    """
    expected_entrance_fee = Web3.toWei(0.025, "ether")
    entrance_fee = lottery.getEntryFee()
    # Assert
    assert lottery_closed == "2"
    assert lottery_opened == "0"
    assert expected_entrance_fee == entrance_fee


def test_cant_enter_unless_started():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only For Local Testing")
    # Act / Assert
    subId = "0"
    lottery = deploy_lottery_local(subId)
    # Below says that if it will throw error that means we could't enter lottery, which is good as we need lottery to be started first
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.buyTicket({"from": get_account(), "value": lottery.getEntryFee()})


def test_can_buy_ticket():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only For Local Testing")
    subId = "0"
    lottery = deploy_lottery_local(subId)
    lottery.startLottery({"from": get_account()})
    # Act
    lottery.buyTicket({"from": get_account(), "value": lottery.getEntryFee()})
    # Assert
    players, players_amount = lottery.getPlayers()
    # We are checking if we have successfully added player to this lottery, so we check if 1st player account is our account for development network
    assert players[0] == get_account()


def test_lottery_picking_winner_and_getters():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only For Local Testing")
    account = get_account()
    vrfCoordinatorV2Mock = get_contract("vrf_coordinator_v2")
    create_sub_tx = vrfCoordinatorV2Mock.createSubscription()
    subId = create_sub_tx.return_value
    vrfCoordinatorV2Mock.fundSubscription(subId, FUND_AMOUNT, {"from": account})
    lottery = deploy_lottery_local(subId)
    vrfCoordinatorV2Mock.addConsumer(subId, lottery.address, {"from": account})
    # Act
    lottery.startLottery({"from": get_account()})
    lottery.buyTicket({"from": get_account(), "value": lottery.getEntryFee()})
    balance_before_picking = lottery.getLotteryBalance()
    players, players_amount = lottery.getPlayers()
    pick_winner_tx = lottery.pickWinner({"from": account})
    requestId = pick_winner_tx.events["RequestedLotteryWinner"]["requestId"]
    fulfill_tx = vrfCoordinatorV2Mock.fulfillRandomWords(requestId, lottery.address, {"from": account})
    prize, commission, success, sent = lottery.getLotteryTransactions()
    balance_after_picking = lottery.getLotteryBalance()
    players_after_picking, players_amount_after_picking = lottery.getPlayers()
    # Assert
    assert balance_before_picking > 1000
    assert players_amount > 0
    assert lottery.getWinner() == account
    assert lottery.s_randomWords(0) != 0
    assert commission > 0 
    assert prize > commission 
    assert success == True
    assert sent == True
    assert balance_after_picking < 1
    assert players_amount_after_picking == 0

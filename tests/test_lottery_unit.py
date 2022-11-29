
from brownie import network, convert, config, LotteryV2
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
   lottery = deploy_lottery_local()
   # Below says if it will throw error that means we could't enter lottery, which is good as we need lottery to be started first
   with pytest.raises(exceptions.VirtualMachineError):
      lottery.buyTicket({"from": get_account(), "value": lottery.getEntranceFee()})


def test_can_start_and_enter_lottery():
   # Arrange
   if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
      pytest.skip("Only For Local Testing")
   lottery = deploy_lottery()
   lottery.startLottery({"from": get_account()})
   # Act
   lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})
   # Assert
   # We are checking if we have successfully added player to this lottery, so we check if 1st player account is our account for development network
   assert lottery.players(0) == get_account()


def test_can_end_lottery():
   # Arrange
   if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
      pytest.skip("Only For Local Testing")
   lottery = deploy_lottery()
   lottery.startLottery({"from": get_account()})
   lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})
   fund_with_link(lottery)
   # Act
   lottery.endLottery({"from": get_account()})
   # Assert
   # Lottery state stands as following OPEN = 0, CLOSED = 1, CALCULATING_WINNER = 2
   assert lottery.lottery_state() == 2


def test_can_pick_winner_correctly():
    pass

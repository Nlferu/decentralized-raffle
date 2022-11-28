
from scripts.helpful_scripts import get_account, get_contract, LOCAL_BLOCKCHAIN_ENVIRONMENTS, FUND_AMOUNT
from brownie import convert, network, config, accounts, LotteryV2
import time

# For local network mock will provide all necessary data
# For testnet we are providing data in "brownie-config.yaml"


def main():
    run_lottery()


def run_lottery():
    account = get_account()
    vrfCoordinatorV2Mock = get_contract("vrf_coordinator_v2")
    # --------------------------------- Below Code Will Run Lottery Locally ---------------------------------
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        # 1. Create subscription
        # 2. Get subscription ID
        # 3. Fund subscription with LINK or ETH as VRF_v2 will convert ETH appropriately
        # 4. Deploy lottery with created above subId
        # 5. Add contract created to subscription list
        # 6. Start lottery
        # 7. Buy tickets (add participants)
        # 8. Fulfilling Request (Only For Local!!!)
        
        print("Running Lottery On Local Network...")
        # Creating Subscription And Getting SubscriptionId...
        create_sub_tx = vrfCoordinatorV2Mock.createSubscription()
        create_sub_tx.wait(1)
        subId = create_sub_tx.return_value
        # Second way to get subscription id
        subID = create_sub_tx.events["SubscriptionCreated"]["subId"]
        print(f'SubscriptionId: {subId, subID}')

        # Funding vrfCoordinatorV2Mock...
        balance, reqCount, owner, consumers = vrfCoordinatorV2Mock.getSubscription(subId)
        print(f'Your Subscription Balance Before Funding: {balance}')
        fund_sub_tx = vrfCoordinatorV2Mock.fundSubscription(subId, FUND_AMOUNT, {"from": account})
        fund_sub_tx.wait(1)
        balance_two, reqCount, owner, consumers = vrfCoordinatorV2Mock.getSubscription(subId)
        print(f'Your Subscription Balance Is: {balance_two}')

        # Deploying Lottery With Generated SubscriptionId...
        lottery = LotteryV2.deploy(
            get_contract("eth_usd_price_feed").address,
            get_contract("vrf_coordinator_v2").address,
            config["networks"][network.show_active()]["gasLane"],
            subId,
            config["networks"][network.show_active()]["callbackGasLimit"],
            {"from": account},
            publish_source = config["networks"][network.show_active()].get("verify", False),
        )
        print("Lottery Has Been Successfully Deployed!")

        # Adding Lottery Contract To Subscription List...
        add_consumer_tx = vrfCoordinatorV2Mock.addConsumer(subId, lottery.address, {"from": account})
        add_consumer_tx.wait(1)

        # Starting Lottery...
        start_lottery()

        # Buying Tickets...
        buy_ticket()
        
        # Generating Random Number And Picking Winner
        pick_winner_tx = lottery.pickWinner({"from": account})
        pick_winner_tx.wait(1)
        players, players_amount = lottery.getPlayers()
        print(f'Players Who Participated: {players}')
        print(f'Players Amount: {players_amount}')

        # Fulfilling The Request...
        requestId = pick_winner_tx.events["RequestedLotteryWinner"]["requestId"]
        print(f'RequestId: {requestId}')
        fulfill_tx = vrfCoordinatorV2Mock.fulfillRandomWords(requestId, lottery.address, {"from": account})
        fulfill_tx.wait(1)
        success = fulfill_tx.events["RandomWordsFulfilled"]["success"]
        print(f'Success is: {success}')
        if(success):
            randomWords = lottery.s_randomWords(0)
            print(f'Random Number Is: {randomWords}')

        # We Can Listen For Outputs In Two Ways!
        winner = fulfill_tx.events["WinnerPicked"]["recentWinner"]
        print(f'Recent Winner Is: {winner}')
        print("Winner Picked!")
        print(f'{lottery.getWinner()} is the new winner!')

        # Checking If Players Array Has Been Cleared...
        players, players_amount = lottery.getPlayers()
        print(f'Players After Winner Picked: {players}')
        print(f'Players Amount: {players_amount}')
    
    # --------------------------------- Below Code Will Run Lottery On Testnet ---------------------------------
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        # 1. Create subscription or get subscription ID
        # 2. Fund subscription if its balance is less than 1 LINK
        # 3. Deploy lottery with created above subId
        # 4. Add contract created to subscription list if not added
        # 5. Start lottery
        # 6. Buy tickets (add participants)
        # 7. Generate random number and pick winner
        # 8. Listen for fulfillRandomWords transfer money events
        
        print("Running Lottery On TestNet...")
        subId = config["networks"][network.show_active()]["subscriptionId"]

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

        # Deploying lottery if it doesn't exist...
        if len(LotteryV2) == 0:
            print("Deploying Lottery...")
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

        # Starting lottery...
        lottery_state = lottery.getLotteryState()
        print(f'Current Lottery State: {lottery_state}')
        if lottery_state == "2":
            print("Starting Lottery...")
            start_lottery()
            time.sleep(10)
        
        # Buying lottery tickets...
        lottery_state2 = lottery.getLotteryState()
        print(f'Current Lottery State: {lottery_state2}')
        if lottery_state2 == "0":
            print("Buying Lottery Tickets...")
            buy_ticket()
            time.sleep(10)

        lottery_balance_wei = lottery.getLotteryBalance({"from": account})
        lottery_balance = float(lottery_balance_wei / 10**18)
        print(f'Current Lottery Contract Balance Is: {lottery_balance} ETH')

        # Picking winner...
        print("Picking winner...")
        pick_winner_tx = lottery.pickWinner({"from": account})
        pick_winner_tx.wait(1)
        time.sleep(180)
        players, players_amount = lottery.getPlayers()
        print(f'Updated Players List: {players}')
        print(f'Players Amount: {players_amount}')
        print(f'{lottery.getWinner()} is the new winner!')

        lottery_state3 = lottery.getLotteryState()
        print(f'Current Lottery State: {lottery_state3}')

        prize_wei, commission_wei, success, sent = lottery.getLotteryTransactions()
        prize = float(prize_wei / 10**18)
        commission = float(commission_wei / 10**18)
        print(f'Lottery Prize Pool: {prize} ETH')
        print(f'Lottery Commission: {commission} ETH')
        print(f'Lottery Transfers: {success} and {sent}')
        if(success):
            randomWords = lottery.s_randomWords(0)
            print(f'Random Number Was: {randomWords}')

        end_lottery_balance_wei = lottery.getLotteryBalance({"from": account})
        end_lottery_balance = float(end_lottery_balance_wei / 10**18)
        print(f'End Lottery Contract Balance Is: {end_lottery_balance}')


def deploy_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
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
    else:
        print("This Function Doesn't Work On Local Testnet")
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
    # Buying 1st ticket...
    buying_ticket_tx_1 = lottery.buyTicket({"from": account, "value": entry_fee})
    buying_ticket_tx_1.wait(1)
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        # Buying 2nd ticket...
        buying_ticket_tx_1 = lottery.buyTicket({"from": accounts[1], "value": entry_fee})
        buying_ticket_tx_1.wait(1)
        # Buying 3rd ticket...
        buying_ticket_tx_1 = lottery.buyTicket({"from": accounts[2], "value": entry_fee})
        buying_ticket_tx_1.wait(1)
    print("You Have Successfully Bought Lottery Tickets!")
    players, players_amount = lottery.getPlayers()
    print(f'Participating Players: {players}')
    print(f'Players Amount: {players_amount}')

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Entry Fee
// If you have ticket, you can take part in lottery
// Picking random winner based on random number

import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";
//import "@chainlink/contracts/src/v0.8/interfaces/LinkTokenInterface.sol";
import "@chainlink/contracts/src/v0.8/interfaces/VRFCoordinatorV2Interface.sol";
import "@chainlink/contracts/src/v0.8/VRFConsumerBaseV2.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract LotteryV2 is VRFConsumerBaseV2, Ownable {

    // Below stores all addresses that bought lottery ticket, same addresses can appear more than once, which will increase chance to win for that address.
    // Address is payable, because we will want to pay winner whole gathered amount (corrected by commission for owners of lottery)
    address payable[] private players;

    // VRFConsumerBaseV2 storage variables -> we add "_i" to all immutable variables
    VRFCoordinatorV2Interface private immutable i_vrfCoordinator;
    bytes32 private immutable i_gasLimit;
    uint64 private immutable i_subsId;
    uint32 private immutable i_callbackGasLimit;
    uint16 private constant REQUEST_CONFIRMATIONS = 3;
    uint32 private constant NUM_WORDS = 1;

    // Variable storing minimum entrance fee.
    uint256 private entryFee;
    // Price feed source.
    AggregatorV3Interface internal price_feed;

    /* Events */
    event LotteryEntrance(address indexed player);
    event RequestedLotteryWinner(uint256 indexed requestId);

    constructor(address _vrfCoordinator, bytes32 _gasLimit, uint64 _subsId, uint32 _callbackGasLimit) VRFConsumerBaseV2(_vrfCoordinator) {
        i_vrfCoordinator = VRFCoordinatorV2Interface(_vrfCoordinator);
        i_gasLimit = _gasLimit;
        i_subsId = _subsId;
        i_callbackGasLimit = _callbackGasLimit;
    }

    // Below function allows you to buy lottery participation ticket.
    function buyTicket() public payable {
        require(msg.value >= getEntryFee(), "Not Enough ETH, you have to pay to participate in lottery!");
        players.push(payable(msg.sender));
        emit LotteryEntrance(msg.sender);
    }

    // Below function defines minimal fee to use buyTicket() function.
    function getEntryFee() public view returns (uint256) {
        (, int256 price, , , ) = price_feed.latestRoundData();
        // Below has to be expressed with 18 decimals. From Chainlink pricefeed, we know ETH/USD has 8 decimals, so we need to multiply by 10^10.
        uint256 adjustedPrice = uint256(price) * 10**10;
        // We cannot return decimals, hence we need to express 50$ with 50 * 10*18 / 2000 (adjusted price of ETH).
        uint256 costToEnter = (entryFee * 10**18) / adjustedPrice;
        return costToEnter;
    }

    function getPlayers() public view returns (address payable[] memory) {
        return players;
    }

    function getRandomNumber() public onlyOwner {
        // 1. Create subscription
        // 2. Get subscription ID
        // 3. Fund subscription with LINK
        // 4. Add contract created to subscription list

        uint256 requestId = i_vrfCoordinator.requestRandomWords(i_gasLimit, i_subsId, REQUEST_CONFIRMATIONS, i_callbackGasLimit, NUM_WORDS);
        emit RequestedLotteryWinner(requestId);
    }

    // function createSub() public onlyOwner {
    //     subsId = COORDINATOR.createSubscription();
    // }

    // function getSub() public view onlyOwner returns (uint64) {
    //     return subsId;
    // }

    // We have to override fulfillRandomWords() as it is "virtual" -> which means it expecting to be overwritten, otherwise we cant compile code.
     function fulfillRandomWords(uint256 requestId, uint256[] memory randomWords) internal override {

     }

    function pickWinner() public onlyOwner {

    }

    // Below function allows us as Owners of lottery to withdraw money gathered on this contract.
    function withdraw() public payable onlyOwner {
        payable(msg.sender).transfer(address(this).balance);
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Entry Fee
// If you have ticket, you can take part in lottery
// Picking random winner based on random number

import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract LotteryV2 is Ownable {

    // Below stores all addresses that bought lottery ticket, same addresses can appear more than once, which will increase chance to win for that address.
    // Address is payable, because we will want to pay winner whole gathered amount (corrected by commission for owners of lottery)
    address payable[] public players;

    // Variable storing minimum fee.
    uint256 public usdEntryFee;
    // Price feed source.
    AggregatorV3Interface internal ethUsdPriceFeed;

    // Below function allows you to buy lottery participation ticket.
    function buyTicket() public payable {
        require(msg.value >= getMinimumFee(), "Not Enough ETH, you have to pay to participate in lottery!");
        players.push(payable(msg.sender));
    }

    // Below function defines minimal fee to use buyTicket() function.
    function getMinimumFee() public view returns (uint256) {
        (, int256 price, , , ) = ethUsdPriceFeed.latestRoundData();
        // Below has to be expressed with 18 decimals. From Chainlink pricefeed, we know ETH/USD has 8 decimals, so we need to multiply by 10^10.
        uint256 adjustedPrice = uint256(price) * 10**10;
        // We cannot return decimals, hence we need to express 50$ with 50 * 10*18 / 2000 (adjusted price of ETH).
        uint256 costToEnter = (usdEntryFee * 10**18) / adjustedPrice;
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
    }

    function pickWinner() public onlyOwner {

    }

    // Below function allows us as Owners of lottery to withdraw money gathered on this contract.
    function withdraw() public payable onlyOwner {
        payable(msg.sender).transfer(address(this).balance);
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract UserTokenTracker {
    struct TokenRecord {
        uint256 totalEarned;
        uint256 totalSpent;
        uint256[] rewardTimestamps;
    }

    mapping(address => TokenRecord) public userTokens;

    event TokensEarned(address indexed user, uint256 amount, string reason);
    event TokensSpent(address indexed user, uint256 amount, string reason);

    function earnTokens(address _user, uint256 _amount, string memory _reason) public {
        userTokens[_user].totalEarned += _amount;
        userTokens[_user].rewardTimestamps.push(block.timestamp);

        emit TokensEarned(_user, _amount, _reason);
    }

    function spendTokens(address _user, uint256 _amount, string memory _reason) public {
        require(userTokens[_user].totalEarned >= _amount, "Insufficient tokens");

        userTokens[_user].totalSpent += _amount;

        emit TokensSpent(_user, _amount, _reason);
    }

    function getUserTokenBalance(address _user) public view returns (uint256) {
        return userTokens[_user].totalEarned - userTokens[_user].totalSpent;
    }
}
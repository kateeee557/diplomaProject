// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract UserAddressFactory {
    mapping(address => address) public userWallets;
    event WalletCreated(address indexed user, address wallet);

    function createUserWallet(address _user) public returns (address) {
        require(userWallets[_user] == address(0), "Wallet already exists");

        address newWallet = address(new UserWallet(_user));
        userWallets[_user] = newWallet;

        emit WalletCreated(_user, newWallet);
        return newWallet;
    }

    function getUserWallet(address _user) public view returns (address) {
        return userWallets[_user];
    }
}

contract UserWallet {
    address public owner;
    uint256 public balance;

    constructor(address _owner) {
        owner = _owner;
    }

    receive() external payable {
        balance += msg.value;
    }

    function withdraw(uint256 amount) public {
        require(msg.sender == owner, "Not authorized");
        require(balance >= amount, "Insufficient balance");
        payable(owner).transfer(amount);
        balance -= amount;
    }
}
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title AcademicToken
 * @dev ERC20 token to reward students for timely submissions
 */
contract AcademicToken is ERC20, Ownable {
    // Events
    event TokensAwarded(address indexed student, uint256 amount, string reason);
    event TokensSpent(address indexed student, uint256 amount, string reason);

    constructor() ERC20("AcademicToken", "ACT") Ownable(msg.sender) {}

    /**
     * @dev Mint tokens to reward students
     * @param student Address of the student to reward
     * @param amount Amount of tokens to mint
     * @param reason Why tokens are being awarded
     */
    function awardTokens(address student, uint256 amount, string memory reason) public onlyOwner {
        _mint(student, amount);
        emit TokensAwarded(student, amount, reason);
    }

    /**
     * @dev Allow spending tokens for benefits
     * @param student Address of the student spending tokens
     * @param amount Amount of tokens to spend
     * @param reason Why tokens are being spent
     */
    function spendTokens(address student, uint256 amount, string memory reason) public onlyOwner {
        require(balanceOf(student) >= amount, "Insufficient token balance");
        _burn(student, amount);
        emit TokensSpent(student, amount, reason);
    }
}
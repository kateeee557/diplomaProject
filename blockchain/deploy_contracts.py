import json
import os
import time
import logging
from web3 import Web3
from solcx import compile_source, install_solc
import config as config_module

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Install solc compiler if not already installed
try:
    install_solc(version='0.8.0')
except Exception as e:
    logger.warning(f"Failed to install solc: {e}")
    logger.warning("You may need to install solcx manually.")

class ContractDeployer:
    def __init__(self, config_name='development'):
        self.config = config_module.config[config_name]()
        self.w3 = Web3(Web3.HTTPProvider(self.config.BLOCKCHAIN_PROVIDER))

        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to blockchain provider")

        self.account = self.w3.eth.accounts[self.config.DEPLOYER_ACCOUNT_INDEX]
        logger.info(f"Using deployer account: {self.account}")

        # Create directories if they don't exist
        self.blockchain_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'blockchain')
        self.contracts_dir = os.path.join(self.blockchain_dir, 'contracts')
        self.abis_dir = os.path.join(self.blockchain_dir, 'abis')
        self.address_file = os.path.join(self.blockchain_dir, 'deployed_addresses.json')

        for directory in [self.blockchain_dir, self.contracts_dir, self.abis_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"Created directory: {directory}")

        # Load previously deployed addresses if they exist
        self.deployed_addresses = {}
        if os.path.exists(self.address_file):
            with open(self.address_file, 'r') as f:
                self.deployed_addresses = json.load(f)
                logger.info(f"Loaded deployed contract addresses: {self.deployed_addresses}")

    def save_deployed_addresses(self):
        """Save deployed contract addresses to file"""
        with open(self.address_file, 'w') as f:
            json.dump(self.deployed_addresses, f, indent=2)
        logger.info(f"Saved deployed contract addresses to {self.address_file}")

    def compile_contract(self, contract_file_path):
        """Compile a solidity contract file"""
        with open(contract_file_path, 'r') as f:
            source = f.read()

        compiled_sol = compile_source(source)

        # Get contract data from compilation result
        contract_id, contract_interface = compiled_sol.popitem()
        return contract_interface

    def deploy_contract(self, contract_interface, *args):
        """Deploy a contract with given arguments"""
        contract = self.w3.eth.contract(
            abi=contract_interface['abi'],
            bytecode=contract_interface['bin']
        )

        # Estimate gas
        gas_estimate = contract.constructor(*args).estimate_gas()

        # Deploy contract
        tx_hash = contract.constructor(*args).transact({
            'from': self.account,
            'gas': gas_estimate
        })

        # Wait for transaction receipt
        logger.info(f"Waiting for transaction receipt...")
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        contract_address = tx_receipt.contractAddress

        return contract_address, contract_interface['abi']

    def check_and_deploy_contracts(self):
        """Check if contracts are deployed, deploy if needed"""
        try:
            # AcademicToken contract
            token_file = os.path.join(self.contracts_dir, 'AcademicToken.sol')
            if not os.path.exists(token_file):
                with open(token_file, 'w') as f:
                    f.write(ACADEMIC_TOKEN_CONTRACT)

            token_address = self.deployed_addresses.get('token_contract')
            if not token_address or not self.check_contract_exists(token_address):
                logger.info("Deploying AcademicToken contract...")
                token_interface = self.compile_contract(token_file)
                token_address, token_abi = self.deploy_contract(token_interface)
                self.deployed_addresses['token_contract'] = token_address

                # Save ABI
                with open(os.path.join(self.abis_dir, 'token_abi.json'), 'w') as f:
                    json.dump(token_abi, f, indent=2)

                self.save_deployed_addresses()
                logger.info(f"AcademicToken deployed at: {token_address}")
            else:
                logger.info(f"Using existing AcademicToken at: {token_address}")

            # DocumentNFT contract
            document_file = os.path.join(self.contracts_dir, 'DocumentNFT.sol')
            if not os.path.exists(document_file):
                with open(document_file, 'w') as f:
                    f.write(DOCUMENT_NFT_CONTRACT)

            document_address = self.deployed_addresses.get('document_contract')
            if not document_address or not self.check_contract_exists(document_address):
                logger.info("Deploying DocumentNFT contract...")
                document_interface = self.compile_contract(document_file)
                document_address, document_abi = self.deploy_contract(document_interface, token_address)
                self.deployed_addresses['document_contract'] = document_address

                # Save ABI
                with open(os.path.join(self.abis_dir, 'document_abi.json'), 'w') as f:
                    json.dump(document_abi, f, indent=2)

                self.save_deployed_addresses()
                logger.info(f"DocumentNFT deployed at: {document_address}")
            else:
                logger.info(f"Using existing DocumentNFT at: {document_address}")

            # UserWalletFactory contract
            wallet_file = os.path.join(self.contracts_dir, 'UserAddressFactory.sol')
            if not os.path.exists(wallet_file):
                with open(wallet_file, 'w') as f:
                    f.write(USER_WALLET_FACTORY_CONTRACT)

            wallet_address = self.deployed_addresses.get('wallet_factory_contract')
            if not wallet_address or not self.check_contract_exists(wallet_address):
                logger.info("Deploying UserWalletFactory contract...")
                wallet_interface = self.compile_contract(wallet_file)
                wallet_address, wallet_abi = self.deploy_contract(wallet_interface)
                self.deployed_addresses['wallet_factory_contract'] = wallet_address

                # Save ABI
                with open(os.path.join(self.abis_dir, 'user_wallet_factory_abi.json'), 'w') as f:
                    json.dump(wallet_abi, f, indent=2)

                self.save_deployed_addresses()
                logger.info(f"UserWalletFactory deployed at: {wallet_address}")
            else:
                logger.info(f"Using existing UserWalletFactory at: {wallet_address}")

            # UserTokenTracker contract
            token_tracker_file = os.path.join(self.contracts_dir, 'UserTokenTracker.sol')
            if not os.path.exists(token_tracker_file):
                with open(token_tracker_file, 'w') as f:
                    f.write(USER_TOKEN_TRACKER_CONTRACT)

            token_tracker_address = self.deployed_addresses.get('token_tracker_contract')
            if not token_tracker_address or not self.check_contract_exists(token_tracker_address):
                logger.info("Deploying UserTokenTracker contract...")
                token_tracker_interface = self.compile_contract(token_tracker_file)
                token_tracker_address, token_tracker_abi = self.deploy_contract(token_tracker_interface)
                self.deployed_addresses['token_tracker_contract'] = token_tracker_address

                # Save ABI
                with open(os.path.join(self.abis_dir, 'user_token_tracker_abi.json'), 'w') as f:
                    json.dump(token_tracker_abi, f, indent=2)

                self.save_deployed_addresses()
                logger.info(f"UserTokenTracker deployed at: {token_tracker_address}")
            else:
                logger.info(f"Using existing UserTokenTracker at: {token_tracker_address}")

            return self.deployed_addresses

        except Exception as e:
            logger.error(f"Error deploying contracts: {e}")
            raise

    def check_contract_exists(self, address):
        """Check if a contract exists at the given address"""
        try:
            # Check if there's code at the address
            code = self.w3.eth.get_code(address)
            return code != b'' and code != '0x'
        except Exception as e:
            logger.error(f"Error checking contract at {address}: {e}")
            return False

# Contract source code
ACADEMIC_TOKEN_CONTRACT = '''// SPDX-License-Identifier: MIT
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
}'''

DOCUMENT_NFT_CONTRACT = '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

interface AcademicToken {
    function awardTokens(address student, uint256 amount, string memory reason) external;
}

/**
 * @title DocumentNFT
 * @dev ERC721 token representing academic documents with immutability
 */
contract DocumentNFT is ERC721URIStorage, Ownable {
    struct Document {
        string fileHash;
        address uploader;
        uint256 timestamp;
        string metadata;
        bool isAssignment;
        uint256 deadline; // 0 if not applicable
    }

    // Document storage
    Document[] public documents;
    mapping(string => bool) private hashExists;
    mapping(uint256 => uint256) private gradeRecords; // tokenId => grade hash

    // Academic token contract
    AcademicToken private academicToken;

    // Constants
    uint256 private constant ON_TIME_REWARD = 10 * 10**18; // 10 tokens

    // Events
    event DocumentMinted(uint256 indexed tokenId, string fileHash, address uploader, string metadata);
    event GradeRecorded(uint256 indexed tokenId, uint256 gradeHash);

    constructor(address _tokenAddress) ERC721("Academic Document", "ADOC") Ownable(msg.sender) {
        academicToken = AcademicToken(_tokenAddress);
    }

    /**
     * @dev Create a new document NFT
     * @param fileHash Hash of the uploaded file
     * @param metadata Additional information about the document
     * @param isAssignment Whether this is an assignment submission
     * @param deadline Deadline timestamp (0 if not an assignment)
     * @return tokenId of the new NFT
     */
    function mintDocument(
        string memory fileHash,
        string memory metadata,
        bool isAssignment,
        uint256 deadline
    ) public returns (uint256) {
        require(!hashExists[fileHash], "Document already exists");

        uint256 tokenId = documents.length;
        documents.push(Document({
            fileHash: fileHash,
            uploader: msg.sender,
            timestamp: block.timestamp,
            metadata: metadata,
            isAssignment: isAssignment,
            deadline: deadline
        }));

        hashExists[fileHash] = true;
        _mint(msg.sender, tokenId);

        // If this is an assignment submission before deadline, reward the student
        if (isAssignment && deadline != 0 && block.timestamp <= deadline) {
            academicToken.awardTokens(
                msg.sender,
                ON_TIME_REWARD,
                "On-time assignment submission"
            );
        }

        emit DocumentMinted(tokenId, fileHash, msg.sender, metadata);
        return tokenId;
    }

    /**
     * @dev Record grade for an assignment
     * @param tokenId ID of the document NFT
     * @param gradeHash Hash of the grade information
     */
    function recordGrade(uint256 tokenId, uint256 gradeHash) public onlyOwner {
        require(_exists(tokenId), "Document does not exist");
        require(documents[tokenId].isAssignment, "Not an assignment");

        gradeRecords[tokenId] = gradeHash;
        emit GradeRecorded(tokenId, gradeHash);
    }

    /**
     * @dev Verify if a document exists with the given hash
     * @param fileHash Hash to verify
     * @return bool whether the document exists
     */
    function verifyDocument(string memory fileHash) public view returns (bool) {
        return hashExists[fileHash];
    }

    /**
     * @dev Get document count
     * @return uint256 count of documents
     */
    function getDocumentCount() public view returns (uint256) {
        return documents.length;
    }

    /**
     * @dev Get document details
     * @param tokenId Token ID of the document
     * @return Document struct with document details
     */
    function getDocument(uint256 tokenId) public view returns (
        string memory fileHash,
        address uploader,
        uint256 timestamp,
        string memory metadata,
        bool isAssignment,
        uint256 deadline
    ) {
        require(_exists(tokenId), "Document does not exist");
        Document memory doc = documents[tokenId];
        return (
            doc.fileHash,
            doc.uploader,
            doc.timestamp,
            doc.metadata,
            doc.isAssignment,
            doc.deadline
        );
    }

    /**
     * @dev Check if a document was submitted before deadline
     * @param tokenId Document token ID
     * @return bool whether submission was on time
     */
    function isSubmittedOnTime(uint256 tokenId) public view returns (bool) {
        require(_exists(tokenId), "Document does not exist");
        Document memory doc = documents[tokenId];

        if (!doc.isAssignment || doc.deadline == 0) {
            return false;
        }

        return doc.timestamp <= doc.deadline;
    }

    /**
     * @dev Get grade for a document
     * @param tokenId Document token ID
     * @return uint256 grade hash
     */
    function getGrade(uint256 tokenId) public view returns (uint256) {
        require(_exists(tokenId), "Document does not exist");
        return gradeRecords[tokenId];
    }
}'''

USER_WALLET_FACTORY_CONTRACT = '''// SPDX-License-Identifier: MIT
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
}'''

USER_TOKEN_TRACKER_CONTRACT = '''// SPDX-License-Identifier: MIT
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
}'''

def deploy_contracts():
    """Deploy all contracts and update config"""
    try:
        deployer = ContractDeployer()
        addresses = deployer.check_and_deploy_contracts()

        # Update config with deployed addresses
        update_config(addresses)

        return addresses
    except Exception as e:
        logger.error(f"Error during contract deployment: {e}")
        raise

def update_config(addresses):
    """Update the application config with deployed contract addresses"""
    try:
        config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.py')

        with open(config_file, 'r') as f:
            config_content = f.read()

        # Update token address
        if 'token_contract' in addresses:
            config_content = config_content.replace(
                "TOKEN_CONTRACT_ADDRESS = '0x'",
                f"TOKEN_CONTRACT_ADDRESS = '{addresses['token_contract']}'"
            )

        # Update document address
        if 'document_contract' in addresses:
            config_content = config_content.replace(
                "DOCUMENT_CONTRACT_ADDRESS = '0x'",
                f"DOCUMENT_CONTRACT_ADDRESS = '{addresses['document_contract']}'"
            )

        # Update wallet factory address
        if 'wallet_factory_contract' in addresses:
            config_content = config_content.replace(
                "USER_WALLET_FACTORY_ADDRESS = '0x'",
                f"USER_WALLET_FACTORY_ADDRESS = '{addresses['wallet_factory_contract']}'"
            )

        # Update token tracker address
        if 'token_tracker_contract' in addresses:
            config_content = config_content.replace(
                "USER_TOKEN_TRACKER_ADDRESS = '0x'",
                f"USER_TOKEN_TRACKER_ADDRESS = '{addresses['token_tracker_contract']}'"
            )

        with open(config_file, 'w') as f:
            f.write(config_content)

        logger.info(f"Updated config file with deployed contract addresses")
    except Exception as e:
        logger.error(f"Error updating config: {e}")

if __name__ == "__main__":
    deploy_contracts()
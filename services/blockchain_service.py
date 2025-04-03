from web3 import Web3
import json
import os
from flask import current_app
import logging

class BlockchainService:
    def __init__(self):
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Default settings for offline mode
        self.offline_mode = True
        self.blockchain_enabled = False
        self.w3 = None
        self.token_contract = None
        self.document_contract = None
        self.wallet_factory_contract = None
        self.token_tracker_contract = None
        self.token_address = None
        self.document_address = None
        self.wallet_factory_address = None
        self.token_tracker_address = None

        # Check if blockchain is enabled in config
        if not current_app.config.get('BLOCKCHAIN_ENABLED', False):
            self.logger.info("Blockchain is disabled in config, operating in offline mode")
            return

        # Initialize Web3 connection
        provider_url = current_app.config['BLOCKCHAIN_PROVIDER']

        # If blockchain provider is empty or None, operate in offline mode
        if not provider_url:
            self.logger.warning("No blockchain provider specified, operating in offline mode")
            return

        try:
            # Initialize Web3 connection
            self.w3 = Web3(Web3.HTTPProvider(provider_url))

            # Validate blockchain connection
            if not self.w3.is_connected():
                self.logger.error("Failed to connect to blockchain provider")
                return  # Stay in offline mode instead of raising exception

            # Connection successful - set flags
            self.offline_mode = False
            self.blockchain_enabled = True

            # Load contract ABIs
            abis_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'blockchain', 'abis')

            # Create abis directory if it doesn't exist
            if not os.path.exists(abis_path):
                os.makedirs(abis_path)

            # Load existing contract ABIs with error handling
            try:
                with open(os.path.join(abis_path, 'token_abi.json'), 'r') as token_file:
                    self.token_abi = json.load(token_file)
            except FileNotFoundError:
                self.logger.error("Token ABI file not found, using placeholder")
                self.token_abi = []  # Empty ABI as placeholder

            try:
                with open(os.path.join(abis_path, 'document_abi.json'), 'r') as document_file:
                    self.document_abi = json.load(document_file)
            except FileNotFoundError:
                self.logger.error("Document ABI file not found, using placeholder")
                self.document_abi = []  # Empty ABI as placeholder

            # Load new contract ABIs with error handling
            try:
                with open(os.path.join(abis_path, 'user_wallet_factory_abi.json'), 'r') as wallet_file:
                    self.wallet_factory_abi = json.load(wallet_file)
            except FileNotFoundError:
                self.logger.error("User Wallet Factory ABI file not found, using placeholder")
                self.wallet_factory_abi = []  # Empty ABI as placeholder

            try:
                with open(os.path.join(abis_path, 'user_token_tracker_abi.json'), 'r') as token_tracker_file:
                    self.token_tracker_abi = json.load(token_tracker_file)
            except FileNotFoundError:
                self.logger.error("User Token Tracker ABI file not found, using placeholder")
                self.token_tracker_abi = []  # Empty ABI as placeholder

            # Contract addresses from config
            self.token_address = current_app.config['TOKEN_CONTRACT_ADDRESS']
            self.document_address = current_app.config['DOCUMENT_CONTRACT_ADDRESS']
            self.wallet_factory_address = current_app.config.get('USER_WALLET_FACTORY_ADDRESS')
            self.token_tracker_address = current_app.config.get('USER_TOKEN_TRACKER_ADDRESS')

            # Initialize contract instances with proper error handling
            try:
                self.token_contract = self.w3.eth.contract(
                    address=self.token_address,
                    abi=self.token_abi
                )
            except Exception as e:
                self.logger.error(f"Failed to initialize token contract: {e}")
                self.token_contract = None

            try:
                self.document_contract = self.w3.eth.contract(
                    address=self.document_address,
                    abi=self.document_abi
                )
            except Exception as e:
                self.logger.error(f"Failed to initialize document contract: {e}")
                self.document_contract = None

            try:
                self.wallet_factory_contract = self.w3.eth.contract(
                    address=self.wallet_factory_address,
                    abi=self.wallet_factory_abi
                )
            except Exception as e:
                self.logger.error(f"Failed to initialize wallet factory contract: {e}")
                self.wallet_factory_contract = None

            try:
                self.token_tracker_contract = self.w3.eth.contract(
                    address=self.token_tracker_address,
                    abi=self.token_tracker_abi
                )
            except Exception as e:
                self.logger.error(f"Failed to initialize token tracker contract: {e}")
                self.token_tracker_contract = None

        except Exception as e:
            self.logger.error(f"Blockchain service initialization error: {e}")
            # Make sure we're in offline mode if there was an error
            self.w3 = None
            self.blockchain_enabled = False
            self.offline_mode = True

    def is_connected(self):
        """Check if blockchain service is connected and operational"""
        if self.w3 is None or not self.blockchain_enabled:
            return False

        try:
            return self.w3.is_connected()
        except:
            return False

    def get_account(self, index=0):
        """Get account from the connected node (for testing)"""
        if not self.is_connected():
            self.logger.warning("Blockchain not connected, returning fake address")
            return "0x0000000000000000000000000000000000000000"  # Fake address

        try:
            return self.w3.eth.accounts[index]
        except Exception as e:
            self.logger.error(f"Error getting blockchain account: {e}")
            return "0x0000000000000000000000000000000000000000"  # Fake address as fallback

    def create_user_wallet(self, user_address):
        """Create a new wallet for a user"""
        if not self.is_connected() or self.wallet_factory_contract is None:
            self.logger.warning("Blockchain not connected or wallet factory not initialized, returning mock receipt")
            return {"transactionHash": b"0x0", "status": 1}  # Mock receipt

        try:
            tx_hash = self.wallet_factory_contract.functions.createUserWallet(
                user_address
            ).transact({'from': self.get_account()})

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            self.logger.info(f"User wallet created for {user_address}")
            return receipt
        except Exception as e:
            self.logger.error(f"Error creating user wallet: {e}")
            return {"transactionHash": b"0x0", "status": 0}  # Mock failed receipt

    def track_token_earning(self, user_address, amount, reason):
        """Track token earning for a user"""
        if not self.is_connected() or self.token_tracker_contract is None:
            self.logger.warning("Blockchain not connected or token tracker not initialized, returning mock receipt")
            return {"transactionHash": b"0x0", "status": 1}  # Mock receipt

        try:
            tx_hash = self.token_tracker_contract.functions.earnTokens(
                user_address, amount, reason
            ).transact({'from': self.get_account()})

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            self.logger.info(f"Tokens earned by {user_address}: {amount} for {reason}")
            return receipt
        except Exception as e:
            self.logger.error(f"Error tracking token earning: {e}")
            return {"transactionHash": b"0x0", "status": 0}  # Mock failed receipt

    def get_user_token_balance(self, user_address):
        """Get user's token balance from blockchain"""
        if not self.is_connected() or self.token_tracker_contract is None:
            self.logger.warning("Blockchain not connected or token tracker not initialized, returning default balance")
            return 10  # Default token balance for development

        try:
            balance = self.token_tracker_contract.functions.getUserTokenBalance(
                user_address
            ).call()
            return balance
        except Exception as e:
            self.logger.error(f"Error getting user token balance: {e}")
            return 0

    def verify_document(self, file_hash):
        """Verify a document's existence on blockchain"""
        if not self.is_connected() or self.document_contract is None:
            self.logger.warning("Blockchain not connected or document contract not initialized, returning mock verification")
            return True  # Mock verification for development

        try:
            if not isinstance(file_hash, str):
                self.logger.warning(f"Invalid hash type: {type(file_hash)}")
                return False

            result = self.document_contract.functions.verifyDocument(file_hash).call()
            self.logger.info(f"Document verification result for {file_hash}: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Document verification error: {e}")
            return False

    def mint_document_nft(self, file_hash, metadata, is_assignment, deadline, from_account):
        """Mint a new document NFT"""
        if not self.is_connected() or self.document_contract is None:
            self.logger.warning("Blockchain not connected or document contract not initialized, returning mock NFT data")
            return (
                {"transactionHash": b"0x0", "status": 1},  # Mock receipt
                "0x0000000000000000000000000000000000000000000000000000000000000000",  # Mock tx hash
                1  # Mock token ID
            )

        try:
            tx_hash = self.document_contract.functions.mintDocument(
                file_hash,
                metadata,
                is_assignment,
                deadline
            ).transact({'from': from_account})

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            # In a real implementation, we would parse the event logs to get the token ID
            # For simplicity in development, we'll just use a mock token ID
            token_id = 1  # This would normally come from event logs

            self.logger.info(f"Document minted with hash {file_hash}")
            return receipt, tx_hash.hex(), token_id
        except Exception as e:
            self.logger.error(f"Error minting document NFT: {e}")
            return (
                {"transactionHash": b"0x0", "status": 0},  # Mock failed receipt
                "0x0",  # Mock tx hash
                0  # Mock token ID (0 indicates failure)
            )

    def record_grade(self, token_id, grade_hash, from_account):
        """Record a grade for a document NFT"""
        if not self.is_connected() or self.document_contract is None:
            self.logger.warning("Blockchain not connected or document contract not initialized, returning mock grade data")
            return (
                {"transactionHash": b"0x0", "status": 1},  # Mock receipt
                "0x0000000000000000000000000000000000000000000000000000000000000000"  # Mock tx hash
            )

        try:
            tx_hash = self.document_contract.functions.recordGrade(
                token_id,
                grade_hash
            ).transact({'from': from_account})

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            self.logger.info(f"Grade recorded for token ID {token_id}")
            return receipt, tx_hash.hex()
        except Exception as e:
            self.logger.error(f"Error recording grade: {e}")
            return (
                {"transactionHash": b"0x0", "status": 0},  # Mock failed receipt
                "0x0"  # Mock tx hash
            )

    def get_grade(self, token_id):
        """Get the grade hash for a document NFT"""
        if not self.is_connected() or self.document_contract is None:
            self.logger.warning("Blockchain not connected or document contract not initialized, returning mock grade hash")
            return 12345  # Mock grade hash

        try:
            grade_hash = self.document_contract.functions.getGrade(token_id).call()
            return grade_hash
        except Exception as e:
            self.logger.error(f"Error getting grade: {e}")
            return 0

# Singleton pattern for blockchain service
blockchain_service = None

def get_blockchain_service():
    global blockchain_service
    if blockchain_service is None:
        blockchain_service = BlockchainService()
    return blockchain_service
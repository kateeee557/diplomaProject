#!/usr/bin/env python3
"""
Setup script for Academic Blockchain platform
This script initializes the project, creates necessary directories and files,
and sets up the database for first use.
"""

import os
import sys
import json
import shutil
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('setup.log')
    ]
)
logger = logging.getLogger(__name__)

def setup_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        'uploads',
        'blockchain/abis',
        'logs',
    ]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")
        else:
            logger.info(f"Directory already exists: {directory}")

def create_abi_files():
    """Create ABI files if they don't exist"""

    # User Wallet Factory ABI
    user_wallet_factory_abi = [
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "user",
                    "type": "address"
                },
                {
                    "indexed": False,
                    "internalType": "address",
                    "name": "wallet",
                    "type": "address"
                }
            ],
            "name": "WalletCreated",
            "type": "event"
        },
        {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "_user",
                    "type": "address"
                }
            ],
            "name": "createUserWallet",
            "outputs": [
                {
                    "internalType": "address",
                    "name": "",
                    "type": "address"
                }
            ],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "_user",
                    "type": "address"
                }
            ],
            "name": "getUserWallet",
            "outputs": [
                {
                    "internalType": "address",
                    "name": "",
                    "type": "address"
                }
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "",
                    "type": "address"
                }
            ],
            "name": "userWallets",
            "outputs": [
                {
                    "internalType": "address",
                    "name": "",
                    "type": "address"
                }
            ],
            "stateMutability": "view",
            "type": "function"
        }
    ]

    # User Token Tracker ABI
    user_token_tracker_abi = [
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "user",
                    "type": "address"
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "amount",
                    "type": "uint256"
                },
                {
                    "indexed": False,
                    "internalType": "string",
                    "name": "reason",
                    "type": "string"
                }
            ],
            "name": "TokensEarned",
            "type": "event"
        },
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "user",
                    "type": "address"
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "amount",
                    "type": "uint256"
                },
                {
                    "indexed": False,
                    "internalType": "string",
                    "name": "reason",
                    "type": "string"
                }
            ],
            "name": "TokensSpent",
            "type": "event"
        },
        {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "_user",
                    "type": "address"
                },
                {
                    "internalType": "uint256",
                    "name": "_amount",
                    "type": "uint256"
                },
                {
                    "internalType": "string",
                    "name": "_reason",
                    "type": "string"
                }
            ],
            "name": "earnTokens",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "_user",
                    "type": "address"
                }
            ],
            "name": "getUserTokenBalance",
            "outputs": [
                {
                    "internalType": "uint256",
                    "name": "",
                    "type": "uint256"
                }
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "_user",
                    "type": "address"
                },
                {
                    "internalType": "uint256",
                    "name": "_amount",
                    "type": "uint256"
                },
                {
                    "internalType": "string",
                    "name": "_reason",
                    "type": "string"
                }
            ],
            "name": "spendTokens",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "",
                    "type": "address"
                }
            ],
            "name": "userTokens",
            "outputs": [
                {
                    "internalType": "uint256",
                    "name": "totalEarned",
                    "type": "uint256"
                },
                {
                    "internalType": "uint256",
                    "name": "totalSpent",
                    "type": "uint256"
                }
            ],
            "stateMutability": "view",
            "type": "function"
        }
    ]

    # Create ABI files if they don't exist
    abi_files = {
        'blockchain/abis/user_wallet_factory_abi.json': user_wallet_factory_abi,
        'blockchain/abis/user_token_tracker_abi.json': user_token_tracker_abi
    }

    for filepath, abi in abi_files.items():
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                json.dump(abi, f, indent=2)
            logger.info(f"Created ABI file: {filepath}")
        else:
            logger.info(f"ABI file already exists: {filepath}")

def update_config():
    """Update configuration file if needed"""
    config_path = 'config.py'

    if os.path.exists(config_path):
        # Backup existing config
        backup_path = f"config.py.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        shutil.copy(config_path, backup_path)
        logger.info(f"Backed up existing config to: {backup_path}")

        # Read existing config
        with open(config_path, 'r') as f:
            config_content = f.read()

        # Check if we need to update contract addresses
        if "'TOKEN_CONTRACT_ADDRESS = '0x...'" in config_content:
            logger.info("Updating placeholder contract addresses in config")
            config_content = config_content.replace(
                "TOKEN_CONTRACT_ADDRESS = '0x...'",
                "TOKEN_CONTRACT_ADDRESS = '0x1234567890123456789012345678901234567890'  # Placeholder address"
            )
            config_content = config_content.replace(
                "DOCUMENT_CONTRACT_ADDRESS = '0x...'",
                "DOCUMENT_CONTRACT_ADDRESS = '0x2345678901234567890123456789012345678901'  # Placeholder address"
            )
            config_content = config_content.replace(
                "USER_WALLET_FACTORY_ADDRESS = '0x...'",
                "USER_WALLET_FACTORY_ADDRESS = '0x3456789012345678901234567890123456789012'  # Placeholder address"
            )
            config_content = config_content.replace(
                "USER_TOKEN_TRACKER_ADDRESS = '0x...'",
                "USER_TOKEN_TRACKER_ADDRESS = '0x4567890123456789012345678901234567890123'  # Placeholder address"
            )

            # Add BLOCKCHAIN_ENABLED setting if it doesn't exist
            if "BLOCKCHAIN_ENABLED" not in config_content:
                config_content = config_content.replace(
                    "# Gas settings",
                    "# Switch to disable blockchain for development if needed\n    BLOCKCHAIN_ENABLED = True\n\n    # Gas settings"
                )

            # Write updated config
            with open(config_path, 'w') as f:
                f.write(config_content)

            logger.info("Updated config file")
        else:
            logger.info("Config file already updated")
    else:
        logger.warning(f"Config file not found: {config_path}")

def initialize_database():
    """Initialize database tables"""
    try:
        from app import create_app, db
        app = create_app('development')

        with app.app_context():
            db.create_all()
            logger.info("Database tables created")

            # Check if we have a test user
            from models.user import User
            from werkzeug.security import generate_password_hash

            if User.query.count() == 0:
                # Create test admin
                admin = User(
                    name='Admin User',
                    email='admin@example.com',
                    role='teacher',
                    blockchain_address='0x5678901234567890123456789012345678901234'
                )
                admin.password_hash = generate_password_hash('admin123')

                # Create test student
                student = User(
                    name='Student User',
                    email='student@example.com',
                    role='student',
                    blockchain_address='0x6789012345678901234567890123456789012345'
                )
                student.password_hash = generate_password_hash('student123')

                db.session.add(admin)
                db.session.add(student)
                db.session.commit()

                logger.info("Created test users:")
                logger.info("  Admin: admin@example.com / admin123")
                logger.info("  Student: student@example.com / student123")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

    return True

def main():
    """Main setup function"""
    logger.info("Starting Academic Blockchain project setup")

    # Create directories
    setup_directories()

    # Create ABI files
    create_abi_files()

    # Update config
    update_config()

    # Initialize database
    if initialize_database():
        logger.info("Database initialized successfully")
    else:
        logger.error("Database initialization failed")

    logger.info("Setup completed. You can now run the application with 'python run.py'")
    logger.info("Test accounts:")
    logger.info("  Admin: admin@example.com / admin123")
    logger.info("  Student: student@example.com / student123")

if __name__ == "__main__":
    main()
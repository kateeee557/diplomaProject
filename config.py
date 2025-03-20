import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'supersecretkey'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///academic_platform.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Blockchain configuration
    BLOCKCHAIN_PROVIDER = 'HTTP://127.0.0.1:7545'  # Local Ganache

    # Test contract addresses (fake addresses for development)
    TOKEN_CONTRACT_ADDRESS = '0x1234567890123456789012345678901234567890'  # Placeholder address
    DOCUMENT_CONTRACT_ADDRESS = '0x2345678901234567890123456789012345678901'  # Placeholder address
    USER_WALLET_FACTORY_ADDRESS = '0x3456789012345678901234567890123456789012'  # Placeholder address
    USER_TOKEN_TRACKER_ADDRESS = '0x4567890123456789012345678901234567890123'  # Placeholder address

    # Account for deploying contracts
    DEPLOYER_ACCOUNT_INDEX = 0

    # Blockchain transaction settings
    BLOCKCHAIN_REQUEST_TIMEOUT = 30  # seconds
    BLOCKCHAIN_MAX_RETRIES = 3

    # Gas settings
    GAS_LIMIT = 3000000
    GAS_PRICE = 20000000000  # 20 gwei

    # Switch to disable blockchain for development if needed
    BLOCKCHAIN_ENABLED = True

    # Logging configuration
    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
        },
        'handlers': {
            'default': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
            },
            'file': {
                'level': 'ERROR',
                'formatter': 'standard',
                'class': 'logging.FileHandler',
                'filename': 'blockchain_errors.log'
            }
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['default', 'file'],
                'level': 'INFO',
                'propagate': True
            },
            'blockchain': {
                'handlers': ['default', 'file'],
                'level': 'DEBUG',
                'propagate': False
            }
        }
    }

class TestingConfig(DevelopmentConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_academic_platform.db'
    BLOCKCHAIN_PROVIDER = 'http://127.0.0.1:7546'  # Test blockchain

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    # Blockchain settings from environment
    BLOCKCHAIN_PROVIDER = os.environ.get('BLOCKCHAIN_PROVIDER')
    TOKEN_CONTRACT_ADDRESS = os.environ.get('TOKEN_CONTRACT_ADDRESS')
    DOCUMENT_CONTRACT_ADDRESS = os.environ.get('DOCUMENT_CONTRACT_ADDRESS')
    USER_WALLET_FACTORY_ADDRESS = os.environ.get('USER_WALLET_FACTORY_ADDRESS')
    USER_TOKEN_TRACKER_ADDRESS = os.environ.get('USER_TOKEN_TRACKER_ADDRESS')

    # Production-specific blockchain settings
    DEPLOYER_ACCOUNT_INDEX = int(os.environ.get('DEPLOYER_ACCOUNT_INDEX', 0))
    BLOCKCHAIN_REQUEST_TIMEOUT = int(os.environ.get('BLOCKCHAIN_REQUEST_TIMEOUT', 60))
    BLOCKCHAIN_MAX_RETRIES = int(os.environ.get('BLOCKCHAIN_MAX_RETRIES', 3))
    GAS_LIMIT = int(os.environ.get('GAS_LIMIT', 3000000))
    GAS_PRICE = int(os.environ.get('GAS_PRICE', 20000000000))

    # Logging for production
    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'production': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
        },
        'handlers': {
            'file': {
                'level': 'ERROR',
                'formatter': 'production',
                'class': 'logging.FileHandler',
                'filename': '/var/log/academic_blockchain/errors.log'
            }
        },
        'loggers': {
            '': {
                'handlers': ['file'],
                'level': 'ERROR',
                'propagate': True
            }
        }
    }

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
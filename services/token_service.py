from app import db
from models.token import TokenTransaction
from models.user import User
from services.blockchain_service import get_blockchain_service
import logging

logger = logging.getLogger(__name__)

def get_token_balance(user_id):
    """Get token balance for a user"""
    # First calculate from database transactions
    rewards = TokenTransaction.query.filter_by(
        user_id=user_id,
        transaction_type='reward'
    ).all()

    spends = TokenTransaction.query.filter_by(
        user_id=user_id,
        transaction_type='spend'
    ).all()

    total_rewards = sum(t.amount for t in rewards)
    total_spends = sum(t.amount for t in spends)

    db_balance = total_rewards - total_spends

    # If the database has a balance, use it
    if db_balance > 0:
        return db_balance

    # Otherwise try blockchain if available
    user = User.query.get(user_id)
    if user and user.blockchain_address:
        try:
            blockchain = get_blockchain_service()
            if blockchain and blockchain.is_connected():
                balance = blockchain.get_user_token_balance(user.blockchain_address)
                return balance
        except Exception as e:
            logger.error(f"Error getting token balance from blockchain: {e}")

    # Return the database balance as default
    return db_balance

def record_token_reward(user_id, amount, description, transaction_hash=None):
    """Record a token reward transaction"""
    try:
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User not found: {user_id}")
            return None

        blockchain_tx = transaction_hash

        # Try to record on blockchain
        try:
            blockchain = get_blockchain_service()
            if blockchain and blockchain.is_connected() and user.blockchain_address:
                # Record on blockchain
                receipt = blockchain.track_token_earning(
                    user.blockchain_address,
                    amount,
                    description
                )

                if receipt and hasattr(receipt, 'transactionHash'):
                    blockchain_tx = receipt.transactionHash.hex()
                    logger.info(f"Token reward recorded on blockchain: {blockchain_tx}")
            else:
                logger.warning("Blockchain service not available - recording token reward in database only")
        except Exception as e:
            logger.error(f"Error recording token reward on blockchain: {e}")
            logger.warning("Continuing with database-only token reward")

        # Create local transaction record
        transaction = TokenTransaction(
            user_id=user_id,
            amount=amount,
            transaction_type='reward',
            description=description,
            blockchain_tx=blockchain_tx
        )

        db.session.add(transaction)

        # Fix: Make sure we update user's total_tokens_earned properly
        user.total_tokens_earned += amount

        db.session.commit()

        return transaction
    except Exception as e:
        logger.error(f"Token reward error: {e}")
        db.session.rollback()
        return None

def record_token_spend(user_id, amount, description, transaction_hash=None):
    """Record a token spend transaction"""
    try:
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User not found: {user_id}")
            return None

        # Check if user has enough tokens
        current_balance = get_token_balance(user_id)
        if current_balance < amount:
            logger.warning(f"Insufficient tokens for user {user_id}")
            return None

        blockchain_tx = transaction_hash

        # Try to record on blockchain
        try:
            blockchain = get_blockchain_service()
            if blockchain and blockchain.is_connected() and user.blockchain_address:
                # Record on blockchain
                receipt = blockchain.token_tracker_contract.functions.spendTokens(
                    user.blockchain_address,
                    amount,
                    description
                ).transact({'from': blockchain.get_account()})

                logger.info(f"Token spend recorded on blockchain")
            else:
                logger.warning("Blockchain service not available - recording token spend in database only")
        except Exception as e:
            logger.error(f"Error recording token spend on blockchain: {e}")
            logger.warning("Continuing with database-only token spend")

        # Create local transaction record
        transaction = TokenTransaction(
            user_id=user_id,
            amount=amount,
            transaction_type='spend',
            description=description,
            blockchain_tx=blockchain_tx
        )

        db.session.add(transaction)

        # Fix: Make sure we update user's total_tokens_spent properly
        user.total_tokens_spent += amount

        db.session.commit()

        return transaction
    except Exception as e:
        logger.error(f"Token spend error: {e}")
        db.session.rollback()
        return None

def get_user_transactions(user_id):
    """Get all token transactions for a user"""
    return TokenTransaction.query.filter_by(user_id=user_id).order_by(TokenTransaction.timestamp.desc()).all()
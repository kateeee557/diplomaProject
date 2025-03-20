from app import db
from models.token import TokenTransaction
from models.user import User
from services.blockchain_service import get_blockchain_service
import logging

logger = logging.getLogger(__name__)

def get_token_balance(user_id):
    """Get token balance for a user"""
    user = User.query.get(user_id)
    if not user or not user.blockchain_address:
        return 0

    try:
        # Try to get balance from blockchain
        blockchain = get_blockchain_service()
        if blockchain:
            balance = blockchain.get_user_token_balance(user.blockchain_address)
            return balance
        else:
            logger.warning("Blockchain service not available - using database balance")
    except Exception as e:
        logger.error(f"Error getting token balance from blockchain: {e}")
        logger.warning("Falling back to database balance")

    # Fallback to database balance
    transactions = TokenTransaction.query.filter_by(user_id=user_id).all()
    balance = sum(t.amount if t.transaction_type == 'reward' else -t.amount
                  for t in transactions)
    return balance

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
            if blockchain and user.blockchain_address:
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
        db.session.commit()

        # Update user's total tokens earned
        try:
            user.total_tokens_earned += amount
            db.session.commit()
        except Exception as e:
            logger.error(f"Error updating user token stats: {e}")

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
            if blockchain and user.blockchain_address:
                # Record on blockchain
                blockchain.token_tracker_contract.functions.spendTokens(
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

        # Update user's total tokens spent
        try:
            user.total_tokens_spent += amount
            db.session.commit()
        except Exception as e:
            logger.error(f"Error updating user token stats: {e}")

        return transaction
    except Exception as e:
        logger.error(f"Token spend error: {e}")
        db.session.rollback()
        return None

def get_user_transactions(user_id):
    """Get all token transactions for a user"""
    return TokenTransaction.query.filter_by(user_id=user_id).order_by(TokenTransaction.timestamp.desc()).all()
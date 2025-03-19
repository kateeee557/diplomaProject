from app import db
from models.token import TokenTransaction
from models.user import User
from services.blockchain_service import get_blockchain_service
import logging

def get_token_balance(user_id):
    """Get token balance for a user"""
    user = User.query.get(user_id)
    if not user or not user.blockchain_address:
        return 0

    try:
        # Try to get balance from blockchain
        blockchain = get_blockchain_service()

        if blockchain.is_connected():
            balance = blockchain.get_user_token_balance(user.blockchain_address)
            return balance
        else:
            logging.warning("Blockchain service not connected, using database balance")
    except Exception as e:
        logging.error(f"Error getting token balance: {e}")

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
            logging.error(f"User not found: {user_id}")
            return None

        blockchain = get_blockchain_service()
        blockchain_tx = transaction_hash

        # Record on blockchain if connected
        if blockchain.is_connected() and user.blockchain_address:
            try:
                receipt = blockchain.track_token_earning(
                    user.blockchain_address,
                    amount,
                    description
                )

                if receipt['status'] == 1:  # Success
                    blockchain_tx = receipt['transactionHash'].hex()
            except Exception as e:
                logging.error(f"Error recording token on blockchain: {e}")

        # Create local transaction record
        transaction = TokenTransaction(
            user_id=user_id,
            amount=amount,
            transaction_type='reward',
            description=description,
            blockchain_tx=blockchain_tx
        )

        db.session.add(transaction)

        # Update user's token stats
        user.update_token_stats(amount, 'reward')

        db.session.commit()
        return transaction
    except Exception as e:
        logging.error(f"Token reward error: {e}")
        db.session.rollback()
        return None

def record_token_spend(user_id, amount, description, transaction_hash=None):
    """Record a token spend transaction"""
    try:
        user = User.query.get(user_id)
        if not user:
            logging.error(f"User not found: {user_id}")
            return None

        blockchain = get_blockchain_service()
        blockchain_tx = transaction_hash

        # Check if user has enough tokens
        current_balance = get_token_balance(user_id)
        if current_balance < amount:
            logging.warning(f"Insufficient tokens for user {user_id}")
            return None

        # Record spend on blockchain if connected
        if blockchain.is_connected() and user.blockchain_address:
            try:
                result = blockchain.token_tracker_contract.functions.spendTokens(
                    user.blockchain_address,
                    amount,
                    description
                ).transact({'from': blockchain.get_account()})

                blockchain_tx = result.hex()
            except Exception as e:
                logging.error(f"Error spending tokens on blockchain: {e}")

        # Create local transaction record
        transaction = TokenTransaction(
            user_id=user_id,
            amount=amount,
            transaction_type='spend',
            description=description,
            blockchain_tx=blockchain_tx
        )

        db.session.add(transaction)

        # Update user's token stats
        user.update_token_stats(amount, 'spend')

        db.session.commit()
        return transaction
    except Exception as e:
        logging.error(f"Token spend error: {e}")
        db.session.rollback()
        return None

def get_user_transactions(user_id):
    """Get all token transactions for a user"""
    return TokenTransaction.query.filter_by(user_id=user_id).order_by(TokenTransaction.timestamp.desc()).all()
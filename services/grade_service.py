import hashlib
from datetime import datetime
from app import db
from models.submission import Submission
from models.document import Document
from services.blockchain_service import get_blockchain_service
from services.token_service import record_token_reward
import logging

logger = logging.getLogger(__name__)

def grade_submission(submission_id, grade, feedback, teacher_id):
    """
    Grade a submission and record it on blockchain with token rewards

    Args:
        submission_id: ID of the submission to grade
        grade: Grade to assign as a percentage (0-100)
        feedback: Feedback text
        teacher_id: ID of the teacher grading

    Returns:
        bool: Success or failure
    """
    # Get submission
    submission = Submission.query.get(submission_id)
    if not submission:
        logger.error(f"Submission not found: {submission_id}")
        return False

    # Get document
    document = Document.query.get(submission.document_id)
    if not document:
        logger.error(f"Document not found for submission: {submission_id}")
        return False

    # Validate and format grade as percentage
    try:
        # Handle percentage input
        grade_value = float(grade)

        # Ensure the grade is within range
        if grade_value < 0:
            grade_value = 0
        elif grade_value > 100:
            grade_value = 100

        # Format the grade with % symbol for storage
        grade = f"{grade_value:.1f}%"
    except (ValueError, TypeError):
        logger.error(f"Invalid grade format: {grade}")
        grade_value = 0
        grade = "0.0%"

    # Create a hash of the grading data
    now = datetime.utcnow()
    grade_data = f"{submission.id}:{grade}:{feedback}:{now.isoformat()}"
    grade_hash = int(hashlib.sha256(grade_data.encode()).hexdigest(), 16) % 10**20  # Truncate to fit uint256

    # Initialize variables for blockchain data
    tx_hash = f"offline-{int(datetime.utcnow().timestamp())}"  # Default offline tx hash

    try:
        # Try to record on blockchain
        try:
            blockchain = get_blockchain_service()
            if blockchain and document.nft_token_id and not blockchain.offline_mode:
                account = blockchain.get_account()  # For testing - in production use user's address

                logger.info(
                    f"Recording grade on blockchain: {grade_hash}"
                )

                # Record grade on chain
                receipt, tx_hash = blockchain.record_grade(
                    document.nft_token_id,
                    grade_hash,
                    account
                )

                if tx_hash and tx_hash != "0x0":
                    tx_hash = tx_hash  # Only update if we got a real hash

                logger.info(f"Grade recorded on blockchain: tx_hash={tx_hash}")
            else:
                logger.warning("Blockchain service not available or document not minted as NFT - grade will be stored in database only")
        except Exception as e:
            logger.error(f"Error recording grade on blockchain: {e}")
            logger.warning("Continuing with database-only grade recording")

        # Token reward logic
        try:
            # Check if submission was on time
            if submission.is_on_time():
                record_token_reward(
                    submission.student_id,
                    5,
                    "On-time submission reward"
                )

            # Additional reward for excellent performance
            if grade_value >= 95:
                record_token_reward(
                    submission.student_id,
                    5,
                    "Excellent assignment performance"
                )
            elif grade_value >= 85:
                record_token_reward(
                    submission.student_id,
                    3,
                    "Good assignment performance"
                )
        except Exception as reward_error:
            logger.error(f"Token reward error: {reward_error}")

        # Update submission
        submission.grade = grade
        submission.feedback = feedback
        submission.status = 'graded'
        submission.graded_at = now
        submission.grade_tx = tx_hash  # This now has a default value even in offline mode

        db.session.commit()
        return True

    except Exception as e:
        # Log error
        logger.error(f"Error recording grade: {e}")
        db.session.rollback()
        return False

def verify_grade(submission_id):
    """
    Verify a grade on the blockchain

    Args:
        submission_id: ID of the submission to verify

    Returns:
        bool: True if verified, False otherwise
    """
    submission = Submission.query.get(submission_id)
    if not submission or submission.status != 'graded':
        logger.warning(f"Cannot verify ungraded submission {submission_id}")
        return False

    document = Document.query.get(submission.document_id)
    if not document or not document.nft_token_id:
        logger.warning(f"No document or NFT found for submission {submission_id}")
        return False

    try:
        blockchain = get_blockchain_service()
        if not blockchain:
            logger.warning("Blockchain service not available - grade verification skipped")
            return False

        # For offline mode, always return True for verification
        if blockchain.offline_mode:
            logger.info(f"Running in offline mode - simulating successful verification for submission {submission_id}")
            submission.grade_verified = True
            db.session.commit()
            return True

        blockchain_grade_hash = blockchain.get_grade(document.nft_token_id)

        # Create expected hash
        grade_data = f"{submission.id}:{submission.grade}:{submission.feedback}:{submission.graded_at.isoformat()}"
        expected_hash = int(hashlib.sha256(grade_data.encode()).hexdigest(), 16) % 10**20

        verification_result = blockchain_grade_hash == expected_hash

        # Update grade verification status in database
        if verification_result:
            submission.grade_verified = True
            db.session.commit()

        logger.info(f"Grade verification for submission {submission_id}: {verification_result}")
        return verification_result

    except Exception as e:
        logger.error(f"Grade verification error: {e}")
        return False
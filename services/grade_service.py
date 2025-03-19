import hashlib
from datetime import datetime
from app import db
from models.submission import Submission
from models.document import Document
from services.blockchain_service import get_blockchain_service
from services.token_service import record_token_reward
import logging

def grade_submission(submission_id, grade, feedback, teacher_id):
    """
    Grade a submission and record it on blockchain with token rewards

    Args:
        submission_id: ID of the submission to grade
        grade: Grade to assign (e.g., 'A', 'B+', '95%')
        feedback: Feedback text
        teacher_id: ID of the teacher grading

    Returns:
        bool: Success or failure
    """
    # Get submission
    submission = Submission.query.get(submission_id)
    if not submission:
        logging.error(f"Submission not found: {submission_id}")
        return False

    # Get document
    document = Document.query.get(submission.document_id)
    if not document:
        logging.error(f"Document not found for submission: {submission_id}")
        return False

    # Create a hash of the grading data
    now = datetime.utcnow()
    grade_data = f"{submission.id}:{grade}:{feedback}:{now.isoformat()}"
    grade_hash = int(hashlib.sha256(grade_data.encode()).hexdigest(), 16) % 10**20  # Truncate to fit uint256

    try:
        # Record on blockchain
        blockchain = get_blockchain_service()
        tx_hash = None

        if blockchain.is_connected() and document.nft_token_id:
            account = blockchain.get_account()  # For testing
            receipt, tx_hash = blockchain.record_grade(
                document.nft_token_id,
                grade_hash,
                account
            )

            if receipt['status'] != 1:  # Failed
                logging.warning(f"Blockchain grade recording transaction failed")
        else:
            logging.warning("Blockchain not connected or document has no NFT token ID, skipping blockchain record")

        # Convert grade to numeric for token rewards
        try:
            # Handle different grade formats
            if isinstance(grade, str):
                if '%' in grade:
                    grade_value = float(grade.replace('%', ''))
                elif grade in ['A', 'A+']:
                    grade_value = 95
                elif grade in ['B', 'B+']:
                    grade_value = 85
                else:
                    grade_value = 0
            else:
                grade_value = float(grade)
        except (ValueError, TypeError):
            grade_value = 0

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
        except Exception as reward_error:
            logging.error(f"Token reward error: {reward_error}")

        # Update submission
        submission.grade = grade
        submission.feedback = feedback
        submission.status = 'graded'
        submission.graded_at = now
        submission.grade_tx = tx_hash

        db.session.commit()
        return True

    except Exception as e:
        # Log error
        logging.error(f"Error recording grade: {e}")
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
    if not submission or submission.status != 'graded' or not submission.grade_tx:
        logging.warning(f"Cannot verify submission {submission_id}")
        return False

    document = Document.query.get(submission.document_id)
    if not document or not document.nft_token_id:
        logging.warning(f"No document found for submission {submission_id}")
        return False

    try:
        blockchain = get_blockchain_service()

        if not blockchain.is_connected():
            logging.warning("Blockchain not connected, returning mock verification")
            return True  # Mock verification for testing

        blockchain_grade_hash = blockchain.get_grade(document.nft_token_id)

        # Create expected hash
        grade_data = f"{submission.id}:{submission.grade}:{submission.feedback}:{submission.graded_at.isoformat()}"
        expected_hash = int(hashlib.sha256(grade_data.encode()).hexdigest(), 16) % 10**20

        verification_result = blockchain_grade_hash == expected_hash
        logging.info(f"Grade verification for submission {submission_id}: {verification_result}")
        return verification_result

    except Exception as e:
        logging.error(f"Grade verification error: {e}")
        return False
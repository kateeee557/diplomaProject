import os
import hashlib
import uuid
from flask import current_app
from app import db
from models.document import Document
from services.blockchain_service import get_blockchain_service
import logging

logger = logging.getLogger(__name__)

def generate_unique_filename(original_filename):
    """Generate a unique filename to prevent collisions"""
    ext = os.path.splitext(original_filename)[1]
    return f"{uuid.uuid4().hex}{ext}"

def hash_file(file_path):
    """Generate SHA-256 hash for a file"""
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def verify_document_on_blockchain(document_id):
    """
    Verify a document's existence on the blockchain

    Args:
        document_id: ID of the document to verify

    Returns:
        bool: Whether the document is verified on blockchain
    """
    document = Document.query.get(document_id)
    if not document:
        logger.warning(f"Document not found: {document_id}")
        return False

    try:
        blockchain = get_blockchain_service()
        if not blockchain:
            logger.warning("Blockchain service not available - document verification skipped")
            return False

        logger.info(f"Attempting to verify document with hash: {document.hash}")

        # Verify document on blockchain
        result = blockchain.verify_document(document.hash)

        logger.info(f"Blockchain verification result: {result}")

        # Optional: Update document verification status in database
        if result:
            document.is_blockchain_verified = True
            db.session.commit()

        return result
    except Exception as e:
        logger.error(f"Verification error: {e}")
        return False

def save_uploaded_file(file, document_type, user_id, is_assignment=False, deadline=0):
    """
    Save an uploaded file and record it on blockchain

    Args:
        file: The uploaded file object
        document_type: Type of document (e.g., 'assignment_submission', 'syllabus')
        user_id: ID of the user uploading the file
        is_assignment: Whether this is an assignment submission
        deadline: Assignment deadline as timestamp (0 if not applicable)

    Returns:
        Document: The created document object
    """
    if not file:
        logger.warning("No file provided for upload")
        return None

    try:
        # Save file with unique name
        unique_filename = generate_unique_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)

        # Calculate hash
        file_hash = hash_file(file_path)

        # Initialize variables for blockchain data
        blockchain_tx = None
        nft_token_id = None

        # Record on blockchain
        try:
            blockchain = get_blockchain_service()
            if blockchain:
                account = blockchain.get_account()  # For testing - in production use user's address

                logger.info(f"Attempting to mint document on blockchain: {file_hash}")

                # Mint NFT
                receipt, tx_hash, token_id = blockchain.mint_document_nft(
                    file_hash,
                    f"{document_type} - {file.filename}",
                    is_assignment,
                    deadline,
                    account
                )

                logger.info(f"Document minted: tx_hash={tx_hash}, token_id={token_id}")

                blockchain_tx = tx_hash
                nft_token_id = token_id
            else:
                logger.warning("Blockchain service not available - document will be stored without blockchain verification")
        except Exception as blockchain_error:
            logger.error(f"Blockchain minting error: {blockchain_error}")
            logger.warning("Continuing without blockchain verification")

        # Create document record
        document = Document(
            user_id=user_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_type=file.content_type if hasattr(file, 'content_type') else 'application/octet-stream',
            file_size=os.path.getsize(file_path),
            hash=file_hash,
            blockchain_tx=blockchain_tx,
            nft_token_id=nft_token_id,
            document_type=document_type
        )

        db.session.add(document)
        db.session.commit()

        return document

    except Exception as general_error:
        logger.error(f"Document upload error: {general_error}")

        # Clean up file if it was created
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass

        return None

def detect_document_similarity(original_doc_path, submitted_doc_path, threshold=0.8):
    """
    Detect similarity between two documents

    Args:
        original_doc_path: Path to the original document
        submitted_doc_path: Path to the submitted document
        threshold: Similarity threshold (0-1)

    Returns:
        float: Similarity percentage
    """
    try:
        # Basic hash-based similarity check
        original_hash = hash_file(original_doc_path)
        submitted_hash = hash_file(submitted_doc_path)

        # Compute Levenshtein distance or other similarity metric
        # This is a placeholder - you'd typically use more sophisticated plagiarism detection
        similarity = 1 - (hamming_distance(original_hash, submitted_hash) / len(original_hash))

        return similarity if similarity >= threshold else 0
    except Exception as e:
        logger.error(f"Similarity detection error: {e}")
        return 0

def hamming_distance(hash1, hash2):
    """
    Compute Hamming distance between two hash strings

    Args:
        hash1: First hash string
        hash2: Second hash string

    Returns:
        int: Hamming distance
    """
    return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
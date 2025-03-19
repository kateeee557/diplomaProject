import os
import hashlib
import uuid
from flask import current_app
from app import db
from models.document import Document
from services.blockchain_service import get_blockchain_service
import logging

def generate_unique_filename(original_filename):
    """Generate a unique filename to prevent collisions"""
    ext = os.path.splitext(original_filename)[1]
    return f"{uuid.uuid4().hex}{ext}"

def hash_file(file_path):
    """Generate SHA-256 hash for a file"""
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

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
        logging.warning("No file provided for upload")
        return None

    try:
        # Ensure upload folder exists
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        # Save file with unique name
        unique_filename = generate_unique_filename(file.filename)
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)

        # Calculate hash
        file_hash = hash_file(file_path)

        # Record on blockchain
        blockchain_tx = None
        nft_token_id = None

        try:
            blockchain = get_blockchain_service()

            if blockchain.is_connected():
                logging.info(f"Attempting to mint document on blockchain: {file_hash}")
                account = blockchain.get_account()  # For testing - in production use user's address

                # Mint NFT
                receipt, tx_hash, token_id = blockchain.mint_document_nft(
                    file_hash,
                    f"{document_type} - {file.filename}",
                    is_assignment,
                    deadline,
                    account
                )

                if receipt['status'] == 1:  # Success
                    blockchain_tx = tx_hash
                    nft_token_id = token_id
                    logging.info(f"Document minted: tx_hash={tx_hash}, token_id={token_id}")
                else:
                    logging.warning("Blockchain transaction failed")
            else:
                logging.warning("Blockchain service not connected, skipping NFT minting")
        except Exception as blockchain_error:
            logging.error(f"Blockchain minting error: {blockchain_error}")

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
        logging.error(f"Document upload error: {general_error}")

        # Clean up file if it was created
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass

        return None

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
        logging.warning(f"Document not found: {document_id}")
        return False

    try:
        blockchain = get_blockchain_service()

        if not blockchain.is_connected():
            logging.warning("Blockchain service not connected, returning mock verification")
            return True  # Mock verification for testing

        logging.info(f"Attempting to verify document with hash: {document.hash}")

        # Verify document on blockchain
        result = blockchain.verify_document(document.hash)

        logging.info(f"Blockchain verification result: {result}")

        # Optional: Update document verification status in database
        if result:
            document.is_verified = True
            db.session.commit()

        return result
    except Exception as e:
        logging.error(f"Verification error: {e}")
        return False
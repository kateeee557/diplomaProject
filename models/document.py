from app import db
from datetime import datetime

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)  # Unique filename in storage
    original_filename = db.Column(db.String(255), nullable=False)  # Original upload name
    file_type = db.Column(db.String(50), nullable=False)  # MIME type
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    hash = db.Column(db.String(64), nullable=False, unique=True)  # SHA-256 hash, now with unique constraint
    blockchain_tx = db.Column(db.String(66), nullable=True)  # Transaction hash
    nft_token_id = db.Column(db.Integer, nullable=True)  # Token ID if minted as NFT
    document_type = db.Column(db.String(50), nullable=True)  # e.g., 'assignment', 'syllabus', etc.
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_blockchain_verified = db.Column(db.Boolean, default=False)  # Verification status

    # Relationships - ensure this doesn't conflict with Submission model
    submission = db.relationship('Submission', backref='document_ref', lazy=True, uselist=False)

    # New relationship for integrity violations
    violations = db.relationship('IntegrityViolation',
                                 foreign_keys='IntegrityViolation.original_document_id',
                                 backref='duplicate_of', lazy=True)

    def is_verified(self):
        """Check if document is verified on blockchain"""
        # If already marked as verified in the database, return True
        if self.is_blockchain_verified:
            return True

        # If has blockchain_tx and nft_token_id, consider verified
        if self.blockchain_tx is not None and self.nft_token_id is not None:
            # Update the verification flag
            self.is_blockchain_verified = True
            try:
                db.session.commit()
            except:
                db.session.rollback()
            return True

        # Otherwise, need to check on blockchain
        try:
            from services.document_service import verify_document_on_blockchain
            # Verify and update status
            is_verified = verify_document_on_blockchain(self.id)
            if is_verified:
                # Update verification status
                self.is_blockchain_verified = True
                if not self.blockchain_tx:
                    self.blockchain_tx = f"verified_{int(datetime.utcnow().timestamp())}"
                if not self.nft_token_id:
                    self.nft_token_id = 0  # Placeholder for now
                try:
                    db.session.commit()
                except:
                    db.session.rollback()
            return is_verified
        except Exception as e:
            print(f"Error verifying document: {e}")
            return False

    def file_path(self):
        """
        Returns the full path to the document file

        This method should be used whenever accessing the physical file
        to ensure consistent path handling across the application.
        """
        try:
            from flask import current_app
            import os

            # Make sure the UPLOAD_FOLDER configuration exists
            if 'UPLOAD_FOLDER' not in current_app.config:
                raise ValueError("UPLOAD_FOLDER not configured in app config")

            upload_folder = current_app.config['UPLOAD_FOLDER']

            # Ensure the upload folder exists
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            # Construct the full path to the file
            full_path = os.path.join(upload_folder, self.filename)

            return full_path
        except Exception as e:
            print(f"Error determining file path: {e}")
            # Return a safe fallback
            import os
            return os.path.join(os.getcwd(), 'uploads', self.filename)

    def __repr__(self):
        return f'<Document {self.id}: {self.original_filename}>'
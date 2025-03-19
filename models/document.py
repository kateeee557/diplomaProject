from app import db
from datetime import datetime

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)  # Unique filename in storage
    original_filename = db.Column(db.String(255), nullable=False)  # Original upload name
    file_type = db.Column(db.String(50), nullable=False)  # MIME type
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    hash = db.Column(db.String(64), nullable=False)  # SHA-256 hash
    blockchain_tx = db.Column(db.String(66), nullable=True)  # Transaction hash
    nft_token_id = db.Column(db.Integer, nullable=True)  # Token ID if minted as NFT
    document_type = db.Column(db.String(50), nullable=True)  # e.g., 'assignment', 'syllabus', etc.
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    submission = db.relationship('Submission', lazy=True, uselist=False)

    def is_verified(self):
        return self.blockchain_tx is not None and self.nft_token_id is not None

    def file_path(self):
        from flask import current_app
        import os
        return os.path.join(current_app.config['UPLOAD_FOLDER'], self.filename)

    def __repr__(self):
        return f'<Document {self.id}: {self.original_filename}>'
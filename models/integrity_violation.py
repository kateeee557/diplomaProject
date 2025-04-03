from app import db
from datetime import datetime

class IntegrityViolation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    document_hash = db.Column(db.String(64), nullable=False)
    original_document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, nullable=True)

    # Relationships
    user = db.relationship('User', backref='integrity_violations')
    original_document = db.relationship('Document')

    def __repr__(self):
        return f'<IntegrityViolation {self.id}: User {self.user_id} attempted to submit document {self.original_document_id}>'
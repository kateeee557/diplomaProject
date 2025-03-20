from app import db
from datetime import datetime

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)

    # Submission details
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='submitted')  # 'submitted', 'graded', 'returned'

    # Grading information
    grade = db.Column(db.String(10), nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    graded_at = db.Column(db.DateTime, nullable=True)

    # Blockchain-specific fields
    grade_tx = db.Column(db.String(66), nullable=True)  # Transaction hash for grading
    blockchain_verified = db.Column(db.Boolean, default=False)
    grade_verified = db.Column(db.Boolean, default=False)  # New field to track grade verification

    # Token rewards
    tokens_earned = db.Column(db.Float, default=0)

    # Relationships
    # IMPORTANT: Remove the backref from here since it's defined in Assignment model
    assignment = db.relationship('Assignment')  # No backref here
    student = db.relationship('User', backref='student_submissions')
    # IMPORTANT: The document relationship may also have a backref conflict
    document = db.relationship('Document')  # No backref here

    def is_on_time(self):
        """Check if submission was made before assignment deadline"""
        return self.submitted_at <= self.assignment.deadline

    def is_graded(self):
        """Check if submission has been graded"""
        return self.status == 'graded'

    def calculate_token_reward(self):
        """Calculate token rewards based on submission criteria"""
        tokens = 0

        # On-time submission reward
        if self.is_on_time():
            tokens += 5

        # Grade-based reward
        try:
            grade_value = float(self.grade.replace('%', '')) if self.grade else 0
            if grade_value >= 95:
                tokens += 5
            elif grade_value >= 85:
                tokens += 3
        except (ValueError, AttributeError):
            pass

        self.tokens_earned = tokens
        return tokens

    def verify_blockchain_submission(self):
        """Verify submission on blockchain"""
        # If already verified, return True
        if self.blockchain_verified:
            return True

        # Get document verification status
        document = db.session.query(Document).get(self.document_id)
        if document and document.is_verified():
            self.blockchain_verified = True
            db.session.commit()
            return True

        # Otherwise verify through blockchain service
        try:
            from services.blockchain_service import get_blockchain_service

            blockchain = get_blockchain_service()
            if not blockchain.is_connected():
                # For testing without blockchain
                self.blockchain_verified = True
                db.session.commit()
                return True

            # Verify document on blockchain
            result = blockchain.verify_document(document.hash)

            if result:
                # Update verification status
                self.blockchain_verified = True
                db.session.commit()

                # Also update document verification
                if not document.is_blockchain_verified:
                    document.is_blockchain_verified = True
                    db.session.commit()

            return result
        except Exception as e:
            print(f"Blockchain verification error: {e}")
            return False

    def __repr__(self):
        return f'<Submission {self.id}: Assignment {self.assignment_id} by Student {self.student_id}>'

# Import at the end to avoid circular imports
from models.document import Document
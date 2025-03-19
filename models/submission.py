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

    # Token rewards
    tokens_earned = db.Column(db.Float, default=0)

    # Relationships
    assignment = db.relationship('Assignment')
    student = db.relationship('User', backref='student_submissions')
    document = db.relationship('Document')

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
        from services.blockchain_service import get_blockchain_service

        try:
            blockchain = get_blockchain_service()
            # Implement verification logic based on your blockchain contract
            self.blockchain_verified = blockchain.verify_document(self.document.hash)
            return self.blockchain_verified
        except Exception as e:
            print(f"Blockchain verification error: {e}")
            return False

    def __repr__(self):
        return f'<Submission {self.id}: Assignment {self.assignment_id} by Student {self.student_id}>'
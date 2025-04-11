from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'teacher'

    # Blockchain-related fields
    blockchain_address = db.Column(db.String(42), nullable=True)  # Ethereum address
    blockchain_wallet_address = db.Column(db.String(42), nullable=True)  # Specific user wallet
    blockchain_nonce = db.Column(db.Integer, default=0)  # For additional security

    # Additional metadata
    photo = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # Blockchain tracking
    total_tokens_earned = db.Column(db.Float, default=0)
    total_tokens_spent = db.Column(db.Float, default=0)

    # Relationships
    assignments = db.relationship('Assignment', backref='teacher', lazy=True)
    submissions = db.relationship('Submission', backref='user', lazy=True)
    documents = db.relationship('Document', backref='owner', lazy=True)
    token_transactions = db.relationship('TokenTransaction', backref='user', lazy=True)

    def set_password(self, password):
        """Set encrypted password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check encrypted password"""
        return check_password_hash(self.password_hash, password)

    def is_student(self):
        """Check if user is a student"""
        return self.role == 'student'

    def is_teacher(self):
        """Check if user is a teacher"""
        return self.role == 'teacher'

    def update_token_stats(self, amount, transaction_type):
        """Update token statistics"""
        if transaction_type == 'reward':
            self.total_tokens_earned += amount
        elif transaction_type == 'spend':
            self.total_tokens_spent += amount

    def get_token_balance(self):
        """Calculate current token balance from transactions"""
        from app import db
        from models.token import TokenTransaction

        # Query rewards and spends separately
        rewards = TokenTransaction.query.filter_by(
            user_id=self.id,
            transaction_type='reward'
        ).all()

        spends = TokenTransaction.query.filter_by(
            user_id=self.id,
            transaction_type='spend'
        ).all()

        # Calculate the total balance
        total_rewards = sum(t.amount for t in rewards)
        total_spends = sum(t.amount for t in spends)

        return total_rewards - total_spends

    def increment_blockchain_nonce(self):
        """Increment nonce for additional security"""
        self.blockchain_nonce += 1

    def __repr__(self):
        return f'<User {self.id}: {self.name} ({self.role})>'
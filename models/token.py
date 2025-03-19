from app import db
from datetime import datetime

class TokenTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'reward', 'spend', etc.
    description = db.Column(db.String(255), nullable=True)
    blockchain_tx = db.Column(db.String(66), nullable=True)  # Transaction hash
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def is_reward(self):
        return self.transaction_type == 'reward'

    def is_spend(self):
        return self.transaction_type == 'spend'

    def __repr__(self):
        return f'<TokenTransaction {self.id}: {self.amount} for User {self.user_id}>'
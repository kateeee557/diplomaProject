from app import db
from datetime import datetime

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships - use this to define the backref for Submission
    submissions = db.relationship('Submission', backref='assignment_ref', lazy=True)

    def is_active(self):
        return datetime.utcnow() <= self.deadline

    def submission_count(self):
        return len(self.submissions)

    def __repr__(self):
        return f'<Assignment {self.id}: {self.title}>'
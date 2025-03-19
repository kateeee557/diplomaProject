from app import db
from datetime import datetime

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    submissions = db.relationship('Submission', lazy=True)

    def is_active(self):  # Make sure this line is properly indented
        return datetime.utcnow() <= self.deadline

    def submission_count(self):  # And this one too
        return len(self.submissions)

    def __repr__(self):  # And this one
        return f'<Assignment {self.id}: {self.title}>'
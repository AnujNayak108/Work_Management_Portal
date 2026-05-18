"""
Check-in comment model.
"""
from datetime import datetime, timezone
from ..extensions import db


class CheckInComment(db.Model):
    """Manager's structured check-in feedback on a goal."""
    __tablename__ = 'checkin_comments'

    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=False)
    quarter = db.Column(db.String(5), nullable=False)  # Q1, Q2, Q3, Q4
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    rating = db.Column(db.String(20), nullable=True)  # below, meets, exceeds
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    author = db.relationship('User', foreign_keys=[author_id])

    def __repr__(self):
        return f'<CheckInComment Goal#{self.goal_id} {self.quarter}>'

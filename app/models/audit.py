"""
Audit Log and Escalation models.
"""
from datetime import datetime, timezone
from ..extensions import db


class AuditLog(db.Model):
    """Tracks all post-lock changes for governance."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    # e.g. goal_edited, goal_unlocked, sheet_approved, sheet_returned
    entity_type = db.Column(db.String(50), nullable=False)  # goal, goal_sheet, etc.
    entity_id = db.Column(db.Integer, nullable=False)
    old_value = db.Column(db.Text, nullable=True)  # JSON string
    new_value = db.Column(db.Text, nullable=True)  # JSON string
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ip_address = db.Column(db.String(45), nullable=True)

    user = db.relationship('User', foreign_keys=[user_id])

    def __repr__(self):
        return f'<AuditLog {self.action} by User#{self.user_id}>'


class Escalation(db.Model):
    """Rule-based escalation for missed deadlines."""
    __tablename__ = 'escalations'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(30), nullable=False)
    # goal_not_submitted, goal_not_approved, checkin_missed
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    escalated_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    level = db.Column(db.Integer, default=1)  # 1=employee, 2=manager, 3=HR
    cycle_id = db.Column(db.Integer, db.ForeignKey('performance_cycles.id'), nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    target_user = db.relationship('User', foreign_keys=[target_user_id], backref='escalations_received')
    escalated_to = db.relationship('User', foreign_keys=[escalated_to_id])
    cycle = db.relationship('PerformanceCycle')

    def __repr__(self):
        return f'<Escalation {self.type} for User#{self.target_user_id}>'

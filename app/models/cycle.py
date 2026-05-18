"""
Performance Cycle model — configurable check-in windows.
"""
from datetime import datetime, timezone, date
from ..extensions import db


class PerformanceCycle(db.Model):
    """A full performance cycle (typically one fiscal year)."""
    __tablename__ = 'performance_cycles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # e.g. "FY 2026-27"
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    # Goal Setting Window
    goal_setting_start = db.Column(db.Date, nullable=False)
    goal_setting_end = db.Column(db.Date, nullable=False)

    # Q1 Check-in (July)
    q1_checkin_start = db.Column(db.Date, nullable=False)
    q1_checkin_end = db.Column(db.Date, nullable=False)

    # Q2 Check-in (October)
    q2_checkin_start = db.Column(db.Date, nullable=False)
    q2_checkin_end = db.Column(db.Date, nullable=False)

    # Q3 Check-in (January)
    q3_checkin_start = db.Column(db.Date, nullable=False)
    q3_checkin_end = db.Column(db.Date, nullable=False)

    # Q4 / Annual (March-April)
    q4_checkin_start = db.Column(db.Date, nullable=False)
    q4_checkin_end = db.Column(db.Date, nullable=False)

    is_active = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    creator = db.relationship('User', foreign_keys=[created_by])

    def current_window(self):
        """Return the current active window name or None."""
        today = date.today()
        if self.goal_setting_start <= today <= self.goal_setting_end:
            return 'goal_setting'
        if self.q1_checkin_start <= today <= self.q1_checkin_end:
            return 'Q1'
        if self.q2_checkin_start <= today <= self.q2_checkin_end:
            return 'Q2'
        if self.q3_checkin_start <= today <= self.q3_checkin_end:
            return 'Q3'
        if self.q4_checkin_start <= today <= self.q4_checkin_end:
            return 'Q4'
        return None

    def is_goal_setting_open(self):
        today = date.today()
        return self.goal_setting_start <= today <= self.goal_setting_end

    def is_checkin_open(self, quarter):
        today = date.today()
        mapping = {
            'Q1': (self.q1_checkin_start, self.q1_checkin_end),
            'Q2': (self.q2_checkin_start, self.q2_checkin_end),
            'Q3': (self.q3_checkin_start, self.q3_checkin_end),
            'Q4': (self.q4_checkin_start, self.q4_checkin_end),
        }
        start, end = mapping.get(quarter, (None, None))
        if start and end:
            return start <= today <= end
        return False

    def __repr__(self):
        return f'<PerformanceCycle {self.name}>'

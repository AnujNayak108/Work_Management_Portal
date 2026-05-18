"""
Check-in Service — Window enforcement and comment management.
"""
from datetime import datetime, timezone
from ..extensions import db
from ..models.checkin import CheckInComment
from ..models.goal import Achievement
from ..models.cycle import PerformanceCycle
from .scoring_service import compute_score


class CheckInError(Exception):
    pass


def get_current_quarter():
    """Get the current active quarter from the active cycle."""
    cycle = PerformanceCycle.query.filter_by(is_active=True).first()
    if not cycle:
        return None, None
    window = cycle.current_window()
    return window, cycle


def is_checkin_allowed(quarter):
    """Check if check-in is currently allowed for the given quarter."""
    cycle = PerformanceCycle.query.filter_by(is_active=True).first()
    if not cycle:
        return False
    if quarter == 'goal_setting':
        return cycle.is_goal_setting_open()
    return cycle.is_checkin_open(quarter)


def log_achievement(goal, quarter, actual_value, completion_date, evidence_notes, user_id):
    """Log an achievement for a goal in a specific quarter."""
    # Check for existing achievement
    existing = Achievement.query.filter_by(
        goal_id=goal.id, quarter=quarter
    ).first()

    if existing:
        existing.actual_value = actual_value
        existing.completion_date = completion_date
        existing.evidence_notes = evidence_notes
        existing.logged_at = datetime.now(timezone.utc)
        existing.logged_by = user_id
        achievement = existing
    else:
        achievement = Achievement(
            goal_id=goal.id,
            quarter=quarter,
            actual_value=actual_value,
            completion_date=completion_date,
            evidence_notes=evidence_notes,
            logged_by=user_id
        )
        db.session.add(achievement)

    # Compute score
    achievement.computed_score = compute_score(goal, achievement)
    db.session.commit()
    return achievement


def add_checkin_comment(goal_id, quarter, author_id, comment, rating=None):
    """Manager adds a structured check-in comment."""
    checkin = CheckInComment(
        goal_id=goal_id,
        quarter=quarter,
        author_id=author_id,
        comment=comment,
        rating=rating
    )
    db.session.add(checkin)
    db.session.commit()
    return checkin


def get_checkin_status(employee_id, cycle_id):
    """Get check-in completion status for an employee across all quarters."""
    from ..models.goal import GoalSheet
    sheet = GoalSheet.query.filter_by(
        employee_id=employee_id, cycle_id=cycle_id
    ).first()

    if not sheet:
        return {'has_sheet': False}

    status = {'has_sheet': True, 'sheet_status': sheet.status}
    for q in ['Q1', 'Q2', 'Q3', 'Q4']:
        achievements = Achievement.query.join(Achievement.goal).filter(
            Achievement.quarter == q,
            Achievement.goal.has(goal_sheet_id=sheet.id)
        ).count()
        status[q] = {
            'logged': achievements,
            'total': sheet.goal_count,
            'complete': achievements >= sheet.goal_count if sheet.goal_count > 0 else False
        }

    return status

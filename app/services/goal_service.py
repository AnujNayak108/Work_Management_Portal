"""
Goal Service — CRUD, validation, locking, shared-goal logic.
"""
import json
from datetime import datetime, timezone
from ..extensions import db
from ..models.goal import GoalSheet, Goal, SharedGoal, Achievement
from ..models.audit import AuditLog


class GoalValidationError(Exception):
    """Raised when goal validation fails."""
    pass


def validate_goals(goals_data):
    """
    Validate a list of goal dicts against business rules.
    Returns list of error messages (empty = valid).
    """
    errors = []

    if len(goals_data) > 8:
        errors.append('Maximum 8 goals allowed per employee.')

    if len(goals_data) == 0:
        errors.append('At least one goal is required.')
        return errors

    total_weightage = sum(int(g.get('weightage', 0)) for g in goals_data)
    if total_weightage != 100:
        errors.append(f'Total weightage must equal 100%. Currently: {total_weightage}%.')

    for i, g in enumerate(goals_data, 1):
        w = int(g.get('weightage', 0))
        if w < 10:
            errors.append(f'Goal {i}: Minimum weightage is 10%. Current: {w}%.')
        if not g.get('title', '').strip():
            errors.append(f'Goal {i}: Title is required.')
        if not g.get('thrust_area', '').strip():
            errors.append(f'Goal {i}: Thrust Area is required.')
        if not g.get('unit_type', '').strip():
            errors.append(f'Goal {i}: Unit of Measurement is required.')

    return errors


def create_goal_sheet(employee_id, cycle_id, goals_data):
    """Create a new goal sheet with goals."""
    errors = validate_goals(goals_data)
    if errors:
        raise GoalValidationError('; '.join(errors))

    sheet = GoalSheet(
        employee_id=employee_id,
        cycle_id=cycle_id,
        status='draft'
    )
    db.session.add(sheet)
    db.session.flush()  # Get sheet.id

    for i, g in enumerate(goals_data):
        goal = Goal(
            goal_sheet_id=sheet.id,
            thrust_area=g['thrust_area'],
            title=g['title'],
            description=g.get('description', ''),
            unit_type=g['unit_type'],
            target_value=float(g['target_value']) if g.get('target_value') else None,
            target_date=g.get('target_date'),
            weightage=int(g['weightage']),
            is_shared=g.get('is_shared', False),
            shared_goal_id=g.get('shared_goal_id'),
            order=i
        )
        db.session.add(goal)

    db.session.commit()
    return sheet


def update_goal_sheet(sheet, goals_data):
    """Update an existing draft/returned goal sheet."""
    if sheet.status not in ('draft', 'returned'):
        raise GoalValidationError('Cannot edit a sheet that is not in draft or returned status.')

    errors = validate_goals(goals_data)
    if errors:
        raise GoalValidationError('; '.join(errors))

    # Delete existing goals
    Goal.query.filter_by(goal_sheet_id=sheet.id).delete()

    for i, g in enumerate(goals_data):
        goal = Goal(
            goal_sheet_id=sheet.id,
            thrust_area=g['thrust_area'],
            title=g['title'],
            description=g.get('description', ''),
            unit_type=g['unit_type'],
            target_value=float(g['target_value']) if g.get('target_value') else None,
            target_date=g.get('target_date'),
            weightage=int(g['weightage']),
            is_shared=g.get('is_shared', False),
            shared_goal_id=g.get('shared_goal_id'),
            order=i
        )
        db.session.add(goal)

    sheet.status = 'draft'
    sheet.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return sheet


def submit_goal_sheet(sheet):
    """Submit a goal sheet for manager approval."""
    if sheet.status not in ('draft', 'returned'):
        raise GoalValidationError('Only draft or returned sheets can be submitted.')

    errors = validate_goals([{
        'title': g.title,
        'thrust_area': g.thrust_area,
        'unit_type': g.unit_type,
        'weightage': g.weightage,
        'target_value': g.target_value,
    } for g in sheet.goals])

    if errors:
        raise GoalValidationError('; '.join(errors))

    sheet.status = 'submitted'
    sheet.submitted_at = datetime.now(timezone.utc)
    db.session.commit()
    return sheet


def approve_goal_sheet(sheet, approver_id, ip_address=None):
    """Manager approves a goal sheet — locks it."""
    sheet.status = 'approved'
    sheet.is_locked = True
    sheet.approved_at = datetime.now(timezone.utc)
    sheet.approved_by = approver_id

    log = AuditLog(
        user_id=approver_id,
        action='sheet_approved',
        entity_type='goal_sheet',
        entity_id=sheet.id,
        new_value=json.dumps({'status': 'approved', 'locked': True}),
        ip_address=ip_address
    )
    db.session.add(log)
    db.session.commit()
    return sheet


def return_goal_sheet(sheet, manager_id, comment, ip_address=None):
    """Manager returns a goal sheet for rework."""
    sheet.status = 'returned'
    sheet.return_comment = comment

    log = AuditLog(
        user_id=manager_id,
        action='sheet_returned',
        entity_type='goal_sheet',
        entity_id=sheet.id,
        new_value=json.dumps({'status': 'returned', 'comment': comment}),
        ip_address=ip_address
    )
    db.session.add(log)
    db.session.commit()
    return sheet


def unlock_goal_sheet(sheet, admin_id, ip_address=None):
    """Admin unlocks a goal sheet for editing."""
    old_status = sheet.status
    sheet.is_locked = False
    sheet.status = 'draft'

    log = AuditLog(
        user_id=admin_id,
        action='sheet_unlocked',
        entity_type='goal_sheet',
        entity_id=sheet.id,
        old_value=json.dumps({'status': old_status, 'locked': True}),
        new_value=json.dumps({'status': 'draft', 'locked': False}),
        ip_address=ip_address
    )
    db.session.add(log)
    db.session.commit()
    return sheet


def edit_goal_inline(goal, changes, editor_id, ip_address=None):
    """Manager inline edit of a goal target (pre-approval only, or admin post-lock)."""
    old_values = {
        'target_value': goal.target_value,
        'target_date': str(goal.target_date) if goal.target_date else None,
        'title': goal.title,
        'description': goal.description,
    }

    if 'target_value' in changes:
        goal.target_value = float(changes['target_value'])
    if 'target_date' in changes:
        goal.target_date = changes['target_date']
    if 'title' in changes:
        goal.title = changes['title']
    if 'description' in changes:
        goal.description = changes['description']

    log = AuditLog(
        user_id=editor_id,
        action='goal_edited',
        entity_type='goal',
        entity_id=goal.id,
        old_value=json.dumps(old_values),
        new_value=json.dumps(changes),
        ip_address=ip_address
    )
    db.session.add(log)
    db.session.commit()
    return goal


def push_shared_goal(shared_goal_id, employee_ids, cycle_id):
    """Push a shared goal to multiple employees' goal sheets."""
    shared = db.session.get(SharedGoal, shared_goal_id)
    if not shared:
        raise GoalValidationError('Shared goal not found.')

    for emp_id in employee_ids:
        # Find or create goal sheet for this employee in this cycle
        sheet = GoalSheet.query.filter_by(
            employee_id=emp_id, cycle_id=cycle_id
        ).first()
        if not sheet:
            sheet = GoalSheet(employee_id=emp_id, cycle_id=cycle_id, status='draft')
            db.session.add(sheet)
            db.session.flush()

        # Add shared goal
        goal = Goal(
            goal_sheet_id=sheet.id,
            thrust_area=shared.thrust_area,
            title=shared.title,
            description=shared.description or '',
            unit_type=shared.unit_type,
            target_value=shared.target_value,
            target_date=shared.target_date,
            weightage=10,  # Default min, employee adjusts
            is_shared=True,
            shared_goal_id=shared.id,
            order=sheet.goal_count
        )
        db.session.add(goal)

    db.session.commit()

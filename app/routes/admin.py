"""
Admin/HR routes — Cycle config, org mgmt, unlock, shared goals, audit log.
"""
import json
from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..extensions import db
from ..models.user import User, Department
from ..models.goal import GoalSheet, SharedGoal
from ..models.cycle import PerformanceCycle
from ..models.audit import AuditLog, Escalation
from ..services.goal_service import unlock_goal_sheet, push_shared_goal
from ..services.escalation_service import check_and_create_escalations, resolve_escalation

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    cycle = PerformanceCycle.query.filter_by(is_active=True).first()
    total_employees = User.query.filter_by(role='employee', is_active=True).count()
    total_managers = User.query.filter_by(role='manager', is_active=True).count()

    stats = {'total_employees': total_employees, 'total_managers': total_managers}
    if cycle:
        stats['sheets_total'] = GoalSheet.query.filter_by(cycle_id=cycle.id).count()
        stats['sheets_draft'] = GoalSheet.query.filter_by(cycle_id=cycle.id, status='draft').count()
        stats['sheets_submitted'] = GoalSheet.query.filter_by(cycle_id=cycle.id, status='submitted').count()
        stats['sheets_approved'] = GoalSheet.query.filter_by(cycle_id=cycle.id, status='approved').count()
        stats['sheets_returned'] = GoalSheet.query.filter_by(cycle_id=cycle.id, status='returned').count()
        stats['pending_escalations'] = Escalation.query.filter_by(resolved=False).count()

    departments = Department.query.all()
    return render_template('admin/dashboard.html',
                           cycle=cycle, stats=stats, departments=departments)


@admin_bp.route('/cycles', methods=['GET', 'POST'])
@login_required
@admin_required
def cycles():
    if request.method == 'POST':
        cycle = PerformanceCycle(
            name=request.form['name'],
            start_date=date.fromisoformat(request.form['start_date']),
            end_date=date.fromisoformat(request.form['end_date']),
            goal_setting_start=date.fromisoformat(request.form['goal_setting_start']),
            goal_setting_end=date.fromisoformat(request.form['goal_setting_end']),
            q1_checkin_start=date.fromisoformat(request.form['q1_start']),
            q1_checkin_end=date.fromisoformat(request.form['q1_end']),
            q2_checkin_start=date.fromisoformat(request.form['q2_start']),
            q2_checkin_end=date.fromisoformat(request.form['q2_end']),
            q3_checkin_start=date.fromisoformat(request.form['q3_start']),
            q3_checkin_end=date.fromisoformat(request.form['q3_end']),
            q4_checkin_start=date.fromisoformat(request.form['q4_start']),
            q4_checkin_end=date.fromisoformat(request.form['q4_end']),
            is_active='is_active' in request.form,
            created_by=current_user.id
        )
        if cycle.is_active:
            PerformanceCycle.query.update({'is_active': False})
        db.session.add(cycle)
        db.session.commit()
        flash('Performance cycle created.', 'success')
        return redirect(url_for('admin.cycles'))

    all_cycles = PerformanceCycle.query.order_by(PerformanceCycle.start_date.desc()).all()
    return render_template('admin/cycles.html', cycles=all_cycles)


@admin_bp.route('/org', methods=['GET', 'POST'])
@login_required
@admin_required
def org_hierarchy():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_department':
            dept = Department(name=request.form['dept_name'])
            db.session.add(dept)
            db.session.commit()
            flash('Department added.', 'success')
        elif action == 'add_user':
            user = User(
                employee_id=request.form['employee_id'],
                email=request.form['email'],
                name=request.form['name'],
                role=request.form['role'],
                department_id=int(request.form['department_id']) if request.form.get('department_id') else None,
                manager_id=int(request.form['manager_id']) if request.form.get('manager_id') else None,
            )
            user.set_password(request.form.get('password', 'changeme'))
            db.session.add(user)
            db.session.commit()
            flash('User added.', 'success')
        return redirect(url_for('admin.org_hierarchy'))

    departments = Department.query.all()
    users = User.query.order_by(User.role, User.name).all()
    managers = User.query.filter(User.role.in_(['manager', 'admin'])).all()
    return render_template('admin/org_hierarchy.html',
                           departments=departments, users=users, managers=managers)


@admin_bp.route('/unlock/<int:sheet_id>', methods=['POST'])
@login_required
@admin_required
def unlock(sheet_id):
    sheet = db.session.get(GoalSheet, sheet_id)
    if not sheet:
        flash('Goal sheet not found.', 'danger')
        return redirect(url_for('admin.dashboard'))
    unlock_goal_sheet(sheet, current_user.id, request.remote_addr)
    flash(f'Goal sheet for {sheet.employee.name} unlocked.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/shared-goal', methods=['GET', 'POST'])
@login_required
@admin_required
def shared_goal():
    if request.method == 'POST':
        sg = SharedGoal(
            title=request.form['title'],
            description=request.form.get('description', ''),
            thrust_area=request.form['thrust_area'],
            unit_type=request.form['unit_type'],
            target_value=float(request.form['target_value']) if request.form.get('target_value') else None,
            target_date=date.fromisoformat(request.form['target_date']) if request.form.get('target_date') else None,
            department_id=int(request.form['department_id']),
            created_by=current_user.id,
        )
        db.session.add(sg)
        db.session.flush()

        # Push to selected employees
        emp_ids = request.form.getlist('employee_ids')
        cycle = PerformanceCycle.query.filter_by(is_active=True).first()
        if emp_ids and cycle:
            push_shared_goal(sg.id, [int(e) for e in emp_ids], cycle.id)

        db.session.commit()
        flash('Shared goal created and pushed.', 'success')
        return redirect(url_for('admin.shared_goal'))

    departments = Department.query.all()
    employees = User.query.filter_by(role='employee', is_active=True).all()
    shared_goals = SharedGoal.query.order_by(SharedGoal.created_at.desc()).all()
    return render_template('admin/exceptions.html',
                           departments=departments, employees=employees,
                           shared_goals=shared_goals)


@admin_bp.route('/audit-log')
@login_required
@admin_required
def audit_log():
    page = request.args.get('page', 1, type=int)
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    return render_template('admin/audit_log.html', logs=logs)


@admin_bp.route('/escalations')
@login_required
@admin_required
def escalations():
    check_and_create_escalations()
    pending = Escalation.query.filter_by(resolved=False).order_by(Escalation.created_at.desc()).all()
    resolved = Escalation.query.filter_by(resolved=True).order_by(Escalation.resolved_at.desc()).limit(20).all()
    return render_template('admin/audit_log.html',
                           escalations_pending=pending, escalations_resolved=resolved,
                           show_escalations=True)


@admin_bp.route('/escalations/<int:esc_id>/resolve', methods=['POST'])
@login_required
@admin_required
def resolve_esc(esc_id):
    resolve_escalation(esc_id)
    flash('Escalation resolved.', 'success')
    return redirect(url_for('admin.escalations'))

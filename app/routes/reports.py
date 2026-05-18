"""
Reports routes — Achievement reports, completion dashboard, analytics.
"""
from flask import Blueprint, render_template, request, Response, send_file
from flask_login import login_required, current_user
from ..models.user import User, Department
from ..models.goal import GoalSheet, Goal, Achievement
from ..models.cycle import PerformanceCycle
from ..models.checkin import CheckInComment
from ..services.export_service import generate_achievement_csv, generate_achievement_excel
from ..services.scoring_service import compute_weighted_score

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/achievement')
@login_required
def achievement_report():
    cycle = PerformanceCycle.query.filter_by(is_active=True).first()
    sheets = []
    if cycle:
        query = GoalSheet.query.filter_by(cycle_id=cycle.id)
        if current_user.role == 'manager':
            team_ids = [u.id for u in User.query.filter_by(manager_id=current_user.id).all()]
            team_ids.append(current_user.id)
            query = query.filter(GoalSheet.employee_id.in_(team_ids))
        sheets = query.all()

    report_data = []
    for sheet in sheets:
        scores = compute_weighted_score(sheet.goals) if sheet.goals else None
        report_data.append({
            'employee': sheet.employee,
            'sheet': sheet,
            'scores': scores,
        })

    return render_template('reports/achievement_report.html',
                           cycle=cycle, report_data=report_data)


@reports_bp.route('/achievement/export')
@login_required
def export_report():
    cycle = PerformanceCycle.query.filter_by(is_active=True).first()
    if not cycle:
        return 'No active cycle', 400

    fmt = request.args.get('format', 'csv')
    if fmt == 'excel':
        output = generate_achievement_excel(cycle.id)
        return send_file(output, as_attachment=True,
                         download_name=f'achievement_report_{cycle.name}.xlsx',
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        csv_data = generate_achievement_csv(cycle.id)
        return Response(csv_data, mimetype='text/csv',
                        headers={'Content-Disposition': f'attachment;filename=achievement_report_{cycle.name}.csv'})


@reports_bp.route('/completion')
@login_required
def completion_dashboard():
    cycle = PerformanceCycle.query.filter_by(is_active=True).first()
    departments = Department.query.all()

    completion_data = []
    if cycle:
        for dept in departments:
            members = User.query.filter_by(department_id=dept.id, is_active=True).all()
            dept_data = {'department': dept.name, 'employees': []}
            for member in members:
                sheet = GoalSheet.query.filter_by(employee_id=member.id, cycle_id=cycle.id).first()
                emp_data = {
                    'name': member.name,
                    'role': member.role,
                    'sheet_status': sheet.status if sheet else 'not_started',
                    'quarters': {}
                }
                for q in ['Q1', 'Q2', 'Q3', 'Q4']:
                    if sheet:
                        ach_count = sum(1 for g in sheet.goals
                                        if any(a.quarter == q for a in g.achievements))
                        emp_data['quarters'][q] = {
                            'done': ach_count,
                            'total': len(sheet.goals),
                            'complete': ach_count >= len(sheet.goals) if sheet.goals else False
                        }
                    else:
                        emp_data['quarters'][q] = {'done': 0, 'total': 0, 'complete': False}
                dept_data['employees'].append(emp_data)
            completion_data.append(dept_data)

    return render_template('reports/completion_dashboard.html',
                           cycle=cycle, completion_data=completion_data)


@reports_bp.route('/analytics')
@login_required
def analytics():
    cycle = PerformanceCycle.query.filter_by(is_active=True).first()
    return render_template('reports/analytics.html', cycle=cycle)

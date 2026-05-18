"""
Seed script — Populate demo data for ATOMQUEST Portal.
Run: python seed.py
"""
from datetime import date
from app import create_app
from app.extensions import db
from app.models.user import User, Department
from app.models.cycle import PerformanceCycle

app = create_app()

with app.app_context():
    db.create_all()

    # Check if already seeded
    if User.query.first():
        print('Database already seeded. Skipping.')
    else:
        # Departments
        eng = Department(name='Engineering')
        mkt = Department(name='Marketing')
        ops = Department(name='Operations')
        db.session.add_all([eng, mkt, ops])
        db.session.flush()

        # Admin
        admin = User(employee_id='ADM001', email='admin@atomberg.com', name='Priya Sharma', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.flush()

        # Managers
        mgr_eng = User(employee_id='MGR001', email='manager.eng@atomberg.com', name='Rahul Verma',
                        role='manager', department_id=eng.id)
        mgr_eng.set_password('manager123')

        mgr_mkt = User(employee_id='MGR002', email='manager.mkt@atomberg.com', name='Anita Desai',
                        role='manager', department_id=mkt.id)
        mgr_mkt.set_password('manager123')

        mgr_ops = User(employee_id='MGR003', email='manager.ops@atomberg.com', name='Vikram Singh',
                        role='manager', department_id=ops.id)
        mgr_ops.set_password('manager123')

        db.session.add_all([mgr_eng, mgr_mkt, mgr_ops])
        db.session.flush()

        # Set department heads
        eng.head_id = mgr_eng.id
        mkt.head_id = mgr_mkt.id
        ops.head_id = mgr_ops.id

        # Employees
        employees_data = [
            ('EMP001', 'emp1@atomberg.com', 'Arjun Patel', eng.id, mgr_eng.id),
            ('EMP002', 'emp2@atomberg.com', 'Sneha Iyer', eng.id, mgr_eng.id),
            ('EMP003', 'emp3@atomberg.com', 'Karan Mehta', eng.id, mgr_eng.id),
            ('EMP004', 'emp4@atomberg.com', 'Divya Nair', mkt.id, mgr_mkt.id),
            ('EMP005', 'emp5@atomberg.com', 'Rohan Gupta', mkt.id, mgr_mkt.id),
            ('EMP006', 'emp6@atomberg.com', 'Meera Joshi', mkt.id, mgr_mkt.id),
            ('EMP007', 'emp7@atomberg.com', 'Aditya Kumar', ops.id, mgr_ops.id),
            ('EMP008', 'emp8@atomberg.com', 'Pooja Reddy', ops.id, mgr_ops.id),
            ('EMP009', 'emp9@atomberg.com', 'Nikhil Sharma', ops.id, mgr_ops.id),
        ]

        for eid, email, name, dept_id, mgr_id in employees_data:
            emp = User(employee_id=eid, email=email, name=name,
                       role='employee', department_id=dept_id, manager_id=mgr_id)
            emp.set_password('emp123')
            db.session.add(emp)

        # Performance Cycle (current year — wide windows for demo)
        cycle = PerformanceCycle(
            name='FY 2026-27',
            start_date=date(2026, 4, 1),
            end_date=date(2027, 3, 31),
            goal_setting_start=date(2026, 5, 1),
            goal_setting_end=date(2026, 6, 30),
            q1_checkin_start=date(2026, 7, 1),
            q1_checkin_end=date(2026, 7, 31),
            q2_checkin_start=date(2026, 10, 1),
            q2_checkin_end=date(2026, 10, 31),
            q3_checkin_start=date(2027, 1, 1),
            q3_checkin_end=date(2027, 1, 31),
            q4_checkin_start=date(2027, 3, 1),
            q4_checkin_end=date(2027, 4, 15),
            is_active=True,
            created_by=admin.id
        )
        db.session.add(cycle)
        db.session.commit()

        print('[OK] Database seeded successfully!')
        print('   - 3 Departments: Engineering, Marketing, Operations')
        print('   - 1 Admin: admin@atomberg.com / admin123')
        print('   - 3 Managers: manager.eng/mkt/ops@atomberg.com / manager123')
        print('   - 9 Employees: emp1-9@atomberg.com / emp123')
        print('   - 1 Active Cycle: FY 2026-27')

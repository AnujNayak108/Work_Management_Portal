"""
Authentication routes — Login, Logout, SSO boilerplate.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from ..models.user import User
from ..extensions import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account is deactivated. Contact HR.', 'danger')
                return render_template('auth/login.html')
            login_user(user, remember=True)
            flash(f'Welcome back, {user.name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# --- SSO Boilerplate (disabled by default) ---

@auth_bp.route('/sso/login')
def sso_login():
    from flask import current_app
    if not current_app.config.get('SSO_ENABLED'):
        flash('SSO is not enabled.', 'warning')
        return redirect(url_for('auth.login'))

    from ..services.sso_service import get_auth_url
    return redirect(get_auth_url())


@auth_bp.route('/sso/callback')
def sso_callback():
    from flask import current_app
    if not current_app.config.get('SSO_ENABLED'):
        return redirect(url_for('auth.login'))

    code = request.args.get('code')
    if not code:
        flash('SSO authentication failed.', 'danger')
        return redirect(url_for('auth.login'))

    from ..services.sso_service import acquire_token, get_user_info
    result = acquire_token(code)
    if 'access_token' in result:
        user_info = get_user_info(result['access_token'])
        if user_info:
            user = User.query.filter_by(email=user_info.get('mail', '')).first()
            if user:
                login_user(user, remember=True)
                return redirect(url_for('index'))
            flash('User not found in system. Contact HR.', 'warning')
    else:
        flash('SSO authentication failed.', 'danger')

    return redirect(url_for('auth.login'))

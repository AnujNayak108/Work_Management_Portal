"""
Application Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    # Escalation
    ESCALATION_DAYS_SUBMIT = int(os.environ.get('ESCALATION_DAYS_SUBMIT', 7))
    ESCALATION_DAYS_APPROVE = int(os.environ.get('ESCALATION_DAYS_APPROVE', 5))
    ESCALATION_DAYS_CHECKIN = int(os.environ.get('ESCALATION_DAYS_CHECKIN', 3))

    # Azure AD / Entra ID SSO
    SSO_ENABLED = os.environ.get('SSO_ENABLED', 'false').lower() == 'true'
    AZURE_CLIENT_ID = os.environ.get('AZURE_CLIENT_ID', '')
    AZURE_CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET', '')
    AZURE_TENANT_ID = os.environ.get('AZURE_TENANT_ID', '')
    AZURE_AUTHORITY = os.environ.get('AZURE_AUTHORITY', '')
    AZURE_REDIRECT_PATH = os.environ.get('AZURE_REDIRECT_PATH', '/auth/sso/callback')
    AZURE_SCOPE = os.environ.get('AZURE_SCOPE', 'User.Read').split(',')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'sqlite:///atomquest.db'
    )


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}

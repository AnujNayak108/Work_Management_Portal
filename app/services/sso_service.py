"""
SSO Service — Microsoft Entra ID (Azure AD) boilerplate.
"""
import msal
from flask import current_app, session, url_for


def _build_msal_app(cache=None):
    """Build a confidential MSAL client application."""
    return msal.ConfidentialClientApplication(
        current_app.config['AZURE_CLIENT_ID'],
        authority=current_app.config['AZURE_AUTHORITY'],
        client_credential=current_app.config['AZURE_CLIENT_SECRET'],
        token_cache=cache
    )


def get_auth_url():
    """Generate the authorization URL for SSO login."""
    app = _build_msal_app()
    auth_url = app.get_authorization_request_url(
        current_app.config['AZURE_SCOPE'],
        redirect_uri=url_for('auth.sso_callback', _external=True)
    )
    return auth_url


def acquire_token(auth_code):
    """Exchange authorization code for access token."""
    app = _build_msal_app()
    result = app.acquire_token_by_authorization_code(
        auth_code,
        scopes=current_app.config['AZURE_SCOPE'],
        redirect_uri=url_for('auth.sso_callback', _external=True)
    )
    return result


def get_user_info(access_token):
    """Fetch user profile from Microsoft Graph API."""
    import requests
    response = requests.get(
        'https://graph.microsoft.com/v1.0/me',
        headers={'Authorization': f'Bearer {access_token}'},
        timeout=10
    )
    if response.status_code == 200:
        return response.json()
    return None

"""
ATOMQUEST HACKATHON 1.0 — Goal Setting & Tracking Portal
Entry point for the Flask application.
"""
from app import create_app

try:
    app = create_app()
except Exception:
    import traceback
    traceback.print_exc()
    raise

if __name__ == '__main__':
    app.run(debug=True, port=5000)

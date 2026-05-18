"""
ATOMQUEST HACKATHON 1.0 — Goal Setting & Tracking Portal
Entry point for the Flask application.
"""
from app import create_app

try:
    app = create_app()
    
    # Automatically initialize the database on startup (for Render deployment)
    with app.app_context():
        from app.extensions import db
        from app.models.user import User
        try:
            db.create_all()
            if not User.query.first():
                import subprocess
                print("Database is empty. Running seed script...")
                subprocess.run(["python", "seed.py"], check=True)
        except Exception as e:
            print(f"Database initialization error: {e}")

except Exception:
    import traceback
    traceback.print_exc()
    raise

if __name__ == '__main__':
    app.run(debug=True, port=5000)

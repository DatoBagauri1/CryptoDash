import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# DB instance
db = SQLAlchemy(model_class=Base)

# Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# DB config
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///crypto_app.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 300, "pool_pre_ping": True}

# Init extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

# Load user function
@login_manager.user_loader
def load_user(user_id):
    # Delay import to break circular import
    from models import User
    return User.query.get(int(user_id))

# --- DELAY IMPORTS UNTIL APP CONTEXT IS READY ---
with app.app_context():
    # Import models here
    from models import User
    db.create_all()

    # Import and register routes AFTER models exist
    from routes import (
        main_bp, auth_bp, dashboard_bp, news_bp,
        charts_bp, sentiment_bp, converter_bp, leaderboard_bp
    )

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(news_bp, url_prefix='/news')
    app.register_blueprint(charts_bp, url_prefix='/charts')
    app.register_blueprint(sentiment_bp, url_prefix='/sentiment')
    app.register_blueprint(converter_bp, url_prefix='/converter')
    app.register_blueprint(leaderboard_bp, url_prefix='/leaderboard')

# Run
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

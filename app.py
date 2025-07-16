import os
import logging
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import redis
from datetime import datetime, timedelta
import uuid

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dekr-ai-assistant-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure CORS
CORS(app)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///dekr_ai.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)

# Initialize Redis for caching
try:
    redis_client = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379"))
    redis_client.ping()
    app.logger.info("Redis connection established")
except Exception as e:
    app.logger.warning(f"Redis connection failed: {e}")
    redis_client = None

# Import routes after app initialization
from api.chat_routes import chat_bp
app.register_blueprint(chat_bp, url_prefix='/api/v1')

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@app.route('/chat')
def chat():
    """Chat interface"""
    # Initialize session if not exists
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session['user_tier'] = 1  # Default to freemium tier
        session['messages_used_today'] = 0
        session['last_message_date'] = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('chat.html')

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# Initialize database
with app.app_context():
    import models  # noqa: F401
    db.create_all()
    app.logger.info("Database initialized")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

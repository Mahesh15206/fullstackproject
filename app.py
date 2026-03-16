# app.py — Main entry point for the Skill Swap Platform
# All routes are organized in the routes/ folder using Flask Blueprints.

import os
from flask import Flask, render_template
from flask_socketio import SocketIO

# ─── App Configuration ────────────────────────────────────────
app = Flask(__name__)
app.secret_key = 'skillswap_secret_key_change_in_production'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

# Initialize SocketIO for real-time chat
socketio = SocketIO(app, async_mode='threading')

# ─── Register Blueprints ──────────────────────────────────────
from routes.auth import auth_bp
from routes.profile import profile_bp
from routes.dashboard import dashboard_bp
from routes.social import social_bp
from routes.chat import chat_bp
from routes.sessions import sessions_bp
from routes.admin import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(social_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(sessions_bp)
app.register_blueprint(admin_bp)

# ─── Register SocketIO Events ─────────────────────────────────
from socket_events import register_socket_events
register_socket_events(socketio)

# ─── Landing Page ─────────────────────────────────────────────
@app.route('/')
def index():
    """Landing page."""
    return render_template('index.html')

# ─── Run the App ──────────────────────────────────────────────
if __name__ == '__main__':
    os.makedirs(os.path.join('static', 'uploads', 'profile_pics'), exist_ok=True)
    os.makedirs(os.path.join('static', 'uploads', 'voice_msgs'), exist_ok=True)
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)

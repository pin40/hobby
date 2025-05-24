from flask import Flask, render_template
import os
from .routes.finance_routes import finance_bp
from .routes.diary_routes import diary_bp
from .routes.calendar_routes import calendar_bp
from .routes.ai_routes import ai_bp # Add this

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    # Load configuration from .env file or environment variables
    # For now, we'll use a default secret key if not set, but this should be properly configured
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'a_default_secret_key_for_development')
    # Ensure SECRET_KEY is set for session management, which it is by the line above.
    # The prompt's suggested additional check for SECRET_KEY is redundant here.
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

    @app.route('/')
    def index():
        return render_template('index.html')

    # Register Blueprints
    app.register_blueprint(finance_bp, url_prefix='/user')
    app.register_blueprint(diary_bp, url_prefix='/user')
    app.register_blueprint(calendar_bp, url_prefix='/user')
    app.register_blueprint(ai_bp, url_prefix='/user') # Add this
            
    return app

if __name__ == '__main__':
    # Ensure .env is loaded for FLASK_SECRET_KEY etc.
    # config.settings should do this on import, but if running app.py directly,
    # you might need to ensure settings are loaded if they influence app creation.
    # from config import settings # To ensure .env is loaded if not already by other imports
    
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=app.config['DEBUG']) # Changed port for clarity if bot is also running

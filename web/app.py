from flask import Flask, render_template
import os

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    # Load configuration from .env file or environment variables
    # For now, we'll use a default secret key if not set, but this should be properly configured
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'a_default_secret_key_for_development')
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

    @app.route('/')
    def index():
        return render_template('index.html')

    # Add more routes here later for finances, diary, calendar, AI assistant

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=app.config['DEBUG'])

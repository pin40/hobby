import os
from dotenv import load_dotenv

# Determine the path to the .env file (assuming it's in the project root)
# For example, if settings.py is in project_root/config/settings.py,
# then project_root is two levels up.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(BASE_DIR, '.env')

# Load the .env file if it exists
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print(f"Warning: .env file not found at {dotenv_path}. Using environment variables directly if set.")

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH')
if not FIREBASE_CREDENTIALS_PATH:
    print("Warning: FIREBASE_CREDENTIALS_PATH is not set. This is required for Firebase Admin SDK.")
# Or individual Firebase variables if preferred:
FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY')
FIREBASE_AUTH_DOMAIN = os.getenv('FIREBASE_AUTH_DOMAIN')
FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')
FIREBASE_STORAGE_BUCKET = os.getenv('FIREBASE_STORAGE_BUCKET')
FIREBASE_MESSAGING_SENDER_ID = os.getenv('FIREBASE_MESSAGING_SENDER_ID')
FIREBASE_APP_ID = os.getenv('FIREBASE_APP_ID')
FIREBASE_DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL')

# Google Calendar Configuration
GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH') # Used for Calendar

# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_PATH = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH') # Specific for Sheets
GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
GOOGLE_SHEETS_DEFAULT_SHEET_NAME = os.getenv('GOOGLE_SHEETS_DEFAULT_SHEET_NAME', 'Finanzas_Log')


# Gemini AI Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_BASE_URL = os.getenv('GEMINI_BASE_URL')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-pro') # Default model if not set

# Flask Configuration
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'a_very_secret_key_in_case_env_is_missing')
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
FLASK_HOST = os.getenv('FLASK_HOST', '127.0.0.1')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5001'))

# Example of how to use these settings:
if __name__ == '__main__':
    print(f"Telegram Token: {TELEGRAM_BOT_TOKEN[:10]}..." if TELEGRAM_BOT_TOKEN else "Not Set")
    print(f"Firebase Credentials Path: {FIREBASE_CREDENTIALS_PATH}")
    print(f"Google Credentials Path: {GOOGLE_CREDENTIALS_PATH}")
    print(f"Gemini API Key: {GEMINI_API_KEY[:10]}..." if GEMINI_API_KEY else "Not Set")
    print(f"Flask Debug Mode: {FLASK_DEBUG}")
    print(f"Flask Host: {FLASK_HOST}")
    print(f"Flask Port: {FLASK_PORT}")

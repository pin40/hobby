# Multifunctional Telegram Bot & Web Frontend

This project is a multifunctional Telegram bot with a Flask web frontend. It includes features for financial management, a personal diary, Google Calendar integration, and an AI assistant powered by Gemini.

## Features

**Telegram Bot:**
*   **Financial Management:**
    *   `/add_income <amount> <description>`: Record income.
    *   `/add_expense <amount> <description>`: Record expenses.
    *   `/balance`: View current financial balance.
    *   `/export_finances`: Receive an Excel file of financial transactions.
*   **Personal Diary:**
    *   `/add_entry <text>`: Save a diary entry.
    *   `/view_entries [all|keyword]`: View diary entries (latest, all, or by keyword).
*   **Google Calendar Integration:**
    *   `/events [max_results]`: List upcoming events from Google Calendar.
    *   `/newevent <YYYY-MM-DD> <HH:MM> <Duration_Minutes> <Summary>`: Add a new event to Google Calendar.
*   **AI Assistant (Gemini):**
    *   `/chat <message>`: Interact with the Gemini AI model.
*   **General:**
    *   `/start`: Initial welcome message.
    *   `/help`: Detailed list of available commands.

**Web Frontend (Flask):**
*   Accessible dashboard with a modern dark theme.
*   **Finances Page (`/user/finances`):**
    *   View income, expenses, and balance.
    *   Export financial data to Excel.
    *   (Note: Displays data for a demo user ID by default).
*   **Diary Page (`/user/diary`):**
    *   View diary entries.
    *   (Note: Displays data for a demo user ID by default).
*   **Calendar Page (`/user/calendar`):**
    *   View upcoming Google Calendar events.
    *   Add new events to Google Calendar.
*   **AI Assistant Page (`/user/ai_assistant`):**
    *   Chat interface to interact with the Gemini AI model.
    *   Configure AI parameters (API Key, Base URL, Model) for the current web session.

## Directory Structure

```
/
├── bot/                # Telegram bot specific logic
│   ├── handlers/       # Command handlers for the bot
│   └── main.py         # Main script for the bot
├── web/                # Flask web application
│   ├── routes/         # Route definitions (Blueprints)
│   ├── static/         # Static files (CSS, JS, images)
│   └── templates/      # HTML templates
├── services/           # Shared services (Firebase, Google Calendar, AI)
├── config/             # Configuration files (e.g., settings.py)
├── .env.example        # Example environment variables file
├── requirements.txt    # Python dependencies
├── run.py              # Main script to run both bot and web app
└── README.md           # This file
```

## Prerequisites

*   Python 3.8+
*   `pip` (Python package installer)
*   A virtual environment tool (e.g., `venv`)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **Create a `.env` file:**
    *   Copy the `.env.example` file to `.env`:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file and provide your actual credentials and API keys.

2.  **Required values in `.env`:**

    *   `TELEGRAM_BOT_TOKEN`: Your Telegram Bot token from BotFather.
    *   `FIREBASE_CREDENTIALS_PATH`: Absolute or relative path to your Firebase service account JSON key file.
        *   Go to your Firebase project settings -> Service accounts.
        *   Generate a new private key and save the JSON file.
    *   `GOOGLE_CREDENTIALS_PATH`: Path to your Google API credentials JSON file. This can be:
        *   **Service Account JSON:** For the bot/app to manage its own calendar or a shared calendar. The service account email will need access to the target Google Calendar.
        *   **OAuth 2.0 Client Secrets JSON (`client_secret.json`):** If you intend to (manually, for now) authorize as a specific user. See "Google Calendar Authentication Note" below.
    *   `GEMINI_API_KEY`: Your API key for the Gemini AI model (e.g., from Google AI Studio).
    *   `FLASK_SECRET_KEY`: A strong, random string used for Flask session security. Generate one yourself (e.g., `python -c 'import os; print(os.urandom(24).hex())'`).

3.  **Optional values in `.env`:**

    *   `GEMINI_BASE_URL`: Custom base URL for Gemini API (if using a proxy like OpenRouter). Defaults to Google's endpoint.
    *   `GEMINI_MODEL`: Specific Gemini model to use (e.g., `gemini-pro`). Defaults to `gemini-pro:generateContent`.
    *   `FLASK_HOST`: Host for the Flask app. Defaults to `127.0.0.1`.
    *   `FLASK_PORT`: Port for the Flask app. Defaults to `5001`.
    *   `FLASK_DEBUG`: Set to `True` for development mode (enables debugger, auto-reloader). Defaults to `True`.


### Google Calendar Authentication Note:

The application supports two main ways to authenticate with Google Calendar:

*   **Service Account (Recommended for most bot use-cases):**
    1.  Create a Service Account in the Google Cloud Console for your project.
    2.  Download its JSON key file and set `GOOGLE_CREDENTIALS_PATH` in your `.env` file to its path.
    3.  Share the target Google Calendar with the service account's email address (found in the JSON key file) and grant it appropriate permissions (e.g., "Make changes to events").
*   **User OAuth (via pre-generated `token.json`):**
    1.  Use the `client_secret.json` file from Google Cloud Console (OAuth 2.0 Client ID for "Desktop app" or "Web application"). Set `GOOGLE_CREDENTIALS_PATH` to its path.
    2.  **You must manually generate a `token.json` file.** The application looks for `config/token.json`. This file stores the user's access and refresh tokens.
    3.  To generate `token.json`, you would typically run a separate script (not included in this project yet, but standard `google-auth-oauthlib` examples show how) that uses `InstalledAppFlow` from `google_auth_oauthlib.flow` to guide you through the browser-based OAuth2 flow. The resulting credentials should be saved as `token.json` in the `/config` directory.
    4.  This method is more complex for a bot and is generally used if the bot needs to act on behalf of a *specific* user's calendar who has gone through the OAuth flow.

## Running the Application

Once dependencies are installed and the `.env` file is configured:

```bash
python run.py
```

This will start:
*   The Telegram bot (polling for updates).
*   The Flask web server (default: `http://127.0.0.1:5001`).

You should see log messages in the console indicating that both services have started.

### Flask Async/ASGI Note:

The Flask web application uses `async` routes for some features (Calendar, AI Assistant pages) to handle background tasks without blocking. While Flask's development server (`app.run()`) has some support for this, for production or more robust async handling, you should run the Flask app using an ASGI server like Hypercorn or Uvicorn:

Example with Hypercorn:
```bash
# Install hypercorn: pip install hypercorn
hypercorn web.app:flask_app --bind ${FLASK_HOST}:${FLASK_PORT}
# (You would then run the bot separately or adjust run.py)
```
For simplicity, `run.py` currently uses `flask_app.run()` via threading.

## Troubleshooting

*   **Firebase Errors:** Ensure `FIREBASE_CREDENTIALS_PATH` is correct and the JSON file is valid. Check Firestore database rules if you have permission issues.
*   **Google Calendar Errors:** Verify `GOOGLE_CREDENTIALS_PATH`. If using a service account, ensure it has permissions on the calendar. If using OAuth, ensure `config/token.json` is valid and for the correct scopes.
*   **API Key Errors (Gemini):** Double-check `GEMINI_API_KEY`.
*   **Port in use:** If Flask fails to start, the port might be in use. Change `FLASK_PORT` in `.env`.

## Contributing

Contributions are welcome! Please feel free to fork the repository, make changes, and submit pull requests.
(Further details on contributing can be added here).

## License

This project is licensed under the MIT License. See the `LICENSE` file for details (though a `LICENSE` file was not explicitly created in this project, one could be added).

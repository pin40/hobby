import threading
import time
import logging
from config import settings # To access FLASK_DEBUG, FLASK_PORT if defined

# Import the main functions from bot and web apps
from bot.main import main as run_telegram_bot
from web.app import create_app

# Configure logging for run.py
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask app setup
flask_app = create_app()
# Note: For async Flask routes to work optimally, an ASGI server (Hypercorn, Uvicorn)
# should be used instead of Flask's default Werkzeug server (app.run()).
# For simplicity in this script, we'll use app.run(), but acknowledge this limitation.
# The FLASK_DEBUG setting is already handled within create_app().
# Define port for Flask app (can be moved to .env and settings.py later)
FLASK_PORT = int(settings.FLASK_PORT) if hasattr(settings, 'FLASK_PORT') and settings.FLASK_PORT else 5001
FLASK_HOST = settings.FLASK_HOST if hasattr(settings, 'FLASK_HOST') and settings.FLASK_HOST else '127.0.0.1'


def start_flask_app():
    logger.info(f"Starting Flask web server on http://{FLASK_HOST}:{FLASK_PORT}...")
    try:
        # Pass debug status from settings to app.run, if not already handled by create_app()
        # flask_app.run(host=FLASK_HOST, port=FLASK_PORT, debug=settings.FLASK_DEBUG)
        # create_app() already sets app.config['DEBUG'] from settings.FLASK_DEBUG
        flask_app.run(host=FLASK_HOST, port=FLASK_PORT)
    except Exception as e:
        logger.error(f"Flask app failed to start or crashed: {e}", exc_info=True)

def start_telegram_bot():
    logger.info("Starting Telegram bot polling...")
    try:
        run_telegram_bot() # This function should contain the application.run_polling()
    except Exception as e:
        logger.error(f"Telegram bot failed to start or crashed: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("Initializing application...")

    # Ensure Firebase and other services are initialized (usually done on import by service modules)
    # from services import firebase_service # Already imported by bot/main.py or web routes
    # if not firebase_service.get_firestore_client():
    #    logger.error("Firebase not initialized. Exiting.")
    #    exit(1)
    # else:
    #    logger.info("Firebase connection seems OK based on service client availability.")


    flask_thread = threading.Thread(target=start_flask_app, name="FlaskThread")
    bot_thread = threading.Thread(target=start_telegram_bot, name="BotThread")

    logger.info("Starting Flask app in a separate thread...")
    flask_thread.start()

    # Give Flask a moment to start before starting the bot
    time.sleep(2) 

    logger.info("Starting Telegram bot in a separate thread...")
    bot_thread.start()

    # Keep the main thread alive, listening for interruptions
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutdown signal received (KeyboardInterrupt).")
        # Note: Proper shutdown of threads/bot/app might need more graceful handling
        # For example, bot_thread might need `application.stop()` if that's how ptb works.
        # Flask's dev server stops with Ctrl+C.
    except Exception as e:
        logger.error(f"Main thread encountered an error: {e}", exc_info=True)
    finally:
        logger.info("Application shutting down.")
        # Threads will exit as they are daemonic by default or when their target functions return.
        # For a cleaner shutdown, one might set them as daemonic or implement explicit stop signals.

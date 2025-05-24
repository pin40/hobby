import logging
from telegram.ext import Application, CommandHandler
from config import settings # Import settings
from bot.handlers import finance_handlers, diary_handlers, calendar_handlers, ai_handlers # Import handlers
# Ensure services.firebase_service is imported if it handles initialization on import,
# or explicitly initialize Firebase here.
from services import firebase_service # This will trigger initialize_firebase()
# Google Calendar service does not need explicit initialization call here as get_calendar_service() is called by handlers
# AI service also does not need explicit initialization as get_gemini_response is called by handlers

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update, context):
    """Sends a welcome message when the /start command is issued."""
    await update.message.reply_text('Hello! I am your multifunctional bot. How can I help you today?')

async def help_command(update, context):
    """Sends a comprehensive help message with all available commands."""
    help_text = (
        "Welcome to your Multifunctional Bot!\n\n"
        "Available commands:\n"
        "/start - Welcome message\n"
        "/help - Show this help message\n\n"
        "Finance Management:\n"
        "/add_income <amount> <description> - Add an income record\n"
        "/add_expense <amount> <description> - Add an expense record\n"
        "/balance - Show your current financial balance\n"
        "/export_finances - Get an Excel sheet of your financial records\n\n"
        "Personal Diary:\n"
        "/add_entry <text> - Add a new diary entry\n"
        "/view_entries [all|keyword] - View diary entries (latest, all, or by keyword)\n\n"
        "Google Calendar:\n"
        "/events [max_results] - View upcoming calendar events\n"
        "/newevent <YYYY-MM-DD> <HH:MM> <Duration_Minutes> <Summary> - Add a new event\n\n"
        "AI Assistant:\n"
        "/chat <message> - Chat with the AI assistant\n"
    )
    await update.message.reply_text(help_text)

def main():
    """Run the bot."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in settings!")
        return

    # Firebase should be initialized by importing firebase_service
    # If explicit initialization is needed:
    # firebase_service.initialize_firebase() 
    # but it's called when firebase_service is imported.

    logger.info("Initializing bot application...")
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Register finance handlers
    application.add_handler(CommandHandler("add_income", finance_handlers.add_income))
    application.add_handler(CommandHandler("add_expense", finance_handlers.add_expense))
    application.add_handler(CommandHandler("balance", finance_handlers.balance))
    application.add_handler(CommandHandler("export_finances", finance_handlers.export_finances))

    # Add diary handlers
    application.add_handler(CommandHandler("add_entry", diary_handlers.add_entry))
    application.add_handler(CommandHandler("view_entries", diary_handlers.view_entries))

    # Add calendar handlers
    application.add_handler(CommandHandler("events", calendar_handlers.view_events_command))
    application.add_handler(CommandHandler("newevent", calendar_handlers.add_event_command))

    # Add AI handlers
    application.add_handler(CommandHandler("chat", ai_handlers.chat_command))
    # Note: The general message handler `ai_message_handler` is not added for now to avoid over-chatty bot.

    logger.info("Bot is starting and polling for updates...")
    application.run_polling()
    logger.info("Bot has stopped.")


if __name__ == '__main__':
    # Note: When running this directly, ensure PYTHONPATH is set correctly
    # so that `config` and `services` can be imported.
    # Example: export PYTHONPATH=/app:$PYTHONPATH (if /app is your project root)
    # This is usually handled by a top-level run script or IDE configuration.
    
    # The import of firebase_service at the top should trigger initialization.
    # If settings.py also needs to be explicitly loaded first (e.g. to load .env for firebase_service)
    # that should be handled before firebase_service is imported.
    # However, settings.py loads .env on its own import.
    
    print("Attempting to run bot/main.py directly...")
    if not settings.TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN is not set. Please check your .env file or environment variables.")
        print("The .env file should be in the project root, and config/settings.py should load it.")
    else:
        print(f"Token found: {settings.TELEGRAM_BOT_TOKEN[:10]}...")
        if firebase_service.get_firestore_client():
            print("Firestore client seems available.")
        else:
            print("Firestore client is NOT available. Check Firebase initialization and credentials.")
        
        main()

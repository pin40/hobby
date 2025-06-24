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
    # This start function is now superseded by finance_handlers.start_command for /start
    # It can be kept for other purposes or removed if /start is solely for finance menu.
    # For now, let's assume /start is handled by finance_handlers.
    await update.message.reply_text('Hello! This is a generic start. Use /menu for the finance assistant.')

async def help_command(update, context):
    """Sends a comprehensive help message with all available commands."""
    help_text = (
        "🤖 *Asistente Financiero FinBot - Ayuda*\n\n"
        "Puedes controlar el bot usando los siguientes comandos y menús:\n\n"
        "*/start o /menu*\n"
        "  Inicia la conversación con el bot y muestra el menú principal de finanzas.\n"
        "  Desde el menú podrás:\n"
        "  ➕ Agregar Ingresos\n"
        "  ➖ Agregar Gastos\n"
        "  💰 Ver Saldo Actual\n"
        "  📋 Ver Historial (próximamente)\n"
        "  🤖 Usar el Asistente IA (próximamente)\n\n"
        "*/export*\n"
        "  Genera y envía un archivo Excel con tus registros financieros.\n\n"
        "*/help*\n"
        "  Muestra este mensaje de ayuda.\n\n"
        "*Otros Módulos (si están activos):*\n\n"
        "*Personal Diary:*\n"
        "  `/add_entry <text>` - Agrega una nueva entrada al diario.\n"
        "  `/view_entries [all|keyword]` - Visualiza entradas del diario.\n\n"
        "*Google Calendar:*\n"
        "  `/events [max_results]` - Visualiza próximos eventos del calendario.\n"
        "  `/newevent <YYYY-MM-DD> <HH:MM> <Duración_Minutos> <Resumen>` - Agrega un nuevo evento.\n\n"
        "*AI Assistant:*\n"
        "  `/chat <message>` - Chatea con el asistente IA.\n"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

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

    # Register general command handlers
    # The original start command is now replaced by the one in finance_handlers for /start and /menu
    # application.add_handler(CommandHandler("start", start)) # This is the generic start, now unused for /start
    application.add_handler(CommandHandler("help", help_command))
    
    # Register all finance handlers from finance_handlers.py
    # This includes /start, /menu, ConversationHandlers, CallbackQueryHandlers for finance features
    for handler in finance_handlers.finance_handlers:
        application.add_handler(handler)

    # Add diary handlers
    # These CommandHandlers should be fine as they are self-contained.
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

import logging
from telegram import Update
from telegram.ext import CallbackContext
from services.google_calendar_service import list_upcoming_events, add_event
# Datetime parsing will be needed for /add_event
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

async def view_events_command(update: Update, context: CallbackContext):
    try:
        max_results = 5
        if context.args and context.args[0].isdigit():
            max_results = int(context.args[0])
        
        message = await list_upcoming_events(max_results=max_results)
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error in view_events_command: {e}", exc_info=True)
        await update.message.reply_text("An error occurred while fetching calendar events.")

async def add_event_command(update: Update, context: CallbackContext):
    # Expected format: /add_event <YYYY-MM-DD> <HH:MM> <Duration_Minutes> <Summary>
    # Example: /add_event 2024-12-25 10:00 60 Christmas Brunch
    try:
        args = context.args
        if len(args) < 4:
            await update.message.reply_text("Usage: /add_event <YYYY-MM-DD> <HH:MM> <Duration_Minutes> <Event Summary>")
            return

        date_str, time_str, duration_min_str, *summary_parts = args
        summary = " ".join(summary_parts)

        start_datetime_str = f"{date_str}T{time_str}:00"
        
        # Validate and parse start time
        try:
            start_datetime = datetime.fromisoformat(start_datetime_str)
        except ValueError:
            await update.message.reply_text("Invalid date or time format. Use YYYY-MM-DD and HH:MM.")
            return

        # Calculate end time
        duration_minutes = int(duration_min_str)
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)
        end_datetime_str = end_datetime.isoformat()

        # For simplicity, assuming UTC for now. Timezone handling should be more robust in a real app.
        message = await add_event(summary, start_datetime.isoformat(), end_datetime.isoformat(), description=f"Event added via Telegram Bot: {summary}")
        await update.message.reply_text(message)

    except ValueError:
        await update.message.reply_text("Invalid duration. Please provide minutes as a number.")
    except Exception as e:
        logger.error(f"Error in add_event_command: {e}", exc_info=True)
        await update.message.reply_text("An error occurred while adding the calendar event.")

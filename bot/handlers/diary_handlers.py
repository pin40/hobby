import logging
from telegram import Update
from telegram.ext import CallbackContext
from services.firebase_service import get_firestore_client
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

async def add_entry(update: Update, context: CallbackContext):
    try:
        user_id = str(update.effective_user.id)
        entry_text = " ".join(context.args)

        if not entry_text:
            await update.message.reply_text("Usage: /add_entry <your diary text>")
            return

        db = get_firestore_client()
        if not db:
            await update.message.reply_text("Error: Database service is not available.")
            return

        entry_data = {
            "text": entry_text,
            "timestamp": datetime.utcnow()
        }
        
        # Path: users/{user_id}/diary/{entry_id}
        await db.collection("users").document(user_id).collection("diary").add(entry_data)
        await update.message.reply_text("Diary entry added successfully.")
    except Exception as e:
        logger.error(f"Error adding diary entry: {e}", exc_info=True)
        await update.message.reply_text("An error occurred while adding your diary entry.")

async def view_entries(update: Update, context: CallbackContext):
    try:
        user_id = str(update.effective_user.id)
        db = get_firestore_client()
        if not db:
            await update.message.reply_text("Error: Database service is not available.")
            return

        # Basic query: Get last 5 entries by default
        # For more complex queries (date, keyword), args parsing would be needed
        query_args = context.args
        
        diary_ref = db.collection("users").document(user_id).collection("diary")
        
        # Using synchronous firebase-admin, so direct call, not await
        # Order by timestamp descending to get the latest entries
        if query_args and query_args[0].lower() == "all":
            entries_query = diary_ref.order_by("timestamp", direction="DESCENDING").stream()
            # entries_to_send = [doc.to_dict() for doc in entries_query] # This line is intentionally missing as per current prompt
        elif query_args and len(query_args[0]) > 0: # Basic keyword search
            keyword = " ".join(query_args)
            # Firestore does not support direct text search like SQL LIKE.
            # For simple keyword search, you'd typically retrieve and filter, or use a search service.
            # This is a placeholder for a more complex search. We'll filter by text containing the keyword.
            # This is inefficient for large datasets.
            all_entries = diary_ref.order_by("timestamp", direction="DESCENDING").stream()
            entries_to_send = []
            for entry_doc in all_entries:
                entry_data = entry_doc.to_dict()
                if keyword.lower() in entry_data.get("text", "").lower():
                    entries_to_send.append(entry_data)
                if len(entries_to_send) >= 10: # Limit results for keyword search
                    break
            if not entries_to_send:
                await update.message.reply_text(f"No diary entries found containing '{keyword}'.")
                return
            # Reverse to show oldest first among the filtered results, or keep as is for newest first
            # For now, keeping newest first from the filtered list.
        else: # Default: last 5 entries
            entries_query = diary_ref.order_by("timestamp", direction="DESCENDING").limit(5).stream()
            entries_to_send = [doc.to_dict() for doc in entries_query]


        if not entries_to_send: # Check after potential filtering
            await update.message.reply_text("No diary entries found.")
            return

        response_message = "Your Diary Entries:\n\n"
        # If not keyword search, entries_to_send is already populated
        # If keyword search, it's also populated.
        
        # Sort entries by timestamp (newest first) if not already sorted, or to ensure order after filtering
        # The default query for last 5 is already newest first. Keyword search also gets newest first.
        
        for entry in reversed(entries_to_send): # Reverse to show oldest first from the selection
            ts = entry['timestamp']
            # Ensure timestamp is datetime object for formatting
            if isinstance(ts, datetime):
                entry_time_str = ts.strftime("%Y-%m-%d %H:%M")
            elif isinstance(ts, str): # Handle if timestamp is already string (e.g. from older data)
                 entry_time_str = ts
            else: # Fallback for other types (like Firestore Timestamp)
                # Assuming it's a Firestore Timestamp, convert to datetime
                try:
                    entry_time_str = ts.strftime("%Y-%m-%d %H:%M") # This might fail if not a true datetime
                except AttributeError:
                     # Attempt to convert from common Firestore timestamp format if needed, though usually it's datetime
                    entry_time_str = str(ts)


            response_message += f"🗓️ *{entry_time_str}*\n"
            response_message += f"📝 {entry['text']}\n\n"
                
        await update.message.reply_text(response_message, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error viewing diary entries: {e}", exc_info=True)
        await update.message.reply_text("An error occurred while retrieving your diary entries.")

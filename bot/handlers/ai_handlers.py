import logging
from telegram import Update
from telegram.ext import CallbackContext, MessageHandler, filters
from services.ai_service import get_gemini_response

logger = logging.getLogger(__name__)

async def chat_command(update: Update, context: CallbackContext):
    """Handles the /chat command or direct messages to the AI."""
    if update.message is None or update.message.text is None:
        return

    user_prompt = ""
    if context.args: # For /chat command with arguments
        user_prompt = " ".join(context.args)
    else: # For direct messages (if this handler is also used for MessageHandler)
        # Remove bot command if it's a reply or forwarded message starting with /chat
        text_to_process = update.message.text
        if text_to_process.startswith('/chat'): # Check if it's actually a /chat command text
             # This part is a bit redundant if used strictly with CommandHandler for /chat
             # but useful if adapting for a general MessageHandler
             command_parts = text_to_process.split(maxsplit=1)
             if len(command_parts) > 1:
                 user_prompt = command_parts[1]
             else: # Just "/chat" was sent
                 await update.message.reply_text("Please provide a message for the AI after /chat.")
                 return
        else: # This branch would be for a general MessageHandler
            user_prompt = text_to_process


    if not user_prompt.strip():
        await update.message.reply_text("What would you like to ask or tell the AI? (e.g., /chat What is the capital of France?)")
        return

    # Inform the user that the AI is processing
    thinking_message = await update.message.reply_text("🤖 Thinking...")

    # Use asyncio.to_thread for the synchronous `get_gemini_response` call
    # to avoid blocking the bot's event loop.
    import asyncio
    ai_response = await asyncio.to_thread(get_gemini_response, user_prompt)
    
    # Edit the "Thinking..." message with the actual response
    if thinking_message:
        await context.bot.edit_message_text(
            chat_id=thinking_message.chat_id,
            message_id=thinking_message.message_id,
            text=ai_response
        )
    else: # Fallback if thinking_message wasn't sent or found
        await update.message.reply_text(ai_response)

# Example of a general message handler (optional, can be added to main.py)
# This would make the bot respond to any text message that isn't a command.
# Be cautious with this, as it might make the bot overly chatty or expensive.
# ai_message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, chat_command)

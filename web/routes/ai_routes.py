"""
Web routes for AI assistant interactions.
Provides a page for chatting with an AI (Gemini by default) and managing
AI configuration settings within the current user's session.
Utilizes async route handling for non-blocking calls to the AI service.
"""
from flask import Blueprint, render_template, request, flash, session, jsonify
from services.ai_service import get_gemini_response as get_ai_response_from_service # Alias
from config import settings as app_settings # For default/env settings
import asyncio # For running async service functions
import os

ai_bp = Blueprint('ai_bp', __name__, template_folder='../templates/ai')

# Keys for session storage
SESSION_GEMINI_API_KEY = 'session_gemini_api_key'
SESSION_GEMINI_BASE_URL = 'session_gemini_base_url'
SESSION_GEMINI_MODEL = 'session_gemini_model'

@ai_bp.route('/ai_assistant', methods=['GET', 'POST'])
async def ai_assistant_page():
    """
    Handles GET requests to display the AI chat interface and configuration form.
    Handles POST requests for updating AI configuration in the session or sending
    a message to the AI.
    This route is asynchronous to allow `await` for AI service calls.
    """
    # Load current AI config from session, fallback to .env settings, then to defaults
    current_config = {
        'api_key': session.get(SESSION_GEMINI_API_KEY, app_settings.GEMINI_API_KEY or ""),
        'base_url': session.get(SESSION_GEMINI_BASE_URL, app_settings.GEMINI_BASE_URL or f"https://generativelanguage.googleapis.com/v1beta/models"),
        'model': session.get(SESSION_GEMINI_MODEL, app_settings.GEMINI_MODEL or "gemini-pro")
    }
    
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_config':
            session[SESSION_GEMINI_API_KEY] = request.form.get('api_key', '').strip()
            session[SESSION_GEMINI_BASE_URL] = request.form.get('base_url', '').strip()
            session[SESSION_GEMINI_MODEL] = request.form.get('model', '').strip()
            
            # Update current_config for immediate reflection on page
            current_config['api_key'] = session[SESSION_GEMINI_API_KEY]
            current_config['base_url'] = session[SESSION_GEMINI_BASE_URL]
            current_config['model'] = session[SESSION_GEMINI_MODEL]

            flash("AI configuration updated for this session.", "success")
            # Return template with updated config to show immediately
            return render_template("ai_assistant.html", ai_config=current_config, chat_history=session.get('chat_history', []))

        elif action == 'send_message':
            user_prompt = request.form.get('prompt')
            if not user_prompt:
                flash("Please enter a message.", "warning")
                return render_template("ai_assistant.html", ai_config=current_config, chat_history=session.get('chat_history', []))

            # Temporarily override app_settings with session config for this call
            # This is a bit of a workaround. A cleaner way would be to pass config to get_ai_response_from_service.
            # For now, we modify a copy of settings or directly use session values.
            
            # Store original settings to restore after the call
            original_key, original_url, original_model = app_settings.GEMINI_API_KEY, app_settings.GEMINI_BASE_URL, app_settings.GEMINI_MODEL
            
            # Use session values if available, otherwise use .env values (already in current_config)
            app_settings.GEMINI_API_KEY = current_config['api_key']
            app_settings.GEMINI_BASE_URL = current_config['base_url']
            app_settings.GEMINI_MODEL = current_config['model']

            if not app_settings.GEMINI_API_KEY:
                flash("AI API Key is not configured. Please set it in the config or .env file.", "danger")
                # Restore original settings
                app_settings.GEMINI_API_KEY, app_settings.GEMINI_BASE_URL, app_settings.GEMINI_MODEL = original_key, original_url, original_model
                return render_template("ai_assistant.html", ai_config=current_config, chat_history=session.get('chat_history', []))

            # Use asyncio.to_thread for the synchronous AI service call
            ai_response_text = await asyncio.to_thread(get_ai_response_from_service, user_prompt)
            
            # Restore original settings from .env immediately after the call
            app_settings.GEMINI_API_KEY, app_settings.GEMINI_BASE_URL, app_settings.GEMINI_MODEL = original_key, original_url, original_model

            # Update chat history in session
            chat_history = session.get('chat_history', [])
            chat_history.append({'user': user_prompt, 'ai': ai_response_text})
            session['chat_history'] = chat_history[-10:] # Keep last 10 exchanges

            # For AJAX calls, one might return jsonify. For form submits, re-render.
            return render_template("ai_assistant.html", ai_config=current_config, chat_history=session['chat_history'])
    
    # GET request: Display chat history and configuration form
    return render_template("ai_assistant.html", ai_config=current_config, chat_history=session.get('chat_history', []))

@ai_bp.route('/ai_assistant/clear_chat', methods=['POST'])
def clear_chat():
    """
    Handles POST requests to clear the AI chat history from the session.
    """
    if 'chat_history' in session:
        session.pop('chat_history')
        flash("Chat history cleared.", "info")
    return redirect(url_for('ai_bp.ai_assistant_page'))

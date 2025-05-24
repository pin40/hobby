"""
AI Service module for interacting with a Generative AI model (Gemini by default).

This service handles the construction of API requests and parsing of responses
for a given AI prompt. It uses configuration from `config.settings` for API keys,
base URLs, and model names.
"""
import logging
import requests # Using requests for a generic HTTP client
from config import settings

logger = logging.getLogger(__name__)

# Default to Google's Generative Language API endpoint if GEMINI_BASE_URL is not set
DEFAULT_GEMINI_API_BASE_URL = f"https://generativelanguage.googleapis.com/v1beta/models"

async def get_gemini_response(prompt: str) -> str:
    """
    Sends a prompt to the configured Gemini AI model and returns the response.

    Args:
        prompt: The user's prompt string to send to the AI.

    Returns:
        A string containing the AI's response, or an error message if the
        request failed or the response was malformed.
        
    Note:
        This function currently uses the synchronous `requests` library.
        In an async application (like one using `python-telegram-bot` or `async` Flask routes),
        this synchronous call should be wrapped with `asyncio.to_thread` by the caller
        to avoid blocking the event loop.
    """
    api_key = settings.GEMINI_API_KEY
    base_url = settings.GEMINI_BASE_URL or DEFAULT_GEMINI_API_BASE_URL
    model = settings.GEMINI_MODEL or "gemini-pro:generateContent" # Default model and action

    if not api_key:
        logger.error("GEMINI_API_KEY is not configured.")
        return "Error: AI Assistant API key is not configured."

    # Construct the full API URL
    # If the model name already includes an action like ':generateContent', use it directly
    if ':' in model:
        url = f"{base_url}/{model}?key={api_key}"
    else: # Otherwise, assume it's just the model name and append a default action
        url = f"{base_url}/{model}:generateContent?key={api_key}"


    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
        # Add other parameters like generationConfig if needed:
        # "generationConfig": {
        #     "temperature": 0.7,
        #     "maxOutputTokens": 2048,
        # }
    }

    try:
        # Since python-telegram-bot handlers are async, and `requests` is sync,
        # ideally, this HTTP request should be run in a separate thread
        # using something like `asyncio.to_thread` in the calling handler,
        # or use an async HTTP client like `httpx`.
        # For now, using synchronous `requests` for simplicity.
        # Caller should use asyncio.to_thread if in an async context.
        response = requests.post(url, headers=headers, json=data, timeout=90) # 90s timeout
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)

        response_json = response.json()
        
        # Adjust based on actual Gemini API response structure
        # Assuming the response looks something like:
        # { "candidates": [ { "content": { "parts": [ { "text": "..." } ] } } ] }
        if response_json.get("candidates") and \
           response_json["candidates"][0].get("content") and \
           response_json["candidates"][0]["content"].get("parts"):
            return response_json["candidates"][0]["content"]["parts"][0]["text"]
        elif response_json.get("error"):
            error_details = response_json["error"].get("message", "Unknown error")
            logger.error(f"Gemini API Error: {error_details}")
            return f"Error from AI: {error_details}"
        else:
            logger.error(f"Unexpected Gemini API response format: {response_json}")
            return "Error: Received an unexpected response from the AI."

    except requests.exceptions.Timeout:
        logger.error(f"Gemini API request timed out to {url}")
        return "Error: The AI assistant took too long to respond."
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"Gemini API HTTP error: {http_err} - Response: {http_err.response.text}")
        return f"Error: Failed to get a response from the AI (HTTP {http_err.response.status_code})."
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Gemini API Request error: {req_err}")
        return f"Error: Could not connect to the AI assistant ({req_err})."
    except Exception as e:
        logger.error(f"Unexpected error interacting with Gemini API: {e}", exc_info=True)
        return "Error: An unexpected error occurred with the AI assistant."

if __name__ == '__main__':
    # For direct testing of this service
    # Ensure GEMINI_API_KEY (and optionally GEMINI_BASE_URL, GEMINI_MODEL) are in .env
    # Example:
    # import asyncio
    # async def test_ai():
    #     print("Testing AI Service...")
    #     # Test with a .env file that has GEMINI_API_KEY
    #     if not settings.GEMINI_API_KEY:
    #         print("GEMINI_API_KEY not found in settings. Please set it in .env")
    #         return
    #     response = await get_gemini_response("Tell me a fun fact about the Roman Empire.")
    #     print(f"AI Response: {response}")
    # asyncio.run(test_ai())
    print("To test AI Service, uncomment the example in __main__ and ensure GEMINI_API_KEY is set.")

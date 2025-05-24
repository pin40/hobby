"""
Google Calendar Service module for interacting with the Google Calendar API.

This service handles authentication (Service Account or User OAuth via token.json),
building the Google Calendar API client, and provides functions for listing
upcoming events and adding new events to the primary calendar.
"""
import logging
import os
from datetime import datetime, timedelta
# TODO: Consider logging critical errors from this module to a file or a more robust system.
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.oauth2.credentials import Credentials as UserCredentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow # For user OAuth flow if run separately
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import settings

logger = logging.getLogger(__name__)

# If modifying these scopes, delete the token.json file.
SCOPES = ['https://www.googleapis.com/auth/calendar']
# Path to store user's access and refresh tokens after first authorization (for user OAuth)
# For a bot, this token.json would typically be for the bot's own calendar or a single managed user.
TOKEN_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'token.json')
# GOOGLE_CREDENTIALS_PATH from settings can be service_account.json or client_secret.json

def get_calendar_service():
    """
    Authenticates and builds the Google Calendar API service client.
    
    Supports two authentication methods based on `settings.GOOGLE_CREDENTIALS_PATH`:
    1. Service Account: If the path points to a `service_account.json` file.
    2. User OAuth: If the path points to a `client_secret.json` file. For this method,
       it first tries to load existing credentials from `token.json`. If not found,
       invalid, or expired and unrefreshable, it indicates that `generate_token.py`
       (or a similar script) should be run to authorize and create `token.json`.
       Interactive OAuth flow is not performed here as it's unsuitable for a running bot/server.

    Returns:
        A Google Calendar API service object if authentication is successful, otherwise None.
    """
    creds = None
    cred_path = os.path.expanduser(settings.GOOGLE_CREDENTIALS_PATH) if settings.GOOGLE_CREDENTIALS_PATH else None

    if not cred_path or not os.path.exists(cred_path):
        logger.warning(f"GOOGLE_CREDENTIALS_PATH ('{cred_path}') is not set or file does not exist.")
        # Try to load token.json if it exists (for user OAuth flow)
        if os.path.exists(TOKEN_JSON_PATH):
            logger.info(f"Loading credentials from token.json: {TOKEN_JSON_PATH}")
            creds = UserCredentials.from_authorized_user_file(TOKEN_JSON_PATH, SCOPES)
        else:
            logger.warning("Cannot initialize Google Calendar service: No valid credentials path and no token.json found.")
            return None
    else:
        # Determine if it's a service account or OAuth client secrets
        if cred_path.endswith('service_account.json'):
            logger.info(f"Using service account credentials from: {cred_path}")
            try:
                creds = ServiceAccountCredentials.from_service_account_file(cred_path, scopes=SCOPES)
            except Exception as e:
                logger.error(f"Failed to load service account credentials: {e}")
                return None
        elif cred_path.endswith('client_secret.json'): # User OAuth credentials
            logger.info(f"Attempting to use user OAuth credentials from: {cred_path}")
            if os.path.exists(TOKEN_JSON_PATH):
                logger.info(f"Loading user credentials from token.json: {TOKEN_JSON_PATH}")
                creds = UserCredentials.from_authorized_user_file(TOKEN_JSON_PATH, SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("User credentials expired, attempting to refresh.")
                    try:
                        creds.refresh(Request())
                    except Exception as e:
                        logger.error(f"Error refreshing user credentials: {e}")
                        creds = None # Could not refresh
                
                if not creds or not creds.valid: # Still not valid, try to run flow (interactive)
                    logger.warning("User credentials not found or invalid, and could not refresh.")
                    logger.warning("Run generate_token.py or a similar script to authorize and create token.json.")
                    # The following flow is interactive and not suitable for a running bot.
                    # It's here for completeness if someone runs this module directly for setup.
                    # flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
                    # print("Please run the OAuth flow by running a dedicated script (e.g., generate_token.py).")
                    # creds = flow.run_local_server(port=0) # This line would block and require user interaction
                    # # Save the credentials for the next run
                    # with open(TOKEN_JSON_PATH, 'w') as token_file:
                    #    token_file.write(creds.to_json())
                    # logger.info(f"New token saved to {TOKEN_JSON_PATH}")
        return None # Cannot proceed without valid token in a bot/server context

    if not creds:
        logger.error("Failed to obtain Google Calendar credentials after all attempts.")
        return None

    try:
        service = build('calendar', 'v3', credentials=creds)
        logger.info("Google Calendar service built successfully.")
        return service
    except HttpError as error:
        logger.error(f'An error occurred building Google Calendar service: {error}')
        return None
    except Exception as e:
        logger.error(f'An unexpected error occurred building Google Calendar service: {e}')
        return None

async def list_upcoming_events(max_results=10):
    """
    Lists upcoming events from the primary Google Calendar.

    Args:
        max_results: The maximum number of events to return. Defaults to 10.

    Returns:
        A string containing a list of upcoming events or an error message.
    """
    service = get_calendar_service()
    if not service:
        return "Error: Google Calendar service is not available."

    try:
        now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = service.events().list(
            calendarId='primary', timeMin=now,
            maxResults=max_results, singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        if not events:
            return "No upcoming events found."

        event_list_str = "Upcoming events:\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            event_list_str += f"- {start}: {event['summary']}\n"
        return event_list_str

    except HttpError as error:
        logger.error(f'An API error occurred with Google Calendar: {error}')
        return f"API Error: Could not retrieve events. {error}"
    except Exception as e:
        logger.error(f'Unexpected error listing events: {e}')
        return f"Unexpected error: {e}"


async def add_event(summary, start_time_str, end_time_str=None, description=None, location=None):
    """
    Adds a new event to the primary Google Calendar.

    Args:
        summary: The summary or title of the event.
        start_time_str: The start time of the event in ISO format (e.g., "YYYY-MM-DDTHH:MM:SS").
        end_time_str: The end time of the event in ISO format. If None, defaults to start_time.
        description: A description for the event.
        location: The location of the event.

    Returns:
        A string confirming the event creation with a link, or an error message.
    """
    service = get_calendar_service()
    if not service:
        return "Error: Google Calendar service is not available."

    try:
        # Datetime format example: "2024-08-15T10:00:00" or "2024-08-15" for all-day.
        # The input strings should be in ISO format. Timezone is assumed to be UTC here
        # as per 'timeZone': 'UTC'. For more flexibility, timezone handling might need enhancement.
        start = {'dateTime': start_time_str, 'timeZone': 'UTC'}
        end = {'dateTime': end_time_str, 'timeZone': 'UTC'} if end_time_str else start

        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': start,
            'end': end,
        }

        created_event = service.events().insert(calendarId='primary', body=event).execute()
        logger.info(f"Event created: {created_event.get('htmlLink')}")
        return f"Event created: {summary} at {start_time_str}. Link: {created_event.get('htmlLink')}"

    except HttpError as error:
        logger.error(f'An API error occurred adding event: {error}')
        return f"API Error: Could not add event. {error}"
    except ValueError as ve: # Catches issues with date/time parsing if not robust
         logger.error(f"Date/Time parsing error: {ve}")
         return "Error: Invalid date/time format. Please use YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD."
    except Exception as e:
        logger.error(f'Unexpected error adding event: {e}')
        return f"Unexpected error: {e}"

if __name__ == '__main__':
    # This section is for testing the service directly.
    # Ensure GOOGLE_CREDENTIALS_PATH is set in .env and points to a valid
    # service_account.json or a client_secret.json (and token.json exists for the latter).
    
    # print("Attempting to list upcoming events...")
    # import asyncio
    # result = asyncio.run(list_upcoming_events())
    # print(result)

    # print("\nAttempting to add a test event...")
    # summary = "Test Event from Script"
    # start_time = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S')
    # end_time = (datetime.utcnow() + timedelta(days=1, hours=1)).strftime('%Y-%m-%dT%H:%M:%S')
    # result_add = asyncio.run(add_event(summary, start_time, end_time, description="A test event added by script."))
    # print(result_add)
    print("To test Google Calendar service, uncomment calls in __main__ and ensure credentials are set up.")
    print("For user OAuth (client_secret.json), you might need to run a separate script first to generate token.json.")

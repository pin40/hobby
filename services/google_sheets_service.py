import gspread
from google.oauth2.service_account import Credentials
from config import settings
import logging

logger = logging.getLogger(__name__)

# Define the scopes needed for Google Sheets API
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file' # Required to create new spreadsheets if needed, or just to access them
]

# Define the headers for the Google Sheet (ensure this matches your sheet structure)
# FirestoreDocID, UserID, TimestampUTC, TimestampMonterrey, Type, Concept, Amount, Category,
# CreatedAtFirestore, UpdatedAtFirestore, DeletedAtFirestore, SheetRowStatus
EXPECTED_HEADERS = [
    "FirestoreDocID", "UserID", "TimestampUTC", "TimestampMonterrey",
    "Type", "Concept", "Amount", "Category",
    "CreatedAtFirestore", "UpdatedAtFirestore", "DeletedAtFirestore", "SheetRowStatus"
]

_gspread_client = None

def get_gspread_client():
    """
    Authenticates with Google Sheets API using service account credentials
    and returns a gspread client instance. Caches the client.
    """
    global _gspread_client
    if _gspread_client:
        return _gspread_client

    if not settings.GOOGLE_SHEETS_CREDENTIALS_PATH:
        logger.error("Google Sheets credentials path not configured in settings.")
        return None

    try:
        creds = Credentials.from_service_account_file(
            settings.GOOGLE_SHEETS_CREDENTIALS_PATH, scopes=SCOPES
        )
        _gspread_client = gspread.authorize(creds)
        logger.info("Successfully authenticated with Google Sheets API.")
        return _gspread_client
    except FileNotFoundError:
        logger.error(f"Google Sheets credentials file not found at: {settings.GOOGLE_SHEETS_CREDENTIALS_PATH}")
        return None
    except Exception as e:
        logger.error(f"Error initializing Google Sheets client: {e}", exc_info=True)
        return None

def get_worksheet(spreadsheet_id: str, sheet_name: str, create_if_missing: bool = True):
    """
    Opens a spreadsheet and gets a specific worksheet (tab).
    If sheet_name is None, it gets the first visible worksheet.
    If create_if_missing is True, it creates the worksheet with headers if it doesn't exist.
    """
    client = get_gspread_client()
    if not client:
        return None

    try:
        spreadsheet = client.open_by_key(spreadsheet_id)

        if sheet_name is None: # Get the first sheet
            worksheet = spreadsheet.sheet1 # sheet1 gets the first visible sheet
            logger.info(f"Accessed first worksheet in spreadsheet ID: {spreadsheet_id}")
        else:
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                logger.info(f"Accessed worksheet '{sheet_name}' in spreadsheet ID: {spreadsheet_id}")
            except gspread.exceptions.WorksheetNotFound:
                if create_if_missing:
                    logger.info(f"Worksheet '{sheet_name}' not found in spreadsheet ID {spreadsheet_id}. Creating it...")
                    worksheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols=str(len(EXPECTED_HEADERS)))
                    worksheet.append_row(EXPECTED_HEADERS) # Add headers to the new sheet
                    logger.info(f"Created worksheet '{sheet_name}' with headers.")
                else:
                    logger.warning(f"Worksheet '{sheet_name}' not found and create_if_missing is False.")
                    return None

        # Verify headers if the sheet is not empty
        if worksheet.row_count > 0 and worksheet.get_values('A1:Z1'): # Check if first row has values
            headers = worksheet.row_values(1)
            if headers != EXPECTED_HEADERS:
                logger.warning(f"Worksheet '{worksheet.title}' has mismatched headers. Expected: {EXPECTED_HEADERS}, Found: {headers}")
                # Optionally, decide how to handle this: overwrite, error out, etc.
                # For now, just log a warning.
        elif not worksheet.get_values('A1:Z1') and create_if_missing: # Empty sheet, ensure headers
             worksheet.append_row(EXPECTED_HEADERS)
             logger.info(f"Added headers to empty worksheet '{worksheet.title}'.")

        return worksheet
    except gspread.exceptions.SpreadsheetNotFound:
        logger.error(f"Spreadsheet not found with ID: {spreadsheet_id}. Ensure it exists and the service account has access.")
        return None
    except Exception as e:
        logger.error(f"Error accessing spreadsheet or worksheet: {e}", exc_info=True)
        return None

def add_record_to_sheet(record_data: list, sheet_name: str = None):
    """
    Adds a single record (list of values) as a new row to the specified Google Sheet.
    If sheet_name is None, it uses the first visible sheet.
    record_data should be a list of values in the order of EXPECTED_HEADERS.
    """
    if not settings.GOOGLE_SHEETS_SPREADSHEET_ID:
        logger.error("Google Sheets Spreadsheet ID not configured.")
        return False

    worksheet = get_worksheet(settings.GOOGLE_SHEETS_SPREADSHEET_ID, sheet_name, create_if_missing=True)
    if not worksheet:
        logger.error("Failed to get worksheet. Record not added.")
        return False

    try:
        if len(record_data) != len(EXPECTED_HEADERS):
            logger.error(f"Record data length ({len(record_data)}) does not match expected headers length ({len(EXPECTED_HEADERS)}). Record: {record_data}")
            return False

        worksheet.append_row(record_data)
        logger.info(f"Successfully added record to Google Sheet '{worksheet.title}': {record_data[0] if record_data else 'N/A_ID'}")
        return True
    except Exception as e:
        logger.error(f"Error adding record to Google Sheet '{worksheet.title}': {e}", exc_info=True)
        return False

# Example of how to format data for add_record_to_sheet:
# from datetime import datetime
# record = [
# "firestore_doc_123", # FirestoreDocID
# "user_abc", # UserID
# datetime.utcnow().isoformat(), # TimestampUTC
# datetime.now(pytz.timezone('America/Monterrey')).isoformat(), # TimestampMonterrey
# "expense", # Type
# "Coffee", # Concept
# 75.50, # Amount
# "Food", # Category
# datetime.utcnow().isoformat(), # CreatedAtFirestore (example, use actual Firestore timestamp)
# datetime.utcnow().isoformat(), # UpdatedAtFirestore (example, use actual Firestore timestamp)
# None, # DeletedAtFirestore
# "ACTIVE" # SheetRowStatus
# ]
# add_record_to_sheet(settings.GOOGLE_SHEETS_SPREADSHEET_ID, "Finances_Log", record)

# TODO: Implement functions for updating and deleting (marking as deleted) records
# def find_row_by_firestore_id(firestore_id: str, worksheet): ...
# def update_record_in_sheet(firestore_id: str, updated_data: dict, worksheet): ...
# def mark_record_as_deleted_in_sheet(firestore_id: str, worksheet): ...

if __name__ == '__main__':
    # This is for testing purposes.
    # Ensure your .env file has GOOGLE_SHEETS_CREDENTIALS_PATH and GOOGLE_SHEETS_SPREADSHEET_ID
    # And that the credentials file is correctly placed.
    logger.info("Testing Google Sheets Service...")

    # Load .env if running directly for testing (main app should handle this via settings)
    from dotenv import load_dotenv
    import os
    # Assuming .env is in the project root, two levels up from services/
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)

    # Reload settings after loading .env for testing
    from config import settings as test_settings # Re-import or use a reloader if settings caches values

    if not test_settings.GOOGLE_SHEETS_CREDENTIALS_PATH or not test_settings.GOOGLE_SHEETS_SPREADSHEET_ID:
        logger.error("Missing GOOGLE_SHEETS_CREDENTIALS_PATH or GOOGLE_SHEETS_SPREADSHEET_ID in .env for testing.")
    else:
        logger.info(f"Using Spreadsheet ID: {test_settings.GOOGLE_SHEETS_SPREADSHEET_ID}")
        logger.info(f"Using Credentials Path: {test_settings.GOOGLE_SHEETS_CREDENTIALS_PATH}")

        client = get_gspread_client()
        if client:
            logger.info("Successfully got gspread client.")
            # Example: Get a specific worksheet (tab) or the first one
            # Replace "Sheet1" with your actual sheet name if needed, or None for first sheet
            worksheet_to_test = get_worksheet(test_settings.GOOGLE_SHEETS_SPREADSHEET_ID, sheet_name="Sheet1")
            if worksheet_to_test:
                logger.info(f"Successfully accessed worksheet: {worksheet_to_test.title}")

                # Test adding a record
                from datetime import datetime, timezone
                import pytz # Ensure pytz is installed for timezone conversion
                monterrey_tz_test = pytz.timezone('America/Monterrey')

                # Ensure Firestore Timestamps are converted to ISO strings for Sheets
                # For server timestamps, they'd resolve to datetime objects when read back,
                # or you might just log when the sheet entry was made.
                # Firestore's server timestamp isn't known until write, so for Sheets, you typically log sheet write time
                # or pass through the resolved Firestore timestamp after the fact.

                # For this example, using current times.
                created_at_fs_mock = datetime.now(timezone.utc)
                updated_at_fs_mock = datetime.now(timezone.utc)

                test_record = [
                    f"test_doc_{datetime.now().strftime('%Y%m%d%H%M%S')}", # FirestoreDocID
                    "test_user_123", # UserID
                    datetime.now(timezone.utc).isoformat(), # TimestampUTC (when this row is being prepared)
                    datetime.now(monterrey_tz_test).isoformat(), # TimestampMonterrey
                    "income", # Type
                    "Test Income from Service", # Concept
                    100.99, # Amount
                    "Testing", # Category
                    created_at_fs_mock.isoformat(), # CreatedAtFirestore (simulated)
                    updated_at_fs_mock.isoformat(), # UpdatedAtFirestore (simulated)
                    None, # DeletedAtFirestore (None or empty string)
                    "ACTIVE" # SheetRowStatus
                ]
                if add_record_to_sheet(test_record, sheet_name="Sheet1"):
                    logger.info("Test record added successfully.")
                else:
                    logger.error("Failed to add test record.")
            else:
                logger.error("Failed to access worksheet for testing.")
        else:
            logger.error("Failed to get gspread client for testing.")

    logger.info("Google Sheets Service test script finished.")

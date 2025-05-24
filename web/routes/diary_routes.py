"""
Web routes for diary-related operations.
Provides a page for viewing diary entries for a demo user.
"""
from flask import Blueprint, render_template, flash
from services.firebase_service import get_firestore_client
from firebase_admin import firestore # For firestore.Query
from datetime import datetime

diary_bp = Blueprint('diary_bp', __name__, template_folder='../templates/diary')

# Using the same DEMO_USER_ID as in finance_routes for consistency
DEMO_USER_ID = "123456789" # Replace with an actual user_id from your Firestore
# TODO: Implement proper user authentication and management.

@diary_bp.route('/diary')
def diary_page():
    """
    Renders the diary page, displaying recent diary entries for the DEMO_USER_ID.
    Fetches up to 20 latest entries from Firestore and handles potential errors.
    """
    db = get_firestore_client()
    if not db:
        flash("Database service is not available.", "danger")
        return render_template("diary.html", entries=[], error=True)

    try:
        diary_ref = db.collection("users").document(DEMO_USER_ID).collection("diary")
        # Fetch entries, ordered by timestamp descending (newest first)
        docs_query = diary_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(20) # Get last 20 entries
        docs = docs_query.stream()

        entries = []
        for doc in docs:
            data = doc.to_dict()
            # Ensure timestamp is python datetime for formatting
            if hasattr(data['timestamp'], 'to_datetime'): # Firestore Timestamp
                data['timestamp'] = data['timestamp'].to_datetime()
            elif isinstance(data['timestamp'], str):
                 data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            # If already Python datetime, it's fine.
            entries.append(data)
        
        return render_template("diary.html", entries=entries, user_id=DEMO_USER_ID)
    except Exception as e:
        flash(f"An error occurred while fetching diary entries: {e}", "danger")
        # TODO: Log the exception e properly
        return render_template("diary.html", entries=[], error=True, error_message=str(e))

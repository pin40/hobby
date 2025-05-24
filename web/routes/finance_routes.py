"""
Web routes for finance-related operations.
Provides pages for viewing financial summaries and exporting financial data.
"""
from flask import Blueprint, render_template, Response, flash
from services.firebase_service import get_firestore_client
from firebase_admin import firestore # For firestore.Query
import pandas as pd
import io
from datetime import datetime

finance_bp = Blueprint('finance_bp', __name__, template_folder='../templates/finances')

# TODO: Replace with a proper user identification mechanism if needed for multi-user web app
# For now, using a placeholder. This ID should exist in your Firestore data for testing.
DEMO_USER_ID = "123456789" # Replace with an actual user_id from your Firestore if you have test data
# TODO: Implement proper user authentication and management instead of a demo user ID.

@finance_bp.route('/finances')
def finances_page():
    db = get_firestore_client()
    if not db:
        flash("Database service is not available.", "danger")
        return render_template("finances.html", income=[], expenses=[], balance=0, error=True)

    try:
        # Fetching data similar to the bot's balance function
        finances_ref = db.collection("users").document(DEMO_USER_ID).collection("finances")
        
        # Synchronous Firestore access
        docs = finances_ref.order_by("timestamp", direction=firestore.Query.ASCENDING).stream()

        all_transactions = []
        total_income = 0.0
        total_expense = 0.0

        for doc in docs:
            data = doc.to_dict()
            # Ensure timestamp is python datetime for formatting, handle Firestore Timestamp
            if hasattr(data['timestamp'], 'to_datetime'): # Check if it's a Firestore Timestamp
                data['timestamp'] = data['timestamp'].to_datetime()
            elif isinstance(data['timestamp'], str): # Or if it's already a string
                 data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')) # basic ISO string to datetime
            # If it's already a Python datetime, it's fine.
            
            all_transactions.append(data)
            if data["type"] == "income":
                total_income += data["amount"]
            elif data["type"] == "expense":
                total_expense += data["amount"]
        
        current_balance = total_income - total_expense
        
        # Separate income and expenses for display
        income_transactions = [t for t in all_transactions if t['type'] == 'income']
        expense_transactions = [t for t in all_transactions if t['type'] == 'expense']

        return render_template(
            "finances.html", 
            income_transactions=income_transactions, 
            expense_transactions=expense_transactions,
            total_income=total_income,
            total_expense=total_expense,
            balance=current_balance,
            user_id=DEMO_USER_ID # For display purposes
        )
    except Exception as e:
        flash(f"An error occurred while fetching financial data: {e}", "danger")
        return render_template("finances.html", income=[], expenses=[], balance=0, error=True, error_message=str(e))

@finance_bp.route('/finances/export')
def export_finances_excel():
    """
    Handles the export of financial data for the DEMO_USER_ID to an Excel file.
    Fetches all finance entries, converts them to a Pandas DataFrame,
    and returns an Excel file as a downloadable response.
    """
    db = get_firestore_client()
    if not db:
        flash("Database service is not available for export.", "danger")
        # This route is called directly, so redirect or error differently
        return "Error: Database service not available.", 500

    try:
        finances_ref = db.collection("users").document(DEMO_USER_ID).collection("finances")
        docs = finances_ref.order_by("timestamp", direction=firestore.Query.ASCENDING).stream()

        records = []
        for doc in docs:
            data = doc.to_dict()
            # Timestamp handling for Pandas DataFrame
            ts = data.get("timestamp")
            if hasattr(ts, 'to_datetime'): # Firestore Timestamp
                timestamp_str = ts.to_datetime().strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(ts, datetime): # Python datetime
                timestamp_str = ts.strftime("%Y-%m-%d %H:%M:%S")
            else: # Fallback
                timestamp_str = str(ts)

            records.append({
                "Timestamp": timestamp_str,
                "Type": data.get("type"),
                "Amount": data.get("amount"),
                "Description": data.get("description")
            })

        if not records:
            flash("No financial data to export.", "info")
            # Redirect to finances page or show a message
            return "No data to export.", 404

        df = pd.DataFrame(records)
        
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, sheet_name="Finances")
        excel_buffer.seek(0)

        return Response(
            excel_buffer.getvalue(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment;filename=finances_{DEMO_USER_ID}_{datetime.now().strftime('%Y%m%d')}.xlsx"}
        )
    except Exception as e:
        flash(f"An error occurred during Excel export: {e}", "danger")
        # Log the error server-side
        # TODO: Replace print with proper logging (e.g., current_app.logger.error(...))
        print(f"Error exporting finances to excel: {e}") 
        return f"Error during export: {e}", 500

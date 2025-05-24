import logging
from telegram import Update, InputFile
from telegram.ext import CallbackContext
from services.firebase_service import get_firestore_client # Adjusted path
import pandas as pd
import io
from datetime import datetime

# Assuming firebase_admin.firestore is the correct way to get Query
from firebase_admin import firestore

logger = logging.getLogger(__name__)

async def add_income(update: Update, context: CallbackContext):
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Usage: /add_income <amount> <description>")
            return

        amount = float(args[0])
        description = " ".join(args[1:])
        user_id = str(update.effective_user.id)

        db = get_firestore_client()
        if not db:
            await update.message.reply_text("Error: Database service is not available.")
            return

        entry = {
            "type": "income",
            "amount": amount,
            "description": description,
            "timestamp": datetime.utcnow()
        }
        # Firestore add is synchronous in firebase-admin
        doc_ref = db.collection("users").document(user_id).collection("finances").add(entry)
        await update.message.reply_text(f"Income of {amount:.2f} for '{description}' added successfully.")
    except ValueError:
        await update.message.reply_text("Invalid amount. Please enter a number for the amount.")
    except Exception as e:
        logger.error(f"Error adding income: {e}", exc_info=True)
        await update.message.reply_text("An error occurred while adding income.")

async def add_expense(update: Update, context: CallbackContext):
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Usage: /add_expense <amount> <description>")
            return

        amount = float(args[0])
        description = " ".join(args[1:])
        user_id = str(update.effective_user.id)

        db = get_firestore_client()
        if not db:
            await update.message.reply_text("Error: Database service is not available.")
            return

        entry = {
            "type": "expense",
            "amount": amount,
            "description": description,
            "timestamp": datetime.utcnow()
        }
        # Firestore add is synchronous
        doc_ref = db.collection("users").document(user_id).collection("finances").add(entry)
        await update.message.reply_text(f"Expense of {amount:.2f} for '{description}' added successfully.")
    except ValueError:
        await update.message.reply_text("Invalid amount. Please enter a number for the amount.")
    except Exception as e:
        logger.error(f"Error adding expense: {e}", exc_info=True)
        await update.message.reply_text("An error occurred while adding expense.")

async def balance(update: Update, context: CallbackContext):
    try:
        user_id = str(update.effective_user.id)
        db = get_firestore_client()
        if not db:
            await update.message.reply_text("Error: Database service is not available.")
            return

        finances_ref = db.collection("users").document(user_id).collection("finances")
        
        # Synchronous stream() for firebase-admin
        docs = finances_ref.stream()

        total_income = 0.0
        total_expense = 0.0

        for doc in docs:
            data = doc.to_dict()
            if data.get("type") == "income" and isinstance(data.get("amount"), (int, float)):
                total_income += data["amount"]
            elif data.get("type") == "expense" and isinstance(data.get("amount"), (int, float)):
                total_expense += data["amount"]
        
        current_balance = total_income - total_expense
        await update.message.reply_text(f"Financial Balance:\n"
                                       f"Total Income: {total_income:.2f}\n"
                                       f"Total Expense: {total_expense:.2f}\n"
                                       f"Current Balance: {current_balance:.2f}")
    except Exception as e:
        logger.error(f"Error calculating balance: {e}", exc_info=True)
        await update.message.reply_text("An error occurred while calculating balance.")

async def export_finances(update: Update, context: CallbackContext):
    try:
        user_id = str(update.effective_user.id)
        db = get_firestore_client()
        if not db:
            await update.message.reply_text("Error: Database service is not available.")
            return

        finances_ref = db.collection("users").document(user_id).collection("finances")
        # Synchronous stream() with ordering for firebase-admin
        docs = finances_ref.order_by("timestamp", direction=firestore.Query.ASCENDING).stream()

        records = []
        for doc in docs:
            data = doc.to_dict()
            # Ensure timestamp is handled correctly, it might be already a datetime object from Firestore
            ts = data.get("timestamp")
            if isinstance(ts, datetime):
                timestamp_str = ts.strftime("%Y-%m-%d %H:%M:%S")
            elif hasattr(ts, 'strftime'): # For Firestore Timestamp objects if returned directly
                 timestamp_str = ts.strftime("%Y-%m-%d %H:%M:%S")
            else: # Fallback if it's some other type or None
                timestamp_str = str(ts) if ts is not None else "N/A"

            records.append({
                "Timestamp": timestamp_str,
                "Type": data.get("type", "N/A"),
                "Amount": data.get("amount", 0),
                "Description": data.get("description", "N/A")
            })

        if not records:
            await update.message.reply_text("No financial data to export.")
            return

        df = pd.DataFrame(records)
        
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, sheet_name="Finances")
        excel_buffer.seek(0)

        await update.message.reply_document(
            document=InputFile(excel_buffer, filename=f"finances_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"),
            caption="Here is your financial data export."
        )

    except Exception as e:
        logger.error(f"Error exporting finances: {e}", exc_info=True)
        await update.message.reply_text("An error occurred while exporting financial data.")

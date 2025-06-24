import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters, CallbackContext
from datetime import datetime
import pytz # For timezone handling
from services.firebase_service import get_firestore_client # Adjusted path
import pandas as pd # Keep for export
import io # Keep for export
from firebase_admin import firestore # Keep for export and balance

# Setup logging
logger = logging.getLogger(__name__)

# States for conversation handlers
CONCEPT, AMOUNT, CATEGORY, CONFIRMATION = range(4)
MENU_PRINCIPAL = ConversationHandler.END # Alias for clarity, signifies returning to no specific state

# Timezone for Monterrey
monterrey_tz = pytz.timezone('America/Monterrey')

def get_current_time_monterrey() -> str:
    """Gets the current time in Monterrey HH:MM AM/PM format."""
    now_monterrey = datetime.now(monterrey_tz)
    return now_monterrey.strftime("%I:%M %p %Z") # Added %Z for timezone abbreviation

# --- Main Menu and Core Commands ---
async def start_command(update: Update, context: CallbackContext) -> int:
    """Sends a welcome message and the main menu."""
    user = update.effective_user
    current_time = get_current_time_monterrey()

    logger.info(f"User {user.id} ({user.username}) accessed main menu via /start or callback.")

    keyboard = [
        [
            InlineKeyboardButton("➕ Agregar Ingreso", callback_data='conv_add_income'),
            InlineKeyboardButton("➖ Agregar Gasto", callback_data='conv_add_expense')
        ],
        [
            InlineKeyboardButton("💰 Ver Saldo", callback_data='view_balance'),
            InlineKeyboardButton("📋 Ver Historial", callback_data='view_history')
        ],
        [
            InlineKeyboardButton("🤖 Asistente IA", callback_data='ai_assistant'),
            InlineKeyboardButton("❌ Salir/Cancelar", callback_data='cancel_op_button') # General cancel/exit button
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Escape MarkdownV2 characters if user.first_name might contain them.
    # For simplicity, assuming it's safe or will be handled by the library.
    welcome_text = (
        f"🤖 ¡Hola {user.first_name}! Soy tu Asistente Financiero FinBot 🤖\n\n"
        f"Zona Horaria: Monterrey\n"
        f"Hora Actual: {current_time}\n\n"
        f"¿Qué te gustaría hacer hoy?"
    )

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        try:
            await query.edit_message_text(text=welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error editing message for main menu: {e}")
            # Fallback: send as new message if edit fails (e.g. message too old)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text=welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

    return MENU_PRINCIPAL # End any active conversation or signify we are at the top level

async def cancel_operation_button(update: Update, context: CallbackContext) -> int:
    """Handles the generic cancel button press, returning to main menu or just acknowledging."""
    query = update.callback_query
    await query.answer("Operación cancelada.")
    logger.info(f"User {update.effective_user.id} pressed general cancel button.")
    # Effectively show the main menu again by calling start_command logic
    return await start_command(update, context)

async def unimplemented_feature(update: Update, context: CallbackContext) -> None:
    """Handles features not yet implemented when a button is pressed."""
    query = update.callback_query
    if query:
        await query.answer("🏗️ Función en construcción.", show_alert=True)
        logger.warning(f"User {update.effective_user.id} tried to access unimplemented feature: {query.data}")
    elif update.message: # Should not happen with buttons but good fallback
        await update.message.reply_text("🏗️ Esta función aún no está implementada.")

# --- Add Income/Expense Conversation Flow ---
async def conv_add_movement_start(update: Update, context: CallbackContext) -> int:
    """Starts the conversation for adding an income or expense based on callback_data."""
    query = update.callback_query
    await query.answer()

    movement_type = "income" if query.data == 'conv_add_income' else "expense"
    context.user_data['movement_type'] = movement_type
    context.user_data['movement_details'] = {} # Reset or initialize details

    type_text = "ingreso" if movement_type == "income" else "gasto"
    logger.info(f"User {update.effective_user.id} started adding a new {type_text}.")

    await query.edit_message_text(
        text=f"✍️ Vamos a registrar un nuevo *{type_text}*.\n\n"
             f"Por favor, introduce el *concepto* (ej: Compra de despensa, Salario):",
        parse_mode='Markdown'
    )
    return CONCEPT

async def receive_concept(update: Update, context: CallbackContext) -> int:
    """Receives the concept and asks for the amount."""
    concept_text = update.message.text
    if not concept_text or len(concept_text.strip()) == 0:
        await update.message.reply_text("El concepto no puede estar vacío. Por favor, introduce un concepto:")
        return CONCEPT

    context.user_data['movement_details']['concept'] = concept_text.strip()
    logger.info(f"User {update.effective_user.id} entered concept: {concept_text.strip()}")

    await update.message.reply_text("💰 Ahora introduce el *monto* (ej: 150.75):", parse_mode='Markdown')
    return AMOUNT

async def receive_amount(update: Update, context: CallbackContext) -> int:
    """Receives the amount and asks for the category."""
    amount_text = update.message.text
    try:
        amount = float(amount_text)
        if amount <= 0:
            await update.message.reply_text("⚠️ El monto debe ser un número positivo mayor que cero. Intenta de nuevo:")
            return AMOUNT
        context.user_data['movement_details']['amount'] = amount
        logger.info(f"User {update.effective_user.id} entered amount: {amount}")

        keyboard = [[InlineKeyboardButton("⏭️ Saltar Categoría", callback_data='skip_category')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🏷️ Opcionalmente, introduce una *categoría* (ej: Comida, Transporte).\n"
            "O presiona 'Saltar Categoría'.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return CATEGORY
    except ValueError:
        await update.message.reply_text("⚠️ Formato de monto inválido. Por favor, introduce un número (ej: 150.75):")
        return AMOUNT

async def receive_category(update: Update, context: CallbackContext) -> int:
    """Receives the category (text) and proceeds to confirmation."""
    category_text = update.message.text
    if not category_text or len(category_text.strip()) == 0:
         # Allow empty category if user just sends message instead of button
        context.user_data['movement_details']['category'] = None
        logger.info(f"User {update.effective_user.id} submitted empty category, treating as skipped.")
    else:
        context.user_data['movement_details']['category'] = category_text.strip()
        logger.info(f"User {update.effective_user.id} entered category: {category_text.strip()}")
    return await show_confirmation_summary(update, context)

async def skip_category(update: Update, context: CallbackContext) -> int:
    """Skips adding a category and proceeds to confirmation."""
    query = update.callback_query
    await query.answer()
    context.user_data['movement_details']['category'] = None
    logger.info(f"User {update.effective_user.id} skipped category.")
    # Message was edited by button press, now show summary
    return await show_confirmation_summary(update, context, from_button=True)


async def show_confirmation_summary(update: Update, context: CallbackContext, from_button: bool = False) -> int:
    """Shows movement details and asks for confirmation. Can be called after text input or button press."""
    details = context.user_data.get('movement_details', {})
    movement_type = context.user_data.get('movement_type', 'movimiento')
    type_text = "Ingreso" if movement_type == "income" else "Gasto"

    # Ensure all keys exist, providing defaults
    concept = details.get('concept', 'N/A')
    amount = details.get('amount', 0.0)
    category = details.get('category', 'Ninguna')

    # Timestamping
    current_time_utc = datetime.utcnow() # For Firebase (best practice)
    current_time_mt = current_time_utc.astimezone(monterrey_tz) # For display

    # Store UTC timestamp in context for saving
    context.user_data['movement_details']['timestamp_utc'] = current_time_utc
    # Store display timestamp if needed, or format on the fly
    details['display_timestamp'] = current_time_mt.strftime('%d/%m/%Y %I:%M %p')


    confirmation_message = (
        f"🧾 *Resumen del {type_text}*\n\n"
        f"*Concepto:* _{concept}_\n"
        f"*Monto:* *${amount:.2f} MXN*\n"
        f"*Categoría:* _{category}_\n"
        f"*Fecha y Hora:* _{details['display_timestamp']}_\n\n"
        f"¿Confirmas guardar este movimiento?"
    )

    keyboard = [
        [InlineKeyboardButton("✅ Confirmar", callback_data='save_movement')],
        # TODO: Add edit buttons: [Concepto], [Monto], [Categoría]
        [InlineKeyboardButton("❌ Cancelar Registro", callback_data='cancel_add_movement')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if from_button and update.callback_query: # e.g. from skip_category or an edit button
        await update.callback_query.edit_message_text(text=confirmation_message, reply_markup=reply_markup, parse_mode='Markdown')
    elif update.message: # Coming from text input (concept, amount, or category)
         await update.message.reply_text(text=confirmation_message, reply_markup=reply_markup, parse_mode='Markdown')
    elif update.callback_query: # Fallback for other callback query entries to this state
        await update.callback_query.edit_message_text(text=confirmation_message, reply_markup=reply_markup, parse_mode='Markdown')
    else: # Should not happen
        logger.error("show_confirmation_summary called without Update or CallbackQuery context")
        await context.bot.send_message(update.effective_chat.id, text=confirmation_message, reply_markup=reply_markup, parse_mode='Markdown')

    return CONFIRMATION

async def save_movement(update: Update, context: CallbackContext) -> int:
    """Saves the movement to Firebase and ends conversation, then shows main menu."""
    query = update.callback_query
    await query.answer("Guardando...") # Temporary feedback

    details = context.user_data.get('movement_details', {})
    movement_type = context.user_data.get('movement_type', 'unknown_type')
    user_id = str(update.effective_user.id)

    # Prepare data for Firebase
    # Using UTC for timestamp as good practice
    entry_to_save = {
        "type": movement_type,
        "amount": details.get('amount'),
        "concept": details.get('concept'), # Changed from 'description' to 'concept'
        "category": details.get('category'),
        "timestamp": details.get('timestamp_utc', datetime.utcnow()), # Firestore will convert to its Timestamp type
        "created_at": firestore.SERVER_TIMESTAMP, # Let Firestore set creation time
        "updated_at": firestore.SERVER_TIMESTAMP, # Let Firestore set update time
        "user_timezone": "America/Monterrey" # Store user's timezone for reference
    }

    try:
        db = get_firestore_client()
        if not db:
            await query.edit_message_text("Error: No se pudo conectar a la base de datos.")
            return await start_command(update, context) # Go to main menu

        # Save to Firestore
        # .add() returns a tuple (timestamp, DocumentReference)
        timestamp_fb, doc_ref = db.collection("users").document(user_id).collection("finances").add(entry_to_save)
        firestore_doc_id = doc_ref.id # Get the actual Firestore document ID

        logger.info(f"User {user_id} saved {movement_type} to Firebase (ID: {firestore_doc_id}): Concept: {entry_to_save['concept']}, Amount: {entry_to_save['amount']}")

        # --- Sync to Google Sheets ---
        try:
            from services.google_sheets_service import add_record_to_sheet, EXPECTED_HEADERS
            from config import settings as app_settings

            # Prepare data for Google Sheets
            # Ensure data aligns with EXPECTED_HEADERS
            # FirestoreDocID, UserID, TimestampUTC, TimestampMonterrey,
            # Type, Concept, Amount, Category,
            # CreatedAtFirestore, UpdatedAtFirestore, DeletedAtFirestore, SheetRowStatus

            # Firestore timestamps are already datetime objects if using SERVER_TIMESTAMP and then read back,
            # or the `timestamp_fb` from the .add() call is the commit timestamp.
            # For simplicity, using the entry_to_save['timestamp'] (which is UTC) and formatting.
            # CreatedAt/UpdatedAt from Firestore are server-side, so we can't know them *before* the write.
            # We can pass what we have or make another read, or simplify what we store in Sheets.
            # For now, let's use the client-generated UTC timestamp for CreatedAt/UpdatedAt in Sheets
            # or acknowledge they might be slightly different from server's version if not re-fetched.

            created_at_iso = entry_to_save['timestamp'].isoformat() # approx created_at
            updated_at_iso = entry_to_save['timestamp'].isoformat() # approx updated_at

            # TimestampMonterrey for display
            timestamp_monterrey_str = entry_to_save['timestamp'].astimezone(monterrey_tz).strftime('%Y-%m-%d %H:%M:%S')


            sheet_record = [
                firestore_doc_id,
                user_id,
                entry_to_save['timestamp'].isoformat(), # TimestampUTC
                timestamp_monterrey_str, # TimestampMonterrey
                entry_to_save['type'],
                entry_to_save['concept'],
                entry_to_save['amount'],
                entry_to_save['category'],
                created_at_iso, # CreatedAtFirestore (approx, from client)
                updated_at_iso, # UpdatedAtFirestore (approx, from client)
                None,  # DeletedAtFirestore (empty for new records)
                "ACTIVE" # SheetRowStatus
            ]

            # Ensure the record matches headers length, defensively
            if len(sheet_record) == len(EXPECTED_HEADERS):
                if app_settings.GOOGLE_SHEETS_SPREADSHEET_ID: # Check if configured
                    sheet_sync_success = add_record_to_sheet(
                        record_data=sheet_record,
                        sheet_name=app_settings.GOOGLE_SHEETS_DEFAULT_SHEET_NAME
                    )
                    if sheet_sync_success:
                        logger.info(f"Successfully synced new record (ID: {firestore_doc_id}) to Google Sheets.")
                    else:
                        logger.error(f"Failed to sync new record (ID: {firestore_doc_id}) to Google Sheets.")
                        # Non-blocking error for user, but logged for admin.
                else:
                    logger.warning("Google Sheets Spreadsheet ID not configured. Skipping sync.")
            else:
                logger.error(f"Mismatch between sheet_record length ({len(sheet_record)}) and EXPECTED_HEADERS length ({len(EXPECTED_HEADERS)}). Skipping GSheets sync.")

        except Exception as e_gsheets:
            logger.error(f"Error during Google Sheets sync for record ID {firestore_doc_id}: {e_gsheets}", exc_info=True)
            # Continue even if GSheets sync fails, Firebase is primary.

        type_text_display = "Ingreso" if movement_type == "income" else "Gasto"
        final_message = (
            f"✅ ¡{type_text_display} guardado exitosamente!\n\n"
            f"Concepto: _{entry_to_save['concept']}_\n"
            f"Monto: *${entry_to_save['amount']:.2f} MXN*\n"
            # f"Tu saldo actual es: 💰 $SALDO_AQUI MXN (próximamente)" # Balance calculation can be intensive
        )
        await query.edit_message_text(text=final_message, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error saving movement to Firebase for user {user_id}: {e}", exc_info=True)
        await query.edit_message_text(f"❌ Ocurrió un error al guardar el movimiento: {e}")

    # Clean up user_data for this conversation
    for key in ['movement_type', 'movement_details']:
        if key in context.user_data:
            del context.user_data[key]

    # After saving, it's good to return to the main menu.
    # We can't directly return start_command output from here if it also tries to edit the same message.
    # So, we'll send a new message for the menu or add a button.
    # For now, let the user call /start or /menu.
    # A "Back to Menu" button on the success message could be an option.
    # Let's try calling start_command to reshow menu. This might cause "Message is not modified" if not careful.
    # The safest is to just end the conversation here. The user can type /start.
    # Or, provide a button on the success message to go back to the menu.

    # Option: Add a "Main Menu" button to the success message
    keyboard = [[InlineKeyboardButton("⬅️ Volver al Menú Principal", callback_data='show_main_menu_from_save')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    current_text = query.message.text # Get current text of the message
    await query.edit_message_text(text=current_text + "\n\n¿Deseas realizar otra acción?", reply_markup=reply_markup, parse_mode='Markdown')

    return MENU_PRINCIPAL # End conversation here


async def cancel_add_movement(update: Update, context: CallbackContext) -> int:
    """Cancels the add movement flow and returns to main menu."""
    query = update.callback_query
    await query.answer("Registro de movimiento cancelado.")
    logger.info(f"User {update.effective_user.id} cancelled adding movement.")

    for key in ['movement_type', 'movement_details']:
        if key in context.user_data:
            del context.user_data[key]

    return await start_command(update, context) # Go back to main menu

# --- Balance Function ---
async def view_balance_command(update: Update, context: CallbackContext):
    """Handles the 'View Balance' button."""
    query = update.callback_query
    await query.answer("Calculando saldo...") # Feedback to user
    user_id = str(update.effective_user.id)

    try:
        db = get_firestore_client()
        if not db:
            await query.edit_message_text("Error: No se pudo conectar a la base de datos.")
            return

        finances_ref = db.collection("users").document(user_id).collection("finances")
        # Ensure querying for non-deleted documents
        docs = finances_ref.where("deleted_at", "==", None).stream()

        total_income = 0.0
        total_expense = 0.0

        for doc in docs:
            data = doc.to_dict()
            amount = data.get("amount", 0.0)
            if not isinstance(amount, (int, float)): # Skip if amount is not a number
                continue

            if data.get("type") == "income":
                total_income += amount
            elif data.get("type") == "expense":
                total_expense += amount
        
        current_balance = total_income - total_expense

        balance_message = (
            f"💰 *Tu Saldo Actual*\n\n"
            f"🟢 Ingresos Totales: *${total_income:,.2f} MXN*\n"
            f"🔴 Gastos Totales: *${total_expense:,.2f} MXN*\n"
            f"-----------------------------------\n"
            f"saldo Final: *${current_balance:,.2f} MXN*\n\n"
            f"Hora del cálculo: {get_current_time_monterrey()}"
        )

        keyboard = [[InlineKeyboardButton("⬅️ Volver al Menú", callback_data='show_main_menu_from_balance')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text=balance_message, reply_markup=reply_markup, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error calculating balance for user {user_id}: {e}", exc_info=True)
        await query.edit_message_text(f"❌ Ocurrió un error al calcular tu saldo: {e}")
        # Optionally, still provide a way back to the menu
        keyboard = [[InlineKeyboardButton("⬅️ Volver al Menú", callback_data='show_main_menu_from_balance_error')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Intenta de nuevo más tarde.", reply_markup=reply_markup)


# --- Placeholder for original command-based functions (can be removed or adapted if no longer needed) ---
# These are kept for reference or if direct command invocation is still desired for some reason.
# They would need `CommandHandler`s in `finance_handlers` list if used.

async def add_income_legacy(update: Update, context: CallbackContext):
    # This is the old command-based way. The new system uses conversations.
    await update.message.reply_text("Para agregar ingresos, por favor usa el menú de botones (escribe /start).")

async def add_expense_legacy(update: Update, context: CallbackContext):
    # This is the old command-based way. The new system uses conversations.
    await update.message.reply_text("Para agregar gastos, por favor usa el menú de botones (escribe /start).")

async def export_finances_command(update: Update, context: CallbackContext):
    """Handles the direct /export command if you want to keep it."""
    query_or_message = update.callback_query if update.callback_query else update.message
    if update.callback_query:
        await update.callback_query.answer("Generando exportación...")

    user_id = str(update.effective_user.id)
    try:
        db = get_firestore_client()
        if not db:
            await query_or_message.reply_text("Error: Database service is not available.")
            return

        finances_ref = db.collection("users").document(user_id).collection("finances")
        # Ensure querying for non-deleted documents and order by timestamp
        docs = finances_ref.where("deleted_at", "==", None).order_by("timestamp", direction=firestore.Query.ASCENDING).stream()

        records = []
        for doc in docs:
            data = doc.to_dict()
            ts_utc = data.get("timestamp") # Should be Firestore Timestamp or UTC datetime
            if isinstance(ts_utc, datetime):
                ts_display = ts_utc.astimezone(monterrey_tz).strftime("%d/%m/%Y %I:%M %p")
            else: # Fallback if it's not datetime (should be, from save_movement)
                ts_display = str(ts_utc) if ts_utc else "N/A"

            records.append({
                "Fecha (Monterrey)": ts_display,
                "Tipo": data.get("type", "N/A").capitalize(),
                "Concepto": data.get("concept", "N/A"),
                "Monto": data.get("amount", 0),
                "Categoría": data.get("category", "N/A")
            })

        if not records:
            await query_or_message.reply_text("No tienes datos financieros para exportar.")
            return

        df = pd.DataFrame(records)
        
        excel_buffer = io.BytesIO()
        # Use a more modern Excel writer if available, or stick to default
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Finanzas")
        excel_buffer.seek(0)

        # Send the file
        # Note: reply_document is a method of Message, not CallbackQuery.
        # We need to send it via context.bot.send_document or query.message.reply_document

        file_to_send = InputFile(excel_buffer, filename=f"FinBot_Export_{user_id}_{datetime.now(monterrey_tz).strftime('%Y%m%d_%H%M%S')}.xlsx")

        if update.callback_query:
            await update.callback_query.message.reply_document(
                document=file_to_send,
                caption="📄 Aquí está tu exportación de datos financieros."
            )
            # Optionally, edit the original message to remove "Generating..." or buttons
            # await update.callback_query.edit_message_text("Exportación completada.")
        else: # From /export command
            await update.message.reply_document(
                document=file_to_send,
                caption="📄 Aquí está tu exportación de datos financieros."
            )

    except Exception as e:
        logger.error(f"Error exporting finances for user {user_id}: {e}", exc_info=True)
        error_message_target = update.callback_query.message if update.callback_query else update.message
        await error_message_target.reply_text(f"❌ Ocurrió un error al exportar tus datos: {e}")

    # If called from a callback, good to return to main menu or end conversation state
    if update.callback_query:
        return await start_command(update, context) # Or specific state
    # If called from a command, it just ends.


# --- Conversation Handler Setup ---
add_movement_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(conv_add_movement_start, pattern='^conv_add_income$'),
        CallbackQueryHandler(conv_add_movement_start, pattern='^conv_add_expense$'),
    ],
    states={
        CONCEPT: [MessageHandler(Filters.text & ~Filters.command, receive_concept)],
        AMOUNT: [MessageHandler(Filters.text & ~Filters.command, receive_amount)],
        CATEGORY: [
            MessageHandler(Filters.text & ~Filters.command, receive_category),
            CallbackQueryHandler(skip_category, pattern='^skip_category$')
        ],
        CONFIRMATION: [
            CallbackQueryHandler(save_movement, pattern='^save_movement$'),
            CallbackQueryHandler(cancel_add_movement, pattern='^cancel_add_movement$')
            # TODO: Add handlers for editing individual fields if implemented
        ],
    },
    fallbacks=[
        CommandHandler('start', start_command),
        CommandHandler('menu', start_command),
        CallbackQueryHandler(cancel_add_movement, pattern='^cancel_add_movement$'), # More specific cancel for this convo
        CallbackQueryHandler(start_command, pattern='^show_main_menu_from_save$'), # Button on save success
    ],
    map_to_parent={ # Allows nesting if this handler is part of a larger conversation
        MENU_PRINCIPAL: ConversationHandler.END
    }
)

# --- Handlers List ---
# This list will be imported by bot/main.py
finance_handlers = [
    CommandHandler('start', start_command),
    CommandHandler('menu', start_command), # Alias for start

    add_movement_conv_handler, # Handles add_income and add_expense button callbacks and subsequent messages

    CallbackQueryHandler(view_balance_command, pattern='^view_balance$'),
    # These ensure that after balance view, clicking "Volver al Menú" works
    CallbackQueryHandler(start_command, pattern='^show_main_menu_from_balance$'),
    CallbackQueryHandler(start_command, pattern='^show_main_menu_from_balance_error$'),

    # Placeholder/Unimplemented features
    CallbackQueryHandler(unimplemented_feature, pattern='^view_history$'), # TODO: Implement history view
    CallbackQueryHandler(unimplemented_feature, pattern='^ai_assistant$'), # TODO: Implement AI assistant

    # Export command (can be part of view_history later)
    CommandHandler('export', export_finances_command), # Keep direct command for now
    # If you want export via button (e.g. under view_history):
    # CallbackQueryHandler(export_finances_command, pattern='^export_data$'),

    CallbackQueryHandler(cancel_operation_button, pattern='^cancel_op_button$'), # General cancel from main menu
]

# Note: The original add_income, add_expense, balance functions that took context.args
# are now superseded by the conversation handler and button-driven flows.
# If direct command versions like "/add_income 50 Salary" are still needed,
# they would require separate CommandHandlers and different function names to avoid collision.
# For this project, focusing on the button/conversation flow is primary.

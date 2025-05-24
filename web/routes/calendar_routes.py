"""
Web routes for Google Calendar interactions.
Provides a page for viewing upcoming calendar events and adding new ones.
Utilizes async route handling for non-blocking calls to the Google Calendar service.
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from services.google_calendar_service import list_upcoming_events, add_event as add_gcal_event # Renamed to avoid conflict
import asyncio # For running async service functions
from datetime import datetime, timedelta # For form processing

calendar_bp = Blueprint('calendar_bp', __name__, template_folder='../templates/calendar')

@calendar_bp.route('/calendar', methods=['GET', 'POST'])
async def calendar_page():
    """
    Handles GET requests to display upcoming calendar events and a form to add new events.
    Handles POST requests to add a new event to the Google Calendar.
    This route is asynchronous to allow `await` for service calls.
    """
    error_message = None
    event_list_str = None
    
    # Handle POST request for adding new event
    if request.method == 'POST':
        summary = request.form.get('summary')
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        duration_str = request.form.get('duration') # Duration in minutes

        if not all([summary, date_str, time_str, duration_str]):
            flash("All event fields (summary, date, time, duration) are required.", "warning")
        else:
            try:
                start_datetime_str = f"{date_str}T{time_str}:00"
                start_datetime_obj = datetime.fromisoformat(start_datetime_str)
                duration_minutes = int(duration_str)
                end_datetime_obj = start_datetime_obj + timedelta(minutes=duration_minutes)
                
                # Assuming UTC for simplicity, align with google_calendar_service
                # The service expects ISO format strings
                add_result = await add_gcal_event(
                    summary, 
                    start_datetime_obj.isoformat(), 
                    end_datetime_obj.isoformat(),
                    description=f"Event added via Web UI: {summary}"
                )
                
                if "Error" in add_result:
                    flash(f"Failed to add event: {add_result}", "danger")
                else:
                    flash(f"Event '{summary}' added successfully!", "success")
                return redirect(url_for('calendar_bp.calendar_page')) # Redirect to refresh and clear form

            except ValueError:
                flash("Invalid date, time, or duration format.", "danger")
            except Exception as e:
                flash(f"An unexpected error occurred while adding event: {str(e)}", "danger")
                # TODO: Log e with current_app.logger.error for server-side details

    # GET request: List upcoming events
    try:
        # list_upcoming_events is an async function
        event_list_str = await list_upcoming_events(max_results=10)
        if "Error" in event_list_str: # Check if the service returned an error message
            error_message = event_list_str
            event_list_str = None # Don't display the error as if it's event content
    except Exception as e:
        error_message = f"Failed to load calendar events: {str(e)}"
        # TODO: Log e with current_app.logger.error for server-side details

    return render_template("calendar.html", events_data=event_list_str, error_message=error_message)

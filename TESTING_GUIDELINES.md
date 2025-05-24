# Manual Testing Guidelines

This document provides a checklist for manually testing the core functionalities of the Multifunctional Telegram Bot and Web Frontend.

**Prerequisites:**
*   The application is installed and configured as per `README.md`.
*   The application is running (`python run.py`).
*   You have access to the Telegram bot and the web frontend.
*   For features involving external services (Firebase, Google Calendar, Gemini), ensure they are correctly set up and accessible.

## I. Telegram Bot Testing

### 1. General Commands
    - [ ] **`/start`**: Send the command. Verify a welcome message is received.
    - [ ] **`/help`**: Send the command. Verify a detailed help message with all commands is received.

### 2. Financial Management
    - [ ] **`/add_income 100 Salary`**: Send command. Verify success message.
    - [ ] **`/add_expense 20 Coffee`**: Send command. Verify success message.
    - [ ] **`/add_income 50 Bonus`**: Send command.
    - [ ] **`/add_expense 10 Lunch`**: Send command.
    - [ ] **`/balance`**: Send command. Verify the balance is calculated correctly (e.g., 100 - 20 + 50 - 10 = 120).
    - [ ] **`/export_finances`**: Send command.
        - [ ] Verify an Excel file is received.
        - [ ] Open the Excel file. Verify it contains the income and expense entries correctly.
    - [ ] **Invalid Input**:
        - [ ] `/add_income ABC` (invalid amount): Verify error message.
        - [ ] `/add_expense` (missing args): Verify usage message.

### 3. Personal Diary
    - [ ] **`/add_entry Today was a good day.`**: Send command. Verify success message.
    - [ ] **`/add_entry Learned about Python asyncio.`**: Send command.
    - [ ] **`/view_entries`**: Send command. Verify the last few entries are displayed, newest first.
    - [ ] **`/view_entries good`**: Send command (keyword search). Verify entries containing "good" are displayed.
    - [ ] **`/view_entries all`**: Send command. Verify all entries are displayed (or a larger number than default).
    - [ ] **Invalid Input**:
        - [ ] `/add_entry` (missing text): Verify usage message.

### 4. Google Calendar Integration
    - (Requires Google Calendar API to be correctly configured and accessible by the bot)
    - [ ] **`/events`**: Send command.
        - [ ] Verify upcoming events are listed (if any).
        - [ ] Verify "No upcoming events found" if none.
    - [ ] **`/events 3`**: Send command. Verify it attempts to list up to 3 events.
    - [ ] **`/newevent 2024-12-25 10:00 60 Christmas Brunch`**: (Use a future date/time)
        - [ ] Verify success message and event creation link/details.
        - [ ] Check your Google Calendar to confirm the event was added.
    - [ ] **Invalid Input**:
        - [ ] `/newevent 2024-12-25 10:00 Brunch` (missing duration): Verify usage message.
        - [ ] `/newevent tomorrow 10am 60 Test` (invalid date/time format): Verify error message.

### 5. AI Assistant (Gemini)
    - (Requires Gemini API Key to be configured)
    - [ ] **`/chat Hello, how are you?`**: Send command. Verify a response is received from the AI.
    - [ ] **`/chat What is the capital of France?`**: Send command. Verify a factual response.
    - [ ] **Invalid Input**:
        - [ ] `/chat` (missing message): Verify usage message.

## II. Web Frontend Testing (Default: `http://127.0.0.1:5001`)

### 1. General Navigation
    - [ ] Open the web frontend in a browser.
    - [ ] **Navbar Links**: Click on "Finances", "Diary", "Calendar", "AI Assistant". Verify each page loads.
    - [ ] **Dark Theme**: Verify all pages display with a consistent dark theme.
    - [ ] **Responsiveness**: Resize the browser window to a smaller width. Verify the layout adjusts and remains usable.
    - [ ] **Favicon**: Check if the browser tab displays a favicon (even if it's a placeholder).

### 2. Finances Page (`/user/finances`)
    - (Assumes DEMO_USER_ID has some data, or test with an ID that has data from bot testing)
    - [ ] **View Data**: Verify income, expenses, and balance are displayed and match data entered via the bot (if using the same user ID).
    - [ ] **Export to Excel**: Click the "Export to Excel" button.
        - [ ] Verify an Excel file is downloaded.
        - [ ] Open the file and check its contents.

### 3. Diary Page (`/user/diary`)
    - (Assumes DEMO_USER_ID has some data)
    - [ ] **View Entries**: Verify diary entries are displayed with timestamps.

### 4. Calendar Page (`/user/calendar`)
    - (Requires Google Calendar service to be working)
    - [ ] **View Events**: Verify upcoming events are listed.
    - [ ] **Add Event Form**:
        - [ ] Fill in the form with valid event details (Summary, Date, Time, Duration).
        - [ ] Click "Add Event".
        - [ ] Verify success flash message.
        - [ ] Verify the event list refreshes/shows the new event (or check Google Calendar directly).
    - [ ] **Invalid Form Input**:
        - [ ] Submit form with missing fields: Verify error/warning message.
        - [ ] Submit form with invalid date/time: Verify error message.

### 5. AI Assistant Page (`/user/ai_assistant`)
    - (Requires Gemini API Key to be configured, either via .env or session override)
    - [ ] **Chat Interface**:
        - [ ] Type a message (e.g., "Hello AI") and submit. Verify AI response is displayed.
        - [ ] Check that chat history is maintained on the page.
    - [ ] **Clear Chat History**: Click button. Verify chat history clears.
    - [ ] **Session AI Configuration**:
        - [ ] Enter a (valid or test) API key, Base URL, Model in the form.
        - [ ] Click "Update Session Config". Verify success flash message.
        - [ ] Test chat again. If a valid key was entered, it should use it. (This is harder to verify directly without knowing if the key is different but valid).
        - [ ] If API key is cleared in session config, verify subsequent chat attempts show an error about missing API key (unless a global one is still set in .env).

## III. General Application Testing
    - [ ] **`run.py` Execution**:
        - [ ] Start the application using `python run.py`. Verify both bot and Flask server start without immediate errors in the console.
    - [ ] **Error Handling**:
        - [ ] Try to trigger known error conditions (e.g., misconfigure an API key temporarily in `.env` and restart, then try to use the feature). Verify user-friendly error messages are shown instead of application crashes.
        - [ ] Check console logs for any unexpected errors during operation.
    - [ ] **`.env` Configuration**:
        - [ ] Test running the app with minimal `.env` (only essential keys).
        - [ ] Test with optional keys (e.g., `GEMINI_BASE_URL`) set.

This list is not exhaustive but covers the main functionalities. Report any bugs or unexpected behavior.

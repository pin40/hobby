"""
Firebase Service module for initializing and providing access to Firestore.

This service handles the initialization of the Firebase Admin SDK using credentials
specified in the application settings. It provides a global Firestore client instance.
"""
import firebase_admin
from firebase_admin import credentials, firestore
import os
from config import settings # Assuming settings.py is in the config directory
# TODO: Consider logging critical errors from this module to a file or a more robust system.

db = None

def initialize_firebase():
    """
    Initializes the Firebase Admin SDK using credentials from settings.
    Sets the global `db` variable to the Firestore client instance.
    This function is designed to be called once on application startup.
    It checks if Firebase has already been initialized to prevent errors.
    """
    global db
    if firebase_admin._apps: # Check if Firebase is already initialized
        print("Firebase Admin SDK already initialized.")
        if db is None: # If db somehow not set, try to get client from default app
            db = firestore.client()
        return

    if not settings.FIREBASE_CREDENTIALS_PATH:
        print("Error: FIREBASE_CREDENTIALS_PATH is not set in the environment/config.")
        print("Firebase Admin SDK could not be initialized.")
        return

    # Expand the path if it uses ~ for home directory
    cred_path = os.path.expanduser(settings.FIREBASE_CREDENTIALS_PATH)

    if not os.path.exists(cred_path):
        print(f"Error: Firebase credentials file not found at {cred_path}")
        print("Firebase Admin SDK could not be initialized.")
        return

    try:
        # No need for the inner check of firebase_admin._apps here,
        # as the outer check already handles it.
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK initialized successfully.")
        db = firestore.client()
    except Exception as e:
        print(f"Error initializing Firebase Admin SDK: {e}")
        db = None

def get_firestore_client():
    """
    Returns the global Firestore client instance.
    If the client is not already initialized, it attempts to initialize Firebase first.
    """
    global db
    if db is None:
        print("Attempting to initialize Firebase as Firestore client is None...")
        initialize_firebase() 
    
    if db is None: # Check again after attempting initialization
        print("Error: Firestore client is not available. Initialization might have failed.")
    return db

# Automatically initialize Firebase when this module is loaded
# This is a common pattern, but consider if explicit initialization is better for your app structure
if db is None: # Ensure it only runs once on import
    initialize_firebase()

if __name__ == '__main__':
    # Example usage:
    print("Attempting to get Firestore client...")
    client = get_firestore_client()
    if client:
        print("Successfully got Firestore client.")
        # Example: List collections (requires Firestore database to be set up)
        try:
            collections = client.collections()
            print("Available collections:")
            for coll in collections:
                print(f"- {coll.id}")
        except Exception as e:
            print(f"Could not list collections (this is okay if DB is empty or not fully set up): {e}")
    else:
        print("Failed to get Firestore client.")

import sys
import time

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

try:
    log("Starting diagnostic...")
    
    log("Importing os, sys, time...")
    import os
    
    log("Importing numpy...")
    import numpy as np
    log("Numpy imported successfully.")
    
    log("Importing spacy...")
    import spacy
    log("Spacy imported successfully (lib only).")
    
    log("Testing spacy.load('en_core_web_sm') - THIS MIGHT HANG...")
    # We do a quick check to see if THIS is the hang
    try:
        # We don't actually load it here to avoid the hang, 
        # but we check if the path exists
        import spacy.util
        if spacy.util.is_package("en_core_web_sm"):
            log("en_core_web_sm model found.")
        else:
            log("en_core_web_sm model NOT found.")
    except Exception as e:
        log(f"Spacy util error: {e}")

    log("Importing Django settings...")
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    import django
    django.setup()
    log("Django setup successful.")

    log("Importing music.models...")
    from music.models import Song, UserProfile
    log("Models imported successful.")

    log("Checking Database connection...")
    from django.db import connection
    connection.ensure_connection()
    log("Database connection successful.")

    log("DIAGNOSTIC COMPLETE: No basic hangs detected at the import level.")

except Exception as e:
    log(f"DIAGNOSTIC FAILED with error: {e}")
except BaseException as e:
    log(f"DIAGNOSTIC CRASHED (likely Memory/System error): {type(e)}")

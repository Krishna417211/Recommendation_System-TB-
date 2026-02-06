import os
import sys
import traceback

# Add current dir to path just in case
sys.path.insert(0, os.path.abspath('.'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_recommender.settings')

print(f"Python executable: {sys.executable}")
print(f"Current working directory: {os.getcwd()}")
print(f"Path: {sys.path}")

try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    print("WSGI Loaded Successfully!")
except Exception:
    print("Failed to load WSGI:")
    traceback.print_exc()

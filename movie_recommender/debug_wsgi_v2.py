import os
import sys
import traceback

# Add current dir to path just in case
sys.path.insert(0, os.path.abspath('.'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_recommender.settings')

try:
    import django
    django.setup()
    
    print("Django setup complete.")
    
    from django.core.servers.basehttp import get_internal_wsgi_application
    print("Attempting to load internal WSGI application...")
    app = get_internal_wsgi_application()
    print("WSGI App Loaded Successfully via basehttp!")
except Exception:
    print("Failed to load:")
    traceback.print_exc()

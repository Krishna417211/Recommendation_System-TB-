from django.conf import settings

def tmdb_settings(request):
    return {
        'tmdb_api_key': getattr(settings, 'TMDB_API_KEY', '')
    }

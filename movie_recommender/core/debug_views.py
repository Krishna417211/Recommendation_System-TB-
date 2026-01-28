from django.http import HttpResponse
from .models import Movie

def debug_view(request):
    m = Movie.objects.first()
    return HttpResponse(f"<h1>Raw Python: {m.title}</h1>")

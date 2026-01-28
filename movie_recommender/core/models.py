from django.db import models

class Movie(models.Model):
    title = models.CharField(max_length=255)
    overview = models.TextField(blank=True, null=True)
    poster_path = models.CharField(max_length=255, blank=True, null=True)
    
    # Storing structured data like genres as JSON (SQLite supports JSON fields in newer Django/SQLite versions, 
    # but TextField is safer for universal compatibility if we swap DBs easily)
    genres = models.TextField(blank=True, null=True)  # Will store "[Action, Adventure]" string
    keywords = models.TextField(blank=True, null=True)
    
    tmdb_id = models.IntegerField(unique=True)
    popularity = models.FloatField(default=0.0)
    vote_average = models.FloatField(default=0.0)
    vote_count = models.IntegerField(default=0)
    
    release_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.title

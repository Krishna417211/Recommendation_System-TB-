from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search, name='search'),
    path('movie/<int:movie_id>/', views.movie_detail, name='movie_detail'),
]

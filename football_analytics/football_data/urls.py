from django.urls import path
from . import views

urlpatterns = [
    path('', views.league_data_view, name='football_data'),
    path('match-details/<str:team_name>/<str:league>/<int:season>/', views.match_details, name='match_details'),
    path('upcoming-games/', views.upcoming_games, name='upcoming_games'),
]

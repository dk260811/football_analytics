from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('league-data/', views.league_data_view, name='football_data'),
    path('match-details/<str:team_name>/<str:league>/<int:season>/', views.match_details, name='match_details'),
    path('upcoming-games/', views.upcoming_games, name='upcoming_games'),
    path('visualisation/', views.visualisation_view, name='visualisation'),
    path('visualisation/data/', views.visualisation_data, name='visualisation_data'),
    path('league-visualisation/', views.league_visualisation_view, name='league_visualisation'),
    path('league-visualisation/data/', views.league_visualisation_data, name='league_visualisation_data'),
    path('get_seasons_for_league/', views.get_seasons_for_league, name='get_seasons_for_league'),
    path('correlations/', views.correlations_view, name='correlations'),
]

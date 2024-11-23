from django.shortcuts import render
from django.db import connection
import requests

def league_data_view(request):
    # Fetch leagues and seasons for the filters
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT name FROM possible_leagues_and_seasons ORDER BY name
        """)
        leagues = [row[0] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT DISTINCT season_year FROM possible_leagues_and_seasons ORDER BY season_year
        """)
        seasons = [row[0] for row in cursor.fetchall()]

    selected_league = request.GET.get('league')
    selected_season = request.GET.get('season')
    league_data = []
    columns = []

    if selected_league and selected_season:
        # Fetch the season_id for the selected league and season
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT season_id
                FROM possible_leagues_and_seasons
                WHERE name = %s AND season_year = %s
            """, [selected_league, selected_season])
            result = cursor.fetchone()
            if result:
                season_id = result[0]
                table_name = f"match_data_{season_id}_final"

                # Fetch data for the selected table with SUM and AVG calculations
                cursor.execute(f""" 
                    SELECT 
                        team_name,
                        count(points) AS games_played,
                        SUM(points) AS total_points,
                        ROUND(CAST(AVG(goals_scored) AS NUMERIC), 2) AS avg_goals_scored,
                        ROUND(CAST(AVG(goals_conceded) AS NUMERIC), 2) AS avg_goals_conceded,
                        ROUND(CAST(AVG(corners_for) AS NUMERIC), 2) AS avg_corners_for,
                        ROUND(CAST(AVG(corners_against) AS NUMERIC), 2) AS avg_corners_against,
                        ROUND(CAST(AVG(offsides_for) AS NUMERIC), 2) AS avg_offsides_for,
                        ROUND(CAST(AVG(offsides_against) AS NUMERIC), 2) AS avg_offsides_against,
                        ROUND(CAST(AVG(yellow_cards_for) AS NUMERIC), 2) AS avg_yellow_cards_for,
                        ROUND(CAST(AVG(yellow_cards_against) AS NUMERIC), 2) AS avg_yellow_cards_against,
                        ROUND(CAST(AVG(red_cards_for) AS NUMERIC), 2) AS avg_red_cards_for,
                        ROUND(CAST(AVG(red_cards_against) AS NUMERIC), 2) AS avg_red_cards_against,
                        ROUND(CAST(AVG(shotsontarget_for) AS NUMERIC), 2) AS avg_shotsontarget_for,
                        ROUND(CAST(AVG(shotsontarget_against) AS NUMERIC), 2) AS avg_shotsontarget_against,
                        ROUND(CAST(AVG(shotsofftarget_for) AS NUMERIC), 2) AS avg_shotsofftarget_for,
                        ROUND(CAST(AVG(shotsofftarget_against) AS NUMERIC), 2) AS avg_shotsofftarget_against,
                        ROUND(CAST(AVG(shots_for) AS NUMERIC), 2) AS avg_shots_for,
                        ROUND(CAST(AVG(shots_against) AS NUMERIC), 2) AS avg_shots_against,
                        ROUND(CAST(AVG(fouls_for) AS NUMERIC), 2) AS avg_fouls_for,
                        ROUND(CAST(AVG(fouls_against) AS NUMERIC), 2) AS avg_fouls_against,
                        ROUND(CAST(AVG(possession_for) AS NUMERIC), 2) AS avg_possession_for,
                        ROUND(CAST(AVG(possession_against) AS NUMERIC), 2) AS avg_possession_against
                    FROM {table_name}
                    GROUP BY team_name
                    ORDER BY total_points DESC;

                """)
                league_data = cursor.fetchall()
                columns = [col[0] for col in cursor.description]

    context = {
        'league_data': league_data,
        'columns': columns,
        'leagues': leagues,
        'seasons': seasons,
        'selected_league': selected_league,
        'selected_season': selected_season,
    }
    return render(request, 'football_data/league_data.html', context)


def match_details(request, team_name, league, season):
    # Fetch the season_id for the given league and season year
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT season_id
            FROM possible_leagues_and_seasons
            WHERE name = %s AND season_year = %s
        """, [league, season])
        result = cursor.fetchone()
        
        if not result:
            # Handle case where no season_id is found
            return render(request, 'football_data/match_details.html', {
                'error_message': "Season ID not found for the selected league and season.",
            })

        season_id = result[0]
        table_name = f"match_data_{season_id}_final"  # Use the correct season_id to construct the table name

        # Fetch specific columns for the selected team
        query = f"""
            SELECT 
                team_name,
                opponent_name,
                homeoraway,
                season,
                game_week,
                goals_scored,
                goals_conceded,
                corners_for,
                corners_against,
                offsides_for,
                offsides_against,
                yellow_cards_for,
                yellow_cards_against,
                red_cards_for,
                red_cards_against,
                shotsontarget_for,
                shotsontarget_against,
                shotsofftarget_for,
                shotsofftarget_against,
                shots_for,
                shots_against,
                fouls_for,
                fouls_against,
                possession_for,
                possession_against,
                stadium_name
            FROM {table_name}
            WHERE team_name = %s
            ORDER BY game_week
        """
        cursor.execute(query, [team_name])  # Only parameterize values, not table names
        match_data = cursor.fetchall()
        columns = [col[0] for col in cursor.description]  # Extract column names

    context = {
        'team_name': team_name,
        'league': league,
        'season': season,
        'match_data': match_data,
        'columns': columns,
    }
    return render(request, 'football_data/match_details.html', context)

"""
def upcoming_games(request):
    games = []
    error_message = None

    if request.method == "POST":
        # Get startdate and enddate from the form
        startdate = request.POST.get("startdate")
        enddate = request.POST.get("enddate")

        # Your API key (replace with your actual key)
        api_key = "928d7e45d921850a05f77b1f6e3fb7b137bd6184c447a44c9d9f6f0cab380ff9"

        # API endpoint
        url = f"https://api.football-data-api.com/todays-matches?key={api_key}&date={startdate}"

        try:
            # Fetch games for the start date
            response = requests.get(url)
            data = response.json()

            if data.get("success"):
                games = [
                    {
                        "id": game["id"],
                        "homeID": game["homeID"],
                        "awayID": game["awayID"],
                        "season": game["season"],
                        "status": game["status"],
                        "roundID": game["roundID"],
                        "game_week": game["game_week"],
                        "competition_id": game["competition_id"],
                    }
                    for game in data["data"]
                ]
            else:
                error_message = "Could not fetch games. Please check your API key or input data."
        except Exception as e:
            error_message = f"An error occurred: {e}"

    return render(
        request,
        "football_data/upcoming_games.html",
        {"games": games, "error_message": error_message},
    )
"""


import requests
from django.db import connection
from django.shortcuts import render

def upcoming_games(request):
    games = []
    error_message = None

    if request.method == "POST":
        # Get startdate and enddate from the form
        startdate = request.POST.get("startdate")
        enddate = request.POST.get("enddate")

        # Your API key (replace with your actual key)
        api_key = "__________"

        # API endpoint
        url = f"https://api.football-data-api.com/todays-matches?key={api_key}&date={startdate}"

        try:
            # Fetch games for the start date
            response = requests.get(url)
            data = response.json()

            if data.get("success"):
                for game in data["data"]:
                    competition_id = game["competition_id"]
                    #table_name = f"match_data_{competition_id}_final"
                    table_name = "match_data_12325_final"
                    #home_id = game["homeID"]
                    home_id = 152
                    away_id = game["awayID"]

                    # Default values for averages and team names
                    home_corners_avg = "NA"
                    away_corners_avg = "NA"
                    home_team_name = "NA"
                    away_team_name = "NA"

                    try:
                        with connection.cursor() as cursor:
                            # Get Home Team Name
                            cursor.execute("""
                                SELECT team_name
                                FROM {table_name}
                                WHERE team_id = %s
                            """, [home_id])
                            home_team_result = cursor.fetchone()
                            home_team_name = home_team_result[0] if home_team_result else "NA"

                            # Get Away Team Name
                            cursor.execute("""
                                SELECT team_name
                                FROM {table_name}
                                WHERE team_id = %s
                            """, [away_id])
                            away_team_result = cursor.fetchone()
                            away_team_name = away_team_result[0] if away_team_result else "NA"

                            # Get Home Corners Average
                            cursor.execute("""
                                SELECT AVG(corners_for)
                                FROM {table_name}
                                WHERE team_id = %s
                            """, [home_id])
                            home_corners_result = cursor.fetchone()
                            home_corners_avg = round(home_corners_result[0], 2) if home_corners_result and home_corners_result[0] is not None else "NA"

                            # Get Away Corners Average
                            cursor.execute("""
                                SELECT AVG(corners_for)
                                FROM {table_name}
                                WHERE team_id = %s
                            """, [away_id])
                            away_corners_result = cursor.fetchone()
                            away_corners_avg = round(away_corners_result[0], 2) if away_corners_result and away_corners_result[0] is not None else "NA"
                    except Exception as e:
                        # Log or handle database-related errors as needed
                        pass

                    # Add the game data to the games list
                    games.append({
                        "id": game["id"],
                        "homeID": game["homeID"],
                        "awayID": game["awayID"],
                        "home_team_name": home_team_name,
                        "away_team_name": away_team_name,
                        "season": game["season"],
                        "status": game["status"],
                        "roundID": game["roundID"],
                        "game_week": game["game_week"],
                        "competition_id": game["competition_id"],
                        "home_corners_avg": home_corners_avg,
                        "away_corners_avg": away_corners_avg,
                    })
            else:
                error_message = "Could not fetch games. Please check your API key or input data."
        except Exception as e:
            error_message = f"An error occurred: {e}"

    return render(
        request,
        "football_data/upcoming_games.html",
        {"games": games, "error_message": error_message},
    )

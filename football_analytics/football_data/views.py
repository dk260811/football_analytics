from django.shortcuts import render
from django.db import connection
import requests
from datetime import datetime, timedelta


def league_data_view(request):

    

    # Fetch leagues and seasons for the filters
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT name FROM "possible_leagues_and_seasons_NEW" WHERE data_available like 'yes' ORDER BY name
        """)
        leagues = [row[0] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT DISTINCT season_year FROM "possible_leagues_and_seasons_NEW" WHERE data_available like 'yes' ORDER BY season_year
        """)
        seasons = [row[0] for row in cursor.fetchall()]

    selected_league = request.GET.get('league')
    selected_season = request.GET.get('season')
    selected_home_or_away = request.GET.get('home_or_away')
    league_data = []
    columns = []

    if selected_season and '/' in selected_season:
        selected_season = selected_season.replace('/', '')


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

                # Build the query
                query = f"""
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
                """

                # Add WHERE clause for home_or_away if selected
                if selected_home_or_away:
                    query += " WHERE homeoraway = %s"
                    params = [selected_home_or_away]
                else:
                    params = []

                # Complete the query
                query += " GROUP BY team_name ORDER BY total_points DESC;"

                # Execute the query
                cursor.execute(query, params)
                league_data = cursor.fetchall()
                columns = [col[0] for col in cursor.description]

    context = {
        'league_data': league_data,
        'columns': columns,
        'leagues': leagues,
        'seasons': seasons,
        'selected_league': selected_league,
        'selected_season': selected_season,
        'selected_home_or_away': selected_home_or_away,
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



def upcoming_games(request):
    games = []
    error_message = None

    if request.method == "POST":
        # Get startdate and enddate from the form
        startdate = request.POST.get("startdate")
        enddate = request.POST.get("enddate")

        # Convert startdate and enddate to datetime objects
        try:
            start_date = datetime.strptime(startdate, "%Y-%m-%d")
            end_date = datetime.strptime(enddate, "%Y-%m-%d")
        except ValueError:
            error_message = "Invalid date format. Please enter dates in YYYY-MM-DD format."
            return render(request, "football_data/upcoming_games.html", {"games": games, "error_message": error_message})

        # API Key and Base URL
        api_key = "928d7e45d921850a05f77b1f6e3fb7b137bd6184c447a44c9d9f6f0cab380ff9"
        base_url = "https://api.football-data-api.com/todays-matches"

        # Generate the date range
        date_range = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

        # Store all fetched games temporarily
        games_data = []

        try:
            # Fetch matches for all dates
            for date in date_range:
                params = {
                    "key": api_key,
                    "date": date.strftime('%Y-%m-%d'),
                }
                response = requests.get(base_url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        for game in data["data"]:
                            game["date"] = date.strftime('%Y-%m-%d')  # Add the date to the game
                            games_data.append(game)
                else:
                    print(f"API error for {date.strftime('%Y-%m-%d')}: {response.status_code}")
        except Exception as e:
            error_message = f"Error fetching data from API: {e}"
            return render(request, "football_data/upcoming_games.html", {"games": games, "error_message": error_message})

        # Extract unique competition IDs and team IDs
        competition_ids = {game["competition_id"] for game in games_data}
        team_ids = {game["homeID"] for game in games_data}.union({game["awayID"] for game in games_data})

        # Bulk query for league names and team metrics
        league_names = {}
        team_metrics_by_competition = {}
        team_names_by_competition = {}

        try:
            with connection.cursor() as cursor:
                # Fetch league names
                cursor.execute("""
                    SELECT season_id, name
                    FROM possible_leagues_and_seasons
                    WHERE season_id IN %s
                """, [tuple(competition_ids)])
                league_names = dict(cursor.fetchall())

                # Fetch team names and metrics, isolating by competition
                for competition_id in competition_ids:
                    # Team Names
                    cursor.execute(f"""
                        SELECT teamid, team_name
                        FROM match_data_{competition_id}_final
                        WHERE teamid IN %s
                    """, [tuple(team_ids)])
                    team_names_by_competition[competition_id] = {row[0]: row[1] for row in cursor.fetchall()}

                    # Team Metrics
                    cursor.execute(f"""
                        SELECT teamid, 
                               AVG(corners_for) AS corners_avg, 
                               AVG(shots_for) AS shots_avg, 
                               AVG(shotsontarget_for) AS shots_on_target_avg,
                               AVG(yellow_cards_for) AS yellow_cards_avg
                        FROM match_data_{competition_id}_final
                        WHERE teamid IN %s
                        GROUP BY teamid
                    """, [tuple(team_ids)])
                    team_metrics_by_competition[competition_id] = {row[0]: row[1:] for row in cursor.fetchall()}
        except Exception as e:
            error_message = f"Database error: {e}"
            return render(request, "football_data/upcoming_games.html", {"games": games, "error_message": error_message})

        # Process games data
        for game in games_data:
            competition_id = game["competition_id"]
            home_id = game["homeID"]
            away_id = game["awayID"]

            # Get league name
            league_name = league_names.get(competition_id, "NA")

            # Get team names
            team_names = team_names_by_competition.get(competition_id, {})
            home_team_name = team_names.get(home_id, "NA")
            away_team_name = team_names.get(away_id, "NA")

            # Get metrics
            team_metrics = team_metrics_by_competition.get(competition_id, {})
            home_metrics = team_metrics.get(home_id, ("NA", "NA", "NA", "NA"))
            away_metrics = team_metrics.get(away_id, ("NA", "NA", "NA", "NA"))

            # Calculate differences
            def calculate_difference(metric1, metric2):
                try:
                    return round(abs(float(metric1) - float(metric2)), 2)
                except (ValueError, TypeError):
                    return "NA"

            corners_diff = calculate_difference(home_metrics[0], away_metrics[0])
            shots_diff = calculate_difference(home_metrics[1], away_metrics[1])
            shots_on_target_diff = calculate_difference(home_metrics[2], away_metrics[2])
            yellow_cards_diff = calculate_difference(home_metrics[3], away_metrics[3])

            # Append game to the final list
            games.append({
                "date": game["date"],
                "season": game.get("season", "NA"),
                "status": game.get("status", "NA"),
                "roundID": game.get("roundID", "NA"),
                "game_week": game.get("game_week", "NA"),
                "league": league_name,
                "home_team_name": home_team_name,
                "away_team_name": away_team_name,
                "home_corners_avg": round(float(home_metrics[0]), 2) if home_metrics[0] != "NA" else "NA",
                "away_corners_avg": round(float(away_metrics[0]), 2) if away_metrics[0] != "NA" else "NA",
                "corners_diff": corners_diff,
                "home_shots": round(float(home_metrics[1]), 2) if home_metrics[1] != "NA" else "NA",
                "away_shots": round(float(away_metrics[1]), 2) if away_metrics[1] != "NA" else "NA",
                "shots_diff": shots_diff,
                "home_shots_on_target": round(float(home_metrics[2]), 2) if home_metrics[2] != "NA" else "NA",
                "away_shots_on_target": round(float(away_metrics[2]), 2) if away_metrics[2] != "NA" else "NA",
                "shots_on_target_diff": shots_on_target_diff,
                "home_yellow_cards": round(float(home_metrics[3]), 2) if home_metrics[3] != "NA" else "NA",
                "away_yellow_cards": round(float(away_metrics[3]), 2) if away_metrics[3] != "NA" else "NA",
                "yellow_cards_diff": yellow_cards_diff,
                "comp_id": competition_id
            })

    return render(request, "football_data/upcoming_games.html", {"games": games, "error_message": error_message})




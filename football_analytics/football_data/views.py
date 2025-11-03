from django.shortcuts import render
from django.db import connection
import requests
from datetime import datetime, timedelta
from django.http import JsonResponse
import statistics # For mean, median
import math     # For sqrt, floor, etc.
import json # Add this import at the top
from collections import Counter


# Define chart colors and helper functions if they are not imported from elsewhere
CHART_COLORS = [
    'rgb(54, 162, 235)',    # Blue
    'rgb(255, 99, 132)',    # Red
    'rgb(75, 192, 192)',    # Green
    'rgb(255, 205, 86)',    # Yellow
    'rgb(153, 102, 255)',   # Purple
    'rgb(255, 159, 64)'     # Orange
]
CHART_BG_COLORS_TRANSPARENT = [
    'rgba(54, 162, 235, 0.5)',
    'rgba(255, 99, 132, 0.5)',
    'rgba(75, 192, 192, 0.5)',
    'rgba(255, 205, 86, 0.5)',
    'rgba(153, 102, 255, 0.5)',
    'rgba(255, 159, 64, 0.5)'
]

def get_kpi_data_for_team(cursor, table_name, kpi_column, team_name):
    """
    Fetches KPI data for a specific team from a given table.
    Returns a list of tuples (game_week, kpi_value).
    """
    # Ensure kpi_column is a valid identifier to prevent SQL injection if it's not from a controlled list.
    # Here, we assume kpi_column is validated before this function is called (e.g., checked against a list of allowed KPIs).
    # The f-string for table_name is also an injection risk if season_id isn't strictly controlled.
    query = f"""
        SELECT game_week, "{kpi_column}"
        FROM "{table_name}"
        WHERE team_name = %s
        ORDER BY game_week
    """
    try:
        cursor.execute(query, [team_name])
        return cursor.fetchall()
    except Exception as e:
        print(f"Error in get_kpi_data_for_team for {team_name}, KPI {kpi_column} in {table_name}: {e}")
        # Depending on desired error handling, you might raise e or return None/[]
        return [] # Return empty list on error to allow main function to continue if possible

def calculate_descriptive_stats(data_values):
    """
    Calculates mean, median, and mode for a list of numeric data_values.
    Returns a dictionary with 'mean', 'median', and 'mode'.
    Handles empty or non-numeric lists gracefully.
    """
    numeric_values = [v for v in data_values if isinstance(v, (int, float)) and not math.isnan(v)]
    if not numeric_values:
        return {'mean': 'N/A', 'median': 'N/A', 'mode': 'N/A'}
    
    mean = round(statistics.mean(numeric_values), 2)
    median = round(statistics.median(numeric_values), 2)
    
    # Calculate mode
    value_counts = Counter(numeric_values)
    max_count = max(value_counts.values())
    modes = [value for value, count in value_counts.items() if count == max_count]
    
    if len(modes) == 1:
        mode = round(modes[0], 2)
    else:
        # If there are multiple modes, show them all
        mode = [round(m, 2) for m in sorted(modes)]
    
    return {'mean': mean, 'median': median, 'mode': mode}


def get_seasons_for_league(request):
    league_name = request.GET.get('league')
    if not league_name:
        return JsonResponse({'error': 'League parameter missing'}, status=400)
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT season_year 
                FROM "possible_leagues_and_seasons_NEW" 
                WHERE name = %s AND data_available like 'yes' 
                ORDER BY season_year
            """, [league_name])
            seasons = [row[0] for row in cursor.fetchall()]
        return JsonResponse({'seasons': seasons})
    except Exception as e:
        return JsonResponse({'error': 'Error fetching seasons from database.', 'details': str(e)}, status=500)


def league_data_view(request):
    # Fetch leagues for the filters
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT name FROM "possible_leagues_and_seasons_NEW" WHERE data_available like 'yes' ORDER BY name
        """
        )
        leagues = [row[0] for row in cursor.fetchall()]

    selected_league = request.GET.get('league')
    selected_season = request.GET.get('season') 
    selected_home_or_away = request.GET.get('home_or_away')
    view_type = request.GET.get('view_type', 'averages') # Default to averages
    
    seasons_for_selected_league = []
    if selected_league:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT season_year 
                FROM "possible_leagues_and_seasons_NEW" 
                WHERE name = %s AND data_available like 'yes' 
                ORDER BY season_year
            """, [selected_league])
            seasons_for_selected_league = [row[0] for row in cursor.fetchall()]

    league_data = []
    raw_columns = [] # Store raw column names from DB
    display_columns = [] # Store formatted names for display

    if selected_league and selected_season:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT season_id
                FROM "possible_leagues_and_seasons_NEW"
                WHERE name = %s AND season_year = %s
            """, [selected_league, selected_season]) 
            result = cursor.fetchone()
            if result:
                season_id = result[0]
                #print(season_id)
                table_name = f"match_data_{season_id}_final"
                #table_name = f"match_data_15050_final"

                # Determine aggregation functions based on view_type
                if view_type == 'totals':
                    agg_goals_scored = "SUM(goals_scored)"
                    agg_goals_conceded = "SUM(goals_conceded)"
                    agg_corners_for = "SUM(corners_for)"
                    agg_corners_against = "SUM(corners_against)"
                    agg_offsides_for = "SUM(offsides_for)"
                    agg_offsides_against = "SUM(offsides_against)"
                    agg_yellow_cards_for = "SUM(yellow_cards_for)"
                    agg_yellow_cards_against = "SUM(yellow_cards_against)"
                    agg_red_cards_for = "SUM(red_cards_for)"
                    agg_red_cards_against = "SUM(red_cards_against)"
                    agg_shotsontarget_for = "SUM(shotsontarget_for)"
                    agg_shotsontarget_against = "SUM(shotsontarget_against)"
                    agg_shotsofftarget_for = "SUM(shotsofftarget_for)"
                    agg_shotsofftarget_against = "SUM(shotsofftarget_against)"
                    agg_shots_for = "SUM(shots_for)"
                    agg_shots_against = "SUM(shots_against)"
                    agg_fouls_for = "SUM(fouls_for)"
                    agg_fouls_against = "SUM(fouls_against)"
                    # Possession is an average, so keep it as AVG or handle differently if totals view means something else for possession
                    agg_possession_for = "ROUND(CAST(AVG(possession_for) AS NUMERIC), 2)" 
                    agg_possession_against = "ROUND(CAST(AVG(possession_against) AS NUMERIC), 2)"
                    # Column aliases might need to change too, e.g., total_goals_scored
                    # For now, keeping original aliases for simplicity, but values will be totals.
                else: # averages (default)
                    agg_goals_scored = "ROUND(CAST(AVG(goals_scored) AS NUMERIC), 2)"
                    agg_goals_conceded = "ROUND(CAST(AVG(goals_conceded) AS NUMERIC), 2)"
                    agg_corners_for = "ROUND(CAST(AVG(corners_for) AS NUMERIC), 2)"
                    agg_corners_against = "ROUND(CAST(AVG(corners_against) AS NUMERIC), 2)"
                    agg_offsides_for = "ROUND(CAST(AVG(offsides_for) AS NUMERIC), 2)"
                    agg_offsides_against = "ROUND(CAST(AVG(offsides_against) AS NUMERIC), 2)"
                    agg_yellow_cards_for = "ROUND(CAST(AVG(yellow_cards_for) AS NUMERIC), 2)"
                    agg_yellow_cards_against = "ROUND(CAST(AVG(yellow_cards_against) AS NUMERIC), 2)"
                    agg_red_cards_for = "ROUND(CAST(AVG(red_cards_for) AS NUMERIC), 2)"
                    agg_red_cards_against = "ROUND(CAST(AVG(red_cards_against) AS NUMERIC), 2)"
                    agg_shotsontarget_for = "ROUND(CAST(AVG(shotsontarget_for) AS NUMERIC), 2)"
                    agg_shotsontarget_against = "ROUND(CAST(AVG(shotsontarget_against) AS NUMERIC), 2)"
                    agg_shotsofftarget_for = "ROUND(CAST(AVG(shotsofftarget_for) AS NUMERIC), 2)"
                    agg_shotsofftarget_against = "ROUND(CAST(AVG(shotsofftarget_against) AS NUMERIC), 2)"
                    agg_shots_for = "ROUND(CAST(AVG(shots_for) AS NUMERIC), 2)"
                    agg_shots_against = "ROUND(CAST(AVG(shots_against) AS NUMERIC), 2)"
                    agg_fouls_for = "ROUND(CAST(AVG(fouls_for) AS NUMERIC), 2)"
                    agg_fouls_against = "ROUND(CAST(AVG(fouls_against) AS NUMERIC), 2)"
                    agg_possession_for = "ROUND(CAST(AVG(possession_for) AS NUMERIC), 2)"
                    agg_possession_against = "ROUND(CAST(AVG(possession_against) AS NUMERIC), 2)"

                query = f"""
                    SELECT 
                        team_name,
                        count(points) AS games_played,
                        SUM(points) AS total_points,
                        {agg_goals_scored} AS avg_goals_scored,
                        {agg_goals_conceded} AS avg_goals_conceded,
                        {agg_corners_for} AS avg_corners_for,
                        {agg_corners_against} AS avg_corners_against,
                        {agg_offsides_for} AS avg_offsides_for,
                        {agg_offsides_against} AS avg_offsides_against,
                        {agg_yellow_cards_for} AS avg_yellow_cards_for,
                        {agg_yellow_cards_against} AS avg_yellow_cards_against,
                        {agg_red_cards_for} AS avg_red_cards_for,
                        {agg_red_cards_against} AS avg_red_cards_against,
                        {agg_shotsontarget_for} AS avg_shotsontarget_for,
                        {agg_shotsontarget_against} AS avg_shotsontarget_against,
                        {agg_shotsofftarget_for} AS avg_shotsofftarget_for,
                        {agg_shotsofftarget_against} AS avg_shotsofftarget_against,
                        {agg_shots_for} AS avg_shots_for,
                        {agg_shots_against} AS avg_shots_against,
                        {agg_fouls_for} AS avg_fouls_for,
                        {agg_fouls_against} AS avg_fouls_against,
                        {agg_possession_for} AS avg_possession_for,
                        {agg_possession_against} AS avg_possession_against
                    FROM {table_name}
                """

                if selected_home_or_away:
                    query += " WHERE homeoraway = %s"
                    params = [selected_home_or_away]
                else:
                    params = []

                query += " GROUP BY team_name ORDER BY total_points DESC;"
                cursor.execute(query, params)
                league_data = cursor.fetchall()
                
                if league_data: # Ensure there's data before processing columns
                    raw_columns = [col[0] for col in cursor.description]
                    for col_name in raw_columns:
                        # Specific transformations for certain column names if needed, then general rule
                        if col_name == "team_name":
                            display_columns.append("Team Name")
                        elif col_name == "games_played":
                            display_columns.append("Games Played")
                        elif col_name == "total_points":
                            display_columns.append("Total Points")
                        # Add more specific cases if title() isn't perfect for all
                        else:
                            # General rule: replace underscores, then title case
                            # Remove "avg_" or "total_" prefix for a cleaner name, then Title Case
                            name_to_format = col_name
                            if name_to_format.startswith("avg_"):
                                name_to_format = name_to_format[4:]
                            elif name_to_format.startswith("total_"): # Though we are not using total_ prefixes in aliases yet
                                name_to_format = name_to_format[6:]
                            
                            display_columns.append(name_to_format.replace('_', ' ').title())
                else:
                    display_columns = [] # No data, no columns to display or handle appropriately
            else: # No season_id found
                league_data = []
                display_columns = []

    context = {
        'league_data': league_data,
        'columns': display_columns, # Pass display_columns to the template
        'leagues': leagues,
        'seasons': seasons_for_selected_league, 
        'selected_league': selected_league,
        'selected_season': selected_season,
        'selected_home_or_away': selected_home_or_away,
        'view_type': view_type, # Pass view_type to the template
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

    def convert_season_format(season):
        """Convert season from '2024/2025' format to '20242025' format"""
        if not season or season == "NA":
            return "NA"
        # Remove any slashes and spaces
        return season.replace('/', '').replace(' ', '')

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
                    try:
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
                        print(f"Skipping table for competition ID {competition_id}: {e}")
                        continue
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

            # Check for "NA" values
            if "NA" in [league_name, home_team_name, away_team_name] or "NA" in home_metrics or "NA" in away_metrics:
                continue  # Skip this game if any "NA" value exists

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
                "season": convert_season_format(game.get("season", "NA")),
                "status": game.get("status", "NA"),
                "roundID": game.get("roundID", "NA"),
                "game_week": game.get("game_week", "NA"),
                "league": league_name,
                "home_team_name": home_team_name,
                "away_team_name": away_team_name,
                "home_corners_avg": round(float(home_metrics[0]), 2),
                "away_corners_avg": round(float(away_metrics[0]), 2),
                "corners_diff": corners_diff,
                "home_shots": round(float(home_metrics[1]), 2),
                "away_shots": round(float(away_metrics[1]), 2),
                "shots_diff": shots_diff,
                "home_shots_on_target": round(float(home_metrics[2]), 2),
                "away_shots_on_target": round(float(away_metrics[2]), 2),
                "shots_on_target_diff": shots_on_target_diff,
                "home_yellow_cards": round(float(home_metrics[3]), 2),
                "away_yellow_cards": round(float(away_metrics[3]), 2),
                "yellow_cards_diff": yellow_cards_diff,
                "comp_id": competition_id
            })

    return render(request, "football_data/upcoming_games.html", {"games": games, "error_message": error_message})


def visualisation_view(request):
    # Fetch leagues for the dropdown
    with connection.cursor() as cursor:
        cursor.execute('''SELECT DISTINCT name FROM "possible_leagues_and_seasons_NEW" WHERE data_available like 'yes' ORDER BY name''')
        leagues = [row[0] for row in cursor.fetchall()]
    # KPI list: (value, display_label)
    kpis = [
        ('goals_scored', 'Goals Scored'),
        ('goals_conceded', 'Goals Conceded'),
        ('corners_for', 'Corners For'),
        ('corners_against', 'Corners Against'),
        ('offsides_for', 'Offsides For'),
        ('offsides_against', 'Offsides Against'),
        ('yellow_cards_for', 'Yellow Cards For'),
        ('yellow_cards_against', 'Yellow Cards Against'),
        ('red_cards_for', 'Red Cards For'),
        ('red_cards_against', 'Red Cards Against'),
        ('shotsontarget_for', 'Shots On Target For'),
        ('shotsontarget_against', 'Shots On Target Against'),
        ('shotsofftarget_for', 'Shots Off Target For'),
        ('shotsofftarget_against', 'Shots Off Target Against'),
        ('shots_for', 'Shots For'),
        ('shots_against', 'Shots Against'),
        ('fouls_for', 'Fouls For'),
        ('fouls_against', 'Fouls Against'),
        ('possession_for', 'Possession For'),
        ('possession_against', 'Possession Against'),
    ]
    selected_league = request.GET.get('league')
    selected_season = request.GET.get('season')
    seasons = []
    teams_for_js = [] # Default to an empty Python list for json_script

    if selected_league:
        with connection.cursor() as cursor:
            cursor.execute(
                '''SELECT DISTINCT season_year FROM "possible_leagues_and_seasons_NEW" WHERE name = %s AND data_available like \'yes\' ORDER BY season_year''',
                [selected_league]
            )
            seasons = [row[0] for row in cursor.fetchall()]
        if selected_season:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''SELECT season_id FROM "possible_leagues_and_seasons" WHERE name = %s AND season_year = %s''',
                    [selected_league, selected_season]
                )
                result = cursor.fetchone()
                if result:
                    season_id = result[0]
                    table_name = f'match_data_{season_id}_final'
                    cursor.execute(f'''SELECT DISTINCT team_name FROM "{table_name}" ORDER BY team_name''')
                    teams_for_js = [row[0] for row in cursor.fetchall()] # Assign the Python list here
    
    return render(request, 'football_data/visualisation.html', {
        'leagues': leagues,
        'seasons': seasons,
        'kpis': kpis, 
        'teams_for_js': teams_for_js, # Pass the raw Python list for json_script
        'selected_league': selected_league,
        'selected_season': selected_season,
    })

def visualisation_data(request):
    league = request.GET.get('league')
    season_year_str = request.GET.get('season')
    kpi_value = request.GET.get('kpi')
    primary_team_name = request.GET.get('team')

    compare_teams_names = []
    for i in range(1, 5):
        ct_name = request.GET.get(f'compare_team{i}')
        if ct_name and ct_name.lower() != 'none' and ct_name != primary_team_name: # Avoid comparing team to itself here
            compare_teams_names.append(ct_name)
    # Ensure unique comparison teams
    compare_teams_names = sorted(list(set(compare_teams_names)))

    print(f"DEBUG: VisData: Primary={primary_team_name}, Compare={compare_teams_names}, KPI={kpi_value}")

    if not (league and season_year_str and kpi_value and primary_team_name):
        return JsonResponse({'error': 'Missing primary selection parameters (league, season, KPI, or team)'}, status=400)

    # Define KPIs directly in this view to avoid issues with calling visualisation_view(None)
    kpis = [
        ('goals_scored', 'Goals Scored'),
        ('goals_conceded', 'Goals Conceded'),
        ('corners_for', 'Corners For'),
        ('corners_against', 'Corners Against'),
        ('offsides_for', 'Offsides For'),
        ('offsides_against', 'Offsides Against'),
        ('yellow_cards_for', 'Yellow Cards For'),
        ('yellow_cards_against', 'Yellow Cards Against'),
        ('red_cards_for', 'Red Cards For'),
        ('red_cards_against', 'Red Cards Against'),
        ('shotsontarget_for', 'Shots On Target For'),
        ('shotsontarget_against', 'Shots On Target Against'),
        ('shotsofftarget_for', 'Shots Off Target For'),
        ('shotsofftarget_against', 'Shots Off Target Against'),
        ('shots_for', 'Shots For'),
        ('shots_against', 'Shots Against'),
        ('fouls_for', 'Fouls For'),
        ('fouls_against', 'Fouls Against'),
        ('possession_for', 'Possession For'),
        ('possession_against', 'Possession Against'),
    ]
    kpis_definition = kpis # Use the directly defined list
    kpi_display_name = dict(kpis_definition).get(kpi_value, kpi_value)

    all_descriptive_stats = {}
    time_series_datasets = []
    histogram_datasets = []
    primary_team_game_weeks = []
    primary_team_kpi_numeric_values = []

    try:
        with connection.cursor() as cursor:
            cursor.execute('''SELECT season_id FROM possible_leagues_and_seasons WHERE name = %s AND season_year = %s''', [league, season_year_str])
            db_season_result = cursor.fetchone()
            if not db_season_result:
                return JsonResponse({'error': 'Invalid league or season for season_id lookup'}, status=400)
            season_id = db_season_result[0]
            table_name = f"match_data_{season_id}_final"

            if kpi_value not in dict(kpis_definition):
                return JsonResponse({'error': 'Invalid KPI'}, status=400)

            # --- Process Primary Team ---
            raw_primary_data = get_kpi_data_for_team(cursor, table_name, kpi_value, primary_team_name)
            if not raw_primary_data:
                return JsonResponse({'error': f'No data found for primary team {primary_team_name} and KPI {kpi_display_name}'}, status=404)

            primary_team_game_weeks = [row[0] for row in raw_primary_data]
            primary_team_kpi_raw_values = [row[1] for row in raw_primary_data]
            primary_team_kpi_numeric_values = [float(v) for v in primary_team_kpi_raw_values if v is not None]
            
            if not primary_team_kpi_numeric_values:
                 return JsonResponse({'error': f'KPI data for {kpi_display_name} is all null for primary team {primary_team_name}'}, status=404)

            all_descriptive_stats[primary_team_name] = calculate_descriptive_stats(primary_team_kpi_numeric_values)
            time_series_datasets.append({
                'label': primary_team_name,
                'data': primary_team_kpi_raw_values, # Use raw for time series to show None as gaps
                'borderColor': CHART_COLORS[0],
                'backgroundColor': CHART_BG_COLORS_TRANSPARENT[0]
            })

            # --- Histogram Binning based on Primary Team ---
            hist_bin_labels = []
            hist_bin_edges = []
            min_primary_kpi = min(primary_team_kpi_numeric_values)
            max_primary_kpi = max(primary_team_kpi_numeric_values)
            num_bins = 5

            if min_primary_kpi == max_primary_kpi:
                hist_bin_labels = [f"{min_primary_kpi:.2f}"]
                hist_bin_edges = [min_primary_kpi, max_primary_kpi]
            else:
                bin_width = (max_primary_kpi - min_primary_kpi) / num_bins
                if bin_width == 0: bin_width = 1 # Fallback for extremely small range
                hist_bin_edges = [min_primary_kpi + i * bin_width for i in range(num_bins + 1)]
                if hist_bin_edges[num_bins] < max_primary_kpi: hist_bin_edges[num_bins] = max_primary_kpi
                for i in range(num_bins):
                    label_edge_upper = f"<{hist_bin_edges[i+1]:.2f}"
                    if i == num_bins -1 : label_edge_upper = f"{hist_bin_edges[i+1]:.2f}" # Inclusive for last bin label text
                    hist_bin_labels.append(f"{hist_bin_edges[i]:.2f} - {label_edge_upper}")
            
            primary_hist_freqs = [0] * len(hist_bin_labels) # Or num_bins if labels match num_bins
            if len(hist_bin_labels) > 0: # Ensure there are bins before trying to populate them
                for val in primary_team_kpi_numeric_values:
                    for i_bin in range(len(hist_bin_labels)):
                        is_last_bin = (i_bin == len(hist_bin_labels) - 1)
                        lower_b = hist_bin_edges[i_bin]
                        upper_b = hist_bin_edges[i_bin+1]
                        if (is_last_bin and val >= lower_b and val <= upper_b) or \
                           (not is_last_bin and val >= lower_b and val < upper_b) or \
                           (val == lower_b and val == upper_b and len(hist_bin_labels) == 1): # Handles single value case
                            primary_hist_freqs[i_bin] += 1
                            break
            
            histogram_datasets.append({
                'label': primary_team_name,
                'data': primary_hist_freqs,
                'borderColor': CHART_COLORS[0],
                'backgroundColor': CHART_COLORS[0] # Solid for bar typically
            })

            # --- Process Comparison Teams ---
            color_idx = 1
            for comp_team_name in compare_teams_names:
                if color_idx >= len(CHART_COLORS): break # Ran out of unique colors

                raw_comp_data = get_kpi_data_for_team(cursor, table_name, kpi_value, comp_team_name)
                if not raw_comp_data: continue # Skip if no data for this comparison team

                comp_kpi_raw_values = [row[1] for row in raw_comp_data]
                comp_kpi_numeric_values = [float(v) for v in comp_kpi_raw_values if v is not None]
                if not comp_kpi_numeric_values: continue

                all_descriptive_stats[comp_team_name] = calculate_descriptive_stats(comp_kpi_numeric_values)
                time_series_datasets.append({
                    'label': comp_team_name,
                    'data': comp_kpi_raw_values,
                    'borderColor': CHART_COLORS[color_idx],
                    'backgroundColor': CHART_BG_COLORS_TRANSPARENT[color_idx]
                })

                comp_hist_freqs = [0] * len(hist_bin_labels)
                if len(hist_bin_labels) > 0:
                    for val in comp_kpi_numeric_values:
                        for i_bin in range(len(hist_bin_labels)):
                            is_last_bin = (i_bin == len(hist_bin_labels) - 1)
                            lower_b = hist_bin_edges[i_bin]
                            upper_b = hist_bin_edges[i_bin+1]
                            if (is_last_bin and val >= lower_b and val <= upper_b) or \
                               (not is_last_bin and val >= lower_b and val < upper_b) or \
                               (val == lower_b and val == upper_b and len(hist_bin_labels) == 1):
                                comp_hist_freqs[i_bin] += 1
                                break
                
                histogram_datasets.append({
                    'label': comp_team_name,
                    'data': comp_hist_freqs,
                    'borderColor': CHART_COLORS[color_idx],
                    'backgroundColor': CHART_COLORS[color_idx]
                })
                color_idx += 1

        response_payload = {
            'kpi_display_name': kpi_display_name,
            'primary_team_name': primary_team_name,
            'descriptive_stats': all_descriptive_stats,
            'time_series_data': {'labels': [f"GW {gw}" for gw in primary_team_game_weeks], 'datasets': time_series_datasets},
            'histogram_data': {'labels': hist_bin_labels, 'datasets': histogram_datasets}
        }
        print(f"DEBUG: Final JSON response: {str(response_payload)[:500]}...") # Log snippet
        return JsonResponse(response_payload)

    except Exception as e:
        import traceback
        print("ERROR in visualisation_data:")
        traceback.print_exc()
        return JsonResponse({'error': f'An unexpected server error occurred: {str(e)}'}, status=500)

def index_view(request):
    return render(request, 'football_data/index.html')

def league_visualisation_view(request):
    # Fetch leagues for the dropdown
    with connection.cursor() as cursor:
        cursor.execute('''SELECT DISTINCT name FROM "possible_leagues_and_seasons_NEW" WHERE data_available like 'yes' ORDER BY name''')
        leagues = [row[0] for row in cursor.fetchall()]
    
    # KPI list: (value, display_label)
    kpis = [
        ('goals_scored', 'Goals Scored'),
        ('goals_conceded', 'Goals Conceded'),
        ('corners_for', 'Corners For'),
        ('corners_against', 'Corners Against'),
        ('offsides_for', 'Offsides For'),
        ('offsides_against', 'Offsides Against'),
        ('yellow_cards_for', 'Yellow Cards For'),
        ('yellow_cards_against', 'Yellow Cards Against'),
        ('red_cards_for', 'Red Cards For'),
        ('red_cards_against', 'Red Cards Against'),
        ('shotsontarget_for', 'Shots On Target For'),
        ('shotsontarget_against', 'Shots On Target Against'),
        ('shotsofftarget_for', 'Shots Off Target For'),
        ('shotsofftarget_against', 'Shots Off Target Against'),
        ('shots_for', 'Shots For'),
        ('shots_against', 'Shots Against'),
        ('fouls_for', 'Fouls For'),
        ('fouls_against', 'Fouls Against'),
        ('possession_for', 'Possession For'),
        ('possession_against', 'Possession Against'),
    ]
    
    selected_league = request.GET.get('league')
    selected_season = request.GET.get('season')
    selected_kpi = request.GET.get('kpi')
    aggregation_type = request.GET.get('aggregation_type', 'averages')  # Default to averages
    
    seasons = []
    
    if selected_league:
        with connection.cursor() as cursor:
            cursor.execute(
                '''SELECT DISTINCT season_year FROM "possible_leagues_and_seasons_NEW" WHERE name = %s AND data_available like 'yes' ORDER BY season_year''',
                [selected_league]
            )
            seasons = [row[0] for row in cursor.fetchall()]
    
    return render(request, 'football_data/league_visualisation.html', {
        'leagues': leagues,
        'seasons': seasons,
        'kpis': kpis,
        'selected_league': selected_league,
        'selected_season': selected_season,
        'selected_kpi': selected_kpi,
        'aggregation_type': aggregation_type,
    })

def league_visualisation_data(request):
    league = request.GET.get('league')
    season_year_str = request.GET.get('season')
    kpi_value = request.GET.get('kpi')
    aggregation_type = request.GET.get('aggregation_type', 'averages')

    compare_leagues_names = []
    for i in range(1, 5):
        cl_name = request.GET.get(f'compare_league{i}')
        if cl_name and cl_name.lower() != 'none' and cl_name != league:
            compare_leagues_names.append(cl_name)
    # Ensure unique comparison leagues
    compare_leagues_names = sorted(list(set(compare_leagues_names)))

    print(f"DEBUG: LeagueVisData: Primary={league}, Compare={compare_leagues_names}, KPI={kpi_value}, Aggregation={aggregation_type}")

    if not (league and season_year_str and kpi_value):
        return JsonResponse({'error': 'Missing required parameters (league, season, or KPI)'}, status=400)

    # Define KPIs
    kpis = [
        ('goals_scored', 'Goals Scored'),
        ('goals_conceded', 'Goals Conceded'),
        ('corners_for', 'Corners For'),
        ('corners_against', 'Corners Against'),
        ('offsides_for', 'Offsides For'),
        ('offsides_against', 'Offsides Against'),
        ('yellow_cards_for', 'Yellow Cards For'),
        ('yellow_cards_against', 'Yellow Cards Against'),
        ('red_cards_for', 'Red Cards For'),
        ('red_cards_against', 'Red Cards Against'),
        ('shotsontarget_for', 'Shots On Target For'),
        ('shotsontarget_against', 'Shots On Target Against'),
        ('shotsofftarget_for', 'Shots Off Target For'),
        ('shotsofftarget_against', 'Shots Off Target Against'),
        ('shots_for', 'Shots For'),
        ('shots_against', 'Shots Against'),
        ('fouls_for', 'Fouls For'),
        ('fouls_against', 'Fouls Against'),
        ('possession_for', 'Possession For'),
        ('possession_against', 'Possession Against'),
    ]
    
    kpi_display_name = dict(kpis).get(kpi_value, kpi_value)

    all_descriptive_stats = {}
    time_series_datasets = []
    histogram_datasets = []
    all_leagues_data = {}

    try:
        with connection.cursor() as cursor:
            # Process all leagues (primary + comparison)
            all_leagues = [league] + compare_leagues_names
            
            for current_league in all_leagues:
                cursor.execute('''SELECT season_id FROM possible_leagues_and_seasons WHERE name = %s AND season_year = %s''', [current_league, season_year_str])
                db_season_result = cursor.fetchone()
                if not db_season_result:
                    continue  # Skip if no data for this league
                
                season_id = db_season_result[0]
                table_name = f"match_data_{season_id}_final"

                if kpi_value not in dict(kpis):
                    continue

                # Determine aggregation function based on aggregation_type
                if aggregation_type == 'totals':
                    agg_function = f"SUM({kpi_value})"
                else:  # averages
                    agg_function = f"AVG({kpi_value})"

                # Query to get aggregated data by game week
                query = f"""
                    SELECT 
                        game_week,
                        {agg_function} as aggregated_value,
                        COUNT(*) as games_count
                    FROM {table_name}
                    WHERE {kpi_value} IS NOT NULL
                    GROUP BY game_week
                    ORDER BY game_week
                """
                
                cursor.execute(query)
                results = cursor.fetchall()
                
                if not results:
                    continue

                # Extract data for charts
                game_weeks = [row[0] for row in results]
                aggregated_values = [float(row[1]) if row[1] is not None else 0 for row in results]
                games_count = [row[2] for row in results]

                all_leagues_data[current_league] = {
                    'game_weeks': game_weeks,
                    'aggregated_values': aggregated_values,
                    'games_count': games_count
                }

            if not all_leagues_data:
                return JsonResponse({'error': f'No data found for any of the selected leagues and KPI {kpi_display_name}'}, status=404)

            # Use primary league's game weeks as the base for all charts
            primary_league_data = all_leagues_data[league]
            base_game_weeks = primary_league_data['game_weeks']
            
            # Create time series datasets for all leagues
            color_idx = 0
            for current_league in all_leagues:
                if current_league not in all_leagues_data:
                    continue
                    
                league_data = all_leagues_data[current_league]
                
                # Calculate descriptive statistics
                numeric_values = [v for v in league_data['aggregated_values'] if v is not None and not math.isnan(v)]
                if numeric_values:
                    all_descriptive_stats[current_league] = calculate_descriptive_stats(numeric_values)
                else:
                    all_descriptive_stats[current_league] = {'mean': 'N/A', 'median': 'N/A', 'mode': 'N/A'}

                # Create time series dataset
                time_series_datasets.append({
                    'label': f'{current_league} - {kpi_display_name} ({aggregation_type.title()})',
                    'data': league_data['aggregated_values'],
                    'borderColor': CHART_COLORS[color_idx % len(CHART_COLORS)],
                    'backgroundColor': CHART_BG_COLORS_TRANSPARENT[color_idx % len(CHART_BG_COLORS_TRANSPARENT)]
                })
                color_idx += 1

            # Create histogram based on primary league data
            primary_numeric_values = [v for v in primary_league_data['aggregated_values'] if v is not None and not math.isnan(v)]
            if primary_numeric_values:
                hist_bin_labels = []
                hist_bin_edges = []
                min_val = min(primary_numeric_values)
                max_val = max(primary_numeric_values)
                num_bins = 5

                if min_val == max_val:
                    hist_bin_labels = [f"{min_val:.2f}"]
                    hist_bin_edges = [min_val, max_val]
                else:
                    bin_width = (max_val - min_val) / num_bins
                    if bin_width == 0: bin_width = 1
                    hist_bin_edges = [min_val + i * bin_width for i in range(num_bins + 1)]
                    if hist_bin_edges[num_bins] < max_val: hist_bin_edges[num_bins] = max_val
                    for i in range(num_bins):
                        label_edge_upper = f"<{hist_bin_edges[i+1]:.2f}"
                        if i == num_bins - 1: label_edge_upper = f"{hist_bin_edges[i+1]:.2f}"
                        hist_bin_labels.append(f"{hist_bin_edges[i]:.2f} - {label_edge_upper}")

                # Calculate histogram frequencies for all leagues
                color_idx = 0
                for current_league in all_leagues:
                    if current_league not in all_leagues_data:
                        continue
                        
                    league_data = all_leagues_data[current_league]
                    numeric_values = [v for v in league_data['aggregated_values'] if v is not None and not math.isnan(v)]
                    
                    if numeric_values:
                        hist_freqs = [0] * len(hist_bin_labels)
                        for val in numeric_values:
                            for i_bin in range(len(hist_bin_labels)):
                                is_last_bin = (i_bin == len(hist_bin_labels) - 1)
                                lower_b = hist_bin_edges[i_bin]
                                upper_b = hist_bin_edges[i_bin+1]
                                if (is_last_bin and val >= lower_b and val <= upper_b) or \
                                   (not is_last_bin and val >= lower_b and val < upper_b) or \
                                   (val == lower_b and val == upper_b and len(hist_bin_labels) == 1):
                                    hist_freqs[i_bin] += 1
                                    break

                        histogram_datasets.append({
                            'label': f'{current_league} - {kpi_display_name}',
                            'data': hist_freqs,
                            'borderColor': CHART_COLORS[color_idx % len(CHART_COLORS)],
                            'backgroundColor': CHART_COLORS[color_idx % len(CHART_COLORS)]
                        })
                        color_idx += 1

            response_payload = {
                'kpi_display_name': kpi_display_name,
                'aggregation_type': aggregation_type,
                'descriptive_stats': all_descriptive_stats,
                'time_series_data': {
                    'labels': [f"GW {gw}" for gw in base_game_weeks],
                    'datasets': time_series_datasets
                },
                'histogram_data': {
                    'labels': hist_bin_labels,
                    'datasets': histogram_datasets
                }
            }
            
            print(f"DEBUG: League visualization response: {str(response_payload)[:500]}...")
            return JsonResponse(response_payload)

    except Exception as e:
        import traceback
        print("ERROR in league_visualisation_data:")
        traceback.print_exc()
        return JsonResponse({'error': f'An unexpected server error occurred: {str(e)}'}, status=500)

def correlations_view(request):
    """
    Renders the correlations page with initial filter options.
    """
    try:
        with connection.cursor() as cursor:
            # Fetch all leagues
            cursor.execute("SELECT DISTINCT name FROM possible_leagues_and_seasons ORDER BY name")
            leagues = [row[0] for row in cursor.fetchall()]

            # Fetch all season years
            cursor.execute("SELECT DISTINCT season_year FROM possible_leagues_and_seasons ORDER BY season_year DESC")
            seasons = [row[0] for row in cursor.fetchall()]

    except Exception as e:
        print(f"Error in correlations_view: {e}")
        leagues, seasons = [], []

    context = {
        'leagues': leagues,
        'seasons': seasons,
        'page_title': 'Correlations',
        'active_page': 'correlations',
    }
    return render(request, 'football_data/correlations.html', context)


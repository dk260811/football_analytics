from django.shortcuts import render
from django.db import connection

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

# Football Analytics Website

A comprehensive Django web application for analyzing football/soccer statistics, providing detailed insights into team performance, league comparisons, match details, and upcoming fixtures.

## Features

### 🏆 League Data
- View aggregated statistics for teams across different leagues and seasons
- Filter by league, season, and home/away matches
- Toggle between averages and totals view
- Display comprehensive metrics including goals, corners, cards, shots, fouls, possession, and more
- Sortable tables with team rankings

### 📊 Team Visualizations
- Visualize key performance indicators (KPIs) for individual teams over time
- Compare up to 4 teams side-by-side
- Time series charts showing performance trends across game weeks
- Histogram analysis for statistical distribution
- Descriptive statistics (mean, median, mode) for each team

### 📈 League Visualizations
- Aggregate league-level statistics visualization
- Compare multiple leagues across the same season
- Time series and histogram views
- Toggle between averages and totals aggregation

### 🔗 Correlations
- Analyze correlations between different football statistics
- Filter by league and season

### 📅 Upcoming Games
- View upcoming fixtures for a specified date range
- Team statistics comparison for each fixture
- Displays average corners, shots, shots on target, and yellow cards
- Highlights differences between teams

### 📋 Match Details
- Detailed match-by-match breakdown for any team
- View all statistics for individual games
- Filter by league and season

## Technology Stack

- **Backend**: Django 5.1.3
- **Database**: PostgreSQL
- **Frontend**: 
  - Bootstrap 5.1.3
  - Chart.js (for data visualizations)
  - Font Awesome 6.4.0
- **External APIs**: Football Data API

## Prerequisites

- Python 3.8+
- PostgreSQL
- pip (Python package manager)

## Installation

1. **Clone the repository** (or navigate to the project directory)
   ```bash
   cd django_website/football_analytics
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install django==5.1.3
   pip install psycopg2-binary
   pip install requests
   ```

4. **Database Configuration**
   
   Configure your PostgreSQL database in `football_analytics/settings.py`:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': os.environ.get('DB_NAME', 'your_db_name'),
           'USER': os.environ.get('DB_USER', 'your_db_user'),
           'PASSWORD': os.environ.get('DB_PASSWORD', 'your_db_password'),
           'HOST': os.environ.get('DB_HOST', 'your_db_host'),
           'PORT': os.environ.get('DB_PORT', '5432'),
       }
   }
   ```
   
   Alternatively, set environment variables:
   - `DB_NAME`
   - `DB_USER`
   - `DB_PASSWORD`
   - `DB_HOST`
   - `DB_PORT`

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser** (optional, for admin access)
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Main page: `http://127.0.0.1:8000/`
   - Admin panel: `http://127.0.0.1:8000/admin/`

## Project Structure

```
football_analytics/
├── football_analytics/          # Project settings
│   ├── settings.py              # Django settings
│   ├── urls.py                  # Main URL configuration
│   ├── wsgi.py
│   └── asgi.py
├── football_data/               # Main application
│   ├── models.py
│   ├── views.py                 # View logic
│   ├── urls.py                  # App URL patterns
│   ├── admin.py
│   └── templates/
│       └── football_data/       # HTML templates
│           ├── index.html
│           ├── league_data.html
│           ├── match_details.html
│           ├── visualisation.html
│           ├── league_visualisation.html
│           ├── correlations.html
│           └── upcoming_games.html
└── manage.py
```

## Database Schema

The application uses the following key tables:

- `possible_leagues_and_seasons_NEW`: Stores available leagues and seasons
- `match_data_{season_id}_final`: Match data tables for each season, containing:
  - Team names and opponent information
  - Goals scored/conceded
  - Corners, offsides
  - Cards (yellow/red)
  - Shots (on target, off target, total)
  - Fouls
  - Possession
  - Game week and season information

## Available KPIs

The application supports analysis of the following Key Performance Indicators:

- Goals (scored/conceded)
- Corners (for/against)
- Offsides (for/against)
- Yellow Cards (for/against)
- Red Cards (for/against)
- Shots On Target (for/against)
- Shots Off Target (for/against)
- Total Shots (for/against)
- Fouls (for/against)
- Possession (for/against)

## API Endpoints

- `/` - Home page
- `/football/league-data/` - League statistics
- `/football/match-details/<team_name>/<league>/<season>/` - Team match details
- `/football/visualisation/` - Team visualizations
- `/football/league-visualisation/` - League visualizations
- `/football/correlations/` - Correlation analysis
- `/football/upcoming-games/` - Upcoming fixtures
- `/football/visualisation/data/` - AJAX endpoint for visualization data
- `/football/league-visualisation/data/` - AJAX endpoint for league visualization data
- `/football/get_seasons_for_league/` - AJAX endpoint for fetching seasons

## Configuration

### Secret Key

**Important**: Before deploying to production, change the `SECRET_KEY` in `settings.py`. Never commit sensitive keys to version control.

### Debug Mode

Set `DEBUG = False` in production and configure `ALLOWED_HOSTS` appropriately.

### Static Files

For production, configure static files collection:
```bash
python manage.py collectstatic
```

## Usage Examples

### Viewing League Data
1. Navigate to "League Data" from the home page
2. Select a league from the dropdown
3. Select a season
4. Optionally filter by home/away
5. Toggle between averages and totals view

### Creating Team Visualizations
1. Navigate to "Team Visualisations"
2. Select league, season, and KPI
3. Choose a primary team
4. Optionally select up to 4 comparison teams
5. View time series and histogram charts

### Viewing Upcoming Games
1. Navigate to "Upcoming Games"
2. Enter start and end dates
3. View fixtures with team statistics comparisons

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Future Enhancements

Based on comments in the code, planned features include:
- Regression analysis tools
- Combination calculator
- Data update functionality for current season only
- Additional statistical analyses

## License

[Specify your license here]

## Contact

[Your contact information]

## Acknowledgments

- Football Data API for fixture data
- Django community for excellent documentation
- Bootstrap and Chart.js for UI components

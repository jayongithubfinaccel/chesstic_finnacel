"""
Service for interacting with Chess.com API and processing chess data.
"""
import requests
from datetime import datetime
from typing import Dict, List, Optional
from app.utils.cache import cache_response


class ChessService:
    """Service for fetching and analyzing chess.com data."""
    
    BASE_URL = "https://api.chess.com/pub"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Chess Analytics App (github.com/yourusername/chesstic_v2)'
        })
    
    @cache_response(ttl=300)  # Cache for 5 minutes
    def get_player_profile(self, username: str) -> Dict:
        """
        Fetch player profile from Chess.com API.
        
        Args:
            username: Chess.com username
            
        Returns:
            Player profile data
        """
        url = f"{self.BASE_URL}/player/{username}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    @cache_response(ttl=60)  # Cache for 1 minute
    def get_player_stats(self, username: str) -> Dict:
        """
        Fetch player statistics from Chess.com API.
        
        Args:
            username: Chess.com username
            
        Returns:
            Player statistics data
        """
        url = f"{self.BASE_URL}/player/{username}/stats"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_games_by_month(self, username: str, year: int, month: int) -> List[Dict]:
        """
        Fetch games for a specific month with complete PGN data.
        
        Args:
            username: Chess.com username
            year: Year (YYYY)
            month: Month (1-12)
            
        Returns:
            List of games with PGN data
        """
        url = f"{self.BASE_URL}/player/{username}/games/{year}/{month:02d}"
        response = self.session.get(url)
        response.raise_for_status()
        data = response.json()
        games = data.get('games', [])
        
        # Games from Chess.com API should already include PGN
        # Ensure each game has necessary fields
        for game in games:
            if 'pgn' not in game:
                game['pgn'] = ''
            if 'end_time' not in game:
                game['end_time'] = 0
                
        return games
    
    def analyze_games(self, username: str, start_date: str, end_date: str) -> Dict:
        """
        Analyze games within a date range.
        
        Args:
            username: Chess.com username
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Analysis results with statistics
        """
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        all_games = []
        current = start
        
        # Fetch games for each month in the range
        while current <= end:
            try:
                games = self.get_games_by_month(username, current.year, current.month)
                all_games.extend(games)
            except requests.exceptions.HTTPError:
                pass  # No games for this month
            
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        
        # Filter games by date range
        filtered_games = self._filter_games_by_date(all_games, start_date, end_date)
        
        # Calculate statistics
        stats = self._calculate_statistics(filtered_games, username)
        
        return {
            'username': username,
            'start_date': start_date,
            'end_date': end_date,
            'total_games': len(filtered_games),
            'statistics': stats,
            'games': filtered_games
        }
    
    def _filter_games_by_date(self, games: List[Dict], start_date: str, end_date: str) -> List[Dict]:
        """Filter games by date range."""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        filtered = []
        for game in games:
            game_date = datetime.fromtimestamp(game.get('end_time', 0))
            if start <= game_date <= end:
                filtered.append(game)
        
        return filtered
    
    def _calculate_statistics(self, games: List[Dict], username: str) -> Dict:
        """Calculate game statistics."""
        stats = {
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'win_rate': 0.0,
            'by_color': {'white': {'wins': 0, 'losses': 0, 'draws': 0},
                        'black': {'wins': 0, 'losses': 0, 'draws': 0}},
            'by_time_control': {}
        }
        
        for game in games:
            # Determine player color
            white = game.get('white', {})
            black = game.get('black', {})
            
            if white.get('username', '').lower() == username.lower():
                color = 'white'
                result = white.get('result')
            else:
                color = 'black'
                result = black.get('result')
            
            # Count results
            if result == 'win':
                stats['wins'] += 1
                stats['by_color'][color]['wins'] += 1
            elif result == 'lose':
                stats['losses'] += 1
                stats['by_color'][color]['losses'] += 1
            else:
                stats['draws'] += 1
                stats['by_color'][color]['draws'] += 1
            
            # Time control statistics
            time_control = game.get('time_control', 'unknown')
            if time_control not in stats['by_time_control']:
                stats['by_time_control'][time_control] = {'wins': 0, 'losses': 0, 'draws': 0}
            
            if result == 'win':
                stats['by_time_control'][time_control]['wins'] += 1
            elif result == 'lose':
                stats['by_time_control'][time_control]['losses'] += 1
            else:
                stats['by_time_control'][time_control]['draws'] += 1
        
        # Calculate win rate
        total = stats['wins'] + stats['losses'] + stats['draws']
        if total > 0:
            stats['win_rate'] = round((stats['wins'] / total) * 100, 2)
        
        return stats

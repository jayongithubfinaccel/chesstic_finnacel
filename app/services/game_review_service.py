"""
Composes ChessService + AnalyticsService into a Telegram-ready win/loss and
opening review for a given date window (used by the daily/weekly review jobs).
"""
from typing import Dict, List

from app.services.chess_service import ChessService
from app.services.analytics_service import AnalyticsService

OPENING_LENGTHS = (4, 5, 6, 7)
COLORS = (('white', '⚪', '♟️ White'), ('black', '⚫', '♟️ Black'))


class GameReviewService:
    """Builds a per-color, per-termination-type, per-opening-length review."""

    def __init__(self, chess_service: ChessService = None, analytics_service: AnalyticsService = None):
        self.chess_service = chess_service or ChessService()
        self.analytics_service = analytics_service or AnalyticsService(
            engine_enabled=False, openai_api_key=''
        )

    def build_review(self, username: str, start_date: str, end_date: str, timezone: str = 'UTC') -> Dict:
        """
        Fetch games for the window and build the full review summary.
        """
        result = self.chess_service.analyze_games(username, start_date, end_date)
        games = result.get('games', [])

        summary = {
            'username': username,
            'start_date': start_date,
            'end_date': end_date,
            'total_games': 0,
        }

        if not games:
            return summary

        enriched = self.analytics_service._parse_and_enrich_games(games, username, timezone)
        summary['total_games'] = len(enriched)
        summary['totals'] = self._count_results(enriched)

        for color, _, _ in COLORS:
            color_games = [g for g in enriched if g['player_color'] == color]
            summary[color] = {
                'totals': self._count_results(color_games),
                'termination_wins': self.analytics_service._analyze_termination_wins(color_games),
                'termination_losses': self.analytics_service._analyze_termination_losses(color_games),
            }

        summary['openings_by_length'] = {
            n: self.analytics_service._analyze_opening_by_prefix_length(enriched, n)
            for n in OPENING_LENGTHS
        }

        return summary

    @staticmethod
    def _count_results(games: List[Dict]) -> Dict:
        return {
            'wins': sum(1 for g in games if g['result'] == 'win'),
            'losses': sum(1 for g in games if g['result'] == 'loss'),
            'draws': sum(1 for g in games if g['result'] == 'draw'),
        }


def format_review_message(summary: Dict, title: str) -> str:
    """
    Render a review summary (from GameReviewService.build_review) as a
    Telegram message. Used for both the daily and weekly review - only the
    title differs.
    """
    if summary['total_games'] == 0:
        return (
            f"{title}\n"
            f"No games played between {summary['start_date']} and {summary['end_date']}."
        )

    lines = [title]
    totals = summary['totals']
    lines.append(
        f"Games played: {summary['total_games']}  |  "
        f"{totals['wins']}W - {totals['losses']}L - {totals['draws']}D"
    )
    lines.append("")

    for color, emoji, _ in COLORS:
        color_summary = summary[color]
        color_totals = color_summary['totals']
        record = f"{color_totals['wins']}W - {color_totals['losses']}L"
        if color_totals['draws']:
            record += f" - {color_totals['draws']}D"
        lines.append(f"{emoji} {color.capitalize()} — {record}")

        win_breakdown = color_summary['termination_wins']['breakdown']
        if win_breakdown:
            won_by = ", ".join(f"{k.capitalize()} {v}" for k, v in win_breakdown.items())
            lines.append(f"  🏁 Won by: {won_by}")

        loss_breakdown = color_summary['termination_losses']['breakdown']
        if loss_breakdown:
            lost_by = ", ".join(f"{k.capitalize()} {v}" for k, v in loss_breakdown.items())
            lines.append(f"  💀 Lost by: {lost_by}")

        lines.append("")

    for num_moves in OPENING_LENGTHS:
        by_color = summary['openings_by_length'][num_moves]
        for color, _, label in COLORS:
            entries = by_color.get(color, [])
            if not entries:
                continue

            lines.append(f"{label} — Opening (first {num_moves} moves)")
            for entry in entries:
                record = f"{entry['wins']}W-{entry['losses']}L"
                if entry['draws']:
                    record += f"-{entry['draws']}D"
                game_word = 'game' if entry['games'] == 1 else 'games'
                lines.append(
                    f"  • {entry['moves']} ({entry['opening_name']}): "
                    f"{entry['games']} {game_word} ({record}, {entry['win_rate']:.0f}%)"
                )
            lines.append("")

    return "\n".join(lines).strip()

"""
CLI entry point for the daily/weekly Telegram chess review.

Intended to be invoked by Windows Task Scheduler:
  - Daily:  python scripts/telegram_review.py --mode daily
  - Weekly: python scripts/telegram_review.py --mode weekly   (run Mondays)

Daily reviews the last 1 day (H-1); weekly reviews the last 7 days (H-7),
both ending yesterday in REVIEW_TIMEZONE.
"""
import argparse
import logging
import os
import sys
from datetime import datetime, timedelta

import pytz
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# .env lives at the project root; load_dotenv() alone searches upward from
# this script's own directory and would miss it (same gotcha as the notebook).
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

from app.services.game_review_service import GameReviewService, format_review_message  # noqa: E402
from app.services.telegram_service import TelegramService  # noqa: E402

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


def compute_date_window(mode: str, timezone_str: str):
    """Return (start_date, end_date) as YYYY-MM-DD strings, both ending yesterday."""
    now = datetime.now(pytz.timezone(timezone_str))
    yesterday = now - timedelta(days=1)
    end_date = yesterday.strftime('%Y-%m-%d')

    if mode == 'daily':
        start_date = end_date
    else:  # weekly
        start_date = (yesterday - timedelta(days=6)).strftime('%Y-%m-%d')

    return start_date, end_date


def main():
    parser = argparse.ArgumentParser(description='Send a daily or weekly chess review to Telegram')
    parser.add_argument('--mode', choices=['daily', 'weekly'], required=True)
    args = parser.parse_args()

    username = os.environ.get('CHESS_USERNAME', '')
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
    timezone_str = os.environ.get('REVIEW_TIMEZONE', 'UTC')

    if not username:
        logger.error('CHESS_USERNAME is not configured in .env')
        sys.exit(1)
    if not bot_token or not chat_id:
        logger.error('TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID are not configured in .env')
        sys.exit(1)

    start_date, end_date = compute_date_window(args.mode, timezone_str)
    title = 'Daily Chess Review' if args.mode == 'daily' else 'Weekly Chess Review'
    date_range_text = start_date if start_date == end_date else f'{start_date} to {end_date}'

    logger.info(f'Building {args.mode} review for {username}: {date_range_text}')

    review_service = GameReviewService()
    summary = review_service.build_review(username, start_date, end_date, timezone_str)

    message = format_review_message(summary, f'📊 {title} — {date_range_text} ({username})')

    telegram_service = TelegramService(bot_token, chat_id)
    sent = telegram_service.send_long_message(message)

    if not sent:
        logger.error('Failed to send Telegram message')
        sys.exit(1)

    logger.info(f'{title} sent successfully ({summary["total_games"]} games)')


if __name__ == '__main__':
    main()

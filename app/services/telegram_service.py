"""
Telegram notification service for sending chess review reports.
"""
import logging
from typing import List

import requests

logger = logging.getLogger(__name__)


class TelegramService:
    """Thin client for sending messages via the Telegram Bot API."""

    API_BASE = "https://api.telegram.org"
    MAX_MESSAGE_LENGTH = 4096  # Telegram's hard limit per sendMessage call

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send_message(self, text: str, parse_mode: str = None) -> bool:
        """
        Send a text message to the configured Telegram chat.

        Plain text by default: usernames, move notation (e.g. "O-O"), and
        opening names can contain Markdown-special characters (a lone "_"
        in a username reads as an unclosed italic marker), which Telegram's
        Markdown parser rejects with a 400 "can't parse entities" error.

        Args:
            text: Message body
            parse_mode: Telegram parse mode ('Markdown', 'MarkdownV2', 'HTML', or None)

        Returns:
            True if Telegram accepted the message, False otherwise.
        """
        if not self.bot_token or not self.chat_id:
            logger.error("Telegram bot token or chat id is not configured")
            return False

        url = f"{self.API_BASE}/bot{self.bot_token}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': text,
        }
        if parse_mode:
            payload['parse_mode'] = parse_mode

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def send_long_message(self, text: str, parse_mode: str = None) -> bool:
        """
        Send a message, splitting it into multiple messages if it exceeds
        Telegram's per-message length limit. Splits on line boundaries so an
        individual opening/termination entry is never cut mid-line.

        Returns:
            True only if every chunk was sent successfully.
        """
        chunks = self._split_into_chunks(text, self.MAX_MESSAGE_LENGTH)
        return all(self.send_message(chunk, parse_mode=parse_mode) for chunk in chunks)

    @staticmethod
    def _split_into_chunks(text: str, max_length: int) -> List[str]:
        lines = text.split('\n')
        chunks = []
        current_lines = []
        current_length = 0

        for line in lines:
            line_length = len(line) + 1  # +1 for the newline that joins it back

            if current_lines and current_length + line_length > max_length:
                chunks.append('\n'.join(current_lines))
                current_lines = []
                current_length = 0

            current_lines.append(line)
            current_length += line_length

        if current_lines:
            chunks.append('\n'.join(current_lines))

        return chunks

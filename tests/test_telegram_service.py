"""
Unit tests for TelegramService, in particular the long-message chunking
that keeps each Telegram API call under the 4096-character limit.
"""
from unittest.mock import patch, MagicMock

import requests

from app.services.telegram_service import TelegramService


class TestSplitIntoChunks:
    def test_short_text_is_a_single_chunk(self):
        text = "line one\nline two\nline three"
        chunks = TelegramService._split_into_chunks(text, max_length=4096)
        assert chunks == [text]

    def test_splits_on_line_boundaries_when_over_limit(self):
        # Each line is 10 chars + newline; max_length=25 fits 2 lines per chunk
        lines = ["0123456789"] * 5
        text = "\n".join(lines)
        chunks = TelegramService._split_into_chunks(text, max_length=25)

        # No chunk exceeds the limit, and no line is split mid-way
        assert all(len(chunk) <= 25 for chunk in chunks)
        for chunk in chunks:
            for line in chunk.split('\n'):
                assert line == "0123456789"

        # Rejoining every chunk reconstructs all original lines
        rejoined = "\n".join(chunks).split('\n')
        assert rejoined == lines

    def test_realistic_weekly_message_stays_under_telegram_limit(self):
        section = "♟️ White — Opening (first 4 moves)\n  • 1. e4 e5 2. Nf3 Nc6 (Italian Game): 3 games (2W-1L, 67%)\n"
        text = section * 60  # force it over 4096 chars
        assert len(text) > 4096

        chunks = TelegramService._split_into_chunks(text, max_length=4096)
        assert len(chunks) > 1
        assert all(len(chunk) <= 4096 for chunk in chunks)


class TestSendLongMessage:
    def test_sends_one_request_per_chunk(self):
        service = TelegramService('fake-token', 'fake-chat-id')
        # 300 lines of ~30 chars each (~9000 chars total) forces multiple chunks
        long_text = "\n".join(f"line {i:04d}: some opening entry text here" for i in range(300))

        with patch('app.services.telegram_service.requests.post') as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            mock_post.return_value.raise_for_status = lambda: None

            result = service.send_long_message(long_text)

        assert result is True
        assert mock_post.call_count > 1
        for call in mock_post.call_args_list:
            sent_text = call.kwargs['json']['text']
            assert len(sent_text) <= 4096

    def test_returns_false_if_any_chunk_fails(self):
        service = TelegramService('fake-token', 'fake-chat-id')

        with patch('app.services.telegram_service.requests.post') as mock_post:
            ok_response = MagicMock(status_code=200)
            ok_response.raise_for_status = lambda: None
            failing_response = MagicMock(status_code=400)
            failing_response.raise_for_status = MagicMock(
                side_effect=requests.exceptions.HTTPError("400 Bad Request")
            )
            mock_post.side_effect = [ok_response, failing_response]
            two_line_text = ("a" * 3000) + "\n" + ("b" * 3000)
            result = service.send_long_message(two_line_text)

        assert result is False

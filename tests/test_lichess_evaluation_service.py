"""
Unit tests for Lichess Evaluation Service.
Iteration 11: Test Lichess Cloud API integration
"""
import pytest
from unittest.mock import patch, Mock
from app.services.lichess_evaluation_service import LichessEvaluationService


class TestLichessEvaluationService:
    """Test cases for Lichess Cloud API evaluation service."""
    
    def test_initialization(self):
        """Test service initialization with default timeout."""
        service = LichessEvaluationService()
        
        assert service.timeout == 5.0
        assert service.stats['api_calls'] == 0
        assert service.stats['hits'] == 0
        assert service.stats['misses'] == 0
        assert service.stats['errors'] == 0
    
    def test_initialization_custom_timeout(self):
        """Test service initialization with custom timeout."""
        service = LichessEvaluationService(timeout=3.0)
        
        assert service.timeout == 3.0
    
    @patch('app.services.lichess_evaluation_service.requests.get')
    def test_evaluate_position_success_with_cp(self, mock_get):
        """Test successful evaluation with centipawn score."""
        # Mock Lichess API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
            "knodes": 12345,
            "depth": 20,
            "pvs": [
                {
                    "moves": "c7c5 g1f3",
                    "cp": 32
                }
            ]
        }
        mock_get.return_value = mock_response
        
        service = LichessEvaluationService()
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        
        result = service.evaluate_position(fen)
        
        assert result == 32
        assert service.stats['api_calls'] == 1
        assert service.stats['hits'] == 1
        assert service.stats['misses'] == 0
    
    @patch('app.services.lichess_evaluation_service.requests.get')
    def test_evaluate_position_success_with_mate(self, mock_get):
        """Test successful evaluation with mate score."""
        # Mock Lichess API response with mate
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4",
            "knodes": 9876,
            "depth": 18,
            "pvs": [
                {
                    "moves": "h5f7",
                    "mate": 1
                }
            ]
        }
        mock_get.return_value = mock_response
        
        service = LichessEvaluationService()
        fen = "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4"
        
        result = service.evaluate_position(fen)
        
        assert result == 10000  # Mate converted to CP
        assert service.stats['hits'] == 1
    
    @patch('app.services.lichess_evaluation_service.requests.get')
    def test_evaluate_position_not_found(self, mock_get):
        """Test evaluation when position not in Lichess cloud."""
        # Mock empty response (position not in database)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        }
        mock_get.return_value = mock_response
        
        service = LichessEvaluationService()
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        
        result = service.evaluate_position(fen)
        
        assert result is None
        assert service.stats['api_calls'] == 1
        assert service.stats['hits'] == 0
        assert service.stats['misses'] == 1
    
    @patch('app.services.lichess_evaluation_service.requests.get')
    def test_evaluate_position_timeout(self, mock_get):
        """Test timeout handling."""
        import requests
        mock_get.side_effect = requests.Timeout("Connection timeout")
        
        service = LichessEvaluationService()
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        
        result = service.evaluate_position(fen)
        
        assert result is None
        assert service.stats['api_calls'] == 1
        assert service.stats['errors'] == 1
    
    @patch('app.services.lichess_evaluation_service.requests.get')
    def test_evaluate_position_request_error(self, mock_get):
        """Test handling of request errors."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")
        
        service = LichessEvaluationService()
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        
        result = service.evaluate_position(fen)
        
        assert result is None
        assert service.stats['errors'] == 1
    
    @patch('app.services.lichess_evaluation_service.requests.get')
    def test_evaluate_position_http_error(self, mock_get):
        """Test handling of HTTP error status."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        service = LichessEvaluationService()
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        
        result = service.evaluate_position(fen)
        
        assert result is None
        assert service.stats['misses'] == 1
    
    @patch('app.services.lichess_evaluation_service.requests.get')
    def test_get_stats(self, mock_get):
        """Test statistics calculation."""
        # Mock multiple calls
        mock_response_hit = Mock()
        mock_response_hit.status_code = 200
        mock_response_hit.json.return_value = {
            "fen": "test",
            "pvs": [{"cp": 50}]
        }
        
        mock_response_miss = Mock()
        mock_response_miss.status_code = 200
        mock_response_miss.json.return_value = {"fen": "test"}
        
        mock_get.side_effect = [mock_response_hit, mock_response_hit, mock_response_miss, mock_response_hit]
        
        service = LichessEvaluationService()
        
        # Make 4 calls: 3 hits, 1 miss
        service.evaluate_position("fen1")
        service.evaluate_position("fen2")
        service.evaluate_position("fen3")
        service.evaluate_position("fen4")
        
        stats = service.get_stats()
        
        assert stats['api_calls'] == 4
        assert stats['hits'] == 3
        assert stats['misses'] == 1
        assert stats['errors'] == 0
        assert stats['hit_rate'] == 75.0
    
    def test_get_stats_no_calls(self):
        """Test statistics when no API calls made."""
        service = LichessEvaluationService()
        
        stats = service.get_stats()
        
        assert stats['api_calls'] == 0
        assert stats['hit_rate'] == 0
    
    def test_reset_stats(self):
        """Test statistics reset."""
        service = LichessEvaluationService()
        service.stats['api_calls'] = 10
        service.stats['hits'] = 8
        service.stats['misses'] = 2
        
        service.reset_stats()
        
        assert service.stats['api_calls'] == 0
        assert service.stats['hits'] == 0
        assert service.stats['misses'] == 0
        assert service.stats['errors'] == 0
    
    @patch('app.services.lichess_evaluation_service.requests.get')
    def test_evaluate_position_negative_mate(self, mock_get):
        """Test evaluation with negative mate score (losing)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "fen": "test",
            "pvs": [{"mate": -3}]
        }
        mock_get.return_value = mock_response
        
        service = LichessEvaluationService()
        
        result = service.evaluate_position("fen")
        
        assert result == -10000  # Losing mate converted to negative CP

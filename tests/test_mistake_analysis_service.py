"""
Unit tests for Mistake Analysis Service
Tests the strategic move sampling logic
"""
import pytest
from app.services.mistake_analysis_service import MistakeAnalysisService


class TestMoveSelectionLogic:
    """Test the strategic move sampling logic"""
    
    @pytest.fixture
    def service(self):
        return MistakeAnalysisService()
    
    def test_select_moves_small_game(self, service):
        """Test that games with ≤30 moves analyze all moves"""
        # 20 moves - should analyze all
        result = service._select_moves_to_analyze(20)
        assert len(result) == 20
        assert result == set(range(20))
        
        # 30 moves - should analyze all (boundary case)
        result = service._select_moves_to_analyze(30)
        assert len(result) == 30
        assert result == set(range(30))
    
    def test_select_moves_medium_game(self, service):
        """Test strategic sampling for 40-move game"""
        result = service._select_moves_to_analyze(40)
        
        # Should analyze 30 moves (first 10 + last 10 + middle 10)
        assert len(result) == 30
        
        # Check first 10 moves are included (indices 0-9)
        for i in range(10):
            assert i in result, f"First 10 moves should include move {i}"
        
        # Check last 10 moves are included (indices 30-39)
        for i in range(30, 40):
            assert i in result, f"Last 10 moves should include move {i}"
        
        # Middle 10 moves should be from indices 10-29
        middle_moves = [i for i in result if 10 <= i < 30]
        assert len(middle_moves) == 10, f"Should have 10 middle moves, got {len(middle_moves)}"
    
    def test_select_moves_large_game(self, service):
        """Test strategic sampling for 60-move game"""
        result = service._select_moves_to_analyze(60)
        
        # Should analyze exactly 30 moves
        assert len(result) == 30
        
        # Check first 10 (0-9)
        first_moves = [i for i in result if i < 10]
        assert len(first_moves) == 10
        
        # Check last 10 (50-59)
        last_moves = [i for i in result if i >= 50]
        assert len(last_moves) == 10
        
        # Check middle 10 (10-49, should have 10 evenly distributed)
        middle_moves = [i for i in result if 10 <= i < 50]
        assert len(middle_moves) == 10
        
        # Middle moves should be somewhat evenly distributed
        # With 40 middle moves and selecting 10, we expect ~4 move spacing
        middle_sorted = sorted(middle_moves)
        if len(middle_sorted) >= 2:
            avg_spacing = (middle_sorted[-1] - middle_sorted[0]) / (len(middle_sorted) - 1)
            assert 2 <= avg_spacing <= 6, f"Middle moves should be evenly distributed, avg spacing: {avg_spacing}"
    
    def test_select_moves_very_large_game(self, service):
        """Test strategic sampling for 80-move game"""
        result = service._select_moves_to_analyze(80)
        
        # Should still analyze exactly 30 moves (capped)
        assert len(result) == 30
        
        # Verify distribution
        first_moves = [i for i in result if i < 10]
        last_moves = [i for i in result if i >= 70]  # last 10 of 80
        middle_moves = [i for i in result if 10 <= i < 70]
        
        assert len(first_moves) == 10
        assert len(last_moves) == 10
        assert len(middle_moves) == 10
    
    def test_select_moves_edge_case_31_moves(self, service):
        """Test edge case with 31 moves (just over boundary)"""
        result = service._select_moves_to_analyze(31)
        
        # Should apply sampling logic and return 30 moves
        assert len(result) == 30
        
        # Should have first 10, last 10, and 10 from middle
        first = [i for i in result if i < 10]
        last = [i for i in result if i >= 21]  # last 10 of 31
        middle = [i for i in result if 10 <= i < 21]
        
        assert len(first) == 10
        assert len(last) == 10
        assert len(middle) == 10
    
    def test_select_moves_boundaries(self, service):
        """Test boundary conditions"""
        # Test with 1 move
        result = service._select_moves_to_analyze(1)
        assert result == {0}
        
        # Test with 0 moves (edge case)
        result = service._select_moves_to_analyze(0)
        assert result == set()
    
    def test_move_indices_valid(self, service):
        """Ensure all returned indices are within valid range"""
        for total_moves in [10, 30, 40, 60, 80, 100]:
            result = service._select_moves_to_analyze(total_moves)
            
            # All indices should be within range [0, total_moves)
            for idx in result:
                assert 0 <= idx < total_moves, f"Invalid index {idx} for {total_moves} total moves"
            
            # Should not have duplicates (is a set)
            assert len(result) == len(set(result))


class TestMistakeAnalysisConfiguration:
    """Test that configuration constants are set correctly"""
    
    def test_configuration_constants(self):
        """Verify the strategic sampling constants are properly configured"""
        service = MistakeAnalysisService()
        
        # Check sampling constants (class constants)
        assert MistakeAnalysisService.FIRST_MOVES_TO_ANALYZE == 10
        assert MistakeAnalysisService.LAST_MOVES_TO_ANALYZE == 10
        assert MistakeAnalysisService.MIDDLE_MOVES_TO_ANALYZE == 10
        assert MistakeAnalysisService.MAX_MOVES_PER_GAME == 30
        
        # Check optimization thresholds (class constants)
        assert MistakeAnalysisService.EARLY_STOP_THRESHOLD == 300  # 300 CP
        assert MistakeAnalysisService.SKIP_EVAL_THRESHOLD == 600  # 600 CP
        
        # Check instance configuration
        assert service.engine_depth == 10  # Should be 10 for better accuracy
        assert service.time_limit == 0.5  # 500ms


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

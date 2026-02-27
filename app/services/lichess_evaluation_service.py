"""
Lichess Cloud Evaluation Service for fast chess position evaluation.
Iteration 11: Performance optimization using Lichess Cloud API
"""
import requests
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class LichessEvaluationService:
    """Service for evaluating chess positions using Lichess Cloud API."""
    
    BASE_URL = "https://lichess.org/api/cloud-eval"
    TIMEOUT = 5.0  # 5 second timeout
    
    def __init__(self, timeout: float = 5.0):
        """
        Initialize Lichess evaluation service.
        
        Args:
            timeout: API request timeout in seconds (default: 5.0)
        """
        self.timeout = timeout
        self.stats = {
            'api_calls': 0,
            'hits': 0,
            'misses': 0,
            'errors': 0
        }
    
    def evaluate_position(self, fen: str) -> Optional[int]:
        """
        Evaluate position using Lichess Cloud API.
        
        Args:
            fen: Board position in FEN notation
            
        Returns:
            Centipawn score (positive = advantage for side to move), or None if not found
        """
        self.stats['api_calls'] += 1
        
        try:
            params = {
                "fen": fen,
                "multiPv": 1
            }
            
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if evaluation exists in cloud
                if "pvs" in data and len(data["pvs"]) > 0:
                    pv_data = data["pvs"][0]
                    
                    # Get centipawn score
                    if "cp" in pv_data:
                        cp_score = pv_data["cp"]
                        self.stats['hits'] += 1
                        logger.debug(f"Lichess eval for {fen[:30]}...: {cp_score} cp (depth {data.get('depth', 'N/A')})")
                        return cp_score
                    
                    # Handle mate scores
                    if "mate" in pv_data:
                        mate_in = pv_data["mate"]
                        # Convert mate to centipawn equivalent
                        # Positive mate = winning, negative = losing
                        cp_score = 10000 if mate_in > 0 else -10000
                        self.stats['hits'] += 1
                        logger.debug(f"Lichess eval for {fen[:30]}...: Mate in {mate_in}")
                        return cp_score
                        
            # Position not found in cloud database
            self.stats['misses'] += 1
            logger.debug(f"Position not in Lichess cloud: {fen[:30]}...")
            return None
            
        except requests.Timeout:
            self.stats['errors'] += 1
            logger.warning("Lichess API timeout")
            return None
        except requests.RequestException as e:
            self.stats['errors'] += 1
            logger.warning(f"Lichess API request error: {e}")
            return None
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Lichess API error: {e}")
            return None
    
    def get_stats(self) -> dict:
        """
        Get API usage statistics.
        
        Returns:
            Dictionary with api_calls, hits, misses, errors counts and hit_rate percentage
        """
        hit_rate = (self.stats['hits'] / self.stats['api_calls'] * 100) if self.stats['api_calls'] > 0 else 0
        return {
            **self.stats,
            'hit_rate': round(hit_rate, 2)
        }
    
    def reset_stats(self):
        """Reset API usage statistics."""
        self.stats = {
            'api_calls': 0,
            'hits': 0,
            'misses': 0,
            'errors': 0
        }

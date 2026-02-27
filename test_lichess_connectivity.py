"""Quick test to verify Lichess API connectivity and coverage."""
import chess
import chess.pgn
from io import StringIO
from app.services.lichess_evaluation_service import LichessEvaluationService

# Sample game from performance tests
SAMPLE_PGN = """[Event "Live Chess"]
[Site "Chess.com"]
[Date "2026.02.26"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O Nf6 5. d3 d6 6. c3 O-O 7. Bb3 a6 
8. Nbd2 Ba7 9. h3 h6 10. Re1 Re8 11. Nf1 Be6 12. Ng3 Bxb3 13. Qxb3 Qd7 
14. Nh2 Rad8 15. Nhf1 Kh7 16. Be3 Bxe3 17. Nxe3 Ne7 18. Nef5 Nxf5 
19. Nxf5 Qe6 20. Qxe6 fxe6 21. Ng3 Nh5 22. Nxh5 1-0
"""

def main():
    print("Testing Lichess Cloud API connectivity...\n")
    
    service = LichessEvaluationService(timeout=5.0)
    
    # Test 1: Starting position (definitely should be in cloud)
    start_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    print(f"1. Testing starting position...")
    result = service.evaluate_position(start_fen)
    print(f"   Result: {result} CP (expected: ~20-40)")
    
    # Test 2: e4 position
    e4_fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
    print(f"\n2. Testing 1.e4 position...")
    result = service.evaluate_position(e4_fen)
    print(f"   Result: {result} CP")
    
    # Test 3: Analyze positions from the sample game
    print(f"\n3. Testing positions from sample game...")
    pgn = chess.pgn.read_game(StringIO(SAMPLE_PGN))
    board = pgn.board()
    
    hits = 0
    misses = 0
    positions_tested = 0
    
    for move_num, move in enumerate(pgn.mainline_moves()):
        board.push(move)
        positions_tested += 1
        
        result = service.evaluate_position(board.fen())
        if result is not None:
            hits += 1
            if move_num < 5:  # Show first 5
                print(f"   Move {move_num + 1}: HIT - {result} CP")
        else:
            misses += 1
            if move_num < 5:
                print(f"   Move {move_num + 1}: MISS")
        
        if move_num >= 9:  # Test first 10 moves
            break
    
    stats = service.get_stats()
    print(f"\n4. Statistics for sample game:")
    print(f"   Positions tested: {positions_tested}")
    print(f"   Hits: {hits} ({hits/positions_tested*100:.1f}%)")
    print(f"   Misses: {misses} ({misses/positions_tested*100:.1f}%)")
    print(f"   Full stats: {stats}")
    
    # Test 4: Very obscure position (likely not in cloud)
    obscure_fen = "8/8/8/4k3/8/8/8/4K3 w - - 0 1"  # Basic K+K endgame
    print(f"\n5. Testing obscure position (K+K endgame)...")
    result = service.evaluate_position(obscure_fen)
    print(f"   Result: {result} CP (expected: 0 - draw)")
    
    final_stats = service.get_stats()
    print(f"\n6. Final Lichess API statistics:")
    print(f"   API Calls: {final_stats['api_calls']}")
    print(f"   Hits: {final_stats['hits']}")
    print(f"   Misses: {final_stats['misses']}")
    print(f"   Hit Rate: {final_stats['hit_rate']:.1f}%")

if __name__ == "__main__":
    main()

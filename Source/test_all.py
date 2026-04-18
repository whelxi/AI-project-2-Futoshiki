import os
import time
import astar
from init import read_input, print_output

try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Test inputs 1-11
    for i in range(1, 12):
        input_num = f"{i:02d}"
        input_path = os.path.join(script_dir, "Inputs", f"input-{input_num}.txt")
        
        print(f"Xử lý input-{input_num}.txt...", end=" ")
        game = read_input(input_path)
        print(f"(n={game.n})", end=" ")
        
        start_time = time.time()
        solved_game = astar.solve_futoshiki_astar(game)
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        if solved_game:
            print(f"✓ Thành công ({elapsed_time:.4f}s)")
        else:
            print(f"✗ Không giải được ({elapsed_time:.4f}s)")
        
except Exception as e:
    print(f"\nLỗi: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

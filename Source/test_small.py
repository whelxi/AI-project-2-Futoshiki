import os
import time
import astar
from init import read_input, print_output

try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Test input-01 first (smaller)
    for input_num in ["01", "02"]:
        input_path = os.path.join(script_dir, "Inputs", f"input-{input_num}.txt")
        
        print(f"Đang xử lý input-{input_num}.txt...")
        game = read_input(input_path)
        print(f"Đã tải dữ liệu: n={game.n}")
        
        start_time = time.time()
        solved_game = astar.solve_futoshiki_astar(game)
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        if solved_game:
            print(f"Giải được! Thời gian: {elapsed_time:.4f} giây\n")
        else:
            print(f"Không tìm được lời giải. Thời gian: {elapsed_time:.4f} giây\n")
        
except Exception as e:
    print(f"Lỗi: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

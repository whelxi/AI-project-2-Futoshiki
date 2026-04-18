import os
import glob
import time
import tracemalloc
import csv

# Import các module đọc/ghi dữ liệu
import game as game_module

# Import các thuật toán
from a_star import solve_futoshiki_astar
from backtracking import solve_futoshiki as solve_backtracking
from forward_backward_chaining import Agent as FBAgent
from sat_optimized import solve_futoshiki_optimized

def run_astar(in_path, out_path):
    game = game_module.read_input(in_path)
    result = solve_futoshiki_astar(game)
    if result:
        game_module.print_output(out_path, result)
        return True
    return False

def run_backtracking(in_path, out_path):
    game = game_module.read_input(in_path)
    if solve_backtracking(game):
        game_module.print_output(out_path, game)
        return True
    return False

def run_fbc(in_path, out_path):
    game = game_module.read_input(in_path)
    agent = FBAgent(game)
    if agent.solve():
        # Tuỳ thuộc vào logic nội bộ của file, in kết quả ra
        game_module.print_output(out_path, agent.game)
        return True
    return False

def run_sat(in_path, out_path):
    # SAT đã tự động handle đọc ghi file bên trong hàm
    try:
        stats = solve_futoshiki_optimized(in_path, out_path)
        return True
    except Exception as e:
        return False

def main():
    input_dir = 'Inputs'
    output_dir = 'Outputs'
    csv_filename = 'Benchmark_Results.csv'

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    input_files = glob.glob(os.path.join(input_dir, 'input-*.txt'))
    input_files.sort()
    
    if not input_files:
        print(f"Không tìm thấy file input nào trong thư mục '{input_dir}'.")
        return

    # Khai báo danh sách các thuật toán cần benchmark (Đã bỏ Brute Force)
    algorithms = {
        "A-Star": run_astar,
        "Backtracking": run_backtracking,
        "Forward-Backward Chaining": run_fbc,
        "SAT Optimized": run_sat
    }

    print("BẮT ĐẦU CHẠY BENCHMARK...")
    print("=" * 60)

    # Mở file CSV để ghi kết quả
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['File Name', 'Algorithm', 'Time (seconds)', 'Memory Peak (MB)', 'Status']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for in_path in input_files:
            filename = os.path.basename(in_path)
            print(f"\nĐang xử lý: {filename}")
            
            for algo_name, algo_func in algorithms.items():
                out_filename = filename.replace('input-', f'output-{algo_name.replace(" ", "_")}-')
                out_path = os.path.join(output_dir, out_filename)
                
                print(f"  -> Chạy {algo_name.ljust(25)}", end="", flush=True)

                # Bắt đầu theo dõi RAM và Thời gian
                tracemalloc.start()
                start_time = time.perf_counter()
                
                status = "Failed"
                try:
                    # Chạy thuật toán
                    is_solved = algo_func(in_path, out_path)
                    if is_solved:
                        status = "Success"
                except Exception as e:
                    status = f"Error"
                
                # Kết thúc đo lường
                end_time = time.perf_counter()
                current_mem, peak_mem = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                run_time = end_time - start_time
                peak_mem_mb = peak_mem / (1024 * 1024)

                print(f"[{status}] | Time: {run_time:.4f}s | Mem: {peak_mem_mb:.4f} MB")

                # Ghi dòng dữ liệu vào CSV
                writer.writerow({
                    'File Name': filename,
                    'Algorithm': algo_name,
                    'Time (seconds)': round(run_time, 4),
                    'Memory Peak (MB)': round(peak_mem_mb, 4),
                    'Status': status
                })

    print("=" * 60)
    print(f"Hoàn thành! Kết quả chi tiết đã được lưu vào: {csv_filename}")

if __name__ == '__main__':
    main()
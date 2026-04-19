import os
import glob
import time
import tracemalloc
import csv
import multiprocessing
import threading

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
        game_module.print_output(out_path, agent.game)
        return True
    return False

def run_sat(in_path, out_path):
    try:
        stats = solve_futoshiki_optimized(in_path, out_path)
        return True
    except Exception as e:
        return False

def memory_monitor(return_dict, stop_event):
    """
    Luồng chạy ngầm để liên tục lấy số liệu peak RAM và lưu vào shared dictionary.
    Nếu process bị kill đột ngột, ta vẫn có số liệu RAM ở giây cuối cùng.
    """
    while not stop_event.is_set():
        time.sleep(0.5) # Lấy mẫu mỗi 0.5 giây để tránh hao tốn tài nguyên
        if tracemalloc.is_tracing():
            current_mem, peak_mem = tracemalloc.get_traced_memory()
            return_dict['peak_mem'] = peak_mem / (1024 * 1024)

def worker_benchmark(algo_func, in_path, out_path, return_dict):
    tracemalloc.start()
    start_time = time.perf_counter()
    
    # Bật luồng theo dõi RAM liên tục
    stop_event = threading.Event()
    monitor_thread = threading.Thread(target=memory_monitor, args=(return_dict, stop_event))
    monitor_thread.daemon = True  # Thread tự động tắt nếu process bị kill
    monitor_thread.start()
    
    try:
        is_solved = algo_func(in_path, out_path)
        status = "Success" if is_solved else "Failed"
    except Exception as e:
        status = "Error"
        
    end_time = time.perf_counter()
    
    # Báo cho luồng RAM dừng lại vì thuật toán đã chạy xong
    stop_event.set()
    
    # Lấy số liệu chốt sổ lần cuối
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return_dict['status'] = status
    return_dict['run_time'] = end_time - start_time
    return_dict['peak_mem'] = peak_mem / (1024 * 1024)

def main():
    input_dir = 'Inputs'
    output_dir = 'Outputs'
    csv_filename = 'Benchmark_Results.csv'
    TIMEOUT_SECONDS = 300 

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    input_files = glob.glob(os.path.join(input_dir, 'input-*.txt'))
    input_files.sort()
    
    if not input_files:
        print(f"Không tìm thấy file input nào trong thư mục '{input_dir}'.")
        return

    algorithms = {
        "A-Star": run_astar,
        "Backtracking": run_backtracking,
        "Forward-Backward Chaining": run_fbc,
        "SAT Optimized": run_sat
    }

    print("BẮT ĐẦU CHẠY BENCHMARK...")
    print(f"Giới hạn thời gian: {TIMEOUT_SECONDS} giây")
    print("=" * 70)

    manager = multiprocessing.Manager()

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

                return_dict = manager.dict()
                # Khởi tạo mặc định tránh lỗi nếu chưa kịp ghi gì đã timeout
                return_dict['peak_mem'] = 0.0 
                
                p = multiprocessing.Process(
                    target=worker_benchmark, 
                    args=(algo_func, in_path, out_path, return_dict)
                )
                p.start()
                p.join(TIMEOUT_SECONDS)
                
                if p.is_alive():
                    p.terminate()
                    p.join()
                    
                    status = "Timeout"
                    run_time = TIMEOUT_SECONDS
                    # Kéo lấy peak RAM đã được luồng phụ lưu lại liên tục trước khi bị kill
                    peak_mem_mb = return_dict.get('peak_mem', 0.0) 
                else:
                    status = return_dict.get('status', 'Error')
                    run_time = return_dict.get('run_time', 0.0)
                    peak_mem_mb = return_dict.get('peak_mem', 0.0)

                print(f"[{status}] | Time: {run_time:.4f}s | Mem: {peak_mem_mb:.4f} MB")

                writer.writerow({
                    'File Name': filename,
                    'Algorithm': algo_name,
                    'Time (seconds)': round(run_time, 4),
                    'Memory Peak (MB)': round(peak_mem_mb, 4),
                    'Status': status
                })

    print("=" * 70)
    print(f"Hoàn thành! Kết quả chi tiết đã được lưu vào: {csv_filename}")

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
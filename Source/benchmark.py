import os
import glob
import time
import tracemalloc
import csv
import multiprocessing
import threading

# Import các module đọc/ghi dữ liệu
import game as game_module

# Import các thuật toán cũ
from a_star import solve_futoshiki_astar
from backtracking import solve_futoshiki as solve_backtracking
from hybrid_inference import FutoshikiFOLAgent
from sat_optimized import solve_futoshiki_optimized

# Import 2 thuật toán mới 
from backward_chaining import FutoshikiFOLAgent as BackwardAgent
from forward_chaining import FutoshikiFOLAgent as ForwardAgent

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

def run_hybrid(in_path, out_path):
    game = game_module.read_input(in_path)
    agent = FutoshikiFOLAgent(game)
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

def run_backward_chaining(in_path, out_path):
    game = game_module.read_input(in_path)
    agent = BackwardAgent(game)
    if agent.solve():
        game_module.print_output(out_path, agent.game)
        return True
    return False

def run_forward_chaining(in_path, out_path):
    game = game_module.read_input(in_path)
    agent = ForwardAgent(game)
    if agent.solve():
        game_module.print_output(out_path, agent.game)
        return True
    return False

def memory_monitor(return_dict, stop_event):
    """
    Luồng chạy ngầm liên tục lấy mẫu RAM.
    Thu thập các mẫu để tính bộ nhớ trung bình và cập nhật bộ nhớ đỉnh.
    """
    samples = []
    while not stop_event.is_set():
        time.sleep(0.1) # Lấy mẫu mỗi 0.1 giây để độ phân giải tốt hơn
        if tracemalloc.is_tracing():
            current_mem, peak_mem = tracemalloc.get_traced_memory()
            samples.append(current_mem / (1024 * 1024))
            return_dict['peak_mem'] = peak_mem / (1024 * 1024)
            
    # Tính trung bình dung lượng RAM đã sử dụng trong suốt quá trình chạy
    if samples:
        return_dict['avg_mem'] = sum(samples) / len(samples)
    else:
        # Nếu thuật toán chạy quá nhanh (chưa tới 0.1s), lấy luôn peak làm average
        return_dict['avg_mem'] = return_dict.get('peak_mem', 0.0)

def worker_benchmark(algo_func, in_path, out_path, return_dict):
    tracemalloc.start()
    start_time = time.perf_counter()
    
    stop_event = threading.Event()
    monitor_thread = threading.Thread(target=memory_monitor, args=(return_dict, stop_event))
    monitor_thread.daemon = True  
    monitor_thread.start()
    
    try:
        is_solved = algo_func(in_path, out_path)
        status = "Success" if is_solved else "Failed"
    except Exception as e:
        status = f"Error: {e}"
        
    end_time = time.perf_counter()
    
    # Báo luồng RAM dừng và đợi chốt số liệu
    stop_event.set()
    monitor_thread.join(timeout=1.0)
    
    # Lấy số liệu lần cuối để tránh bỏ sót nếu thread bị gián đoạn
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return_dict['status'] = status
    return_dict['run_time'] = end_time - start_time
    
    # Đảm bảo peak_mem là giá trị lớn nhất ghi nhận được
    final_peak = peak_mem / (1024 * 1024)
    if final_peak > return_dict.get('peak_mem', 0.0):
        return_dict['peak_mem'] = final_peak

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
        "Hybrid Inference": run_hybrid,
        "SAT Optimized": run_sat,
        "Backward Chaining FOL": run_backward_chaining,
        "Forward Chaining FOL": run_forward_chaining
    }   

    print("BẮT ĐẦU CHẠY BENCHMARK...")
    print(f"Giới hạn thời gian (TLE): {TIMEOUT_SECONDS} giây (5 phút)")
    print("=" * 70)

    manager = multiprocessing.Manager()

    with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
        # Cập nhật fieldnames có thêm cột Memory Average
        fieldnames = ['File Name', 'Algorithm', 'Time (seconds)', 'Memory Peak (MB)', 'Memory Avg (MB)', 'Status']
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
                return_dict['peak_mem'] = 0.0 
                return_dict['avg_mem'] = 0.0
                
                p = multiprocessing.Process(
                    target=worker_benchmark, 
                    args=(algo_func, in_path, out_path, return_dict)
                )
                p.start()
                p.join(TIMEOUT_SECONDS)
                
                if p.is_alive():
                    p.terminate()
                    p.join()
                    
                    status = "Timeout (TLE)"
                    run_time = TIMEOUT_SECONDS
                    peak_mem_mb = return_dict.get('peak_mem', 0.0) 
                    avg_mem_mb = return_dict.get('avg_mem', peak_mem_mb) # Lấy avg hoặc peak nếu timeout đột ngột
                else:
                    status = return_dict.get('status', 'Error')
                    run_time = return_dict.get('run_time', 0.0)
                    peak_mem_mb = return_dict.get('peak_mem', 0.0)
                    avg_mem_mb = return_dict.get('avg_mem', 0.0)

                print(f"[{status}] | Time: {run_time:.4f}s | Peak: {peak_mem_mb:.4f} MB | Avg: {avg_mem_mb:.4f} MB")

                writer.writerow({
                    'File Name': filename,
                    'Algorithm': algo_name,
                    'Time (seconds)': round(run_time, 4),
                    'Memory Peak (MB)': round(peak_mem_mb, 4),
                    'Memory Avg (MB)': round(avg_mem_mb, 4),
                    'Status': status
                })

    print("=" * 70)
    print(f"Hoàn thành! Kết quả chi tiết đã được lưu vào: {csv_filename}")

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
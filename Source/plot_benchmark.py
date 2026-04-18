import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def plot_benchmark_results(csv_filename='Benchmark_Results.csv'):
    if not os.path.exists(csv_filename):
        print(f"Không tìm thấy file '{csv_filename}'. Vui lòng chạy file benchmark.py trước để tạo dữ liệu.")
        return

    # Đọc dữ liệu từ file CSV
    df = pd.read_csv(csv_filename)

    # Thiết lập style cho đồ thị
    sns.set_theme(style="whitegrid")
    
    # Tạo thư mục chứa biểu đồ nếu chưa có
    output_dir = 'Charts'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("Đang vẽ biểu đồ...")

    # ---------------------------------------------------------
    # 1. Biểu đồ cột: Thời gian chạy trung bình của từng thuật toán
    # ---------------------------------------------------------
    plt.figure(figsize=(10, 6))
    # Tính trung bình thời gian, ẩn error bar để đồ thị gọn hơn
    sns.barplot(data=df, x='Algorithm', y='Time (seconds)', errorbar=None, palette='viridis')
    plt.title('Thời gian chạy trung bình của các thuật toán', fontsize=14, fontweight='bold')
    plt.ylabel('Thời gian trung bình (giây)', fontsize=12)
    plt.xlabel('Thuật toán', fontsize=12)
    plt.xticks(rotation=15)
    plt.tight_layout()
    time_chart_path = os.path.join(output_dir, 'Average_Time_Chart.png')
    plt.savefig(time_chart_path, dpi=300)
    plt.close()

    # ---------------------------------------------------------
    # 2. Biểu đồ cột: Bộ nhớ tiêu thụ (RAM) trung bình
    # ---------------------------------------------------------
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df, x='Algorithm', y='Memory Peak (MB)', errorbar=None, palette='magma')
    plt.title('Bộ nhớ tiêu thụ đỉnh (Peak Memory) trung bình', fontsize=14, fontweight='bold')
    plt.ylabel('Bộ nhớ (MB)', fontsize=12)
    plt.xlabel('Thuật toán', fontsize=12)
    plt.xticks(rotation=15)
    plt.tight_layout()
    mem_chart_path = os.path.join(output_dir, 'Average_Memory_Chart.png')
    plt.savefig(mem_chart_path, dpi=300)
    plt.close()

    # ---------------------------------------------------------
    # 3. Biểu đồ đường (Line Chart): Thời gian chạy qua từng test case
    # ---------------------------------------------------------
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=df, x='File Name', y='Time (seconds)', hue='Algorithm', marker='o', linewidth=2)
    plt.title('Biến động thời gian chạy qua các Test Case', fontsize=14, fontweight='bold')
    plt.ylabel('Thời gian (giây)', fontsize=12)
    plt.xlabel('File Input', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.legend(title='Thuật toán')
    plt.tight_layout()
    line_chart_path = os.path.join(output_dir, 'Time_Per_Testcase_Chart.png')
    plt.savefig(line_chart_path, dpi=300)
    plt.close()
    
    # ---------------------------------------------------------
    # 4. Biểu đồ cột chồng: Tỷ lệ giải thành công (Success Rate)
    # ---------------------------------------------------------
    plt.figure(figsize=(10, 6))
    status_counts = df.groupby(['Algorithm', 'Status']).size().unstack(fill_value=0)
    status_counts.plot(kind='bar', stacked=True, color=['#ff9999', '#66b3ff'], figsize=(10, 6))
    plt.title('Tỷ lệ giải thành công theo từng Thuật toán', fontsize=14, fontweight='bold')
    plt.ylabel('Số lượng Test Case', fontsize=12)
    plt.xlabel('Thuật toán', fontsize=12)
    plt.xticks(rotation=15)
    plt.legend(title='Trạng thái')
    plt.tight_layout()
    status_chart_path = os.path.join(output_dir, 'Success_Rate_Chart.png')
    plt.savefig(status_chart_path, dpi=300)
    plt.close()

    print(f"Đã lưu các biểu đồ thành công vào thư mục '{output_dir}':")
    print(f" 1. {time_chart_path}")
    print(f" 2. {mem_chart_path}")
    print(f" 3. {line_chart_path}")
    print(f" 4. {status_chart_path}")

if __name__ == '__main__':
    plot_benchmark_results()
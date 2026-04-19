import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np

def plot_benchmark_results(csv_filename='Benchmark_Results.csv'):
    if not os.path.exists(csv_filename):
        print(f"Không tìm thấy file '{csv_filename}'. Vui lòng chạy file benchmark.py trước để tạo dữ liệu.")
        return

    # Đọc dữ liệu từ file CSV
    df = pd.read_csv(csv_filename)

    # ĐIỂM CHẠM THIẾT KẾ 1: Làm sạch dữ liệu trục X
    # Rút gọn 'input-01.txt' thành '1', '2'... giúp trục X thoáng hơn
    if 'File Name' in df.columns:
        df['Test Case'] = df['File Name'].str.replace('input-', '', regex=False).str.replace('.txt', '', regex=False)
    else:
        df['Test Case'] = df.index # Backup nếu không có cột File Name

    # Thiết lập phong cách thiết kế hiện đại, tối giản (Minimalist)
    sns.set_theme(style="whitegrid", font_scale=1.1)
    # Tùy chỉnh thêm: Bỏ viền đồ thị (Spines) để trông thanh thoát hơn
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.spines.right'] = False
    
    output_dir = 'Charts'
    os.makedirs(output_dir, exist_ok=True)

    print("Đang vẽ biểu đồ chuẩn Designer...")

    # =========================================================
    # 1. Biểu đồ cột: Thời gian chạy trung bình 
    # =========================================================
    plt.figure(figsize=(10, 6))
    
    # Tính trung bình để vẽ
    avg_time = df.groupby('Algorithm')['Time (seconds)'].mean().reset_index()
    avg_time = avg_time.sort_values(by='Time (seconds)') # Sắp xếp từ nhanh nhất đến chậm nhất
    
    ax1 = sns.barplot(data=avg_time, x='Algorithm', y='Time (seconds)', palette='crest')
    
    # ĐIỂM CHẠM THIẾT KẾ 2: Thêm nhãn số liệu trực tiếp lên cột (Data labels)
    for container in ax1.containers:
        ax1.bar_label(container, fmt='%.3f s', padding=5, fontsize=11, color='#333333')

    plt.title('Thời Gian Chạy Trung Bình (Càng thấp càng tốt)', fontsize=15, fontweight='bold', pad=20)
    plt.ylabel('Thời gian (giây)', fontsize=12, color='#555555')
    plt.xlabel('', fontsize=12) # Bỏ chữ 'Thuật toán' vì người xem tự hiểu
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'Average_Time_Chart.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # =========================================================
    # 2. Biểu đồ cột: Bộ nhớ tiêu thụ (RAM) trung bình
    # =========================================================
    plt.figure(figsize=(10, 6))
    
    avg_mem = df.groupby('Algorithm')['Memory Peak (MB)'].mean().reset_index()
    avg_mem = avg_mem.sort_values(by='Memory Peak (MB)')
    
    ax2 = sns.barplot(data=avg_mem, x='Algorithm', y='Memory Peak (MB)', palette='flare')
    
    for container in ax2.containers:
        ax2.bar_label(container, fmt='%.1f MB', padding=5, fontsize=11, color='#333333')

    plt.title('Bộ Nhớ Tiêu Thụ Đỉnh Trung Bình (Peak Memory)', fontsize=15, fontweight='bold', pad=20)
    plt.ylabel('Bộ nhớ (MB)', fontsize=12, color='#555555')
    plt.xlabel('')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'Average_Memory_Chart.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # =========================================================
    # 3. Biểu đồ đường: Biến động thời gian (Áp dụng Direct Labeling)
    # =========================================================
    plt.figure(figsize=(12, 6))
    
    # Dùng palette màu phân biệt rõ ràng
    ax3 = sns.lineplot(data=df, x='Test Case', y='Time (seconds)', hue='Algorithm', 
                       marker='o', markersize=8, linewidth=2.5, palette='tab10')
    
    # ĐIỂM CHẠM THIẾT KẾ 3: Direct Labeling - Thay thế Legend bằng Text cuối đường đồ thị
    ax3.get_legend().remove() # Tắt legend mặc định
    
    # Xác định điểm cuối cùng của mỗi thuật toán để ghi chú
    for algo in df['Algorithm'].unique():
        algo_data = df[df['Algorithm'] == algo]
        if not algo_data.empty:
            # Lấy toạ độ x, y cuối cùng
            last_x_val = algo_data['Test Case'].iloc[-1]
            last_y_val = algo_data['Time (seconds)'].iloc[-1]
            
            # Lấy màu của đường line tương ứng
            line_color = ax3.lines[list(df['Algorithm'].unique()).index(algo)].get_color()
            
            # Chèn text sát bên cạnh điểm cuối cùng
            plt.text(x=len(algo_data) - 1 + 0.15,  # Nhích sang phải một chút
                     y=last_y_val, 
                     s=algo, 
                     color=line_color, 
                     fontweight='bold', 
                     fontsize=11,
                     va='center')

    # Nới rộng trục X để có không gian chứa chữ (tránh bị cắt)
    plt.xlim(-0.5, len(df['Test Case'].unique()) + 1.5)

    plt.title('Biến Động Thời Gian Chạy Qua Các Test Case', fontsize=15, fontweight='bold', pad=20)
    plt.ylabel('Thời gian (giây)', fontsize=12, color='#555555')
    plt.xlabel('Test Case', fontsize=12, color='#555555')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'Time_Per_Testcase_Chart.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # =========================================================
    # 4. Biểu đồ cột chồng: Tỷ lệ giải thành công (Success Rate)
    # =========================================================
    plt.figure(figsize=(10, 6))
    
    # Đảm bảo có cột Status, nếu có 'Success', 'Timeout', 'Fail',...
    if 'Status' in df.columns:
        status_counts = df.groupby(['Algorithm', 'Status']).size().unstack(fill_value=0)
        
        # ĐIỂM CHẠM THIẾT KẾ 4: Chọn màu sắc mang ý nghĩa (Xanh = Tốt/Thành công, Đỏ/Xám = Lỗi)
        # Tự động map màu nếu biết trước tên status (ví dụ: 'Success', 'Fail')
        color_map = []
        for col in status_counts.columns:
            if str(col).lower() in ['success', 'passed', 'ok']:
                color_map.append('#2ecc71') # Xanh lá
            elif str(col).lower() in ['timeout']:
                color_map.append('#f1c40f') # Vàng
            else:
                color_map.append('#e74c3c') # Đỏ

        if not color_map: # Fallback nếu không khớp tên
            color_map = sns.color_palette("Set2", len(status_counts.columns))

        ax4 = status_counts.plot(kind='bar', stacked=True, color=color_map, figsize=(10, 6), edgecolor='white')
        
        plt.title('Tỷ Lệ Giải Thành Công Của Các Thuật Toán', fontsize=15, fontweight='bold', pad=20)
        plt.ylabel('Số lượng Test Case', fontsize=12, color='#555555')
        plt.xlabel('')
        plt.xticks(rotation=0) # Để nhãn nằm ngang
        
        # Sửa lại Legend cho đẹp
        plt.legend(title='Trạng thái', frameon=False, bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'Success_Rate_Chart.png'), dpi=300, bbox_inches='tight')
        plt.close()

    print(f"✨ Hoàn tất! Các biểu đồ 'chuẩn Designer' đã được lưu tại '{output_dir}/'")

if __name__ == '__main__':
    plot_benchmark_results()
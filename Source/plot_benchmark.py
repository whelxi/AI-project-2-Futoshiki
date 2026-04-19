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

    # Rút gọn tên Test Case
    if 'File Name' in df.columns:
        df['Test Case'] = df['File Name'].str.replace('input-', '', regex=False).str.replace('.txt', '', regex=False)
    else:
        df['Test Case'] = df.index

    # =========================================================
    # CẤU HÌNH DESIGN SYSTEM
    # =========================================================
    sns.set_theme(style="whitegrid", font_scale=1.1)
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.spines.right'] = False
    plt.rcParams['font.family'] = 'sans-serif'
    
    # Hệ màu phân cực
    color_map = {
        'SAT Optimized': '#10B981',             # Xanh ngọc
        'A-Star': '#3B82F6',                    # Xanh dương
        'Forward-Backward Chaining': '#F59E0B', # Vàng cam
        'Backtracking': '#EF4444'               # Đỏ
    }
    
    unique_algos = df['Algorithm'].unique()
    palette = [color_map.get(algo, '#888888') for algo in unique_algos]

    output_dir = 'Charts'
    os.makedirs(output_dir, exist_ok=True)

    print("Đang render biểu đồ...")

    # =========================================================
    # 1. Biểu đồ cột: Thời gian chạy trung bình 
    # =========================================================
    plt.figure(figsize=(10, 6))
    avg_time = df.groupby('Algorithm')['Time (seconds)'].mean().reset_index()
    avg_time = avg_time.sort_values(by='Time (seconds)')
    
    ax1 = sns.barplot(data=avg_time, x='Algorithm', y='Time (seconds)', palette=palette, order=avg_time['Algorithm'])
    
    for container in ax1.containers:
        ax1.bar_label(container, fmt='%.3f s', padding=5, fontsize=11, fontweight='bold', color='#333')

    plt.title('Thời Gian Chạy Trung Bình\n(Càng thấp càng tốt)', fontsize=16, fontweight='bold', pad=20, color='#1F2937')
    plt.ylabel('Thời gian (giây)', fontsize=12, color='#4B5563')
    plt.xlabel('') 
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'Average_Time_Chart.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # =========================================================
    # 2. Biểu đồ cột: Bộ nhớ tiêu thụ (RAM) trung bình - CẬP NHẬT TRẦN 2MB
    # =========================================================
    plt.figure(figsize=(10, 6))
    avg_mem = df.groupby('Algorithm')['Memory Peak (MB)'].mean().reset_index()
    avg_mem = avg_mem.sort_values(by='Memory Peak (MB)')
    
    ax2 = sns.barplot(data=avg_mem, x='Algorithm', y='Memory Peak (MB)', palette=palette, order=avg_mem['Algorithm'])
    
    MEM_MAX_LIMIT = 2.0
    ax2.set_ylim(0, MEM_MAX_LIMIT + 0.3) # Dư ra một chút không gian phía trên để đặt Text

    # Vẽ đường đứt nét giới hạn 2MB
    plt.axhline(y=MEM_MAX_LIMIT, color='#9CA3AF', linestyle='--', linewidth=1.5, zorder=0)
    plt.text(x=-0.4, y=MEM_MAX_LIMIT + 0.05, s='Ngưỡng hiển thị đồ thị (2 MB)', color='#6B7280', fontsize=9, fontstyle='italic')

    # Xử lý Label thông minh cho các cột vượt quá 2MB
    for i, p in enumerate(ax2.patches):
        val = p.get_height()
        algo_name = avg_mem.iloc[i]['Algorithm']
        bar_color = color_map.get(algo_name, '#888888')

        if val > MEM_MAX_LIMIT:
            # Nếu vượt trần, ghim thẻ label ở mép trên đồ thị
            ax2.text(p.get_x() + p.get_width()/2., MEM_MAX_LIMIT + 0.1, f'{val:.1f} MB', 
                     fontsize=11, fontweight='bold', color='white', ha='center', va='bottom',
                     bbox=dict(facecolor=bar_color, edgecolor='none', boxstyle='round,pad=0.3'))
        else:
            # Nếu dưới trần, hiển thị bình thường
            ax2.text(p.get_x() + p.get_width()/2., val + 0.05, f'{val:.1f} MB', 
                     fontsize=11, fontweight='bold', color='#333', ha='center', va='bottom')

    plt.title('Bộ Nhớ Tiêu Thụ Đỉnh Trung Bình\n(Cắt ngọn ở mức 2MB để hiển thị chi tiết)', fontsize=16, fontweight='bold', pad=20, color='#1F2937')
    plt.ylabel('Bộ nhớ (MB)', fontsize=12, color='#4B5563')
    plt.xlabel('')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'Average_Memory_Chart.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # =========================================================
    # 3. Biểu đồ đường: Biến động thời gian - CẬP NHẬT TRẦN 10s
    # =========================================================
    plt.figure(figsize=(12, 6.5))
    
    ax3 = sns.lineplot(data=df, x='Test Case', y='Time (seconds)', hue='Algorithm', 
                       marker='o', markersize=8, linewidth=2.5, palette=palette, hue_order=unique_algos)
    
    ax3.get_legend().remove()
    
    Y_MAX_LIMIT = 10  # Đã giảm từ 50s xuống 10s
    ax3.set_ylim(-0.5, Y_MAX_LIMIT + 1)

    plt.axhline(y=Y_MAX_LIMIT, color='#9CA3AF', linestyle='--', linewidth=1.5, zorder=0)
    plt.text(x=-0.2, y=Y_MAX_LIMIT + 0.2, s='Ngưỡng hiển thị đồ thị (10s)', color='#6B7280', fontsize=9, fontstyle='italic')

    for algo in unique_algos:
        algo_data = df[df['Algorithm'] == algo].reset_index(drop=True)
        if algo_data.empty: continue
            
        color = ax3.lines[list(unique_algos).index(algo)].get_color()
        
        for idx, row in algo_data.iterrows():
            if row['Time (seconds)'] > Y_MAX_LIMIT:
                plt.text(x=idx, y=Y_MAX_LIMIT + 0.2, s=f"{row['Time (seconds)']:.0f}s", 
                         color='white', fontweight='bold', fontsize=9, ha='center', va='bottom',
                         bbox=dict(facecolor=color, edgecolor='none', boxstyle='round,pad=0.3'))

        last_x_idx = len(algo_data) - 1
        last_y_val = algo_data['Time (seconds)'].iloc[-1]
        
        display_y = min(last_y_val, Y_MAX_LIMIT)
        
        plt.text(x=last_x_idx + 0.15, y=display_y, s=algo, 
                 color=color, fontweight='bold', fontsize=11, va='center')

    plt.xlim(-0.5, len(df['Test Case'].unique()) + 1.5)
    plt.title('Biến Động Thời Gian Chạy Qua Các Test Case\n(Cắt ngọn ở mức 10s để hiển thị chi tiết)', 
              fontsize=16, fontweight='bold', pad=20, color='#1F2937')
    plt.ylabel('Thời gian (giây)', fontsize=12, color='#4B5563')
    plt.xlabel('Test Case', fontsize=12, color='#4B5563')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'Time_Per_Testcase_Chart.png'), dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✨ Hoàn tất! Các biểu đồ đã được lưu tại '{output_dir}/'")

if __name__ == '__main__':
    plot_benchmark_results()
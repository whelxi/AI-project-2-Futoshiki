import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np

def plot_benchmark_results(csv_filename='Benchmark_Results.csv'):
    if not os.path.exists(csv_filename):
        print(f"File '{csv_filename}' not found. Please run the benchmark script first to generate data.")
        return

    df = pd.read_csv(csv_filename)

    if 'File Name' in df.columns:
        df['Test Case'] = df['File Name'].str.replace('input-', '', regex=False).str.replace('.txt', '', regex=False)
    else:
        df['Test Case'] = df.index.astype(str) 

    sns.set_theme(style="whitegrid", font_scale=1.1)
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.spines.right'] = False
    
    output_dir = 'Charts'
    os.makedirs(output_dir, exist_ok=True)

    print("Generating Designer-standard charts...")
    plt.figure(figsize=(10, 6))
    
    avg_time = df.groupby('Algorithm')['Time (seconds)'].mean().reset_index()
    avg_time = avg_time.sort_values(by='Time (seconds)') # Sort fastest to slowest
    
    ax1 = sns.barplot(data=avg_time, x='Algorithm', y='Time (seconds)', palette='crest')
    
    for container in ax1.containers:
        ax1.bar_label(container, fmt='%.3f s', padding=5, fontsize=11, color='#333333')

    plt.title('Average Runtime (Lower is better)', fontsize=15, fontweight='bold', pad=20)
    plt.ylabel('Time (seconds)', fontsize=12, color='#555555')
    plt.xlabel('') # Remove 'Algorithm' as it's self-explanatory
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'Average_Time_Chart.png'), dpi=300, bbox_inches='tight')
    plt.close()

    plt.figure(figsize=(10, 6))
    
    avg_mem = df.groupby('Algorithm')['Memory Peak (MB)'].mean().reset_index()
    avg_mem = avg_mem.sort_values(by='Memory Peak (MB)')
    
    ax2 = sns.barplot(data=avg_mem, x='Algorithm', y='Memory Peak (MB)', palette='flare')
    
    for container in ax2.containers:
        ax2.bar_label(container, fmt='%.1f MB', padding=5, fontsize=11, color='#333333')

    plt.title('Average Peak Memory Consumption', fontsize=15, fontweight='bold', pad=20)
    plt.ylabel('Memory (MB)', fontsize=12, color='#555555')
    plt.xlabel('')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'Average_Memory_Chart.png'), dpi=300, bbox_inches='tight')
    plt.close()

    plt.figure(figsize=(12, 6))
    
    ax3 = sns.lineplot(data=df, x='Test Case', y='Time (seconds)', hue='Algorithm', 
                       marker='o', markersize=8, linewidth=2.5, palette='tab10')
    
    ax3.set_yscale('log')
    
    ax3.grid(False)

    plt.legend(title='Algorithm', bbox_to_anchor=(1.05, 1), loc='upper left', frameon=False)
    
    x_categories = list(df['Test Case'].unique())

    timeouts = df[df['Time (seconds)'] >= 300]
    for _, row in timeouts.iterrows():
        try:
            x_idx = x_categories.index(row['Test Case'])
            plt.scatter(x_idx, row['Time (seconds)'], color='red', marker='X', s=120, zorder=5)
            plt.annotate('TIMEOUT\n(5m+)', 
                         xy=(x_idx, row['Time (seconds)']),
                         xytext=(0, 15), textcoords='offset points',
                         color='red', fontweight='bold', ha='center', fontsize=10)
        except ValueError:
            pass

    plt.title('Runtime Variation Across Test Cases (Log Scale)', fontsize=15, fontweight='bold', pad=20)
    plt.ylabel('Runtime (seconds, log scale)', fontsize=12, color='#555555')
    plt.xlabel('Test Case', fontsize=12, color='#555555')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'Time_Per_Testcase_Chart.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    plt.figure(figsize=(10, 6))
    
    if 'Status' in df.columns:
        status_counts = df.groupby(['Algorithm', 'Status']).size().unstack(fill_value=0)
        
        color_map = []
        for col in status_counts.columns:
            if str(col).lower() in ['success', 'passed', 'ok']:
                color_map.append('#2ecc71') # Green
            elif str(col).lower() in ['timeout']:
                color_map.append('#f1c40f') # Yellow
            else:
                color_map.append('#e74c3c') # Red

        if not color_map: # Fallback
            color_map = sns.color_palette("Set2", len(status_counts.columns))

        ax4 = status_counts.plot(kind='bar', stacked=True, color=color_map, figsize=(10, 6), edgecolor='white')
        
        plt.title('Algorithm Success Rate', fontsize=15, fontweight='bold', pad=20)
        plt.ylabel('Number of Test Cases', fontsize=12, color='#555555')
        plt.xlabel('')
        plt.xticks(rotation=0) 
        
        plt.legend(title='Status', frameon=False, bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'Success_Rate_Chart.png'), dpi=300, bbox_inches='tight')
        plt.close()

    plt.figure(figsize=(10, 6))
    
    if 'Memory Avg (MB)' in df.columns:
        avg_avg_mem = df.groupby('Algorithm')['Memory Avg (MB)'].mean().reset_index()
        avg_avg_mem = avg_avg_mem.sort_values(by='Memory Avg (MB)')
        
        ax5 = sns.barplot(data=avg_avg_mem, x='Algorithm', y='Memory Avg (MB)', palette='mako')
        
        for container in ax5.containers:
            ax5.bar_label(container, fmt='%.4f MB', padding=5, fontsize=11, color='#333333')

        plt.title('Average Average Memory Consumption', fontsize=15, fontweight='bold', pad=20)
        plt.ylabel('Memory (MB)', fontsize=12, color='#555555')
        plt.xlabel('')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'Average_Avg_Memory_Chart.png'), dpi=300, bbox_inches='tight')
        plt.close()

    print(f"Done! charts have been saved to '{output_dir}/'")

if __name__ == '__main__':
    plot_benchmark_results()
import os
import glob
import time
import tracemalloc
import csv
import game as out_module

class FutoshikiBackwardAgent:
    def __init__(self, game):
        self.game = game
        self.n = game.n
        self.domains = [
            [
                set(range(1, self.n + 1)) if game.grid[r][c] == 0 else {game.grid[r][c]}
                for c in range(self.n)
            ]
            for r in range(self.n)
        ]

    def _is_consistent(self, r, c, val):
        for i in range(self.n):
            if self.game.grid[r][i] == val or self.game.grid[i][c] == val:
                return False
        
        hor, ver = self.game.horizontal, self.game.vertical
        if c > 0 and self.game.grid[r][c-1] != 0:
            if hor[r][c-1] == 1 and self.game.grid[r][c-1] >= val: return False
            if hor[r][c-1] == -1 and self.game.grid[r][c-1] <= val: return False
        if c < self.n - 1 and self.game.grid[r][c+1] != 0:
            if hor[r][c] == 1 and val >= self.game.grid[r][c+1]: return False
            if hor[r][c] == -1 and val <= self.game.grid[r][c+1]: return False
        if r > 0 and self.game.grid[r-1][c] != 0:
            if ver[r-1][c] == 1 and self.game.grid[r-1][c] >= val: return False
            if ver[r-1][c] == -1 and self.game.grid[r-1][c] <= val: return False
        if r < self.n - 1 and self.game.grid[r+1][c] != 0:
            if ver[r][c] == 1 and val >= self.game.grid[r+1][c]: return False
            if ver[r][c] == -1 and val <= self.game.grid[r+1][c]: return False
        return True

    def backward_chaining(self):
        query = self._get_unassigned_goal()
        if not query:
            return True 

        r, c = query
        
        for val in sorted(list(self.domains[r][c])):
            if self._is_consistent(r, c, val):
                self.game.grid[r][c] = val
                
                if self.backward_chaining():
                    return True
                
                self.game.grid[r][c] = 0

        return False

    def _get_unassigned_goal(self):
        best_cell = None
        min_size = self.n + 1
        for i in range(self.n):
            for j in range(self.n):
                if self.game.grid[i][j] == 0:
                    if len(self.domains[i][j]) < min_size:
                        min_size = len(self.domains[i][j])
                        best_cell = (i, j)
        return best_cell

    def solve(self):
        return self.backward_chaining()

def main():
    input_dir = 'Inputs'
    output_dir = 'Outputs'
    csv_filename = 'Result_Backward.csv'

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    input_files = glob.glob(os.path.join(input_dir, 'input-*.txt'))
    input_files.sort()
    
    if not input_files:
        print(f"Not found: '{input_dir}'.")
        return

    with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['File Name', 'Time (seconds)', 'Memory Peak (MB)', 'Status']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for in_path in input_files:
            filename = os.path.basename(in_path)
            out_filename = filename.replace('input-', 'output-')
            out_path = os.path.join(output_dir, out_filename)

            print(f"Run Backward Chaining: {filename}...")
            
            try:
                game = out_module.read_input(in_path)
                agent = FutoshikiBackwardAgent(game)

                tracemalloc.start()
                start_time = time.time()
                
                is_solved = agent.solve()
                
                end_time = time.time()
                current_mem, peak_mem = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                run_time = end_time - start_time
                peak_mem_mb = peak_mem / (1024 * 1024)

                if is_solved:
                    out_module.print_output(out_path, game)
                    status = "Success"
                    print(f" -> Solved! Time: {run_time:.4f}s | Memory: {peak_mem_mb:.4f} MB")
                else:
                    status = "Failed"
                    print(f" -> No solution found.")

                writer.writerow({
                    'File Name': filename,
                    'Time (seconds)': round(run_time, 4),
                    'Memory Peak (MB)': round(peak_mem_mb, 4),
                    'Status': status
                })

            except Exception as e:
                print(f"error: {filename} - {e}")
                writer.writerow({
                    'File Name': filename,
                    'Time (seconds)': 0,
                    'Memory Peak (MB)': 0,
                    'Status': f"Error: {e}"
                })
                
            print("-" * 40)
            
    print(f"\n=> {csv_filename}")

if __name__ == '__main__':
    main()
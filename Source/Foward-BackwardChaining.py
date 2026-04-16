import os
import glob
import time
import tracemalloc
import csv
import game as out_module

class FutoshikiFOLAgent:
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

    def forward_chaining(self):
        changed = True
        while changed:
            changed = False
            
            for r in range(self.n):
                for c in range(self.n):
                    if len(self.domains[r][c]) == 1:
                        val = list(self.domains[r][c])[0]
                        for i in range(self.n):
                            if i != c and val in self.domains[r][i]:
                                self.domains[r][i].remove(val)
                                changed = True
                            if i != r and val in self.domains[i][c]:
                                self.domains[i][c].remove(val)
                                changed = True

            for r in range(self.n):
                for c in range(self.n):
                    if c < self.n - 1 and self.game.horizontal[r][c] != 0:
                        if self._apply_inequality_axiom(r, c, r, c + 1, self.game.horizontal[r][c] == 1):
                            changed = True
                    if r < self.n - 1 and self.game.vertical[r][c] != 0:
                        if self._apply_inequality_axiom(r, c, r + 1, c, self.game.vertical[r][c] == 1):
                            changed = True

            for r in range(self.n):
                for c in range(self.n):
                    if not self.domains[r][c]:
                        return False 
        
        self._synchronize_grid()
        return True

    def _apply_inequality_axiom(self, r1, c1, r2, c2, is_less_than):
        changed = False
        dom1, dom2 = self.domains[r1][c1], self.domains[r2][c2]
        
        if is_less_than:
            new_d1 = {v for v in dom1 if v < max(dom2)}
            new_d2 = {v for v in dom2 if v > min(dom1)}
        else:
            new_d1 = {v for v in dom1 if v > min(dom2)}
            new_d2 = {v for v in dom2 if v < max(dom1)}

        if len(new_d1) < len(dom1):
            self.domains[r1][c1] = new_d1
            changed = True
        if len(new_d2) < len(dom2):
            self.domains[r2][c2] = new_d2
            changed = True
        return changed

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

    def _synchronize_grid(self):
        for r in range(self.n):
            for c in range(self.n):
                if len(self.domains[r][c]) == 1:
                    self.game.grid[r][c] = list(self.domains[r][c])[0]

    def solve(self):
        self.forward_chaining()
        
        is_complete = all(all(cell != 0 for cell in row) for row in self.game.grid)
        if not is_complete:
            return self.backward_chaining()
        return True

def main():
    input_dir = 'Inputs'
    output_dir = 'Outputs'
    csv_filename = 'Tracking-Logic.csv'

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

            print(f"Run Logic Agent: {filename}...")
            
            try:
                game = out_module.read_input(in_path)
                agent = FutoshikiFOLAgent(game)

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
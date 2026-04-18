import os
import glob
import time
import tracemalloc
import csv
import game as out_module

class FutoshikiForwardAgent:
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
        dom1, dom2 = self.domains[r1][c1], self.domains[r2][c2]
        
        if not dom1 or not dom2:
            return False
            
        changed = False
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

    def _synchronize_grid(self):
        for r in range(self.n):
            for c in range(self.n):
                if len(self.domains[r][c]) == 1:
                    self.game.grid[r][c] = list(self.domains[r][c])[0]

    def solve(self):
        self.forward_chaining()
        is_complete = all(all(cell != 0 for cell in row) for row in self.game.grid)
        return is_complete

def main():
    input_dir = 'Inputs'
    output_dir = 'Outputs'
    csv_filename = 'Result_Forward.csv'

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

            print(f"Run Forward Chaining: {filename}...")
            
            try:
                game = out_module.read_input(in_path)
                agent = FutoshikiForwardAgent(game)

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
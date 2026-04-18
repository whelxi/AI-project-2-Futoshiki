# new_forward_backward_chaining.py
import os
import glob
import time
import tracemalloc
import csv
import game as out_module

class Agent:
    def __init__(self, game):
        self.game = game
        self.n = game.n
        
        # Knowledge Base stored as True Facts and Rules (Implications)
        self.kb_facts = set() 
        self.kb_rules = []    # List of tuples: ( [premise_callbacks], conclusion_callback )

        # For quick state tracking
        self.cell_domains = {}
        for r in range(self.n):
            for c in range(self.n):
                self.cell_domains[(r, c)] = set(range(1, self.n + 1))

    def _add_fact(self, r, c, val):
        """Adds a proven fact to the KB and updates domains."""
        fact = f"Val({r},{c},{val})"
        if fact not in self.kb_facts:
            self.kb_facts.add(fact)
            self.cell_domains[(r, c)] = {val}
            return True
        return False

    def _remove_from_domain(self, r, c, val):
        """Deduces NotVal(r,c,val). If domain hits 1, triggers a new Fact."""
        if val in self.cell_domains[(r, c)]:
            self.cell_domains[(r, c)].remove(val)
            if len(self.cell_domains[(r, c)]) == 0:
                raise ValueError("Contradiction found!")
            if len(self.cell_domains[(r, c)]) == 1:
                # Modus Ponens: All other options false -> this option is True
                last_val = list(self.cell_domains[(r, c)])[0]
                return [(r, c, last_val)]
        return []

    def setup_horn_clauses(self):
        """
        Translates constraints into specific inference rules (Horn clauses)
        Structure: If Premises are True -> Deduce Conclusion
        """
        # Load initial facts from the board
        for r in range(self.n):
            for c in range(self.n):
                val = self.game.grid[r][c]
                if val != 0:
                    self._add_fact(r, c, val)

    def forward_chaining(self):
        """
        Applies Modus Ponens exhaustively. 
        Takes known facts and propagates them through domain restrictions.
        """
        agenda = list(self.kb_facts)
        processed = set()

        try:
            while agenda:
                fact_str = agenda.pop(0)
                if fact_str in processed: continue
                processed.add(fact_str)

                # Parse fact: "Val(r,c,v)"
                parts = fact_str.replace("Val(", "").replace(")", "").split(",")
                r, c, v = int(parts[0]), int(parts[1]), int(parts[2])

                new_deductions = []

                # Rule: Val(r,c,v) -> NotVal(row_peers)
                for i in range(self.n):
                    if i != c: new_deductions.extend(self._remove_from_domain(r, i, v))
                
                # Rule: Val(r,c,v) -> NotVal(col_peers)
                for i in range(self.n):
                    if i != r: new_deductions.extend(self._remove_from_domain(i, c, v))

                # Rule: Inequality Constraints (Modus Ponens application)
                # Check Horizontal
                if c < self.n - 1 and self.game.horizontal[r][c] != 0:
                    constraint = self.game.horizontal[r][c]
                    for neighbor_v in list(self.cell_domains[(r, c+1)]):
                        if constraint == 1 and not (v < neighbor_v): # Left < Right
                            new_deductions.extend(self._remove_from_domain(r, c+1, neighbor_v))
                        elif constraint == -1 and not (v > neighbor_v): # Left > Right
                            new_deductions.extend(self._remove_from_domain(r, c+1, neighbor_v))
                            
                if c > 0 and self.game.horizontal[r][c-1] != 0:
                    constraint = self.game.horizontal[r][c-1]
                    for neighbor_v in list(self.cell_domains[(r, c-1)]):
                        if constraint == 1 and not (neighbor_v < v): # Left < Right
                            new_deductions.extend(self._remove_from_domain(r, c-1, neighbor_v))
                        elif constraint == -1 and not (neighbor_v > v): # Left > Right
                            new_deductions.extend(self._remove_from_domain(r, c-1, neighbor_v))

                # Check Vertical
                if r < self.n - 1 and self.game.vertical[r][c] != 0:
                    constraint = self.game.vertical[r][c]
                    for neighbor_v in list(self.cell_domains[(r+1, c)]):
                        if constraint == 1 and not (v < neighbor_v): # Top < Bottom
                            new_deductions.extend(self._remove_from_domain(r+1, c, neighbor_v))
                        elif constraint == -1 and not (v > neighbor_v): # Top > Bottom
                            new_deductions.extend(self._remove_from_domain(r+1, c, neighbor_v))

                if r > 0 and self.game.vertical[r-1][c] != 0:
                    constraint = self.game.vertical[r-1][c]
                    for neighbor_v in list(self.cell_domains[(r-1, c)]):
                        if constraint == 1 and not (neighbor_v < v): # Top < Bottom
                            new_deductions.extend(self._remove_from_domain(r-1, c, neighbor_v))
                        elif constraint == -1 and not (neighbor_v > v): # Top > Bottom
                            new_deductions.extend(self._remove_from_domain(r-1, c, neighbor_v))

                # Add deduced facts to agenda
                for new_r, new_c, new_v in new_deductions:
                    if self._add_fact(new_r, new_c, new_v):
                        agenda.append(f"Val({new_r},{new_c},{new_v})")

            return True # FC completed without contradiction
            
        except ValueError:
            return False # Contradiction detected during Modus Ponens

    def backward_chaining(self, cell_idx=0):
        """
        Prolog-style Backward Chaining (SLD Resolution emulation).
        Goal: Prove Solved() :- Prove(Val(0,0,V00)), Prove(Val(0,1,V01))...
        """
        if cell_idx == self.n * self.n:
            return True # Base Case: All goals proven!

        r = cell_idx // self.n
        c = cell_idx % self.n

        # If already proven by Forward Chaining
        if len(self.cell_domains[(r, c)]) == 1:
            return self.backward_chaining(cell_idx + 1)

        # SLD Resolution: Try to unify goal Val(r,c,?) with remaining domain values
        possible_values = list(self.cell_domains[(r, c)])
        
        for val in possible_values:
            # Snapshot State
            snapshot_domains = {k: set(v) for k, v in self.cell_domains.items()}
            snapshot_facts = set(self.kb_facts)

            # Hypothesis: We assert the goal is true, and verify it doesn't break rules
            self.cell_domains[(r, c)] = {val}
            self.kb_facts.add(f"Val({r},{c},{val})")
            
            # Use FC to check consistency of this hypothesis (Constraint Logic Programming)
            if self.forward_chaining():
                if self.backward_chaining(cell_idx + 1):
                    return True # Goal fully proven!

            # Backtrack: Hypothesis was false
            self.cell_domains = snapshot_domains
            self.kb_facts = snapshot_facts
            
            # Since hypothesis was false, we deduce NotVal
            try:
                self._remove_from_domain(r, c, val)
                self.forward_chaining() # Propagate the failure
            except ValueError:
                pass # Already backtracking, ignore

        return False # Could not prove any goal

    def _sync_grid(self):
        for r in range(self.n):
            for c in range(self.n):
                if len(self.cell_domains[(r, c)]) == 1:
                    self.game.grid[r][c] = list(self.cell_domains[(r, c)])[0]

    def solve(self):
        self.setup_horn_clauses()
        
        # 1. Forward Chaining (Modus Ponens)
        if not self.forward_chaining():
            return False 
            
        # 2. Backward Chaining (SLD Resolution / Goal Proving)
        if not self.backward_chaining():
            return False
            
        self._sync_grid()
        return True

# -------------------------------------------------------------------
# MAIN EXECUTION
# -------------------------------------------------------------------
"""def main():
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

            print(f"Run True Logic Agent: {filename}...")
            
            try:
                game = out_module.read_input(in_path)
                agent = Agent(game)

                tracemalloc.start()
                start_time = time.time()
                
                is_solved = agent.solve()
                
                end_time = time.time()
                current_mem, peak_mem = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                run_time = end_time - start_time
                peak_mem_mb = peak_mem / (1024 * 1024)

                if is_solved:
                    out_module.print_output(out_path, game, agent.game.grid)
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
                
            print("-" * 40)

if __name__ == '__main__':
    main()"""
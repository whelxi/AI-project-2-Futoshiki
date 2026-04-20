import os
import glob
import time
import tracemalloc
import csv
import sys
from collections import deque
import game as out_module
from kb import Term, Predicate, Rule, is_variable, unify, unify_var

sys.setrecursionlimit(5000)

class FutoshikiFOLAgent:
    def __init__(self, game):
        self.game = game
        self.N = game.n
        self.rules = []          
        self.static_facts = []   

    def T(self, name, is_var=False):
        return Term(str(name), is_var)

    def P(self, name, args):
        return Predicate(name, args)

    def build_kb(self):
        """Xây dựng FOL KB bằng các luật chứa Biến (Variables) thay vì hằng số"""
        N = self.N
        R, C, V, V1, V2 = [self.T(n, True) for n in ["R", "C", "V", "V1", "V2"]]
        R1, C1, R2, C2 = [self.T(n, True) for n in ["R1", "C1", "R2", "C2"]]

        for a in range(N):
            for b in range(N):
                if a != b:
                    self.static_facts.append(self.P("DiffCoord", [self.T(a), self.T(b)]))
        
        for a in range(1, N + 1):
            for b in range(1, N + 1):
                if a != b:
                    self.static_facts.append(self.P("DiffVal", [self.T(a), self.T(b)]))
        
        for a in range(1, N + 1):
            for b in range(1, N + 1):
                if a <= b: self.static_facts.append(self.P("LessThanEq", [self.T(a), self.T(b)]))
                if a >= b: self.static_facts.append(self.P("GreaterThanEq", [self.T(a), self.T(b)]))

        for r in range(N):
            for c in range(N):
                if c < N - 1 and self.game.horizontal[r][c] != 0:
                    if self.game.horizontal[r][c] == 1:   # (r,c) < (r,c+1)
                        self.static_facts.append(self.P("LessThanCell", [self.T(r), self.T(c), self.T(r), self.T(c+1)]))
                    elif self.game.horizontal[r][c] == 2: # (r,c) > (r,c+1)
                        self.static_facts.append(self.P("LessThanCell", [self.T(r), self.T(c+1), self.T(r), self.T(c)]))
                if r < N - 1 and self.game.vertical[r][c] != 0:
                    if self.game.vertical[r][c] == 1:   # (r,c) < (r+1,c)
                        self.static_facts.append(self.P("LessThanCell", [self.T(r), self.T(c), self.T(r+1), self.T(c)]))
                    elif self.game.vertical[r][c] == 2: # (r+1,c) < (r,c)
                        self.static_facts.append(self.P("LessThanCell", [self.T(r+1), self.T(c), self.T(r), self.T(c)]))

        self.rules.append(Rule(self.P("NotVal", [R, C, V2]),
                               [self.P("Val", [R, C, V1]), self.P("DiffVal", [V1, V2])]))

        self.rules.append(Rule(self.P("NotVal", [R2, C, V]),
                               [self.P("Val", [R1, C, V]), self.P("DiffCoord", [R1, R2])]))
        self.rules.append(Rule(self.P("NotVal", [R, C2, V]),
                               [self.P("Val", [R, C1, V]), self.P("DiffCoord", [C1, C2])]))

        self.rules.append(Rule(self.P("NotVal", [R2, C2, V2]),
                               [self.P("LessThanCell", [R1, C1, R2, C2]),
                                self.P("Val", [R1, C1, V1]),
                                self.P("LessThanEq", [V2, V1])]))
        
        self.rules.append(Rule(self.P("NotVal", [R1, C1, V1]),
                               [self.P("LessThanCell", [R1, C1, R2, C2]),
                                self.P("Val", [R2, C2, V2]),
                                self.P("GreaterThanEq", [V1, V2])]))

    def match_premises(self, premises, known_facts, theta):
        if not premises:
            yield theta
            return
        
        first = premises[0]
        candidates = known_facts.get(first.name, [])
        for fact in candidates:
            new_theta = unify(first, fact, theta.copy())
            if new_theta is not None:
                yield from self.match_premises(premises[1:], known_facts, new_theta)

    def run_forward_chaining(self, agenda_list, inferred_set, known_facts):
        agenda = deque(agenda_list)
        queued_set = set(str(f) for f in agenda_list)

        while agenda:
            fact = agenda.popleft()
            fact_str = str(fact)
            
            if fact_str in inferred_set:
                continue

            # Đánh dấu đã chứng minh
            inferred_set.add(fact_str)
            if fact.name not in known_facts:
                known_facts[fact.name] = []
            known_facts[fact.name].append(fact)

            if fact.name == "Val":
                opp = self.P("NotVal", fact.args)
                if str(opp) in inferred_set: return False
            elif fact.name == "NotVal":
                opp = self.P("Val", fact.args)
                if str(opp) in inferred_set: return False

            if fact.name == "NotVal":
                r_name = fact.args[0].name
                c_name = fact.args[1].name
                
                not_vals = [f for f in known_facts.get("NotVal", []) 
                            if f.args[0].name == r_name and f.args[1].name == c_name]
                
                if len(not_vals) == self.N - 1:
                    excluded = {int(f.args[2].name) for f in not_vals}
                    for v in range(1, self.N + 1):
                        if v not in excluded:
                            new_val_fact = self.P("Val", [self.T(r_name), self.T(c_name), self.T(v)])
                            head_str = str(new_val_fact)
                            if head_str not in inferred_set and head_str not in queued_set:
                                queued_set.add(head_str)
                                agenda.append(new_val_fact)
                            break

            for rule in self.rules:
                for i, p in enumerate(rule.body):
                    if p.name != fact.name:
                        continue
                    
                    theta = unify(p, fact, {})
                    if theta is not None:
                        other_premises = rule.body[:i] + rule.body[i+1:]
                        for final_theta in self.match_premises(other_premises, known_facts, theta):
                            head_inst = rule.head.substitute(final_theta)
                            head_str = str(head_inst)
                            
                            if head_str not in inferred_set and head_str not in queued_set:
                                queued_set.add(head_str)
                                agenda.append(head_inst)
        return True

    def backtrack(self, inferred_set, known_facts):
        N = self.N
        is_solved = True
        
        for r in range(N):
            for c in range(N):
                assigned = False
                for v in range(1, N + 1):
                    if f"Val({r},{c},{v})" in inferred_set:
                        assigned = True
                        self.game.grid[r][c] = v
                        break
                if not assigned:
                    is_solved = False
                    
        if is_solved: return True

        best_cell = None
        min_domain = N + 1
        best_domain = []

        for r in range(N):
            for c in range(N):
                assigned = False
                domain = []
                for v in range(1, N + 1):
                    if f"Val({r},{c},{v})" in inferred_set:
                        assigned = True
                        break
                    if f"NotVal({r},{c},{v})" not in inferred_set:
                        domain.append(v)
                        
                if not assigned:
                    if len(domain) < min_domain:
                        min_domain = len(domain)
                        best_cell = (r, c)
                        best_domain = domain

        if best_cell is None or min_domain == 0:
            return False 

        r, c = best_cell
        for v in best_domain:
            new_inferred = inferred_set.copy()
            new_known_facts = {k: v_list.copy() for k, v_list in known_facts.items()}
            agenda = [self.P("Val", [self.T(r), self.T(c), self.T(v)])]
            if self.run_forward_chaining(agenda, new_inferred, new_known_facts):
                if self.backtrack(new_inferred, new_known_facts):
                    return True
                    
        return False

    def solve(self):
        self.build_kb()
        
        inferred_set = set()
        known_facts = {}
        
        for fact in self.static_facts:
            if fact.name not in known_facts:
                known_facts[fact.name] = []
            known_facts[fact.name].append(fact)
            inferred_set.add(str(fact))

        agenda = []
        for r in range(self.N):
            for c in range(self.N):
                val = self.game.grid[r][c]
                if val != 0:
                    agenda.append(self.P("Val", [self.T(r), self.T(c), self.T(val)]))

        if not self.run_forward_chaining(agenda, inferred_set, known_facts):
            return False
            
        return self.backtrack(inferred_set, known_facts)


def main():
    input_dir = 'Inputs'
    output_dir = 'Outputs'
    csv_filename = 'Result_FOL.csv'

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

            print(f"Run True FOL Forward Chaining: {filename}...")
            
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
                    print(f" -> No solution found (Contradiction).")

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
            
    print(f"\n=> Report exported to {csv_filename}")

if __name__ == '__main__':
    main()
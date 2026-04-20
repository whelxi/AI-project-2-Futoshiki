import os
import glob
import time
import tracemalloc
import csv
import game as out_module
# Thêm Rule vào import
from kb import Term, Predicate, Rule

class SLDProver:
    def __init__(self, facts, rules=None):
        """
        Khởi tạo SLD prover với Knowledge Base gồm các Sự thật (Facts) và Luật (Rules).
        """
        self.facts = facts
        self.rules = rules if rules is not None else []

    def unify_terms(self, t1, t2, theta):
        while t1.is_var and t1.name in theta:
            t1 = theta[t1.name]
        while t2.is_var and t2.name in theta:
            t2 = theta[t2.name]

        if t1.name == t2.name and t1.is_var == t2.is_var:
            return theta
        
        if t1.is_var:
            new_theta = theta.copy()
            new_theta[t1.name] = t2
            return new_theta
            
        if t2.is_var:
            new_theta = theta.copy()
            new_theta[t2.name] = t1
            return new_theta
            
        return None

    def unify_preds(self, p1, p2, theta):
        if p1.name != p2.name or len(p1.args) != len(p2.args):
            return None
        
        curr_theta = theta
        for a1, a2 in zip(p1.args, p2.args):
            curr_theta = self.unify_terms(a1, a2, curr_theta)
            if curr_theta is None:
                return None
        return curr_theta

    def resolve(self, goals, theta):
        if not goals:
            return theta  
        
        goal = goals[0]
        rest = goals[1:]
        
        # 1. SLD Resolution với các Facts (Sự thật)
        for fact in self.facts:
            new_theta = self.unify_preds(goal, fact, theta)
            if new_theta is not None:
                result = self.resolve(rest, new_theta)
                if result is not None:
                    return result
                    
        # 2. SLD Resolution với các Rules (Luật)
        for rule in self.rules:
            # Unify mục tiêu hiện tại với phần Đầu (Head) của luật
            new_theta = self.unify_preds(goal, rule.head, theta)
            if new_theta is not None:
                # Nếu khớp, thay thế mục tiêu bằng phần Thân (Body) của luật và đẩy vào danh sách chờ
                new_goals = rule.body + rest
                result = self.resolve(new_goals, new_theta)
                if result is not None:
                    return result
                    
        return None 


class FutoshikiFOLAgent:
    def __init__(self, game):
        self.game = game
        self.n = game.n
        self.kb_facts = []
        self._build_knowledge_base()

    def _build_knowledge_base(self):
        for i in range(1, self.n + 1):
            self.kb_facts.append(Predicate("Domain", [Term(str(i))]))
        
        for i in range(1, self.n + 1):
            for j in range(1, self.n + 1):
                if i != j:
                    self.kb_facts.append(Predicate("NotEq", [Term(str(i)), Term(str(j))]))
                    
        for i in range(1, self.n + 1):
            for j in range(i + 1, self.n + 1):
                self.kb_facts.append(Predicate("LessThan", [Term(str(i)), Term(str(j))]))

    def solve(self):
        prover = SLDProver(self.kb_facts)
        goals = []
        vars_dict = {}

        for r in range(self.n):
            for c in range(self.n):
                val = self.game.grid[r][c]
                if val != 0:
                    vars_dict[(r, c)] = Term(str(val))
                else:
                    vars_dict[(r, c)] = Term(f"V_{r}_{c}", is_var=True)

        # Xây dựng Rules cho Engine và tạo truy vấn Val(i, j, ?)
        for r in range(self.n):
            for c in range(self.n):
                v = vars_dict[(r, c)]
                body_conditions = []
                
                # Biến chưa biết -> lấy từ Domain
                if v.is_var:
                    body_conditions.append(Predicate("Domain", [v]))

                for prev_c in range(c):
                    body_conditions.append(Predicate("NotEq", [v, vars_dict[(r, prev_c)]]))
                
                for prev_r in range(r):
                    body_conditions.append(Predicate("NotEq", [v, vars_dict[(prev_r, c)]]))

                if c > 0:
                    hor = self.game.horizontal[r][c-1]
                    left_v = vars_dict[(r, c-1)]
                    if hor == 1:     
                        body_conditions.append(Predicate("LessThan", [left_v, v]))
                    elif hor == -1:  
                        body_conditions.append(Predicate("LessThan", [v, left_v]))

                if r > 0:
                    ver = self.game.vertical[r-1][c]
                    top_v = vars_dict[(r-1, c)]
                    if ver == 1:     
                        body_conditions.append(Predicate("LessThan", [top_v, v]))
                    elif ver == -1:  
                        body_conditions.append(Predicate("LessThan", [v, top_v]))

                # Định nghĩa Head của Luật: Val(r, c, v)
                head = Predicate("Val", [Term(str(r)), Term(str(c)), v])
                
                if body_conditions:
                    # Nếu có ràng buộc, thêm vào KB dưới dạng một Rule
                    prover.rules.append(Rule(head, body_conditions))
                else:
                    # Nếu là ô đã có giá trị cố định sẵn và không dính ràng buộc trước đó (ví dụ ô 0,0)
                    prover.facts.append(head)

                # Truy vấn chuẩn đề bài: Query Val(i, j, ?)
                goals.append(Predicate("Val", [Term(str(r)), Term(str(c)), v]))

        # Thực thi SLD Resolution (Conjunction của toàn bộ truy vấn Val trên lưới)
        solution_theta = prover.resolve(goals, {})

        if solution_theta is not None:
            for r in range(self.n):
                for c in range(self.n):
                    if self.game.grid[r][c] == 0:
                        var_name = f"V_{r}_{c}"
                        
                        resolved_term = solution_theta[var_name]
                        while resolved_term.is_var and resolved_term.name in solution_theta:
                            resolved_term = solution_theta[resolved_term.name]
                            
                        self.game.grid[r][c] = int(resolved_term.name)
            return True
        
        return False


def main():
    input_dir = 'Inputs'
    output_dir = 'Outputs'
    csv_filename = 'Result_Backward_FOL.csv'

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

            print(f"Run FOL SLD Resolution: {filename}...")
            
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
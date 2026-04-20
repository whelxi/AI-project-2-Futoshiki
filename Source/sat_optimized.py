from pysat.solvers import Solver
from game import read_input, print_output
from kb import Term, Predicate, And, Or, Not

def get_var(r: int, c: int, v: int, n: int) -> int:
    """
    Maps a (row, column, value) to a unique 1D integer for the SAT solver.
    r: row (0 to n-1)
    c: col (0 to n-1)
    v: value (1 to n)
    Returns an integer > 0.
    """
    return r * n * n + c * n + v

def make_balanced_or(exprs):
    if not exprs: return None
    if len(exprs) == 1: return exprs[0]
    mid = len(exprs) // 2
    return Or(make_balanced_or(exprs[:mid]), make_balanced_or(exprs[mid:]))

def make_balanced_and(exprs):
    if not exprs: return None
    if len(exprs) == 1: return exprs[0]
    mid = len(exprs) // 2
    return And(make_balanced_and(exprs[:mid]), make_balanced_and(exprs[mid:]))

def extract_literals(expr, n):
    if isinstance(expr, Or):
        return extract_literals(expr.left, n) + extract_literals(expr.right, n)
    elif isinstance(expr, Not):
        # Bên trong Not chắc chắn là một Predicate (do đã qua NNF của to_cnf)
        pred = expr.expr
        r, c, v = int(pred.args[0].name), int(pred.args[1].name), int(pred.args[2].name)
        return [-get_var(r, c, v, n)]
    elif isinstance(expr, Predicate):
        r, c, v = int(expr.args[0].name), int(expr.args[1].name), int(expr.args[2].name)
        return [get_var(r, c, v, n)]
    else:
        raise ValueError(f"Unexpected expression type in clause: {type(expr)}")

def extract_clauses(expr, n):
    if isinstance(expr, And):
        return extract_clauses(expr.left, n) + extract_clauses(expr.right, n)
    else:
        # Nếu đã đến tầng Or hoặc Literal, ta đóng gói thành 1 clause
        return [extract_literals(expr, n)]

def solve_futoshiki_optimized(input_file: str, output_file: str) -> dict:
    game = read_input(input_file)
    n = game.n
    formulas = []

    def Val(r, c, v):
        return Predicate("Val", [Term(str(r)), Term(str(c)), Term(str(v))])

    for r in range(n):
        for c in range(n):
            formulas.append(make_balanced_or([Val(r, c, v) for v in range(1, n + 1)]))
            for v1 in range(1, n + 1):
                for v2 in range(v1 + 1, n + 1):
                    formulas.append(Or(Not(Val(r, c, v1)), Not(Val(r, c, v2))))

    for r in range(n):
        for v in range(1, n + 1):
            for c1 in range(n):
                for c2 in range(c1 + 1, n):
                    formulas.append(Or(Not(Val(r, c1, v)), Not(Val(r, c2, v))))

    for c in range(n):
        for v in range(1, n + 1):
            for r1 in range(n):
                for r2 in range(r1 + 1, n):
                    formulas.append(Or(Not(Val(r1, c, v)), Not(Val(r2, c, v))))

    for r in range(n):
        for c in range(n):
            val = game.grid[r][c]
            if val != 0:
                formulas.append(Val(r, c, val))

    for r in range(n):
        for c in range(n - 1):
            if game.horizontal[r][c] == 1:  # Left < Right
                for v in range(1, n + 1):
                    for k in range(1, v + 1):
                        formulas.append(Or(Not(Val(r, c, v)), Not(Val(r, c + 1, k))))
            elif game.horizontal[r][c] == -1:  # Left > Right
                for v in range(1, n + 1):
                    for k in range(v, n + 1):
                        formulas.append(Or(Not(Val(r, c, v)), Not(Val(r, c + 1, k))))

    for r in range(n - 1):
        for c in range(n):
            if game.vertical[r][c] == 1:  # Top < Bottom
                for v in range(1, n + 1):
                    for k in range(1, v + 1):
                        formulas.append(Or(Not(Val(r, c, v)), Not(Val(r + 1, c, k))))
            elif game.vertical[r][c] == -1:  # Top > Bottom
                for v in range(1, n + 1):
                    for k in range(v, n + 1):
                        formulas.append(Or(Not(Val(r, c, v)), Not(Val(r + 1, c, k))))

    full_kb = make_balanced_and(formulas)
    cnf_kb = full_kb.to_cnf()
    clauses = extract_clauses(cnf_kb, n)

    with Solver(name='g3') as solver:
        for clause in clauses:
            solver.add_clause(clause)
        
        if not solver.solve():
            raise ValueError(f"UNSATISFIABLE – no solution found for {input_file}")
            
        solution = solver.get_model()
        
        stats = solver.accum_stats()
        inferences = stats.get('propagations', 0) + stats.get('decisions', 0)
        if inferences == 0:
            inferences = len(clauses)

    solved_grid = [[0] * n for _ in range(n)]
    for lit in solution:
        if lit > 0:
            lit_zero_indexed = lit - 1
            v = (lit_zero_indexed % n) + 1
            c = (lit_zero_indexed // n) % n
            r = (lit_zero_indexed // (n * n))
            solved_grid[r][c] = v

    game.grid = solved_grid
    print_output(output_file, game)
    
    return {"clauses": len(clauses), "inferences": inferences}
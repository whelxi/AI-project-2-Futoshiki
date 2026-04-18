from pysat.solvers import Solver
from game import read_input, print_output

def get_var(r: int, c: int, v: int, n: int) -> int:
    """
    Maps a (row, column, value) to a unique 1D integer for the SAT solver.
    r: row (0 to n-1)
    c: col (0 to n-1)
    v: value (1 to n)
    Returns an integer > 0.
    """
    return r * n * n + c * n + v

def solve_futoshiki_optimized(input_file: str, output_file: str) -> dict:
    """Solves Futoshiki using direct CNF encoding, completely bypassing FOL overhead."""
    game = read_input(input_file)
    n = game.n
    clauses = []

    # 1. Cell Constraints: Every cell (r, c) must have exactly one value.
    for r in range(n):
        for c in range(n):
            # At least one value
            clauses.append([get_var(r, c, v, n) for v in range(1, n + 1)])
            # At most one value (pairwise mutual exclusion)
            for v1 in range(1, n + 1):
                for v2 in range(v1 + 1, n + 1):
                    clauses.append([-get_var(r, c, v1, n), -get_var(r, c, v2, n)])

    # 2. Row Constraints: Every value appears exactly once in a row.
    for r in range(n):
        for v in range(1, n + 1):
            # We only need "at most once" here because the cell constraints 
            # and pigeonhole principle will enforce the "at least once".
            for c1 in range(n):
                for c2 in range(c1 + 1, n):
                    clauses.append([-get_var(r, c1, v, n), -get_var(r, c2, v, n)])

    # 3. Column Constraints: Every value appears exactly once in a column.
    for c in range(n):
        for v in range(1, n + 1):
            for r1 in range(n):
                for r2 in range(r1 + 1, n):
                    clauses.append([-get_var(r1, c, v, n), -get_var(r2, c, v, n)])

    # 4. Given Facts: Lock in the pre-filled cells.
    for r in range(n):
        for c in range(n):
            val = game.grid[r][c]
            if val != 0:
                clauses.append([get_var(r, c, val, n)])

    # 5. Horizontal Inequalities
    for r in range(n):
        for c in range(n - 1):
            if game.horizontal[r][c] == 1:  # Left < Right
                for v in range(1, n + 1):
                    # If Left is 'v', Right cannot be <= 'v'
                    for k in range(1, v + 1):
                        clauses.append([-get_var(r, c, v, n), -get_var(r, c + 1, k, n)])
            elif game.horizontal[r][c] == -1:  # Left > Right
                for v in range(1, n + 1):
                    # If Left is 'v', Right cannot be >= 'v'
                    for k in range(v, n + 1):
                        clauses.append([-get_var(r, c, v, n), -get_var(r, c + 1, k, n)])

    # 6. Vertical Inequalities
    for r in range(n - 1):
        for c in range(n):
            if game.vertical[r][c] == 1:  # Top < Bottom
                for v in range(1, n + 1):
                    # If Top is 'v', Bottom cannot be <= 'v'
                    for k in range(1, v + 1):
                        clauses.append([-get_var(r, c, v, n), -get_var(r + 1, c, k, n)])
            elif game.vertical[r][c] == -1:  # Top > Bottom
                for v in range(1, n + 1):
                    # If Top is 'v', Bottom cannot be >= 'v'
                    for k in range(v, n + 1):
                        clauses.append([-get_var(r, c, v, n), -get_var(r + 1, c, k, n)])

    # 7. Solve with PySAT
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

    # 8. Decode the solution back into the grid
    solved_grid = [[0] * n for _ in range(n)]
    for lit in solution:
        if lit > 0:
            # Reverse engineer the variable integer back into r, c, v
            lit_zero_indexed = lit - 1
            v = (lit_zero_indexed % n) + 1
            c = (lit_zero_indexed // n) % n
            r = (lit_zero_indexed // (n * n))
            solved_grid[r][c] = v

    print_output(output_file, game)
    
    return {"clauses": len(clauses), "inferences": inferences}
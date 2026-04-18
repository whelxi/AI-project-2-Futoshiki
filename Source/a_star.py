# astar.py
import heapq
import copy

class AStarNode: 
    def __init__(self, grid, g_cost, game, h_cost=None):
        self.grid = grid
        self.g_cost = g_cost
        self.game = game
        
        if h_cost is None:
           self.h_cost = self.calc_heuristic()
        else:
            self.h_cost = h_cost
            
        self.f_cost = self.g_cost + self.h_cost
    
    def calc_heuristic(self):
        """
        Calculates the heuristic cost.
        h(n) = (Number of empty cells) + (0.01 * total valid choices remaining)
        
        Why the 0.01 fractional part? 
        In CSPs, g(n) + empty_cells is always a constant (Total Cells). 
        This flat f(n) makes A* degrade into BFS. 
        By adding a tiny fraction based on remaining valid choices, we force A* to prioritize states that are closer to being fully constrained (MRV logic), 
        creating a true search gradient while remaining virtually admissible.
        """
        empty_count = 0
        total_valid_choices = 0
        n = self.game.n
        
        for i in range(n):
            for j in range(n):
                if self.grid[i][j] == 0:
                    empty_count += 1
                    # Count how many numbers can legally fit here
                    for val in range(1, n + 1):
                        if is_valid(self.grid, i, j, val, self.game):
                            total_valid_choices += 1
                            
        # If there are empty cells but NO valid choices left, this is a dead end.
        if empty_count > 0 and total_valid_choices == 0:
            return float('inf') 
            
        return empty_count + (0.01 * total_valid_choices)

    def is_goal(self):
        return self.h_cost < 1.0 # Due to the fractional part, goal is < 1, not exactly 0

    def __lt__(self, other):
        return self.f_cost < other.f_cost
        
def is_valid(grid, r, c, val, game):
    n = game.n
    
    # check row and column
    for i in range(n): 
        if grid[r][i] == val:
            return False
        if grid[i][c] == val:
            return False
    
    # check horizontal constraints
    if c > 0 and grid[r][c - 1] != 0: 
        constraint = game.horizontal[r][c - 1]
        if constraint == 1 and not (grid[r][c-1] < val): return False  
        if constraint == -1 and not (grid[r][c-1] > val): return False 
        
    if c < n - 1 and grid[r][c + 1] != 0: 
        constraint = game.horizontal[r][c]
        if constraint == 1 and not (val < grid[r][c+1]): return False
        if constraint == -1 and not (val > grid[r][c+1]): return False
        
    # check vertical constraints
    if (r > 0 and grid[r - 1][c] != 0): 
        constraint = game.vertical[r - 1][c]
        if constraint == 1 and not (grid[r-1][c] < val): return False 
        if constraint == -1 and not (grid[r-1][c] > val): return False 
    
    if (r < n - 1 and grid[r + 1][c] != 0): 
        constraint = game.vertical[r][c]
        if constraint == 1 and not (val < grid[r+1][c]): return False
        if constraint == -1 and not (val > grid[r+1][c]): return False
   
    return True

def get_successors(node, game):
    """Generates successors. Standard A* explores the first available empty cell."""
    successors = []
    n = game.n
    
    empty_r, empty_c = -1, -1
    for i in range(n):
        for j in range(n):
            if node.grid[i][j] == 0:
                empty_r, empty_c = i, j
                break
        if empty_r != -1: break
        
    if empty_r == -1: return successors 

    for val in range(1, n + 1):
        if is_valid(node.grid, empty_r, empty_c, val, game):
            new_grid = copy.deepcopy(node.grid)
            new_grid[empty_r][empty_c] = val
            successors.append(AStarNode(new_grid, node.g_cost + 1, game))
            
    return successors

def solve_futoshiki_astar(game):
    """Main A* execution."""
    start_node = AStarNode(game.grid, 0, game)
    open_list = [start_node]
    closed_set = set()
    
    nodes_expanded = 0

    while open_list:
        current = heapq.heappop(open_list)
        nodes_expanded += 1

        if current.is_goal():
            print(f"Solved! Nodes expanded: {nodes_expanded}")
            game.grid = current.grid 
            return game

        grid_tuple = tuple(tuple(row) for row in current.grid)
        if grid_tuple in closed_set:
            continue
        closed_set.add(grid_tuple)

        for child in get_successors(current, game):
            # Optimization: Don't add dead-ends to the queue
            if child.h_cost != float('inf'):
                heapq.heappush(open_list, child)

    print("No solution found.")
    return None
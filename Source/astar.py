import heapq
import copy

class AStarNode: 
    def __init__(self, grid, g_cost, game, h_cost=None):
        self.grid = grid
        self.g_cost = g_cost
        self.game = game
        if h_cost is None:
            self.h_cost = self.calc_heuristic_1()
        else:
            self.h_cost = h_cost
        self.f_cost = self.g_cost + self.h_cost
    
    def calc_heuristic_1(self):
        # Heuristic 1: Đếm số lượng ô trống (số 0)
        empty_count = sum(row.count(0) for row in self.grid)
        return empty_count

    def calc_heuristic_2(self):
        """
        Heuristic 2 (tối ưu): Đếm số ô trống bị ràng buộc.
        Sử dụng danh sách constrained_cells đã được precompute.
        """
        constrained_empty_count = 0
        for i, j in self.game.constrained_cells:
            if self.grid[i][j] == 0:
                constrained_empty_count += 1
        return constrained_empty_count
        
    def is_goal(self):
        return self.h_cost == 0

    def __lt__(self, other):
        return self.f_cost < other.f_cost
        
def  is_valid(grid, r, c, val, game):
    n = game.n
    
    #check row and column
    for i in range(n): 
        if grid[r][i] == val:
            return False
        if grid[i][c] == val:
            return False
    
    # check horizontal constraints
    # check left 
    if c > 0 and grid[r][c - 1] != 0: 
        constraint = game.horizontal[r][c - 1]
        if constraint == 1 and not (grid[r][c-1] < val): return False  
        if constraint == -1 and not (grid[r][c-1] > val): return False 
        
    # check right
    if c < n - 1 and grid[r][c + 1] != 0: 
        constraint = game.horizontal[r][c]
        if constraint == 1 and not (val < grid[r][c+1]): return False
        if constraint == -1 and not (val > grid[r][c+1]): return False
        
    # check vertical constraints
    # check up
    if (r > 0 and grid[r - 1][c] != 0): 
        constraint = game.vertical[r - 1][c]
        if constraint == 1 and not (grid[r-1][c] < val): return False 
        if constraint == -1 and not (grid[r-1][c] > val): return False 
    
    #check down 
    if (r < n - 1 and grid[r + 1][c] != 0): 
        constraint = game.vertical[r][c]
        if constraint == 1 and not (val < grid[r+1][c]): return False
        if constraint == -1 and not (val > grid[r+1][c]): return False
   
    return True

def get_successors(node, game):
    """Tìm 1 ô trống và sinh ra các trạng thái hợp lệ."""
    successors = []
    n = game.n
    
    # Tìm ô trống đầu tiên (có thể tối ưu bằng cách tìm ô có ít lựa chọn nhất - MRV)
    empty_r, empty_c = -1, -1
    for i in range(n):
        for j in range(n):
            if node.grid[i][j] == 0:
                empty_r, empty_c = i, j
                break
        if empty_r != -1: break
        
    if empty_r == -1: return successors # Không còn ô trống

    # Thử điền các số từ 1 đến N
    for val in range(1, n + 1):
        if is_valid(node.grid, empty_r, empty_c, val, game):
            # Nếu hợp lệ, tạo Node mới
            new_grid = copy.deepcopy(node.grid)
            new_grid[empty_r][empty_c] = val
            successors.append(AStarNode(new_grid, node.g_cost + 1, game))
            
    return successors

def get_successors_straght(node, game):
    """Tìm 1 ô trống (ưu tiên ô có ràng buộc) và sinh ra các trạng thái hợp lệ."""
    successors = []
    n = game.n
    
    best_r, best_c = -1, -1
    
    # Bước 1 (MRV): Ưu tiên tìm các ô trống đang bị kẹp bởi dấu < hoặc >
    for i in range(n):
        for j in range(n):
            if node.grid[i][j] == 0:
                has_constraint = False
                if j > 0 and game.horizontal[i][j-1] != 0: has_constraint = True
                if j < n - 1 and game.horizontal[i][j] != 0: has_constraint = True
                if i > 0 and game.vertical[i-1][j] != 0: has_constraint = True
                if i < n - 1 and game.vertical[i][j] != 0: has_constraint = True
                
                if has_constraint:
                    best_r, best_c = i, j
                    break 
        if best_r != -1: break
        
    # Bước 2: Nếu đã điền xong hết các ô có dấu, mới tìm ô trống tự do bình thường
    if best_r == -1:
        for i in range(n):
            for j in range(n):
                if node.grid[i][j] == 0:
                    best_r, best_c = i, j
                    break
            if best_r != -1: break
            
    # Bảng đã kín (Mặc dù is_goal đã chặn trước, nhưng vẫn nên có bước này)
    if best_r == -1: return successors 

    # Bước 3: Thử điền các số từ 1 đến N
    for val in range(1, n + 1):
        if is_valid(node.grid, best_r, best_c, val, game):
            new_grid = copy.deepcopy(node.grid)
            new_grid[best_r][best_c] = val
            # Tạo Node mới, cộng g_cost lên 1
            successors.append(AStarNode(new_grid, node.g_cost + 1, game))
            
    return successors

def get_successors_mrv(node, game):
    """Tìm ô trống có ít lựa chọn nhất (MRV) và sinh ra các trạng thái hợp lệ."""
    successors = []
    n = game.n
    
    # MRV Heuristic: Tìm ô trống có ít lựa chọn nhất
    best_cell = None
    min_choices = n + 1
    
    for i in range(n):
        for j in range(n):
            if node.grid[i][j] == 0:
                # Đếm số lựa chọn hợp lệ cho ô này
                valid_count = 0
                for val in range(1, n + 1):
                    if is_valid(node.grid, i, j, val, game):
                        valid_count += 1
                
                # Nếu ô này có ít lựa chọn hơn, lưu lại
                if valid_count < min_choices:
                    min_choices = valid_count
                    best_cell = (i, j)
                    
                    # Nếu không có lựa chọn nào, return ngay
                    if min_choices == 0:
                        return successors
    
    if best_cell is None:
        return successors  # Không còn ô trống
    
    empty_r, empty_c = best_cell
    
    # Thử điền các số từ 1 đến N
    for val in range(1, n + 1):
        if is_valid(node.grid, empty_r, empty_c, val, game):
            # Nếu hợp lệ, tạo Node mới
            new_grid = copy.deepcopy(node.grid)
            new_grid[empty_r][empty_c] = val
            successors.append(AStarNode(new_grid, node.g_cost + 1, game))
            
    return successors


def solve_futoshiki_astar(game):
    """Hàm chạy thuật toán A* chính."""
    start_node = AStarNode(game.grid, 0, game)
    open_list = [start_node]
    closed_set = set()
    
    nodes_expanded = 0

    while open_list:
        current = heapq.heappop(open_list)
        nodes_expanded += 1

        if current.is_goal():
            print(f"Solved! Nodes expanded: {nodes_expanded}")
            game.grid = current.grid # Cập nhật kết quả vào game
            return game

        grid_tuple = tuple(tuple(row) for row in current.grid)
        if grid_tuple in closed_set:
            continue
        closed_set.add(grid_tuple)

        for child in get_successors_mrv(current, game):
            child_tuple = tuple(tuple(row) for row in child.grid)
            if child_tuple not in closed_set:
                heapq.heappush(open_list, child)

    print("No solution found.")
    return None
    
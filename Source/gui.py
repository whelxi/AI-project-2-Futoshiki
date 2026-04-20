import streamlit as st
import time
import copy
import heapq

from game import GameInstance
from a_star import AStarNode, get_successors_mrv
from sat_optimized import solve_futoshiki_optimized
import backtracking as bt
import bruteforce as bf
from hybrid_inference import FutoshikiFOLAgent

st.set_page_config(page_title="Futoshiki Solver Visualizer", layout="wide")
st.title("Futoshiki Algorithm Visualizer")

def render_grid_html(game: GameInstance, current_grid=None):
    if current_grid is None:
        current_grid = game.grid
    
    n = game.n
    html = f"<div style='display: grid; grid-template-columns: repeat({n*2-1}, 40px); grid-gap: 5px; justify-content: center; margin-bottom: 20px; font-family: monospace; font-size: 20px; text-align: center; align-items: center;'>"
    
    for r in range(n):
        for c in range(n):
            val = current_grid[r][c]
            text = str(val) if val != 0 else ""
            bg_color = "#4CAF50" if val != 0 else "#2E2E2E" 
            border = "2px solid #FFF" if game.grid[r][c] != 0 else "1px solid #888" 
            
            html += f"<div style='width: 40px; height: 40px; background-color: {bg_color}; border: {border}; border-radius: 5px; line-height: 40px; font-weight: bold; color: white;'>{text}</div>"
            
            if c < n - 1:
                constraint = game.horizontal[r][c]
                symbol = "<" if constraint == 1 else ">" if constraint == -1 else "&nbsp;"
                html += f"<div style='color: #FFC107; font-weight: bold;'>{symbol}</div>"
        
        if r < n - 1:
            for c in range(n):
                constraint = game.vertical[r][c]
                symbol = "^" if constraint == 1 else "v" if constraint == -1 else "&nbsp;"
                html += f"<div style='color: #FFC107; font-weight: bold; height: 30px; display: flex; align-items: center; justify-content: center;'>{symbol}</div>"
                if c < n - 1:
                    html += f"<div></div>" 
                    
    html += "</div>"
    return html

def parse_uploaded_file(uploaded_file):
    content = uploaded_file.getvalue().decode("utf-8")
    lines = content.strip().split('\n')
    n = int(lines[0].strip())
    
    grid = [[0]*n for _ in range(n)]
    horizontal = [[0]*n for _ in range(n)]
    vertical = [[0]*n for _ in range(n)]
    
    d = 0
    for line in lines[1:]:
        if not line.strip(): continue
        row_data = [int(x) for x in line.split(', ')]
        if d < n:
            grid[d] = row_data
        elif d < 2*n:
            horizontal[d - n] = row_data
        else:
            vertical[d - 2*n] = row_data
        d += 1
    return GameInstance(n, grid, horizontal, vertical)

def solve_astar_generator(game):
    start_node = AStarNode(game.grid, 0, game)
    open_list = [start_node]
    closed_set = set()
    nodes_expanded = 0

    while open_list:
        current = heapq.heappop(open_list)
        nodes_expanded += 1

        if nodes_expanded % 10 == 0 or current.is_goal(): 
            yield current.grid, nodes_expanded, current.is_goal()

        if current.is_goal():
            break

        grid_tuple = tuple(tuple(row) for row in current.grid)
        if grid_tuple in closed_set: continue
        closed_set.add(grid_tuple)

        for child in get_successors_mrv(current, game):
            child_tuple = tuple(tuple(row) for row in child.grid)
            if child_tuple not in closed_set:
                heapq.heappush(open_list, child)

def solve_backtracking_generator(game):
    nodes_expanded = [0]
    is_solved = [False]
    
    def backtrack():
        if is_solved[0]: return
        
        empty_pos = bt.find_empty(game.grid, game.n)
        if not empty_pos:
            is_solved[0] = True
            yield game.grid, nodes_expanded[0], True
            return
            
        r, c = empty_pos
        for val in range(1, game.n + 1):
            if bt.is_safe(game, r, c, val):
                game.grid[r][c] = val
                nodes_expanded[0] += 1
                
                if nodes_expanded[0] % 5 == 0: 
                    yield game.grid, nodes_expanded[0], False
                    
                yield from backtrack()
                if is_solved[0]: return
                    
                game.grid[r][c] = 0
                
    yield from backtrack()

def solve_bruteforce_generator(game):
    empty_cells = []
    for i in range(game.n):
        for j in range(game.n):
            if game.grid[i][j] == 0:
                empty_cells.append((i, j))
                
    nodes_expanded = [0]
    is_solved = [False]
    
    def brute_force(index):
        if is_solved[0]: return
        
        if index == len(empty_cells):
            if bf.is_board_valid(game):
                is_solved[0] = True
                yield game.grid, nodes_expanded[0], True
            return
            
        r, c = empty_cells[index]
        for val in range(1, game.n + 1):
            game.grid[r][c] = val
            nodes_expanded[0] += 1
            
            if nodes_expanded[0] % 100 == 0: 
                yield game.grid, nodes_expanded[0], False
                
            yield from brute_force(index + 1)
            if is_solved[0]: return
                
        game.grid[r][c] = 0
        
    yield from brute_force(0)

with st.sidebar:
    st.header("Algorithm Settings")
    uploaded_file = st.file_uploader("Upload input file (.txt)", type=["txt"])
    
    algo_choice = st.selectbox("Select Algorithm", [
    "A* Search", 
    "Backtracking",
    "Brute Force",
    "Hybrid Inference", 
    "SAT"
    ])
    
    animation_speed = st.slider("Animation Speed", 0.01, 0.5, 0.1)
    run_button = st.button("Run Algorithm", type="primary")

if uploaded_file is not None:
    game_instance = parse_uploaded_file(uploaded_file)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Futoshiki Board")
        board_placeholder = st.empty()
        board_placeholder.markdown(render_grid_html(game_instance), unsafe_allow_html=True)
        
    with col2:
        st.subheader("Progress")
        status_text = st.empty()
        metrics_placeholder = st.empty()

    if run_button:
        animated_algos = ["A* Search", "Backtracking", "Brute Force", "Hybrid Inference"]
        
        if algo_choice in animated_algos:
            status_text.info(f"Searching using {algo_choice}...")
            
            generator = None
            metrics_label = "Nodes Expanded"
            
            if algo_choice == "A* Search":
                generator = solve_astar_generator(game_instance)
            elif algo_choice == "Backtracking":
                generator = solve_backtracking_generator(game_instance)
            elif algo_choice == "Brute Force":
                generator = solve_bruteforce_generator(game_instance)
            elif algo_choice == "Hybrid Inference":
                agent = FutoshikiFOLAgent(game_instance)
                generator = agent.solve_generator() 
                metrics_label = "Facts Deduced"
            
            for current_grid, metric_val, is_goal in generator:
                board_placeholder.markdown(render_grid_html(game_instance, current_grid), unsafe_allow_html=True)
                metrics_placeholder.metric(metrics_label, metric_val)
                
                delay = animation_speed if algo_choice != "Hybrid Inference" else animation_speed / 2
                time.sleep(delay) 
                
                if is_goal:
                    status_text.success("Solution found!")
                    break
            else:
                status_text.error("No solution found or contradiction detected.")

        elif algo_choice == "SAT":
            with open("temp_input.txt", "wb") as f:
                f.write(uploaded_file.getvalue())
            
            start_time = time.time()
            try:
                n = game_instance.n
                log_placeholder = metrics_placeholder.empty()
                
                def show_sat_math(phase, math_example, delay=0.8):
                    status_text.info(phase)
                    log_placeholder.markdown(f"""
                    <div style='background-color: #1E1E1E; padding: 15px; border-radius: 5px; border-left: 4px solid #FFC107;'>
                        <h4 style='margin-top: 0; color: #FFF;'>{phase}</h4>
                        <span style='color: #AAA;'>Visualize Logic CNF:</span>
                        <pre style='background-color: #000; color: #4CAF50; padding: 10px; border-radius: 3px; font-size: 14px;'>{math_example}</pre>
                    </div>
                    """, unsafe_allow_html=True)
                    time.sleep(delay)

                show_sat_math("Phase 1: Variable Mapping",
                         f"var = r*{n*n} + c*{n} + v\nEx: cell (0,0) assigns 1 will be variable X_{0*n*n + 0*n + 1}",
                         animation_speed * 10)
                
                show_sat_math("Phase 2: Cell Constraints",
                         f"Cell (0,0) must have: [1, 2, ..., {n}]\nCell (0,0) only have 1 number: can't be either 1 or 2 -> [-1, -2]",
                         animation_speed * 10)
                
                show_sat_math("Phase 3: Collumns and rows constraints",
                         "Row 0 can't repeatly have 1:\n[-1, -5] (if (0,0)=1 then (0,1) can't be 1)",
                         animation_speed * 10)

                show_sat_math("Phase 4: Inequation constraints",
                         "If Left < Right, and Left = 2:\nCan't be 1 or 2: [-X, -Y]",
                         animation_speed * 10)

                status_text.warning("Phase 5: PySAT C++ Solver is running (CDCL/DPLL)...")
                log_placeholder.markdown("""
                <div style='background-color: #4A148C; padding: 15px; border-radius: 5px;'>
                    <h4 style='margin-top: 0; color: #FFF;'>Solving...</h4>
                    <span style='color: #DDD;'>Thực thi thuật toán tìm kiếm Boolean trên C++ backend.</span>
                </div>
                """, unsafe_allow_html=True)
                
                stats = solve_futoshiki_optimized("temp_input.txt", "temp_output.txt")
                
                show_sat_math("Phase 6: Decoding CNF Model",
                         "Found a Model!\nEx: Literal 5 is TRUE -> back-translate: (0,1) = 1\nUpdating onto the board...",
                         animation_speed * 10)
                
                # Cập nhật kết quả cuối
                with open("temp_output.txt", "r") as f:
                    output_lines = f.readlines()
                
                solved_grid = []
                for i in range(game_instance.n):
                    row_str = output_lines[i*2].replace("<", " ").replace(">", " ")
                    solved_grid.append([int(x) for x in row_str.split()])
                
                board_placeholder.markdown(render_grid_html(game_instance, solved_grid), unsafe_allow_html=True)
                
                runtime = time.time() - start_time
                status_text.success(f"SAT Completed in {runtime:.4f}s")
                
                log_placeholder.empty()
                col_m1, col_m2 = metrics_placeholder.columns(2)
                col_m1.metric("CNF Clauses", stats["clauses"])
                col_m2.metric("Inferences", stats["inferences"])
                
            except Exception as e:
                status_text.error(f"Error running SAT: {e}")

else:
    st.info("Please upload an input file from the Sidebar to start.")
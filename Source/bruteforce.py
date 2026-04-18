import os
import glob
import game as out_module

def is_board_valid(game):
    n = game.n
    grid = game.grid
    horiz = game.horizontal
    vert = game.vertical

    for i in range(n):
        row_set = set()
        col_set = set()
        for j in range(n):
            val_r = grid[i][j]
            if val_r < 1 or val_r > n or val_r in row_set:
                return False
            row_set.add(val_r)
            
            val_c = grid[j][i]
            if val_c < 1 or val_c > n or val_c in col_set:
                return False
            col_set.add(val_c)

    for i in range(n):
        for j in range(n):
            if j < n - 1:
                if horiz[i][j] == 1 and grid[i][j] >= grid[i][j+1]: 
                    return False
                if horiz[i][j] == -1 and grid[i][j] <= grid[i][j+1]: 
                    return False
            
            if i < n - 1:
                if vert[i][j] == 1 and grid[i][j] >= grid[i+1][j]: 
                    return False
                if vert[i][j] == -1 and grid[i][j] <= grid[i+1][j]: 
                    return False

    return True

def solve_brute_force(game, empty_cells, index):
    if index == len(empty_cells):
        return is_board_valid(game)
        
    r, c = empty_cells[index]
    
    for val in range(1, game.n + 1):
        game.grid[r][c] = val
        if solve_brute_force(game, empty_cells, index + 1):
            return True
            
    game.grid[r][c] = 0
    return False

def solve_futoshiki_bf(game):
    empty_cells = []
    for i in range(game.n):
        for j in range(game.n):
            if game.grid[i][j] == 0:
                empty_cells.append((i, j))
                
    return solve_brute_force(game, empty_cells, 0)

def main():
    input_dir = 'Inputs'
    output_dir = 'Outputs' 

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    input_files = glob.glob(os.path.join(input_dir, 'input-*.txt'))
    input_files.sort()
    
    if not input_files:
        print(f"Not found: '{input_dir}'.")
        return

    for in_path in input_files:
        filename = os.path.basename(in_path)
        out_filename = filename.replace('input-', 'output-')
        out_path = os.path.join(output_dir, out_filename)

        print(f"Run Brute Force: {filename}...")
        
        try:
            game = out_module.read_input(in_path)

            if solve_futoshiki_bf(game):
                out_module.print_output(out_path, game)
                print("Solved!")
            else:
                print(f"No solution: {filename}")
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            
        print("-" * 40)

if __name__ == '__main__':
    main()
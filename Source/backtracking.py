import os
import glob
import game as out_module

def is_safe(game, r, c, val):
    n = game.n
    grid = game.grid
    horiz = game.horizontal
    vert = game.vertical

    for i in range(n):
        if grid[r][i] == val or grid[i][c] == val:
            return False

    if c > 0 and grid[r][c-1] != 0:
        if horiz[r][c-1] == 1 and grid[r][c-1] >= val: 
            return False
        if horiz[r][c-1] == -1 and grid[r][c-1] <= val: 
            return False
            
    if c < n - 1 and grid[r][c+1] != 0:
        if horiz[r][c] == 1 and val >= grid[r][c+1]: 
            return False
        if horiz[r][c] == -1 and val <= grid[r][c+1]: 
            return False
        
    if r > 0 and grid[r-1][c] != 0:
        if vert[r-1][c] == 1 and grid[r-1][c] >= val: 
            return False
        if vert[r-1][c] == -1 and grid[r-1][c] <= val: 
            return False
            
    if r < n - 1 and grid[r+1][c] != 0:
        if vert[r][c] == 1 and val >= grid[r+1][c]: 
            return False
        if vert[r][c] == -1 and val <= grid[r+1][c]: 
            return False

    return True

def find_empty(grid, n):
    for i in range(n):
        for j in range(n):
            if grid[i][j] == 0:
                return i, j
    return None

def solve_futoshiki(game):
    empty_pos = find_empty(game.grid, game.n)
    
    if not empty_pos:
        return True 

    r, c = empty_pos

    for val in range(1, game.n + 1):
        if is_safe(game, r, c, val):
            game.grid[r][c] = val 
            
            if solve_futoshiki(game):
                return True
                
            game.grid[r][c] = 0 

    return False

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

        print(f"Run: {filename}...")
        
        try:
            game = out_module.read_input(in_path)

            if solve_futoshiki(game):
                out_module.print_output(out_path, game)
            else:
                print(f"error: {filename}")
        except Exception as e:
            print(f"error: {filename}")
            
        print("-" * 40)

if __name__ == '__main__':
    main()
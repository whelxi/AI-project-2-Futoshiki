import os
import astar

from init import read_input, print_output

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    for i in range(1, 11):
        input_num = f"{i:02d}"
        input_path = os.path.join(script_dir, "Inputs", f"input-{input_num}.txt")
        output_path = os.path.join(script_dir, "Outputs", f"output-{input_num}.txt")
        
        print(f"Processing input-{input_num}.txt...")
        game = read_input(input_path)
        
        solved_game = astar.solve_futoshiki_astar(game)
        if solved_game:
            print_output(output_path, solved_game)
            print(f"Solved! Output saved to output-{input_num}.txt\n")
        else:
            print(f"Failed to solve input-{input_num}.txt\n")
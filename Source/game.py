import sys
from typing import List

class GameInstance:
    def __init__(self, n, grid, horizontal, vertical):
        self.n = n
        self.grid = grid
        self.horizontal = horizontal
        self.vertical = vertical

def print_output(path, game):
    file = open(path, 'w')
    for i in range(game.n):
        for j in range(game.n - 1):
            file.write(str(game.grid[i][j]))
            if game.horizontal[i][j] == 1:
                file.write("<")
            elif game.horizontal[i][j] == -1:
                file.write(">")
            else:
                file.write(" ")
        file.write(str(game.grid[i][game.n - 1]))
        file.write("\n")

        if (i == game.n - 1):
            break

        for j in range(game.n):
            if game.vertical[i][j] == 1:
                file.write("^ ")
            elif game.vertical[i][j] == -1:
                file.write("v ")
            else:
                file.write("  ")
        file.write("\n")

def read_input(path):
    file = open(path, 'r')
    n = int(file.readline())

    grid = [[0 for _ in range(n)] for _ in range(n)]
    horizontal = [[0 for _ in range(n)] for _ in range(n)]
    vertical = [[0 for _ in range(n)] for _ in range(n)]

    d = 0
    for line in file.readlines(): 
        if d < n:
            grid[d] = [int(x) for x in line.split(', ')]
        elif d < 2*n:
            horizontal[d - n] = [int(x) for x in line.split(', ')]
        else:
            vertical[d - 2*n] = [int(x) for x in line.split(', ')]
        d += 1
    
    file.close()
    return GameInstance(n, grid, horizontal, vertical)

if __name__ == "__main__":
    game = read_input("Inputs/input-01.txt")
    print_output("output.txt", game)
import random

class GridMap:
    def __init__(self):
        self.status = {"UNKNOWN": -1, "FREE": 0, "OCCUPIED": 1}
        self.grid_size = 10
        self.map = [[self.status["UNKNOWN"] for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.current_position = [self.grid_size // 2, self.grid_size // 2] 
        self.map[self.current_position[0]][self.current_position[1]] = self.status["FREE"]
        self.directions = { 'up': (-1, 0), 'down': (1, 0), 'left': (0, -1), 'right': (0, 1)}


    def is_valid(self, pos):
        x, y = pos
        return 0 <= x < self.grid_size and 0 <= y < self.grid_size
    
    def update_map(self, reading):
        x, y = self.current_position
        front = x+1, y
        if self.is_valid(front):
            self.map[x+1][y] = reading['front']
        right = x, y+1
        if self.is_valid(right):
            self.map[x][y+1] = reading['right']
        left = x, y-1
        if self.is_valid(left):
            self.map[x][y-1] = reading['left']
        back = x-1, y
        if self.is_valid(back):
            self.map[x-1][y] = reading['back']   

    def move_robot(self):
        moves = list(self.directions.keys())
        random.shuffle(moves)
        for move in moves:
            dx, dy = self.directions[move]
            new_pos = [self.current_position[0] + dx, self.current_position[1] + dy]

            if self.map[new_pos[0]][new_pos[1]] == self.status["OCCUPIED"]:
                continue

            if not self.is_valid(new_pos):
                print("Hit the boundary! Cannot move.")
                continue

            self.current_position = new_pos
            self.map[new_pos[0]][new_pos[1]] = self.status["FREE"]
            print(f"Moved to {new_pos}")
            break
    

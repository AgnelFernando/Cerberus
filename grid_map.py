import logging
import random
from enum import Enum
from patrol_service import Direction

logger = logging.getLogger(__name__)

class CellStatus(Enum):
    UNKNOWN = -1
    FREE = 0
    OCCUPIED = 1

class GridMap:
    def __init__(self):
        self.grid_size = 10
        self.map = [[CellStatus.UNKNOWN for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.current_position = [self.grid_size // 2, self.grid_size // 2] 
        self.map[self.current_position[0]][self.current_position[1]] = CellStatus.FREE
        self.directions = { Direction.FRONT: (-1, 0), Direction.BACK: (1, 0), 
                           Direction.LEFT: (0, -1), Direction.RIGHT: (0, 1)}


    def is_valid(self, pos):
        x, y = pos
        return 0 <= x < self.grid_size and 0 <= y < self.grid_size
    
    def update_map(self, reading: dict[Direction, CellStatus]) -> None:
        x, y = self.current_position
        front = x+1, y
        if self.is_valid(front):
            self.map[x+1][y] = reading[Direction.FRONT]
        right = x, y+1
        if self.is_valid(right):
            self.map[x][y+1] = reading[Direction.RIGHT]
        left = x, y-1
        if self.is_valid(left):
            self.map[x][y-1] = reading[Direction.LEFT]
        back = x-1, y
        if self.is_valid(back):
            self.map[x-1][y] = reading[Direction.BACK]   

    def move_robot(self):
        for move in [Direction.FRONT, Direction.LEFT, Direction.RIGHT, Direction.BACK]:
            dx, dy = self.directions[move]
            new_pos = [self.current_position[0] + dx, self.current_position[1] + dy]

            if not self.is_valid(new_pos):
                print("Hit the boundary! Cannot move.")
                continue

            if self.map[new_pos[0]][new_pos[1]] == CellStatus.OCCUPIED:
                continue

            self.current_position = new_pos
            self.map[new_pos[0]][new_pos[1]] = CellStatus.FREE
            logger.info(f"Moved to {new_pos}")
            return move
    

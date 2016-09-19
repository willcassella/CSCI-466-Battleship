import os

class BSGame:
    """Width and height of the board"""
    BOARD_WIDTH = 10
    BOARD_HEIGHT = 10

    """The types of tiles that appear on the board"""
    TILE_WATER = '_'
    TILE_CARRIER = 'C'
    TILE_BATTLESHIP = 'B'
    TILE_CRUISER = 'R'
    TILE_SUBMARINE = 'S'
    TILE_DESTROYER = 'D'
    TILE_UNKNOWN = '?' # Only used for opponent's board, indicates we don't know what's gonna come through that tile
    TILE_UNKNOWN_SHIP = 'X' # Only used for opponent's board, indicates we hit a sihp (but we don't know what kind)
    TILE_NAME = {TILE_WATER: 'water', TILE_CARRIER: 'carrier', TILE_BATTLESHIP: 'battleship', TILE_CRUISER: 'cruiser',
                 TILE_UNKNOWN: 'unknown', TILE_UNKNOWN_SHIP: 'unknown_ship', TILE_SUBMARINE: 'submarine', TILE_DESTROYER: 'destroyer'}

    def __init__(self):
        # Initialze board and record of opponent's shots
        self.board = [[BSGame.TILE_UNKNOWN for x in range(BSGame.BOARD_WIDTH)] for y in range(BSGame.BOARD_HEIGHT)]
        self.opponent_shots = [[False for x in range(BSGame.BOARD_WIDTH)] for y in range(BSGame.BOARD_HEIGHT)]
        self.lost_ships = []


    """The shot fired was out of bounds"""
    SHOT_OUT_OF_BOUNDS = -2

    """A shot has previously been fired in this position"""
    SHOT_REDUNDANT = -1

    """The shot didn't hit anything'"""
    SHOT_MISS = 0

    """The shot hit something, but did not sink anything"""
    SHOT_HIT = 1

    """The shot hit something, and sank it"""
    SHOT_SINK = 2

    def fire(self, x, y):
        # Make sure the shot is within bounds of the board
        if not 0 <= x < BSGame.BOARD_WIDTH or not 0 <= y < BSGame.BOARD_HEIGHT:
             return (BSGame.SHOT_OUT_OF_BOUNDS, None)

        # Make sure the opponent hasn't shot here before
        if self.opponent_shots[x][y]:
            return (BSGame.SHOT_REDUNDANT, None)

        # Register the opponents shot, and figure out if they missed/hit/sunk anything
        self.opponent_shots[x][y] = True
        result = self.board[x][y]

        # Check if they missed
        if result == BSGame.TILE_WATER:
            return (BSGame.SHOT_MISS, None)

        # Check if any unhit squares with this ship exist on this row
        for checkX in range(0, BSGame.BOARD_WIDTH):
            if self.board[checkX][y] == result and not self.opponent_shots[checkX][y]:
                return (BSGame.SHOT_HIT, result)

        # Check if any unhit squares with this ship exist on this column
        for checkY in range(0, BSGame.BOARD_HEIGHT):
            if self.board[x][checkY] == result and not self.opponent_shots[x][checkY]:
                return (BSGame.SHOT_HIT, result)

        # They must have sunk
        self.lost_ships.append(result)
        return (BSGame.SHOT_SINK, result)


def load_bs_game(path):
    game = BSGame()

    # Load board configuration from file, if it exists (otherwise return default configuration)
    if os.path.isfile(path):
        file = open(path, 'r')
    else:
        return game;

    y = 0
    for line in file.readlines():
        if y >= BSGame.BOARD_HEIGHT:
            for ship in line:
                game.lost_ships.append(ship)
        else:
            for x in range(BSGame.BOARD_WIDTH):
                game.board[x][y] = line[x]
            y += 1
    file.close()
    return game

def save_bs_game(game, path):
    file = open(path, 'w')
    for y in range(BSGame.BOARD_HEIGHT):
        for x in range(BSGame.BOARD_WIDTH):
            file.write(game.board[x][y])
        file.write("\n")
    for ship in game.lost_ships:
        file.write(ship)
    file.close()

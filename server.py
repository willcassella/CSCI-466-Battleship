import time
import os
from sys import argv
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

class BattleShipGame:
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

    def __init__(self, path):
        # Initialze board and record of opponent's shots
        self.board = [[None for x in range(BattleShipGame.BOARD_WIDTH)] for y in range(BattleShipGame.BOARD_HEIGHT)]
        self.opponent_shots = [[False for x in range(BattleShipGame.BOARD_WIDTH)] for y in range(BattleShipGame.BOARD_HEIGHT)]

        # Load board configuration from file
        with open(path, 'r') as f:
            y = 0
            for line in f.readlines():
                for x in range(BattleShipGame.BOARD_WIDTH):
                    self.board[x][y] = line[x]
                y += 1


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
        if not 0 <= x < BattleShipGame.BOARD_WIDTH or not 0 <= y < BattleShipGame.BOARD_HEIGHT:
             return (BattleShipGame.SHOT_OUT_OF_BOUNDS, None)

        # Make sure the opponent hasn't shot here before
        if self.opponent_shots[x][y]:
            return (BattleShipGame.SHOT_REDUNDANT, None)

        # Register the opponents shot, and figure out if they missed/hit/sunk anything
        self.opponent_shots[x][y] = True
        result = self.board[x][y]

        # Check if they missed
        if result == BattleShipGame.TILE_WATER:
            return (BattleShipGame.SHOT_MISS, None)

        # Check if any unhit squares with this ship exist on this row
        for checkX in range(0, BattleShipGame.BOARD_WIDTH):
            if self.board[checkX][y] == result and not self.opponent_shots[checkX][y]:
                return (BattleShipGame.SHOT_HIT, result)

        # Check if any unhit squares with this ship exist on this column
        for checkY in range(0, BattleShipGame.BOARD_HEIGHT):
            if self.board[x][checkY] == result and not self.opponent_shots[x][checkY]:
                return (BattleShipGame.SHOT_HIT, result)

        # They must have sunk
        return (BattleShipGame.SHOT_SINK, result)


def wfile_writestr(wfile, value):
    wfile.write(bytes(value, "utf-8"))


def render_own_board(wfile, game):
        wfile_writestr(wfile, '<html><head><title>Board</title><link rel="stylesheet" href="css/board.css"></head><body>')
        wfile_writestr(wfile, '<h1>BATTLESHIP</h1>')
        wfile_writestr(wfile, '<div id="button-container">')
        wfile_writestr(wfile, '<a href="own_board.html"><button>Refresh</button></a>')
        wfile_writestr(wfile, '<a href="opponent_board.html"><button>View Opponent\'s Board</button></a>')
        wfile_writestr(wfile, '</div>')

        for y in range(BattleShipGame.BOARD_HEIGHT):
            wfile_writestr(wfile, '<div class="row">')
            for x in range(BattleShipGame.BOARD_WIDTH):

                # Get the class for the tile
                if game.board[x][y] == BattleShipGame.TILE_WATER:
                    tile = "water"
                elif game.board[x][y] == BattleShipGame.TILE_CARRIER:
                    tile = "ship carrier"
                elif game.board[x][y] == BattleShipGame.TILE_BATTLESHIP:
                    tile = "ship battleship"
                elif game.board[x][y] == BattleShipGame.TILE_CRUISER:
                    tile = "ship cruiser"
                elif game.board[x][y] == BattleShipGame.TILE_SUBMARINE:
                    tile = "ship submarine"
                else:
                    tile = "ship destroyer"

                wfile_writestr(wfile, '<div class="tile %s">' % tile)

                if game.opponent_shots[x][y]:
                    wfile_writestr(wfile, '<div class="shot"></div>')

                wfile_writestr(wfile, '</div>')

            wfile_writestr(wfile, '</div>')
        wfile_writestr(wfile, '</body></html>')


def render_opponent_board(wfile, path):
    return


# Create an instance of the game
game = BattleShipGame(argv[2])

class BattleShipServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)

        if self.path == "/own_board.html":
            self.send_header("Content-type", "text/html")
            self.end_headers()
            render_own_board(self.wfile, game)
            return

        if self.path == "/opponent_board.html":
            self.send_header("Content-type", "text/html")
            self.end_headers()
            render_opponent_board(self.wfile, "opponent_board.txt")
            return

        if self.path.endswith(".css"):
            self.send_header("Content-type", "text/css")
            self.end_headers()
            with open(os.getcwd() + self.path, 'r') as f:
                wfile_writestr(self.wfile, f.read())
            return

        if self.path.endswith(".png"):
            self.send_header("Content-type", "image/png")
            self.end_headers()
            with open(os.getcwd() + self.path, 'rb') as f:
                self.wfile.write(f.read())
            return

    def do_POST(self):
        # Get the post arguments
        length = int(self.headers['Content-Length'])
        post_data = parse_qs(self.rfile.read(length).decode('utf-8'))

        # Try to get the x and y coordinates to fire at
        try:
            x = int(post_data['x'][0])
            y = int(post_data['y'][0])
        except:
            self.send_response(400)
            self.end_headers()
            print(time.asctime(), "Bad POST arguments - %s" % post_data)
            return

        # Run game logic
        result,ship = game.fire(x, y)

        # If shot was out of bounds, send BAD REQUEST and return
        if result == BattleShipGame.SHOT_OUT_OF_BOUNDS:
            self.send_response(400)
            self.end_headers()
            print(time.asctime(), "Shot out of bounds - %s,%s" % (x, y))
            return

        # If shot has already been fired in the same place, send GONE and return
        if result == BattleShipGame.SHOT_REDUNDANT:
            self.send_response(410)
            self.end_headers()
            print(time.asctime(), "Shot redundant - %s,%s" % (x, y))
            return

        # Request was valid, so send OK status
        self.send_response(200)
        self.send_header("Content-type", "text/text")
        self.end_headers()

        if result == BattleShipGame.SHOT_MISS:
            self.wfile.write(bytes("hit=0", "utf-8"))
            print(time.asctime(), "Shot missed - %s,%s" % (x, y))

        elif result == BattleShipGame.SHOT_HIT:
            self.wfile.write(bytes("hit=1", "utf-8"))
            print(time.asctime(), "Shot hit %s - %s,%s" % (ship, x, y))

        elif result == BattleShipGame.SHOT_SINK:
            self.wfile.write(bytes("hit=1&sink=%s" % ship, "utf-8"))
            print(time.asctime(), "Shot sank %s - %s,%s" % (ship, x, y))


# Configuration of the server
HOST_NAME = "localhost"
host_port = int(argv[1])

# Set up the server
server = HTTPServer((HOST_NAME, host_port), BattleShipServer)
print(time.asctime(), "Server Started - %s:%s" % (HOST_NAME, host_port))

# Run the server until the user interrupts
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass

# Close the server
server.server_close()
print(time.asctime(), "Server Stopped - %s:%s" % (HOST_NAME, host_port))
import time
import os
from sys import argv
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import BattleShip

def wfile_writestr(wfile, value):
    wfile.write(bytes(value, "utf-8"))


def render_board(wfile, game):
    wfile_writestr(wfile, '<h1>BATTLESHIP</h1>')

    # Render x-index tiles
    wfile_writestr(wfile, '<div class="row"><div class="tile"></div>')
    for x in range(BattleShip.BSGame.BOARD_WIDTH):
        wfile_writestr(wfile, '<div class="tile x-index">%s</div>' % x)
    wfile_writestr(wfile, '</div>') # Close x-index row

    # Render tiles
    for y in range(BattleShip.BSGame.BOARD_HEIGHT):
        wfile_writestr(wfile, '<div class="row">')
        wfile_writestr(wfile, '<div class="tile y-index">%s</div>' % y)

        for x in range(BattleShip.BSGame.BOARD_WIDTH):
            # Get the class for the tile
            if game.board[x][y] == BattleShip.BSGame.TILE_WATER:
                tile = "water"
            elif game.board[x][y] == BattleShip.BSGame.TILE_UNKNOWN:
                tile = "unknown"
            else:
                tile = "ship " + BattleShip.BSGame.TILE_NAME[game.board[x][y]]

            wfile_writestr(wfile, '<div class="tile %s" title="%s,%s">' % (tile, x, y))
            if game.opponent_shots[x][y] or game.board[x][y] == BattleShip.BSGame.TILE_UNKNOWN_SHIP:
                wfile_writestr(wfile, '<div class="shot"></div>')

            wfile_writestr(wfile, '</div>') # Close tile div
        wfile_writestr(wfile, '</div>') # Close row div


def render_sunk_list(wfile, game, message):
    # Render list of sunken ships
    if len(game.lost_ships) > 0:
        wfile_writestr(wfile, "<p>%s</p><ul>" % message)
        for lost in game.lost_ships:
            wfile_writestr(wfile, "<li>%s</li>" % BattleShip.BSGame.TILE_NAME[lost])
        wfile_writestr(wfile, "</ul>") # Close ship list

def render_own_board(wfile, game):
        # Render header
        wfile_writestr(wfile, '<html><head><title>Battleship</title><link rel="stylesheet" href="css/board.css"></head><body>')

        # Render board
        render_board(wfile, game)

        # Render buttons
        wfile_writestr(wfile, '<div id="button-container">')
        wfile_writestr(wfile, '<a href="own_board.html"><button>Refresh</button></a>')
        wfile_writestr(wfile, '<a href="opponent_board.html"><button>View Opponent\'s Board</button></a>')
        wfile_writestr(wfile, '</div>') # Close button container

        # Render list of lost ships
        render_sunk_list(wfile, game, "You have lost:")
        wfile_writestr(wfile, '</body></html>') # Close html


def render_opponent_board(wfile, path):
    # Render header
    wfile_writestr(wfile, '<html><head><title>Battleship</title><link rel="stylesheet" href="css/board.css"><head><body>')

    # Open the file containing the board and render it
    game = BattleShip.load_bs_game(path)
    render_board(wfile, game)

    # Render buttons
    wfile_writestr(wfile, '<div id="button-container">')
    wfile_writestr(wfile, '<a href="opponent_board.html"><button>Refresh</button></a>')
    wfile_writestr(wfile, '<a href="own_board.html"><button>View Your Board</button></a>')
    wfile_writestr(wfile, '</div>') # Close button container

    # Render list of sunk ships
    render_sunk_list(wfile, game, "You have sunk:")
    wfile_writestr(wfile, '</body></html>') # Close html


class BattleShipServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)

        if self.path == "/own_board.html":
            self.send_header("Content-type", "text/html")
            self.end_headers()
            global my_game
            render_own_board(self.wfile, my_game)
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
        global my_game
        result,ship = my_game.fire(x, y)

        # If shot was out of bounds, send BAD REQUEST and return
        if result == BattleShip.BSGame.SHOT_OUT_OF_BOUNDS:
            self.send_response(400)
            self.end_headers()
            print(time.asctime(), "Shot out of bounds - %s,%s" % (x, y))
            return

        # If shot has already been fired in the same place, send GONE and return
        if result == BattleShip.BSGame.SHOT_REDUNDANT:
            self.send_response(410)
            self.end_headers()
            print(time.asctime(), "Shot redundant - %s,%s" % (x, y))
            return

        # Request was valid, so send OK status
        self.send_response(200)
        self.send_header("Content-type", "text/text")
        self.end_headers()

        if result == BattleShip.BSGame.SHOT_MISS:
            self.wfile.write(bytes("hit=0", "utf-8"))
            print(time.asctime(), "Shot missed - %s,%s" % (x, y))

        elif result == BattleShip.BSGame.SHOT_HIT:
            self.wfile.write(bytes("hit=1", "utf-8"))
            print(time.asctime(), "Shot hit %s - %s,%s" % (ship, x, y))

        elif result == BattleShip.BSGame.SHOT_SINK:
            self.wfile.write(bytes("hit=1&sink=%s" % ship, "utf-8"))
            print(time.asctime(), "Shot sank %s - %s,%s" % (ship, x, y))


# Create an instance of the game
my_game = BattleShip.load_bs_game(argv[2])

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
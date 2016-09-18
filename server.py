import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

class BattleShipGame:
    """Width and height of the board"""
    BOARD_WIDTH = 10
    BOARD_HEIGHT = 10

    def __init__(self):
        self.board = [['-' for x in range(BattleShipGame.BOARD_WIDTH)] for y in range(BattleShipGame.BOARD_HEIGHT)]
        self.opponent_shots = [[False for x in range(BattleShipGame.BOARD_WIDTH)] for y in range(BattleShipGame.BOARD_HEIGHT)]
    
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
        if result == '-':
            return (BattleShipGame.SHOT_MISS, None)
        
        # If they hit a destroyer, it's automatically a sink
        if result == 'D':
            return (BattleShipGame.SHOT_SINK, 'D')
        
        # Check if any unhit squares with this ship exist on this row
        for checkX in range(0, BattleShipGame.BOARD_WIDTH):
            if self.board[checkX][y] == result and not self.opponent_shots[checkX][y]:
                return (BattleShipGame.SHOT_HIT, result)

        # Check if any unhit squares with this ship exist on this column
        for checkY in range(0, BattleShipGame.BOARD_HEIGHT):
            if self.board[x][checkY] == result and not self.opponent_shots[x][checlY]:
                return (BattleShipGame.SHOT_HIT, result)

        # They must have sunk
        return (BattleShipGame.SHOT_SINK, result)

# Create an instance of the game
game = BattleShipGame()

class BattleShipServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>Title goes here.</title></head>", "utf-8"))
        self.wfile.write(bytes("<body><p>This is a test.</p>", "utf-8"))
        self.wfile.write(bytes("<p>You accessed path: %s</p>" % self.path, "utf-8"))
        self.wfile.write(bytes("</body></html>", "utf-8"))
    
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
HOST_PORT = 5000

# Set up the server
server = HTTPServer((HOST_NAME, HOST_PORT), BattleShipServer)
print(time.asctime(), "Server Started - %s:%s" % (HOST_NAME, HOST_PORT))

# Run the server until the user interrupts
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass

# Close the server
server.server_close()
print(time.asctime(), "Server Stopped - %s:%s" % (HOST_NAME, HOST_PORT))
import urllib
from urllib.request import Request, urlopen
from urllib.parse import parse_qs, urlencode
from sys import argv
import BattleShip

host_name = argv[1]
host_port = int(argv[2])
url = "http://" + host_name + ":" + str(host_port)
x = int(argv[3])
y = int(argv[4])

# Setup HTTP POST
data = urlencode({ 'x': x, 'y': y })
request = Request(url, data.encode('ascii'))

# Load existing game state

try:
    # Send the request
    response = urlopen(request)
    response_data = parse_qs(response.read())

    # Load the existing view of the opponents board
    game = BattleShip.load_bs_game("opponent_board.txt")
    print(response_data)

    # Check the result
    if response_data[b'hit'][0] == b'1':
        game.board[x][y] = BattleShip.BSGame.TILE_UNKNOWN_SHIP
        if b'sink' in response_data:
            ship = response_data[b'sink'][0].decode("ascii")
            print(ship)
            game.lost_ships.append(ship)
            print("You sunk a {}!".format(BattleShip.BSGame.TILE_NAME[ship]))
        else:
            print("You hit something!")
    else:
        game.board[x][y] = BattleShip.BSGame.TILE_WATER
        print("You missed")

    # Save the view of the opponents board
    BattleShip.save_bs_game(game, "opponent_board.txt")

except urllib.error.HTTPError as e:
    if e.code == 400:
        print("Bad coordinates")
    elif e.code == 410:
        print("You've already shot here")
    pass

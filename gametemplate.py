import sys
import json

from ants import Ants

class Game(object):
    def __init__(self, opts):
        self.ants = Ants(opts)
        sys.stdout.write('-done\n')
        sys.stdout.flush()

    def getTurn(self):
        return self.ants.turn

if __name__ == "__main__":
    while (True):
        operation = sys.stdin.readline().strip()

        if operation == "-opts":
            opts = sys.stdin.readline()
            game = Game(json.loads(opts))
        elif operation == "?turn":
            sys.stdout.write(str(game.getTurn()) + '\n')
            sys.stdout.flush()
import sys
import json

from ants import Ants

class Game(object):
    def __init__(self, opts):
        self.ants = Ants(opts)
        sys.stdout.write('-done\n')
        sys.stdout.flush()

if __name__ == "__main__":
    operation = sys.stdin.readline().strip()

    if operation == "-opts":
        opts = sys.stdin.readline()
        game = Game(json.loads(opts))
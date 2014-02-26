import sys
import json

from ants import Ants

operation = sys.stdin.readline()

if operation == '-opts':
    opts = sys.stdin.readline()
    game = Game(json.loads(opts))


class Game:
    def __init__(self, opts):
        self.ants = Ants(opts)
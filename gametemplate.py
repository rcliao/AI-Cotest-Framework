import sys
import json

from ants import Ants

class Game(object):
    def __init__(self, opts):
        self.ants = Ants(opts)
        self.job_done()

    def get_turn(self):
        return self.ants.turn

    def kill_player(self, player):
        self.ants.kill_player(player)
        self.job_done()

    def start_game(self):
        self.ants.start_game()

    def is_alive(self, player):
        sys.stdout.write(json.dumps(self.ants.is_alive(player)) + "\n")
        sys.stdout.flush()

    def get_player_start(self, player):
        sys.stdout.write(self.ants.get_player_start(player))
        sys.stdout.flush()

    def get_player_state(self, player):
        sys.stdout.write(self.ants.get_player_state(player))
        sys.stdout.flush()

    def get_state(self):
        sys.stdout.write(self.ants.get_state())
        sys.stdout.flush()

    def start_turn(self):
        self.ants.start_turn()
        self.job_done()

    def game_over(self):
        sys.stdout.write(json.dumps(self.ants.game_over()))
        sys.stdout.flush()

    def do_moves(self, player, moves):
        sys.stdout.write(json.dumps(self.ants.do_moves(player, moves)))

    def finish_turn(self):
        self.ants.finish_turn()
        self.job_done()

    def get_stats(self):
        sys.stdout.write(json.dumps(self.ants.get_stats()))

    def finish_game(self):
        self.ants.finish_game()
        self.job_done()

    def get_scores(self):
        sys.stdout.write(json.dumps(self.ants.get_scores()))

    def get_replay(self):
        sys.stdout.write(json.dumps(self.ants.get_replay()))

    def job_done(self):
        sys.stdout.write('-job done\n')
        sys.stdout.flush()

if __name__ == "__main__":
    while (True):
        operation = sys.stdin.readline().strip()

        if operation == "+opts":
            opts = sys.stdin.readline()
            game = Game(json.loads(opts))
        elif operation == "?turn":
            sys.stdout.write(str(game.get_turn()) + '\n')
            sys.stdout.flush()
        elif operation == "-kill_player":
            playerLine = sys.stdin.readline()
            player = json.loads(opts)
            game.kill_player(player)
        elif operation == "-start_game":
            game.start_game()
        elif operation == "?is_alive":
            playerLine = sys.stdin.readline()
            player = json.loads(opts)
            game.is_alive(player)
        elif operation == "?player_start":
            playerLine = sys.stdin.readline()
            player = json.loads(opts)
            game.get_player_start(player)
        elif operation == "?player_state":
            playerLine = sys.stdin.readline()
            player = json.loads(opts)
            game.get_player_state(player)
        elif operation == "?state":
            game.get_state()
        elif operation == "-start_turn":
            game.start_turn()
        elif operation == "-game_over":
            game.game_over()
        elif operation == "-do_moves":
            playerLine = sys.stdin.readline()
            player = json.loads(opts)
            movesLine = sys.stdin.readline()
            moves = json.loads(opts)
            game.do_moves(player, moves)
        elif operation == "-finish_turn":
            game.finish_turn()
        elif operation == "?stats":
            game.get_stats()
        elif operation == "-finish_game":
            game.finish_game()
        elif operation == "?scores":
            game.get_scores()
        elif operation == "?replay":
            game.get_replay()
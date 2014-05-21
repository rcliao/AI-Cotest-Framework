#!/usr/bin/env python

import select
import socket
import sys
import os
import logging
import json
import random
import threading
from pyskills import trueskill
import subprocess

from math import ceil, sqrt
from time import time, sleep
import json

from time import time, asctime
import datetime

# Game engine speicific
from engine import run_game

# database
import game_db


# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.CRITICAL)
# create formatter
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
# add formatter to ch
ch.setFormatter(formatter)

# create logger
log = logging.getLogger('tcp')
log.setLevel(logging.INFO)
# add ch to logger
log.addHandler(ch)

DONE_MSG = "--job_done"

BUFSIZ = 4096

MAP_PLAYERS_INDEX = 0
MAP_COLS_INDEX = 1
MAP_ROWS_INDEX = 2
MAP_GAMES_INDEX = 3


# ugly global
class Bookkeeper:
    players = set()
    games = set()

book = Bookkeeper()


def load_map_info():
    maps = {}
    for root, dirs, filenames in os.walk("maps"):
        for filename in filenames:
            file = os.path.join(root, filename)
            mf = open(file, "r")
            for line in mf:
                if line.startswith('players'):
                    p = int(line.split()[1])
                if line.startswith('rows'):
                    r = int(line.split()[1])
                if line.startswith('cols'):
                    c = int(line.split()[1])
            mf.close()
            maps[file] = [p, r, c, 0]
    return maps


class TcpBox(threading.Thread):
    def __init__(self, sock):
        threading.Thread.__init__(self)
        self.sock = sock
        self.inp_lines = []

        # db stuff
        self.name = ""
        self.game_id = 0

        self.start()

    def __del__(self):
        try:
            book.players.remove(self.name)
        except:
            pass
        self._close()

    def run(self):
        while self.sock:
            line = ""
            while(self.sock):
                try:
                    c = self.sock.recv(1)
                except Exception, e:
                    self._close()
                    break
                if (not c):
                    break
                elif (c == '\r'):
                    continue
                elif (c == '\n'):
                    break
                else:
                    line += c
            if line:
                self.inp_lines.append(line)

    def _close(self):
        try:
            self.sock.close()
        except:
            pass
        self.sock = None

    def kill(self):
        try:
            self.write("end\nyou timed out.\n\n")
        except:
            pass

        self._close()

    def write(self, str):
        try:
            self.sock.sendall(str)
        except Exception, e:
            pass

    def write_line(self, line):
        return self.write(line + "\n")

    def read_line(self, timeout=0):
        if (len(self.inp_lines) == 0) or (not self.sock):
            return None
        line = self.inp_lines[0]
        self.inp_lines = self.inp_lines[1:]
        return line

    # dummies
    def release(self):
        self._close()

    def pause(self):
        pass

    def resume(self):
        pass

    def read_error(self, timeout=0):
        return None


class TcpGame(threading.Thread):
    """ This is the game implementation and the usage of the ant game
    """
    def __init__(self, id, tourn_id, opts, map_name, nplayers, mananger):
        threading.Thread.__init__(self)
        self.id = id
        self.tourn_id = tourn_id
        self.opts = opts
        # keep track of which player (used in the ranking, not the actual bot)
        # is playing
        self.players = []
        self.bot_status = []
        self.map_name = map_name
        self.nplayers = nplayers

        # this is where bot is, bunch of socket connnection so far
        self.bots = []

        # this is the game wrapper process
        # TODO: change this compile and run file to support other package later
        self.game = subprocess.Popen(
            ['python', 'gametemplate.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        )

        # send opts to game
        self.game.stdin.write('+opts\n')
        self.game.stdin.flush()
        self.game.stdin.write(json.dumps(opts) + '\n')
        self.game.stdin.flush()

        if self.game.stdout.readline().strip() != '-job done':
            print 'System failed to start the game'

        self.mananger = mananger

    # when the server closes ends
    def __del__(self):
        try:
            book.games.remove(self.id)
        except:
            pass
        for b in self.bots:
            b.kill()

    def run(self):
        starttime = time()
        log.info("run game %d %s %s" % (self.id, self.map_name, self.players))
        # when the game start, send the hello meesage to each bot
        for i, p in enumerate(self.bots):
            p.write(
                "INFO: game " + str(self.id) + " " + str(self.map_name)
                + " : " + str(self.players) + "\n"
            )

        logging.warning("start running game")

        # get the result after the game being ran
        # where run_game comes from the game engine
        # to separate the game engine, take out here
        game_result = run_game(self.game, self.bots, self.opts)

        logging.warning("finished running game and start getting turn text")

        # ask game for turn number
        self.game.stdin.write('?turn\n')
        self.game.stdin.flush()

        turnText = self.game.stdout.readline()

        logging.warning("finished running gane and get the turn text")

        turn = int(turnText)

        try:
            states = game_result["status"]
        except:
            logging.error("broken game %d: %s" % (self.id, game_result))
            return
        if turn < 1:
            logging.error("broken game %d (0 turns)" % (self.id))
            return
        scores = game_result["score"]
        ranks = game_result["rank"]

        # count draws
        draws = 0
        hist = [0]*len(ranks)
        for r in ranks:
            hist[r] += 1
        for h in hist:
            if h > 0:
                draws += (h-1)

        # save replay, add playernames to it
        game_result['game_id'] = self.id
        game_result['playernames'] = []
        for i, p in enumerate(self.players):
            game_result['playernames'].append(p)

        # save result as json to db
        db = game_db.GameDB()
        data = json.dumps(game_result)

        db.add_replay(self.tourn_id, self.id, data)

        plr = {}
        for i, p in enumerate(self.players):
            # for each player get the final score of the game and update to the
            # Tourn_GameIndex table
            plr[p] = (scores[i], states[i])
            db.update(
                "insert into Tourn_GameIndex values(?, ?, ?, ?)",
                (None, self.tourn_id, p, self.id)
            )
        db.add_tourn_game(
            self.tourn_id,
            self.id,
            self.map_name,
            turn,
            draws,
            json.dumps(plr)
        )

        # update trueskill
        # if sum(ranks) >= len(ranks)-1:
        if self.opts['trueskill'] == 'jskills':
            self.calk_ranks_js(self.tourn_id, self.players, ranks, db)
        else:
            # default
            self.calc_ranks_py(self.tourn_id, self.players, ranks, db)

        # update rankings
        for i, p in enumerate(
            db.retrieve(
                "select bot_id from Tourn_Entries \
                    where tourn_id=1 \
                    order by skill desc",
                ()
            )
        ):
            db.update_player_rank(self.tourn_id, p[0], i+1)
        db.con.commit()

        # after each game, remove all the bots and restart the new tournament
        db.update_tournament_activity( self.tourn_id )
        db.con.commit()

        # dbg display
        ds = time() - starttime
        mins = int(ds / 60)
        secs = ds - mins*60
        log.info("saved game %d : %d turns %dm %2.2fs" % (self.id,turn,mins,secs) )
        log.info("players: %s" % self.players)
        log.info("ranks  : %s   %s draws" % (ranks, draws) )
        log.info("scores : %s" % scores)
        log.info("status : %s" % states)


    def calc_ranks_py( self, tourn_id, players, ranks, db ):
        class TrueSkillPlayer(object):
            def __init__(self, name, skill, rank):
                self.name = name
                self.old_skill = skill
                self.skill = skill
                self.rank = rank

        ts_players = []
        for i, p in enumerate(players):
            pdata = db.get_player((troun_id, p))
            ts_players.append( TrueSkillPlayer(i, (pdata[0][6],pdata[0][7]), ranks[i] ) )

        try:
            trueskill.AdjustPlayers(ts_players)
        except Exception, e:
            log.error(e)
            return

        for i, p in enumerate(players):
            mu = ts_players[i].skill[0]
            sigma = ts_players[i].skill[1]
            skill = mu - sigma * 3
            db.update_player_skill(tourn_id, p, skill, mu, sigma)

    def calk_ranks_js(self, tourn_id, players, ranks, db):
        # java needs ';' as separator for win23, ':' for nix&mac
        sep = ':'
        if os.name == 'nt':
            sep = ';'
        try:
            classpath = "jskills/JSkills_0.9.0.jar"+sep+"jskills"
            tsupdater = subprocess.Popen(
                ["java", "-cp", classpath, "TSUpdate"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            lines = []
            for i, p in enumerate(players):
                pdata = db.get_player(tourn_id, p)
                lines.append(
                    "P %s %d %f %f\n" % (
                        p,
                        ranks[i],
                        pdata[0][6],
                        pdata[0][7]
                    )
                )

            for i, p in enumerate(players):
                tsupdater.stdin.write(lines[i])

            tsupdater.stdin.write("C\n")
            tsupdater.stdin.flush()
            tsupdater.wait()
        except Exception, e:
            log.error(str(e.split('\n')[0]))
            return
        try:
            result = tsupdater.stderr.readline().split()

            # if result.find("Maximum iterations")>0:
            #    log.error( "jskills:  Maximum iterations reached")
            return
        except Exception, e:
            log.error(str(e))

        for i, p in enumerate(players):
            # this might seem like a fragile way to handle the output of
            # TSUpdate but it is meant as a double check that we are getting
            # good and complete data back

            result = tsupdater.stdout.readline().split()

            if len(result) < 3:
                logging.error("invalid jskill result " + str(result))
                return

            if str(p) != result[0]:
                logging.error(
                    "Unexpected player name in TSUpdate result. %s != %s" % (
                        player,
                        result[0]
                    )
                )
                break

            mu = float(result[1].replace(",", "."))
            sigma = float(result[2].replace(",", "."))
            skill = mu - sigma * 3
            db.update_player_skill(tourn_id, p, skill, mu, sigma)


class TCPGameServer(object):
    def __init__(self, opts, ip, port, maps, mananger):
        self.opts = opts
        self.maps = maps

        # tcp binding options
        self.ip = ip
        self.port = port
        self.backlog = 5

        self.tourn_id = 1

        self.bind()

        self.mananger = mananger

    def addplayer(self, game, name, sock):
        box = TcpBox(sock)
        box.name = name
        box.game_id = game.id
        game.bots.append(box)
        game.players.append(name)
        book.players.add(name)
        return len(game.bots)

    def bind(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.ip, self.port))
        log.info('Listening to port %d ...' % self.port)
        self.server.listen(self.backlog)

    def shutdown(self):
        log.info('Shutting down server...')
        self.server.close()
        self.server = None

    def select_map(self):
        # try to find a map that does not need more players than available
        max_players = len(book.players)/2
        if max_players < 2:
            max_players = 2
        map_path = random.choice(self.maps.keys())

        while(self.maps[map_path][MAP_PLAYERS_INDEX] > max_players):
            map_path = random.choice(self.maps.keys())
        self.maps[map_path][MAP_GAMES_INDEX] += 1

        data = ""
        f = open(map_path, 'r')
        for line in f:
            data += line
            if line.startswith('players'):
                nplayers = line.split()[1]
        f.close()
        return map_path, data, int(nplayers)

    def create_game(self, mananger):
        # get a map and create antsgame
        self.latest += 1
        map_name, map_data, nplayers = self.select_map()
        opts = self.opts
        opts['map'] = map_data

        log.info("game %d %s needs %d players" % (
            self.latest,
            map_name,
            nplayers)
        )
        g = TcpGame(
            self.latest,
            self.tourn_id,
            opts,
            map_name,
            nplayers,
            mananger
        )
        book.games.add(g.id)
        return g

    def reject_client(self, client, message, dolog=True):
        try:
            if dolog:
                log.info(message)
            client.sendall("INFO: " + message + "\nend\ngo\n")
            client.close()
            client = None
        except:
            pass

    def kill_client(self, client, message, dolog=True, name=""):
        try:
            if dolog:
                log.info(message)
            client.sendall("killbot" + message)
            client.close()
            client = None
            self.db.delete_kill_name(name)
        except:
            pass

    def serve(self):
        # have to create the game before collecting respective num of players:
        self.db = game_db.GameDB()
        self.kill_list = self.db.get_kill_client()
        games = self.db.retrieve(
            "select id from Tourn_Games \
                where tourn_id=? \
                order by id desc limit 1;",
            (self.tourn_id, )
        )
        if len(games) > 0:
            self.latest = int(games[0][0])
        else:
            self.latest = 0

        next_game = self.create_game(self.mananger)
        t = 0
        while self.server:
            try:
                inputready, outputready, exceptready =
                select.select([self.server], [], [], 0.1)
            except select.error, e:
                log.exception(e)
                break
            except socket.error, e:
                log.exception(e)
                break
            except KeyboardInterrupt, e:
                return

            try:
                for s in inputready:
                    if s == self.server:
                        # find the client connected to server
                        client, address = self.server.accept()
                        data = client.recv(4096).strip()
                        data = data.split(" ")

                        operation = data[0]

                        if operation == "TOURNAMENT":

                            # switch the tourn_id
                            self.tourn_id = data[1]

                        elif operation == "USER":

                            name = data[1]
                            name_ok = True

                            # it kinda works, but for loop needs to be redone
                            i = -1
                            for entry in self.kill_list:
                                if (entry[i] == name):
                                    self.kill_client(
                                        client,
                                        "deleted because on kill_list",
                                        True,
                                        name
                                    )
                                    break

                            for bw in [
                                "shit",
                                "porn",
                                "pr0n",
                                "pron",
                                "dick",
                                "tits",
                                "hitler",
                                "fuck",
                                "gay",
                                "cunt",
                                "asshole"
                            ]:
                                if name.find(bw) > -1:
                                    self.kill_client(
                                        client,
                                        "can you think of another name \
                                            than '%s', please ?" % name)
                                    name_ok = False
                                    break
                            if not name_ok:
                                continue
                            # if in 'single game per player(name)' mode,
                            # just reject the connection here..
                            if (name in book.players)
                            and (str(self.opts['multi_games']) == "False"):
                                self.reject_client(
                                    client,
                                    "%s is already running a game." % name,
                                    False
                                )
                                continue
                            # already in next_game ?
                            if name in next_game.players:
                                self.reject_client(
                                    client,
                                    '%s is already queued for game %d' % (
                                        name, next_game.id),
                                    False
                                )
                                continue

                            # start game if enough players joined
                            avail = self.addplayer(next_game, name, client)

                            if avail == -1:
                                continue
                            log.info(
                                'user %s connected to game %d (%d/%d)' % (
                                    name,
                                    next_game.id,
                                    avail,
                                    next_game.nplayers
                                )
                            )
                            if avail == next_game.nplayers:
                                next_game.start()
                                next_game = self.create_game(self.mananger)

                # remove bots from next_game that died between connect
                # and the start of the game
                for i, b in enumerate(next_game.bots):
                    if (not b.sock) or (not b.is_alive):
                        log.info(
                            "removed %s from next_game:%d" % (
                                b.name,
                                next_game.id
                            )
                        )
                        del(next_game.bots[i])
                        del(next_game.players[i])

                if t % 25 == 1:
                    log.info(
                        "%d games, %d players online." % (
                            len(book.games),
                            len(book.players)
                        )
                    )
                    self.kill_list = self.db.get_kill_client()

                # if t % 250 == 1:
                #    for player in book.players:
                #        print(player.name)
                #        print("hello?")

                t += 1

                sleep(0.005)
            except:
                pass

        self.shutdown()


def main(mananger, ip='', tcp_port=2081):

    opts = {
        # tcp opts:
        'turns': 750,
        'loadtime': 5000,
        'turntime': 5000,
        'viewradius2': 77,
        'attackradius2': 5,
        'spawnradius2': 1,
        'attack': 'focus',
        'food': 'symmetric',
        'food_rate': (1, 8),
        'food_turn': (12, 30),
        'food_start': (75, 175),
        'food_visible': (2, 4),
        'cutoff_percent': 0.66,
        'cutoff_turn': 150,
        'kill_points': 2,
        'trueskill': 'jskills',
        'multi_games': 'True'
    }
    maps = load_map_info()
    if len(maps) == 0:
        print("Error: Found no maps! Please create a few in the maps/ folder.")
        return

    tcp = TCPGameServer(opts, ip, tcp_port, maps, mananger)
    tcp.serve()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 3:
        import os
        fpid = os.fork()
        # Running as daemon now. PID is fpid
        if fpid != 0:
            sys.exit(0)
    elif len(sys.argv) > 2:
        main(sys.argv[1], int(sys.argv[2]))
    elif len(sys.argv) > 1:
        main(int(sys.argv[1]))
    else:
        main()

#!/usr/bin/env python

import time
import traceback
import os
import random
import sys
import json
import io
if sys.version_info >= (3,):
    def unicode(s):
        return s

import logging


class HeadTail(object):
    'Capture first part of file write and discard remainder'
    def __init__(self, file, max_capture=510):
        self.file = file
        self.max_capture = max_capture
        self.capture_head_len = 0
        self.capture_head = unicode('')
        self.capture_tail = unicode('')

    def write(self, data):
        if self.file:
            self.file.write(data)
        capture_head_left = self.max_capture - self.capture_head_len
        if capture_head_left > 0:
            data_len = len(data)
            if data_len <= capture_head_left:
                self.capture_head += data
                self.capture_head_len += data_len
            else:
                self.capture_head += data[:capture_head_left]
                self.capture_head_len = self.max_capture
                self.capture_tail += data[capture_head_left:]
                self.capture_tail = self.capture_tail[-self.max_capture:]
        else:
            self.capture_tail += data
            self.capture_tail = self.capture_tail[-self.max_capture:]

    def flush(self):
        if self.file:
            self.file.flush()

    def close(self):
        if self.file:
            self.file.close()

    def head(self):
        return self.capture_head

    def tail(self):
        return self.capture_tail

    def headtail(self):
        if self.capture_head != '' and self.capture_tail != '':
            sep = unicode('\n..\n')
        else:
            sep = unicode('')
        return self.capture_head + sep + self.capture_tail


def run_game(game, bots, options):
    '''
    This is where game initially runs
    '''

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.CRITICAL)
    # create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # add formatter to ch
    ch.setFormatter(formatter)

    # create logger
    log = logging.getLogger('game_runner')
    log.setLevel(logging.INFO)
    # add ch to logger
    log.addHandler(ch)

    # file descriptors for replay and streaming formats
    replay_log = options.get('replay_log', None)
    stream_log = options.get('stream_log', None)
    verbose_log = options.get('verbose_log', None)
    # file descriptors for bots, should be list matching # of bots
    input_logs = options.get('input_logs', [None]*len(bots))
    output_logs = options.get('output_logs', [None]*len(bots))
    error_logs = options.get('error_logs', [None]*len(bots))

    capture_errors = options.get('capture_errors', False)

    ''' game options and setup '''
    turns = int(options['turns'])
    loadtime = float(options['loadtime']) / 1000
    turntime = float(options['turntime']) / 1000
    strict = options.get('strict', False)
    end_wait = options.get('end_wait', 0.0)

    location = options.get('location', 'localhost')
    game_id = options.get('game_id', 0)

    error = ''

    bot_status = []
    bot_turns = []
    if capture_errors:
        error_logs = [HeadTail(log) for log in error_logs]
    try:
        # create bot sandboxes and test bot connection
        for b, bot in enumerate(bots):
            bot_status.append('survived')
            bot_turns.append(0)

            # ensure it started
            if not bot.sock:
                bot_status[-1] = 'crashed'
                if verbose_log:
                    verbose_log.write('bot %s did not start\n' % b)
                print('ERR : bot %s did not start\n' % b)
                # game.kill_player(b)
                game.stdin.write('-kill_player\n')
                game.stdin.flush()
                game.stdin.write(json.dumps(b))
                game.stdin.flush()

                if game.stdout.readline().strip() != "-job done":
                    print "Error : Game didn't kill bot"

        if stream_log:
            stream_log.write(game.get_player_start())
            stream_log.flush()

        if verbose_log:
            verbose_log.write('running for %s turns\n' % turns)

        for turn in range(turns+1):
            # print turn, bots
            if turn == 0:

                log.info("game starting")

                # game.start_game()
                game.stdin.write('-start_game\n')
                game.stdin.flush()

                log.info("started game")

                if game.stdout.readline().strip() != "-job done":
                    print "Error : Game didn't start"

            # send game state to each player
            for b, bot in enumerate(bots):
                log.info("testin player alive")
                # check if bot is alive
                # game.is_alive(b)
                alive = is_alive(game, b)

                log.info(
                    "is player " + str(b) + " alive ?? " + str(alive))

                if alive:
                    if turn == 0:
                        # game.get_player_start(b)
                        log.info("starting player")

                        game.stdin.write("?player_start\n")
                        game.stdin.flush()
                        game.stdin.write(str(b) + "\n")
                        game.stdin.flush()

                        player_start = str(json.loads(game.stdout.readline()))
                        start = player_start + 'ready\n'

                        # print start
                        bot.write(start)
                        if input_logs and input_logs[b]:
                            input_logs[b].write(start)
                            input_logs[b].flush()
                    else:
                        log.info("geetting player state")

                        # game.get_player_state(b)
                        game.stdin.write("?player_state\n")
                        game.stdin.flush()
                        game.stdin.write(str(b) + '\n')

                        player_state = str(json.loads(game.stdout.readline()))

                        log.info("player state done ")

                        state = 'turn ' + str(turn) + '\n' + player_state + 'go\n'

                        bot.write(state)
                        # print state
                        if input_logs and input_logs[b]:
                            input_logs[b].write(state)
                            input_logs[b].flush()
                        bot_turns[b] = turn

            # process start of turn
            if turn > 0:
                if stream_log:
                    stream_log.write('turn %s\n' % turn)
                    stream_log.write(
                        'score %s\n' % ' '.join(
                            [str(s) for s in game.get_scores()])
                    )
                    # game.get_state()
                    game.stdin.write("?state")
                    game.stdin.flush()

                    state = game.stdout.readline()
                    stream_log.write(state)
                    stream_log.flush()
                # processing all other normal turns
                # game.start_turn()

                log.info("starting turn " + str(turn))

                game.stdin.write('-start_turn\n')
                game.stdin.flush()

                log.info("started turn")

                if game.stdout.readline().strip() != "-job done":
                    print "Error: Game failed to start turn"

            # set up the turn time accordingly
            if turn == 0:
                time_limit = loadtime
            else:
                time_limit = turntime

            if options.get('serial', False):
                # int(True) is 1
                simul_num = int(options['serial'])
            else:
                simul_num = len(bots)

            # create object to hold bot moves
            bot_moves = [[] for b in bots]
            error_lines = [[] for b in bots]
            statuses = [None for b in bots]
            bot_list = [(b, bot) for b, bot in enumerate(bots)
                        if is_alive(game, b)]

            # NOTE: not sure why this has to be randomized
            random.shuffle(bot_list)
            for group_num in range(0, len(bot_list), simul_num):
                pnums, pbots = zip(*bot_list[group_num:group_num + simul_num])
                # this get moves will get bot move
                # if there is error here, update bot status
                moves, errors, status = get_moves(
                    game, pbots, pnums, time_limit, turn)
                for p, b in enumerate(pnums):
                    bot_moves[b] = moves[p]
                    error_lines[b] = errors[p]
                    statuses[b] = status[p]

            # handle any logs that get_moves produced
            for b, errors in enumerate(error_lines):
                if errors:
                    if error_logs and error_logs[b]:
                        error_logs[b].write(
                            unicode('\n').join(errors)+unicode('\n'))
            # set status for timeouts and crashes
            for b, status in enumerate(statuses):
                if status is not None:
                    bot_status[b] = status
                    bot_turns[b] = turn

            # process all moves
            log.info("check if game is over")

            bot_alive = [is_alive(game, b) for b in range(len(bots))]
            game.stdin.write("?game_over\n")
            game.stdin.flush()

            game_over_text = game.stdout.readline().strip()

            game_over = game_over_text == "True"

            log.info("game over text: " + str(game_over_text))
            log.info("game is over: " + str(game_over))

            if turn > 0 and not game_over:
                for b, moves in enumerate(bot_moves):
                    if is_alive(game, b):
                        # this is processing move and getting the game response
                        # which is either valid, ignored, or invalid
                        # game.do_moves(b, moves)
                        log.info("processing moves")

                        game.stdin.write('-do_moves\n')
                        game.stdin.flush()
                        game.stdin.write(str(b) + '\n')
                        game.stdin.flush()
                        game.stdin.write(json.dumps(moves) + "\n")
                        game.stdin.flush()

                        log.info("finish do moves")

                        log.info("process moves result")

                        result = json.loads(game.stdout.readline())

                        log.info("result " + str(result))

                        valid, ignored, invalid = result
                        if output_logs and output_logs[b]:
                            output_logs[b].write('# turn %s\n' % turn)
                            if valid:
                                if output_logs and output_logs[b]:
                                    output_logs[b].write('\n'.join(valid)+'\n')
                                    output_logs[b].flush()
                        if ignored:
                            for inv in ignored:
                                bots[b].write(
                                    'INFO: ignored ' + str(inv) + '\n')
                            if error_logs and error_logs[b]:
                                error_logs[b].write(
                                    'turn %4d bot %s ignored actions:\n'
                                    % (turn, b))
                                error_logs[b].write('\n'.join(ignored)+'\n')
                                error_logs[b].flush()
                            if output_logs and output_logs[b]:
                                output_logs[b].write('\n'.join(ignored)+'\n')
                                output_logs[b].flush()
                        if invalid:
                            for inv in invalid:
                                bots[b].write(
                                    'INFO: invalid ' + str(inv) + '\n')
                            if strict:
                                # when the move player pass back
                                # game engine will also remove player from game
                                # game.kill_player(b)
                                kill_player(game, b)
                                bot_status[b] = 'invalid'
                                bot_turns[b] = turn
                            if error_logs and error_logs[b]:
                                error_logs[b].write(
                                    'turn %4d bot %s invalid actions:\n'
                                    % (turn, b))
                                error_logs[b].write('\n'.join(invalid)+'\n')
                                error_logs[b].flush()
                            if output_logs and output_logs[b]:
                                output_logs[b].write('\n'.join(invalid)+'\n')
                                output_logs[b].flush()

                        log.info("finished processing result")

            if turn > 0:
                # when the turn is done, call finish_turn
                # game.finish_turn()

                log.info("finishing turn")

                game.stdin.write("-finish_turn\n")
                game.stdin.flush()

                if game.stdout.readline().strip() != "-job done":
                    print "ERROR: something is wrnog when finishing turn"

                log.info("finished turn")

            # send ending info to eliminated bots
            bots_eliminated = []
            for b, alive in enumerate(bot_alive):
                if alive and not is_alive(game, b):
                    bots_eliminated.append(b)
            for b in bots_eliminated:

                log.info("kill bot " + str(b))

                # game.get_scores(b)[0]

                game.stdin.write("?score\n")
                game.stdin.flush()
                game.stdin.write(str(b) + '\n')
                game.stdin.flush()

                bot_score = json.loads(game.stdout.readline())

                if verbose_log:
                    verbose_log.write(
                        'turn %4d bot %s eliminated\n' % (turn, b))
                if bot_status[b] == 'survived':
                    # could be invalid move
                    bot_status[b] = 'eliminated'
                    bot_turns[b] = turn
                state = 'end\ngame ' + str(bots[b].game_id) + ": \
                    " + str(bot_status[b]) + " score: " + str(bot_score) + " \
                    turn: " + str(turn) + "\ngo\n"
                # tell bot you are out
                bots[b].write(state)
                if input_logs and input_logs[b]:
                    input_logs[b].write(state)
                    input_logs[b].flush()
                if end_wait:
                    bots[b].resume()
            if bots_eliminated and end_wait:
                if verbose_log:
                    verbose_log.write(
                        'waiting {0} seconds for bots to process end turn\n'
                        .format(end_wait))
                time.sleep(end_wait)
            for b in bots_eliminated:
                bots[b].kill()

            if verbose_log:
                # game.get_stats()
                game.stdin.write("?stats\n")
                game.stdin.flush()

                stats = json.loads(game.stdout.readline())
                stat_keys = sorted(stats.keys())
                s = 'turn %4d stats: ' % turn
                if turn % 50 == 0:
                    verbose_log.write(' '*len(s))
                    for key, values in stats.items():
                        verbose_log.write(
                            ' {0:^{1}}'.format(
                                key,
                                max(len(key), len(str(values)))
                            )
                        )
                    verbose_log.write('\n')
                verbose_log.write(s)
                for key, values in stats.items():
                    verbose_log.write(
                        ' {0:^{1}}'.format(
                            values,
                            max(len(key), len(str(values)))
                        )
                    )
                verbose_log.write('\n')

            if game_over:
                break

        # send bots final state and score, output to replay file
        # game.finish_game()

        log.info("finishing game")

        game.stdin.write('-finish_game\n')
        game.stdin.flush()

        if game.stdout.readline().strip() != "-job done":
            print "ERROR: something is wrnog when finishing game"

        log.info("game finished")

        log.info("getting scores")

        game.stdin.write("?scores\n")
        game.stdin.flush()

        score = json.loads(game.stdout.readline())

        log.info("got score!")

        score_line = 'score %s\n' % ' '.join(map(str, score))
        status_line = 'status %s\n' % ' '.join(map(str, bot_status))
        end_line = 'end\nplayers %s\n' % len(bots) + score_line + status_line

        if stream_log:
            stream_log.write(end_line)
            stream_log.write(game.get_state())
            stream_log.flush()
        if verbose_log:
            verbose_log.write(score_line)
            verbose_log.write(status_line)
            verbose_log.flush()

        log.info("before sending end to player")

        for b, bot in enumerate(bots):
            if (is_alive(game, b)) and (bots[b].sock is not None):
                log.info("loading scores by player")

                game.stdin.write("?score\n")
                game.stdin.flush()
                game.stdin.write(str(b) + '\n')
                game.stdin.flush()

                score_player = json.loads(game.stdout.readline())

                log.info("loading scores by player done")

                state = 'end\ngame ' + str(bots[b].game_id) + ": " + str(bot_status[b]) + " score: " + str(score_player) + " turn: " + str(turn) + "\ngo\n"

                log.info(state)

                bot.write(state)
                if input_logs and input_logs[b]:
                    input_logs[b].write(state)
                    input_logs[b].flush()

        log.info("after sending end to player")

    except Exception as e:
        # TODO: sanitize error output, tracebacks shouldn't be sent to workers
        error = traceback.format_exc()
        if verbose_log:
            verbose_log.write(traceback.format_exc())
    finally:
        if end_wait:
            for bot in bots:
                bot.resume()
            if verbose_log:
                verbose_log.write(
                    'waiting {0} seconds for bots to process end turn\n'
                    .format(end_wait))
            time.sleep(end_wait)
        for bot in bots:
            if bot.is_alive:
                bot.kill()
            bot.release()

    if error:
        game_result = {'error': error}
    else:
        # game.get_scores()
        game.stdin.write("?scores\n")
        game.stdin.flush()

        scores = json.loads(game.stdout.readline())

        # game.get_replay()
        game.stdin.write("?replay\n")
        game.stdin.flush()

        replay = json.loads(game.stdout.readline())

        game_result = {
            'challenge': 'ants',
            'location': location,
            'game_id': game_id,
            'status': bot_status,
            'playerturns': bot_turns,
            'score': scores,
            'rank': [sorted(scores, reverse=True).index(x) for x in scores],
            'replayformat': 'json',
            'replaydata': replay,
            'game_length': turn
        }
        if capture_errors:
            game_result['errors'] = [head.headtail() for head in error_logs]

    if replay_log:
        json.dump(game_result, replay_log, sort_keys=True)

    return game_result


def is_alive(game, player):
    game.stdin.write("?is_alive\n")
    game.stdin.flush()
    game.stdin.write(str(player) + '\n')
    game.stdin.flush()

    alive_text = game.stdout.readline().strip()

    return alive_text == "True"


def kill_player(game, player):
    game.stdin.write('-kill_player\n')
    game.stdin.flush()
    game.stdin.write(json.dumps(player) + '\n')
    game.stdin.flush()

    if game.stdout.readline().strip() != "-job done":
        print "Error : Game didn't kill bot"


def get_moves(game, bots, bot_nums, time_limit, turn):
    bot_finished = [not is_alive(game, bot_nums[b]) for b in range(len(bots))]
    bot_moves = [[] for b in bots]
    error_lines = [[] for b in bots]
    statuses = [None for b in bots]
    start_time = time.time()

    # resume all bots
    for bot in bots:
        if bot.is_alive:
            bot.resume()

    # loop until received all bots send moves or are dead
    #   or when time is up
    while (sum(bot_finished) < len(bot_finished) and
            time.time() - start_time < time_limit):
        time.sleep(0.01)
        for b, bot in enumerate(bots):
            if bot_finished[b]:
                # already got bot moves
                continue
            if not bot.is_alive:
                error_lines[b].append(
                    unicode('turn %4d bot %s crashed') % (turn, bot_nums[b]))
                statuses[b] = 'crashed'
                line = bot.read_error()
                while line is not None:
                    error_lines[b].append(line)
                    line = bot.read_error()
                bot_finished[b] = True
                kill_player(game, bot_nums[b])
                # bot is dead
                continue

            # read a maximum of 100 lines per iteration
            for x in range(100):
                line = bot.read_line()
                if line is None:
                    # stil waiting for more data
                    break
                line = line.strip()
                if line.lower() == 'go':
                    bot_finished[b] = True
                    # bot finished sending data for this turn
                    break
                bot_moves[b].append(line)

            for x in range(100):
                line = bot.read_error()
                if line is None:
                    break
                error_lines[b].append(line)
    # pause all bots again
    for bot in bots:
        if bot.is_alive:
            bot.pause()

    # kill timed out bots
    for b, finished in enumerate(bot_finished):
        if not finished:
            error_lines[b].append(
                unicode('turn %4d bot %s timed out') % (turn, bot_nums[b]))
            statuses[b] = 'timeout'
            bot = bots[b]
            for x in range(100):
                line = bot.read_error()
                if line is None:
                    break
                error_lines[b].append(line)
            kill_player(game, bot_nums[b])
            bots[b].kill()

    return bot_moves, error_lines, statuses

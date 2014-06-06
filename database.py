#!/usr/bin/env python

import sqlite3
import datetime
import zlib
import os


class ContestDB():
    def __init__(self, file="ai_contenst_db.sqlite3"):
        self.db_is_new = not os.path.exists(file)
        self.con = sqlite3.connect(file)
        self.recreate()

    def __del__(self):
        try:
            self.con.close()
        except:
            pass

    def recreate(self):
        cur = self.con.cursor()
        try:
            cur.execute("create table \
                Users(\
                    id INTEGER PRIMARY KEY AUTOINCREMENT,\
                    name TEXT UNIQUE,\
                    password TEXT,\
                    email TEXT\
                )")

            cur.execute("create table \
                Bots(\
                    id INTEGER PRIMARY KEY AUTOINCREMENT,\
                    owner_id INTEGER,\
                    name TEXT UNIQUE,\
                    language TEXT\
                )")

            cur.execute("create table \
                Games(\
                    id INTEGER PRIMARY KEY AUTOINCREMENT,\
                    creator_id INTEGER,\
                    name TEXT UNIQUE,\
                    language TEXT,\
                    instruction_location TEXT,\
                    visualizer_location TEXT\
                )")

            cur.execute("create table \
                Tournaments(\
                    id INTEGER PRIMARY KEY AUTOINCREMENT,\
                    creator_id INTEGER,\
                    game_id INTEGER,\
                    name TEXT UNIQUE,\
                    password TEXT,\
                    start_date DATE,\
                    end_date DATE,\
                    last_active DATE\
                )")

            cur.execute("create table \
                Tourn_GameIndex(\
                    id INTEGER PRIMARY KEY AUTOINCREMENT,\
                    tourn_id INTEGER,\
                    player TEXT,\
                    gameid INTEGER\
                )")

            cur.execute("create table \
                Tourn_Games(\
                    id INTEGER primary key AUTOINCREMENT,\
                    tourn_id INTEGER,\
                    players TEXT,\
                    map TEXT,\
                    datum DATE,\
                    turns INTEGER DEFAULT 0,\
                    draws INTEGER DEFAULT 0\
                )")

            cur.execute("create table \
                Tourn_Entries(\
                    id INTEGER PRIMARY KEY AUTOINCREMENT,\
                    tourn_id INTEGER,\
                    bot_id INTEGER,\
                    lastseen DATE,\
                    rank INTEGER DEFAULT 1000,\
                    skill real DEFAULT 0.0,\
                    mu real DEFAULT 50.0,\
                    sigma real DEFAULT 13.3,\
                    ngames INTEGER DEFAULT 0,\
                    status bool DEFAULT True\
                )")

            cur.execute("create table \
                Tourn_Replays(\
                    id INTEGER,\
                    tourn_id INTEGER,\
                    json BLOB\
                )")

            cur.execute("create table \
                kill_client(\
                    name TEXT UNIQUE\
                )")

            if self.db_is_new:
                # Some predefined data
                self.update(
                    "insert into Users values(?, ?, ?, ?)",
                    (None, 'admin', 'cs460Ant', 'rcliao01@gmail.com')
                )

                self.con.commit()

            self.con.commit()
        except:
            pass

    # SQL INTERFACE

    def now(self):
        return datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    def update_defered(self, sql, tup=()):
        cur = self.con.cursor()
        cur.execute(sql, tup)

    def update(self, sql, tup=()):
        self.update_defered(sql, tup)
        self.con.commit()

    def retrieve(self, sql, tup=()):
        cur = self.con.cursor()
        cur.execute(sql, tup)
        return cur.fetchall()

    # READ

    def get_replay(self, t_id, id):
        rep = self.retrieve(
            "select json from Tourn_Replays where tourn_id=? AND id=?",
            (t_id, id)
        )
        return zlib.decompress(rep[0][0])

    def get_games(self):
        return self.retrieve(
            "select * from Games"
        )

    def get_game(self, game_id):
        return self.retrieve(
            "select * from Games where id = ?",
            (game_id, )
        )

    def num_tourn_games(self, t_id):
        return int(
            self.retrieve(
                "select count(*) from Tourn_Games where tourn_id=?",
                (t_id, )
            )[0][0]
        )

    def get_tourn_games(self, t_id, offset, num):
        return self.retrieve(
            "select * from Tourn_Games \
                where tourn_id=? \
                order by id desc limit ? offset ?",
            (t_id, num, offset)
        )

    def get_tourn_games_for_player(self, t_id, offset, num, player):
        arr = self.retrieve(
            "select gameid from Tourn_GameIndex \
                where tourn_id=? AND player=? \
                order by gameid desc limit ? offset ?",
            (t_id, player, num, offset)
        )
        g = []
        for a in arr:
            z = self.retrieve(
                "select * from Tourn_Games\
                 where tourn_id=? AND id=?",
                (t_id, a[0])
            )
            g.append(z[0])
        return g

    def num_tourn_games_for_player(self, t_id, player):
        return int(
            self.retrieve(
                "select count(*) from Tourn_GameIndex \
                    where tourn_id=? AND player=?",
                (t_id, player)
            )[0][0]
        )

    def num_players(self, t_id):
        return int(
            self.retrieve(
                "select count(*) from Tourn_Entries \
                    where tourn_id=?",
                (t_id, )
            )[0][0]
        )

    def get_bots(self, username):
        return self.retrieve(
            "select b.name, e.status, b.id, t.id, t.name from Bots AS b \
                INNER JOIN Users u on u.id=b.owner_id \
                INNER JOIN Tourn_Entries as e on b.id=e.bot_id \
                INNER JOIN Tournaments as t on e.tourn_id = t.id \
                where u.name=?",
            (username, )
        )

    def get_bot(self, botname):
        return self.retrieve(
            "select * from Bots where name=?",
            (botname, )
        )

    def authenticate_user(self, name, password):
        return self.retrieve(
            "select id from Users where name=? AND password=?",
            (name, password)
        )

    def get_ranks(self, t_id, table_lines, offset):
        return self.retrieve(
            "select * from Tourn_Entries as e \
                inner join Bots as b on e.bot_id = b.id \
                where tourn_id=? \
                order by skill desc limit ? offset ?",
            (t_id, table_lines, offset)
        )

    # Checks if a username is available
    # Returns True if available
    # Returns False if not available (already in database)
    def check_username(self, username):
        if self.retrieve("select id from Users where name=?", (username, )):
            return False
        else:
            return True

    def get_tournaments(self, tournamentname='', username=''):
        if tournamentname:
            return self.retrieve(
                "select * from Tournaments where name=?",
                (tournamentname, )
            )
        else:
            # only return the public tournament
            if username:
                user_id = self.retrieve(
                    "select * from Users where name=?",
                    (username, )
                )[0][0]
                return self.retrieve(
                    "select * from Tournaments \
                        where password = '' \
                        or password is null \
                        or creator_id=?",
                    (user_id, )
                )
            else:
                return self.retrieve(
                    "select * from Tournaments \
                        where password = '' or password is null"
                    )

    def get_tournament_name(self, t_id):
        return self.retrieve(
            "select name from Tournaments where id=?",
            (t_id, )
        )

    def get_bot_tournaments(self, t_id, bot_id):
        return self.retrieve(
            "select * from Tourn_Entries \
                where tourn_id=? AND bot_id=?",
            (t_id, bot_id)
        )

    def get_tournaments_user(self, username):
        user = self.retrieve(
            "select * from Users where name=?",
            (username, )
        )
        return self.retrieve(
            "select * from Tournaments \
                where creator_id=?",
            (user[0][0], )
        )

    def get_kill_client(self):
        sql = "select * from kill_client"
        return self.retrieve(sql)

    def get_player_lastseen(self, t_id, bot_id):
        return self.retrieve(
            "select lastseen from Tourn_Entries \
                where tourn_id=? AND bot_id=?",
            (t_id, name)
        )

    def get_player(self, t_id, botname):
        sql = "select * from Tourn_Entries AS e \
            INNER JOIN Bots AS b on e.bot_id=b.id \
            where e.tourn_id=? AND b.name=?"
        return self.retrieve(sql, (t_id, botname))

    def get_last_active_tourn(self):
        sql = "select * from Tournaments \
            ORDER BY date(last_active) DESC LIMIT 1"
        return self.retrieve(sql)

    def get_live_bots(self, t_id):
        sql = "select * from Bots as b \
            INNER JOIN Tourn_Entries as e on e.bot_id = b.id \
            where e.tourn_id = ? and e.status=1"
        return self.retrieve(sql, (t_id, ))

    def get_tourn_game(self, t_id):
        sql = "select * from Games as g \
            inner join Tournaments as t on g.id = t.game_id \
            where t.id = ?"
        return self.retrieve(sql, (t_id, ))

    # WRITE

    def add_replay(self, t_id, id, txt):
        data = buffer(zlib.compress(txt))
        self.update(
            "insert into Tourn_Replays values(?, ?, ?)",
            (id, t_id, data)
        )

    def add_tourn_game(self, t_id, i, map, turns, draws, players):
        self.update(
            "insert into Tourn_Games values(?, ?, ?, ?, ?, ?, ?)",
            (i, t_id, players, self.now(), map, turns, draws)
        )

    def add_tournament(self, username, tournamentname, password, gamename):
        user = self.retrieve(
            "select * from Users where name=?",
            (username, )
        )
        game_id = self.retrieve(
            "select id from Games where name=?",
            (gamename, )
        )[0][0]
        if password:
            self.update(
                "insert into Tournaments values(?,?,?,?,?,?,?,?)",
                (
                    None,
                    user[0][0],
                    game_id,
                    tournamentname,
                    password,
                    self.now(),
                    self.now(),
                    self.now()
                )
            )
        else:
            self.update(
                "insert into Tournaments values(?,?,?,?,?,?,?,?)",
                (
                    None,
                    user[0][0],
                    game_id,
                    tournamentname,
                    None,
                    self.now(),
                    self.now(),
                    self.now()
                )
            )

    def add_user(self, name, password, email):
        self.update(
            "insert into Users values(?,?,?,?)",
            (None, name, password, email)
        )

    def add_game(self, username, gamename, language, instruction, visualizer):
        user_id = self.retrieve(
            "select id from Users where name = ?",
            (username, )
        )[0][0]
        self.update(
            "insert into Games values(?,?,?,?,?,?)",
            (None, user_id, gamename, language, instruction, visualizer)
        )

    def enroll_bot(self, t_id, bot_id):
        existingbot = self.retrieve(
            "select * from Tourn_Entries \
                where bot_id=? and tourn_id=?",
            (bot_id, t_id)
        )
        if len(existingbot) == 0:
            self.update(
                "insert into Tourn_Entries values(?,?,?,?,?,?,?,?,?,?)",
                (
                    None,
                    t_id,
                    bot_id,
                    self.now(),
                    1000,
                    0.0,
                    50.0,
                    50.0/3.0,
                    0,
                    1
                )
            )

    def disenroll_bot(self, t_id, bot_id):
        self.update(
            "delete from Tourn_Entries \
                where tourn_id=? and bot_id=?",
            (t_id, bot_id)
        )

    def add_bot(self, username, botname, language):
        u_id = self.retrieve(
            "select id from Users where name=?",
            (username, )
        )
        self.update(
            "insert into Bots values(?,?,?,?)",
            (None, u_id[0][0], botname, language)
        )

    def terminate_bot(self, botname, t_id):
        bot_id = self.retrieve(
            "select id from Bots where name=?",
            (botname, )
        )
        self.update_defered(
            "update Tourn_Entries \
                SET status=0 where bot_id=? and tourn_id=?",
            (bot_id[0][0], t_id)
        )

    def start_bot(self, botname, t_id):
        bot_id = self.retrieve(
            "select id from Bots where name=?",
            (botname, )
        )
        self.update_defered(
            "update Tourn_Entries \
                SET status=1 where bot_id=? and tourn_id=?",
            (bot_id[0][0], t_id)
        )

    def delete_player(self, name):
        self.update("insert into kill_client values('%s');" % name)

    def delete_kill_name(self, name):
        self.update("delete from kill_client where name = '%s';" % name)

    def delete_tournament(self, t_id):
        self.update("delete from Tournaments where id=?", (t_id, ))

    def update_player_skill(self, t_id, botname, skill, mu, sig):
        bot_id = self.retrieve(
            "select id from Bots where name=?",
            (botname, )
        )
        self.update_defered(
            "update Tourn_Entries \
                set ngames=ngames+1, lastseen=?, skill=?, mu=?, sigma=? \
                where tourn_id=? AND bot_id=?",
            (self.now(), skill, mu, sig, t_id, bot_id[0][0])
        )

    def update_player_status(self, t_id, bot_id, status):
        self.update_defered(
            "update Tourn_Entries \
                set status=? where tourn_id=? bot_id=?",
            (status, t_id, bot_id)
        )

    # needs a final commit()
    def update_player_rank(self, t_id, bot_id, rank):
        self.update_defered(
            "update Tourn_entries \
                set rank=? where tourn_id=? AND bot_id=?",
            (rank, t_id, bot_id)
        )

    def update_tournament_activity(self, t_id):
        sql = "update Tournaments set last_active=? where id=?"
        self.update_defered(sql, (self.now(), t_id))

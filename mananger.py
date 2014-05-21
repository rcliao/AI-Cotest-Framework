import threading

import tcpclient
import game_db

"""
    This mananger will match live bots in the same tournament, and instantiate
    bots as tcpclients to connect to tcpserver
"""

# dirty global to track which bot is currently active
current_bots = []


def addBot(cmd, botname):
    bot = botClient(cmd, botname)
    bot.setName(botname)

    for b in current_bots:
        if not b.is_alive():
            current_bots.remove(b)

    if not isBotAlive(bot):
        current_bots.append(bot)
        bot.start()
        print bot.getName()


def isBotAlive(bot):
    for b in current_bots:
        if b.getName() == bot.getName():
            return True

    return False


class botClient(threading.Thread):
    def __init__(self, cmd, botname):
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.botname = botname

    def run(self):
        tcpclient.tcp('localhost', 2081, self.cmd, self.botname, {})


def run():
    # create a infinite loop to server for mananger
    db = game_db.GameDB()
    while(True):
        last_active = db.get_last_active_tourn()

        if last_active:

            active_bots = db.get_live_bots(last_active[0][0])

            for bot in active_bots:
                # TODO: implement more language support
                if bot[3] == "java":
                    botname = bot[2]
                    cmd = "java -jar Bots/" + botname + ".jar"
                    addBot(cmd, botname)


def main():
    run()

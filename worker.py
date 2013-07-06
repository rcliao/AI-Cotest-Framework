#!/usr/bin/env python
# -*- coding: utf-8 -*-
import threading

import tcpclient


class BotClient(threading.Thread):
    def __init__(self, cmd, botname, password):
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.botname = botname
        self.password = password

    def run(self):
        tcpclient.run_forever('localhost', 2081, self.cmd,
                              self.botname, self.password)


def addBot(cmd, botname, password):
    BotClient(cmd, botname, password).start()


def main():
    # so far nothing will be executed, maybe add a way to loop through the
    # /Bots/ folder to find all the bot and execute them or loop though DB
    # to find Bots to execute automatically
    BotClient.start()

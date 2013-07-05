# TODO: all these import are directly from tcpclient, check if anything is not necessary
import threading
import subprocess
import time
import sys
import re
import string
import random
from socket import socket, AF_INET, SOCK_STREAM

import tcpclient

def addBot(cmd, botname, password):
	botClient(cmd, botname, password).start()

class botClient(threading.Thread):
	def __init__(self, cmd, botname, password):
		threading.Thread.__init__(self)
		self.cmd = cmd
		self.botname = botname
		self.password = password

	def run(self):
		tcpclient.run_forever('localhost', 2081, self.cmd, self.botname, self.password)


def main():
	# so far nothing will be executed, maybe add a way to loop through the
	# /Bots/ folder to find all the bot and execute them or loop though DB
	# to find Bots to execute automatically
	botClient.start()

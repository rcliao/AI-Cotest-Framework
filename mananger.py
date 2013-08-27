import threading
import subprocess
import time
import sys
import re
import string
import random
from socket import socket, AF_INET, SOCK_STREAM

import tcpclient
import game_db

"""
	This mananger will match live bots in the same tournament, and instantiate bots as tcpclients
	to connect to tcpserver

	TODO:
		Change the tcpclient to run locally instead of the socket connection to server,
		this probably also requires changes in tcpserver.
"""

# dirty global to track which bot is currently active
current_bots = []

def addBot(cmd, botname):
	botClient(cmd, botname).start()
	current_bots.append(botname)

def removeBot(botname):
	current_bots.remove( botname )


class botClient(threading.Thread):
	def __init__(self, cmd, botname):
		threading.Thread.__init__(self)
		self.cmd = cmd
		self.botname = botname

	def run(self):
		tcpclient.run_forever('localhost', 2081, self.cmd, self.botname)

def run():
	# create a infinite loop to server for mananger
	db = game_db.GameDB()
	while( True ):
		if len(current_bots) == 0:
			last_active = db.get_last_active_tourn()

			active_bots = db.get_live_bots( last_active[0][0] )

			for bot in active_bots:
				# TODO: implement more language support
				if bot[3] == "java":
					botname = bot[2]
					if botname not in current_bots:
						cmd = "java -jar Bots/" + botname + ".jar"
						print 'started a java bot'
						addBot(cmd, botname)


def main():
	run()

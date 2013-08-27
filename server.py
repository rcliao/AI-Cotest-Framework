# A service that starts everything else, and make connection between server and
# worker easier instead of relying on the socket connection

import tcpserver
import webserverG2
import threading
import signal
import mananger

class WebThread(threading.Thread):
    def __init__(self, workers):
        threading.Thread.__init__(self)
        self.workers = workers
        
    def run(self):
        webserverG2.main(2080, workers)

class TCPThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        tcpserver.main()

class WorkerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        worker.main()

    def addBot(self, cmd, botname):
        worker.addBot(cmd, botname)

if __name__ == '__main__':

    try:
        tcpthread = TCPThread()
        tcpthread.start()
        workers = WorkerThread()
        workers.start()
        webthread = WebThread(workers)
        webthread.start()
    except KeyboardInterrupt:
        pass
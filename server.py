# A service that starts everything else, and make connection between server and
# worker easier instead of relying on the socket connection

import tcpserver
import webserver
import threading
import signal
import mananger

class WebThread(threading.Thread):
    def __init__(self, manangerThread):
        threading.Thread.__init__(self)
        self.manangerThread = manangerThread
        
    def run(self):
        webserver.main(2080, self.manangerThread)

class TCPThread(threading.Thread):
    def __init__(self, manangerThread):
        threading.Thread.__init__(self)
        self.manangerThread = manangerThread

    def run(self):
        tcpserver.main(manangerThread)

class ManangerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        mananger.main()

    def addBot(self, cmd, botname):
        mananger.addBot(cmd, botname)


if __name__ == '__main__':

    try:
        manangerThread = ManangerThread()
        tcpthread = TCPThread(manangerThread)
        tcpthread.start()
        webthread = WebThread(manangerThread)
        webthread.start()

        manangerThread.start()
    except KeyboardInterrupt:
        manangerThread.kill()
        tcpthread.kill()
        webthread.kill()
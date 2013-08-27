# A service that starts everything else, and make connection between server and
# worker easier instead of relying on the socket connection

import tcpserver
import webserver
import threading
import signal
import mananger

class WebThread(threading.Thread):
    def __init__(self, mananger):
        threading.Thread.__init__(self)
        self.manangerThread = manangerThread
        
    def run(self):
        webserver.main(2080, manangerThread)

class TCPThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        tcpserver.main()

class ManangerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        mananger.main()

if __name__ == '__main__':

    try:
        tcpthread = TCPThread()
        tcpthread.start()
        manangerThread = ManangerThread()
        manangerThread.start()
        webthread = WebThread(manangerThread)
        webthread.start()
    except KeyboardInterrupt:
        pass
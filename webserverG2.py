from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import os
import re
import threading
import logging
import json
import random
import time
import SimpleHTTPServer
import socket
import cgi
import Cookie

import urllib
import urlparse

import game_db
from tcpserver import load_map_info

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# add formatter to ch
ch.setFormatter(formatter)

# create logger
log = logging.getLogger('web')
log.setLevel(logging.DEBUG)
# add ch to logger
log.addHandler(ch)

# TODO: maybe creating another stylesheet file would be easier for our life ...
#   Instead of this static css file throughout the website
style = """
    a{
        text-decoration: none;
        color:#000;
    }
    a:hover{
        color:#aaa;
    }
    body {
        font-family:Calibri,Helvetica,Arial;
        font-size:11pt;
        color:#111;
        width: 1000px;
        margin: 0 auto;
        /*background: -webkit-gradient(linear, left top, 0% 100%, from(#E6E6B8), to(#4C4C3D));*/
        background-color: rgb(82,82,77);
        background-image: -webkit-gradient(linear, 0 0, 0 100%, color-stop(.1, rgba(255, 255, 255, .3)), color-stop(.5, transparent), to(transparent));
        -webkit-background-size: 5px 3px;
    }
    #wrapper {
        margin: 0px auto;
        padding: 10px 10px;
        width: 1000px;
        min height: 600px;
        background: #F0F0F0;
        border-style:groove;
        border-width:5px;
        border-color:#FFCC33;
        border-top-style:none;
    }
    #headerIMG {
        width:1020px;
        border-style:groove;
        border-width:5px;
        border-color:#FFCC33;
        border-top-style:none;
        border-bottom-style:none;
    }
    #headerwrap {
        width: 1000px;
        float: left;
        margin: 0 auto;
    }
    #header {
        font-size:14pt;
        color:#FFF;
        height: 40px;
        background: #FFCC33;
        /*border-radius: 10px;*/
        border: 1px solid #ebb81f;
        margin: 10px;
        padding: 5px;
    }
    hr {
        color:#111;
        background-color:#555;
    }
    table.tablesorter {
        background-color: #CDCDCD;
        font-family: Calibri,Helvetica,Arial;
        font-size: 11pt;
        margin: 10px 10px 15px 10px;
        text-align:left;
    }
    table.tablesorter thead tr th tfoot  {
        background-color:#E6EEEE;
        border:1px solid #FFFFFF;
        font-size:8pt;
        padding:4px 40px 4px 4px;
        background-position:right center;
        background-repeat:no-repeat;
        cursor:pointer;
    }
    table.tablesorter tbody td {
        background-color:#FFFFFF;
        color:#3D3D3D;
        padding:4px;
        vertical-align:top;
    }
    table.tablesorter tbody tr.odd td {
        background-color:#F0F0F6;
    }
    table.tablesorter thead tr .headerSortUp {
        background-color:#AAB;
    }
    table.tablesorter thead tr .headerSortDown {
        background-color:#BBC;
    }
"""

table_lines = 100

class AntsHttpServer(HTTPServer):
    def __init__(self, *args):
        self.opts = None

        ## anything static gets cached on startup here.
        self.cache = {}
        self.cache_file("/favicon.ico","favicon.ico")
        self.cache_file("/tcpclient.py", "clients/tcpclient.py")
        self.cache_file("/tcpclient.py3", "clients/tcpclient.py3")
        self.cache_dir("js")
        self.cache_dir("maps")
        self.cache_dir("data/img")

        self.maps = load_map_info()
        self.db = game_db.GameDB()

        HTTPServer.__init__(self, *args)


    def cache_file(self,fname,fpath):
        try:
            f = open(fpath,"rb")
            data = f.read()
            f.close()
            log.info("added static %s to cache." % fname)
            self.cache[fname] = data
        except Exception, e:
            log.error("caching %s failed. %s" % (fname,e))


    def cache_dir(self, dir):
        for root,dirs,filenames in os.walk(dir):
            for filename in filenames:
                # fpath is the actual system path.
                fpath = os.path.join(root, filename)
                # fname is the name used by the client.
                fname = '/' + fpath
                fname = fname.replace('\\', '/')
                self.cache_file(fname, fpath)


class AntsHttpHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def __init__(self, *args):
        SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(self, *args)

    ## this suppresses logging from SimpleHTTPRequestHandler
    ## comment this method if you want to see them
    ##def log_message(self,format,*args):
    ##    pass
    
    def send_head(self, type='text/html'):
        self.send_response(200)
        self.send_header('Content-type',type)
        self.end_headers()

    def header(self, title):
        self.send_head()

        head = """<html><head>
        <!--link rel="icon" href='/favicon.ico'-->
        <title>"""  + title + """</title>
        <style>"""  + style + """</style>"""
        if str(self.server.opts['sort'])=='True':
            head += """
                <script src="http://code.jquery.com/jquery-1.9.1.js"></script>
                <script type="text/javascript" src="/js/jquery.tablesorter.min.js"></script>
                <script src="http://code.jquery.com/ui/1.10.3/jquery-ui.js"></script>
                """
        head += """</head><body><b>
        <div id="headerIMG">
        <img src="/data/img/header4ants.jpg">
        </div>
        <div id="wrapper">
        <div id = "headerwrap">
        """
        if (self.check_auth()):
            head += """
            <a href="/logout">Hi, """ + self.username + """ logout here!</a>
            """
        else:
            head += """<a href='/login' name=top> Login </a> | 
            <a href='/register' name=top> Register </a>"""

        head += """
        <div id="header">
        <a href='/howto' name=top><img src="/data/img/gettingStartedIco.png"/> Getting Started </a> &nbsp;&nbsp;&nbsp;&nbsp;
        <a href='/' name=top><img src="/data/img/gameLogIco.png"/> Games </a> &nbsp;&nbsp;&nbsp;&nbsp;
        <a href='/ranking'><img src="/data/img/rankingsIco.png"/> Rankings </a> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <a href='/maps'><img src="/data/img/mapsIco.png"/> Maps </a> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        """
        if (self.check_auth()):
            head += """
            <a href='/user/""" + self.username + """' title='Profile'> Profile </a>
            """
        head += """
        </div>
        </div>
        <br><p></b>
        """
        return head


    def footer_sort(self, id):
        if str(self.server.opts['sort'])=='True':
            return """
                <script>
                $(document).ready(function() { $("#%s").tablesorter(); });
                </script>
            """ % id
        return ""

    def footer(self):
        apic="^^^"
        return "<p><br> &nbsp;<a href=#top title='crawl back to the top'> " + apic + "</a>"


    def serve_visualizer(self, match):
        try:
            junk,gid = match.group(0).split('.')
            replaydata = self.server.db.get_replay( 1, gid )
        except Exception, e:
            self.send_error(500, '%s' % (e,))
            return
        html = """
            <html>
            <head>
                <title>Ant Canvas</title>
                <script type="text/javascript" src="/js/visualizer.js"></script>
                <script type="text/javascript">
                    window.isFullscreenSupported = function() {
                        return false;
                    };

                    function init() {
                        var options = new Options();
                        options.data_dir = '/data/';
                        options.embedded = true;
                        var visualizer = new Visualizer(document.body, options);
                        visualizer.loadReplayData('"""+replaydata+"""');
                    }
                </script>
                <style type="text/css">
                    html { margin:0; padding:0; }
                    body { margin:0; padding:0; overflow:hidden; }
                </style>
            </head>
            <body>
               <script>init();</script>
            </body>
            </html>
            """
        self.wfile.write(html)


    def game_head(self):
        return """<table id='games' class='tablesorter' width='98%'>
            <thead><tr><th>Game </th><th>Players</th><th>Turns</th><th>Date</th><th>Map</th></tr></thead>"""


    def game_line(self, g):
        html = "<tr><td width=10%><a href='/replay." + str(g[0]) + "' title='Run in Visualizer'> Replay " + str(g[0]) + "</a></td><td>"
        for key, value in sorted(json.loads(g[2]).iteritems(), key=lambda (k,v): (v,k), reverse=True):
            html += "&nbsp;&nbsp;<a href='/player/" + str(key) + "' title='"+str(value[1])+"'>"+str(key)+"</a> (" + str(value[0]) + ") &nbsp;"
        html += "</td><td>" + str(g[5]) + "</td>"
        html += "</td><td>" + str(g[3]) + "</td>"
        html += "<td><a href='/map/" + str(g[4]) + "' title='View the map'>" + str(g[4]) + "</a></td>"
        html += "</tr>\n"
        return html


    def rank_head(self):
        return """<table id='players' class='tablesorter' width='98%'>
            <thead><tr><th>Rank</th><th>Player</th><th>Skill</th><th>Mu</th><th>Sigma</th><th>Games</th><th>Last Seen</th><th>Delete</th><th>Status</th></tr></thead>"""

    def page_counter(self,url,nelems):
        if nelems < table_lines: return ""
        html = "<table class='tablesorter'><tr><td>Page</td><td>&nbsp;&nbsp;"
        for i in range(min((nelems+table_lines)/table_lines,10)):
            html += "<a href='"+url+"p"+str(i)+"'>"+str(i)+"</a>&nbsp;&nbsp;&nbsp;"
        html += "</td></tr></table>"
        return html

    def rank_line( self, p ):
        html = "<tr>"
        #Bot Rank
        html += "<td>%d</td>"    % p[4]
        #Bot Name
        html += "<td><a href='/player/" + str(p[12]) + "'><b>"+str(p[12])+"</b></a></td>"
        
        html += "<td>%2.4f</td>" % p[5]
        html += "<td>%2.4f</td>" % p[6]
        html += "<td>%2.4f</td>" % p[7]
        html += "<td>%d</td>"    % p[8]
        html += "<td>%s</td>"    % p[3]
        html += "<td><a href='/ranking?%s'><b>delete</b></a></td>" % str("delete=" + str(p[2]))
        html += "<td>%s</td>"    % p[9]
        html += "</tr>\n"
        return html

    def bots_head(self):
        return """<table id='players' class='tablesorter' width='98%'>
            <thead><tr><th>Bot Name</th><th>Status</th><th>Operation</th></tr></thead>"""

    def bots_line( self, p ):
        html = "<tr>"
        #Bot Name
        html += "<td><a href='/player/" + str(p[2]) + "'><b>"+str(p[2])+"</b></a></td>"
        html += "<td> TBI </td>"
        html += "<td>\
                <form enctype='multipart/form-data' action='/uploading' method='post'>\
                <input type='file'  name='file'><input type='submit' name='Upload' value='Upload'>\
                <input type='submit' name='Terminate' value='Terminate'>\
                <input type='submit' name='Start' value='Start'></td>\
                <input type='hidden' name='botname' value=" + str(p[1]) + "/>\
                </form>"
        html += "</tr>\n"
        return html

    def serve_howto(self, match):
        html = self.header( "HowTo" )
        html += """
        Here's how to play a game on TCP...</ br>
        <ol>
        <li>Download the starter package from <a href="">here</a> and get started with <a href="">tutorial</a></li>
        <li>Sign up an account</li>
        <li>Sign in with your account and go to your profile page</li>
        <li>Upload your bot</li>
        <li>Once you uploaded your bot, your bot will be automatically enrolled for the "Main Tournament"</li>
        <li>Check your status under the tournament you selected</li>
        <li>Profit!</li>
        </ol>
        </ br>
        """
        html += self.footer()
        html += "</body></html>"
        self.wfile.write(html)

    def serve_maps(self, match):
        html = self.header( "%d maps" % len(self.server.maps) )
        html += "<table id='maps' class='tablesorter' width='70%'>"
        html += "<thead><tr><th>Mapname</th><th>Players</th><th>Rows</th><th>Cols</th></tr></thead>"
        html += "<tbody>"
        for k,v in self.server.maps.iteritems():
            html += "<tr><td><a href='/map/"+str(k)+"'>"+str(k)+"</a></td><td>"+str(v[0])+"</td><td>"+str(v[1])+"</td><td>"+str(v[2])+"</td></tr>\n"
        html += "</tbody>"
        html += "</table>"
        html += self.footer()
        html += self.footer_sort('maps')
        html += "</body></html>"
        self.wfile.write(html)


    def serve_main(self, match):
        html = self.header("Ant Server")
        html += self.game_head()
        html += "<tbody>"
        offset=0
        if match and (len(match.group(0))>2):
            offset=table_lines * int(match.group(0)[2:])

        for g in self.server.db.get_games(1, offset,table_lines):
            html += self.game_line(g)
        html += "</tbody></table>"
        html += self.page_counter("/", self.server.db.num_games( 1 ) )
        html += self.footer()
        html += self.footer_sort('games')
        html += "</div></body></html>"
        self.wfile.write(html)


    def serve_player(self, match):
        # get player name using match(Regex)
        player = match.group(0).split("/")[2]
        res = self.server.db.get_player(1, player)
        if len(res)< 1:
            self.send_error(404, 'Player Not Found: %s' % self.path)
            return
        html = self.header( player )
        html += self.rank_head()
        html += "<tbody>"
        html += self.rank_line( res[0] )
        html += "</tbody></table>"
        html += self.game_head()
        html += "<tbody>"
        offset = 0
        if match:
            toks = match.group(0).split("/")
            if len(toks)>3:
                offset=table_lines * int(toks[3][1:])
        for g in self.server.db.get_games_for_player(1, offset, table_lines, player):
            html += self.game_line(g)
        html += "</tbody></table>"
        html += self.page_counter("/player/"+player+"/", self.server.db.num_games_for_player(1, player) )
        html += self.footer()
        html += self.footer_sort('games')
        html += "</body></html>"
        self.wfile.write(html)



    def serve_ranking(self, match):
        html = self.header("Rankings")
        html += self.rank_head()

        path2 = urlparse.urlparse(self.path)
        path3 = urlparse.parse_qs(path2.query)
        if 'delete' in path3:
            #html += "val of delete: " + str(path3['delete']) + "<br/>"
            cleanParam = str(path3['delete']).replace("[","")
            cleanParam = cleanParam.replace("]","")
            cleanParam = cleanParam.replace("'","")
            #html += "new val: " + cleanParam
            self.server.db.delete_player(cleanParam)

        html += "<tbody>"
        offset=0
        if match:
            toks = match.group(0).split("/")
            if len(toks)>2:
                offset=table_lines * int(toks[2][1:])
        for p in self.server.db.get_ranks(1, table_lines, offset):
            html += self.rank_line( p )

        html += "</tbody></table>"
        html += self.page_counter("/ranking/", self.server.db.num_players( 1 ) )
        html += self.footer()
        html += self.footer_sort('players')
        html += self.path
        #html += str(path2) + "<br/>"
        #html += str(path3) + "<br/>"


            #self.server.db.delete_player(str(path3['delete']))
            #self.server.db.delete_player(str(path3['delete']))
        #path3 = urlparse.parse_qs(path2.query)['delete']
        #html += str(path3)
        #html += urlparse.urlparse(self.path)
        #html += urlparse.parse_qs(urlparse.uslparse(self.path).query)['delete']
        html += "</body></html>"
        self.wfile.write(html)


    def serve_map( self, match ):
        try:
            mapname = match.group(1)
            m = self.server.cache[mapname]
        except:
            self.send_error(404, 'Map Not Found: %s' % self.path)
            return
        w=0
        h=0
        s=5
        jsmap = "var jsmap=[\n"
        for line in m.split('\n'):
            line = line.strip().lower()
            if not line or line[0] == '#':
                continue
            key, value = line.split(' ')
            if key == 'm':
                jsmap += '\"' + value + "\",\n"
            if key == 'rows':
                h = int(value)
            if key == 'cols':
                w = int(value)
        jsmap += "]\n"

        html = self.header(mapname)
        html += "&nbsp;&nbsp;&nbsp;<canvas width="+str(s*w)+" height="+str(s*h)+" id='C'><p>\n<script>\n"+jsmap+"var square = " + str(s) + "\n"
        html +="""
            var colors = { '%':'#1e3f5d', '.':'#553322', 'a':'#4ca9c8', 'b':'#6a9a2a', 'c':'#8a2b44', 'd':'#ff5d00', 'e':'#4ca9c8', 'f':'#6a9a2a', 'g':'#8a2b44', 'h':'#ff5d00', '0':'#4ca9c8', '1':'#6a9a2a', '2':'#8a2b44', '3':'#ff5d00', '4':'#4ca9c8', '5':'#6a9a2a', '6':'#8a2b44', '7':'#ff5d00' }
            var C = document.getElementById('C')
            var V = C.getContext('2d');
            for (var r=0; r<jsmap.length; r++) {
                var line = jsmap[r]
                for (var c=0; c<line.length; c++) {
                    V.fillStyle = colors[line[c]]
                    V.fillRect(c*square,r*square,square,square);
                }
            }
            </script>
            </canvas>
            """
        html += self.footer()
        html += "</body></html>"
        self.wfile.write(html)


    ## static files aer served from cache
    def serve_file(self, match):
        mime = {'png':'image/png','jpg':'image/jpeg','jpeg':'image/jpeg','gif':'image/gif','js':'text/javascript','py':'application/python','html':'text/html'}
        try:
            junk,end = match.group(0).split('.')
            mime_type = mime[end]
        except:
            mime_type = 'text/plain'

        fname = match.group(0)
        if not fname in self.server.cache:
            self.send_error(404, 'File Not Found: %s' % self.path)
            return

        self.send_head(mime_type)
        self.wfile.write(self.server.cache[fname] )

    def serve_upload(self, match):
        if self.check_auth():
            # create the html page for uploading file using the same header
            html = self.header("Upload File Here")
            html += """
            <form enctype="multipart/form-data" action="/uploading" method="post">
            <p>Password: <input type="text" name="password"></p>
            <p>File: <input type="file" name="file"></p>
            <p><input type="submit" value="Upload"></p>
            </form>
            </body></html>
            """
            self.wfile.write(html)
        else:
            # code 301 for redirect
            self.send_response(301)
            self.send_header("Location", "login")
            self.end_headers()

    def serve_uploading(self, match):
        # get the form data from the post request
        form = cgi.FieldStorage(
            fp=self.rfile, 
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })

        # A nested FieldStorage instance holds the file
        fileitem = form['file']
        password = form.getfirst('password', '')
        username = form.getfirst('username', '')
        botname = form.getfirst('botname', '')

        
        if "Upload" in form:
            # Test if the file was uploaded
            if fileitem.filename:
               
               # strip leading path from file name to avoid directory traversal attacks
               fn = os.path.basename(fileitem.filename)
               # upload the bot under /Bots/ Folder as it is
               open('Bots/' + fn, 'wb').write(fileitem.file.read())
               message = 'The file "' + fn + '" was uploaded successfully'
               
            else:
               message = 'No file was uploaded'

            # Automatically execute the bot as tcpclient
            if fn:
                # init the filename, filepath to create command differently for each extension
                botname,sep,ext = fn.rpartition('.')

                if ext == 'jar':
                    command = 'java -jar Bots/' + fn
                    language = 'java'
            
                self.server.workers.addBot(command, botname)

                existingBot = self.server.db.get_bot( botname )

                if not existingBot:
                    # TODO: change to add bot including username later
                    self.server.db.add_bot( username, botname, language )
                    self.server.db.enroll_bot( 1, botname )
               
            
            html = self.header("File Uploaded")
            html += message + """
            </body></html>
            """
            self.wfile.write(html)
        elif "Terminate" in form:
            # terminate bot
            # self.server.db.terminate_bot( botname )
            print 'Terminate Bot' + botname
            pass
        elif "Start" in form:
            # start bot
            # self.server.db.start_bot( botname )
            print 'Start Bot' + botname
            pass

    def serve_register(self, match):
        #TODO add client side check for each of the fields
        html = self.header("Register")
        html += """
        <form enctype="multipart/form-data" action="/registering" method="post">
        <p>Username: <input type="text" name="username"></p>
        <p>Password: <input type="password" name="password"></p>
        <p>Email: <input type="text" name="email"></p>
        <p><input type="submit" value="Register"></p>
        </form>
        </body></html>
        """
        self.wfile.write(html)

    def serve_registering(self, match):
        form = cgi.FieldStorage(
            fp=self.rfile, 
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })

        username = form.getfirst("username","")
        password = form.getfirst("password","")
        email = form.getfirst("email","")
        message = ""

        if username and password and email:
            # all fields are required
            usercheck = self.server.db.check_username(username)
            log.info("usercheck:  %s" % usercheck)

            if usercheck:
                log.info("Registering user: %s" % username)
                self.server.db.add_user(username, password, email)
                message = "User: %s successfully registered" % username

            else:
                message = "The username %s is not available. Please choose another name." % username
        else:
            message = "Please fill out all the fields"

        html = self.header("Registration")
        html += message + """
        </body></html>
        """
        self.wfile.write(html)

    def serve_login(self, match):
        if self.check_auth():
            # if user is already login, he doesnt need to login again
            self.send_response(301)
            self.send_header("Location", '/')
            self.end_headers()
        else:
            #TODO add client side check for each of the fields
            html = self.header("Login")
            html += """
            <form enctype="multipart/form-data" action="/auth" method="post">
            <p>Username: <input type="text" name="username"></p>
            <p>Password: <input type="password" name="password"></p>
            <p><input type="submit" value="Login"></p>
            </form>
            </body></html>
            """
            self.wfile.write(html)

    def serve_auth(self, match):
        form = cgi.FieldStorage(
            fp=self.rfile, 
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })

        # Instantiate a SimpleCookie object
        cookie = Cookie.SimpleCookie()

        username = form.getfirst("username","")
        password = form.getfirst("password","")
        message = ""

        # code 301 for redirect
        self.send_response(301)

        if username and password:
            # all fields are required
            usercheck = self.server.db.authenticate_user( username, password )

            if usercheck:
                # The SimpleCookie instance is a mapping username to username
                cookie['username'] = username
                self.send_header('Set-Cookie', cookie.output(header=''))
                # redirect back to home page
                self.send_header("Location", '/')
                self.end_headers()

            else:
                message = "User logged in failed, forgot username or password?"
                self.end_headers()
                self.wfile.write("No username ?")
        else:
            message = "Please fill out all the fields"

    def serve_logout(self, match):
        # change the cookie['username'] to guest to indicate this user logged out
        cookie = Cookie.SimpleCookie()

        self.send_response(200)

        # if user decide to logout, set username back to guest
        cookie['username'] = 'guest'
        self.send_header('Set-Cookie', cookie.output(header=''))
        # redirect back to home page
        self.end_headers()

        # dummy way of creating a response
        html = """<html><head>
        <!--link rel="icon" href='/favicon.ico'-->
        <title>User Authentication</title>
        <style>"""  + style + """</style>"""
        if str(self.server.opts['sort'])=='True':
            html += """
                <script src="http://code.jquery.com/jquery-1.9.1.js"></script>
                <script type="text/javascript" src="/js/jquery.tablesorter.min.js"></script>
                <script src="http://code.jquery.com/ui/1.10.3/jquery-ui.js"></script>
                """
        html += """</head><body><b>
        <div id="headerIMG">
        <img src="/data/img/header4ants.jpg">
        </div>
        <div id="wrapper">
        <div id = "headerwrap">
        """
        if (self.check_auth()):
            html += """
            <a href="/logout">Hi, """ + self.username + """ logout here!</a>
            """
        else:
            html += """<a href='/login' name=top> Login </a> | 
            <a href='/register' name=top> Register </a>"""

        html += """
        <div id="header">
        <a href='/howto' name=top><img src="data/img/gettingStartedIco.png"/> Getting Started </a> &nbsp;&nbsp;&nbsp;&nbsp;
        <a href='/' name=top><img src="data/img/gameLogIco.png"/> Games </a> &nbsp;&nbsp;&nbsp;&nbsp;
        <a href='/ranking'><img src="data/img/rankingsIco.png"/> Rankings </a> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <a href='/maps'><img src="data/img/mapsIco.png"/> Maps </a> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <a href='/upload' title='Upload your bot'><img src="data/img/uploadIco.png"/> Upload Bot </a> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <a href='/admin' title='Admin'> Admin </a>
        </div>
        </div>
        <br><p></b>
        """
        html += """
        User has logg out.
        </body></html>
        """
        self.wfile.write(html)

    def check_auth(self):
        # an utility function to check if user is logged or not
        cookie = Cookie.SimpleCookie()

        if "Cookie" in self.headers:
            cookie = Cookie.SimpleCookie(self.headers["Cookie"])

        # if the user has no session, redirect this user to login page
        if (not cookie):
            log.info('no cookies in header')
            return False
        else:
            if (not cookie['username'].value or str(cookie['username'].value) == 'guest'):
                return False
            else:
                self.username = str(cookie['username'].value)
                return True

    def serve_admin(self,match):
        pass

    def serve_user(self, match):
        # get player name using match(Regex)
        user = match.group(0).split("/")[2]

        cookie = Cookie.SimpleCookie()

        if "Cookie" in self.headers:
            cookie = Cookie.SimpleCookie(self.headers["Cookie"])

        if cookie:

            if str(cookie['username'].value) == str(user):
        
                html = self.header( user )

                # TODO: get all bots under this user

                # dummy way of init bot as empty list
                # TODO: remove this later once got DB working
                self.user_bots = self.server.db.get_bots((user))

                if len(self.user_bots) >= 1:
                    html += '<p>Your bot(s) are as follow: </p>'
                    # case if user already has bot(s) running
                    # show all the bot rank table
                    for bot in self.user_bots:
                        html += self.bots_head()
                        html += "<tbody>"
                        html += self.bots_line( bot )
                        html += "</tbody></table>"

                # note: there is a hidden field include the username field
                html += "<hr>"
                html += "Upload your new bot here </br>"
                html += """
                <form enctype="multipart/form-data" action="/uploading" method="post">
                <p>Bot: <input type="file" name="file"></p>
                <p><input type="submit" value="Upload" name="Upload"></p>
                <input type="hidden" name="username" value=""" + user + """>
                </form>
                </body></html>
                """

                # TODO: create/join tournament form

                # Testing purpose i'm getting username of my own bot

                html += "</body></html>"
                
                self.wfile.write(html)

            else:
                pass

        else:
            #todo change this to redirect to login page
            pass


    def do_GET(self):

        if self.path == '/':
            self.serve_main(None)
            return

        for regex, func in (
                ('^\/howto', self.serve_howto),
                ('^\/ranking/p([0-9]?)', self.serve_ranking),
                ('^\/ranking', self.serve_ranking),
                ('^\/howto', self.serve_howto),
                ('^\/maps', self.serve_maps),
                ('^\/register', self.serve_register),
                ('^\/login', self.serve_login),
                ('^\/logout', self.serve_logout),
                ('^\/admin', self.serve_admin),
                ('^\/map(\/.*)', self.serve_map),
                ('^\/player\/(.*)', self.serve_player),
                ('^\/user\/(.*)', self.serve_user),
                ('^\/replay\.([0-9]+)', self.serve_visualizer),
                ('^\/p([0-9]?)', self.serve_main),
                ('^\/?(.*)', self.serve_file),
                ):
            match = re.search(regex, self.path)
            if match:
                func(match)
                return
        self.send_error(404, 'File Not Found: %s' % self.path)

    def do_POST(self):
        if self.path == '/':
            self.serve_main(None)
            return

        for regex, func in (
                ('^\/uploading', self.serve_uploading),
                ('^\/registering', self.serve_registering),
                ('^\/auth', self.serve_auth),
                ):
            match = re.search(regex, self.path)
            if match:
                func(match)
                return
        self.send_error(404, 'File Not Found: %s' % self.path)


def main(web_port, workers, root_folder = ''):

    opts = {
        ## web opts:
        'sort': 'True',            # include tablesorter & jquery and have sortable tables(requires ~70kb additional download)

        ## read only info
        'host': socket.gethostname(),
    }


    web = AntsHttpServer(('', web_port), AntsHttpHandler)
    web.workers = workers
    web.opts = opts
    web.serve_forever()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 3:
        import os
        fpid = os.fork()
        if fpid!=0:
          # Running as daemon now. PID is fpid
          sys.exit(0)
    elif len(sys.argv) > 2:
        main(int(sys.argv[1]), str(sys.argv[2]))
    elif len(sys.argv) > 1:
        main(int(sys.argv[1]))
    else:
        main(2080)
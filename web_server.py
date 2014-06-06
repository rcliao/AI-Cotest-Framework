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
import zipfile
import shutil

import urllib
from urlparse import urlparse, parse_qs

import database
from tournament_manager import load_map_info

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
# add formatter to ch
ch.setFormatter(formatter)

# create logger
log = logging.getLogger('web')
log.setLevel(logging.WARNING)
# add ch to logger
log.addHandler(ch)

table_lines = 100


class ContestHttpServer(HTTPServer):
    def __init__(self, *args):
        self.opts = None

        # anything static gets cached on startup here.
        self.cache = {}
        # self.cache_file("/favicon.ico","favicon.ico")
        self.cache_dir("js")
        self.cache_dir("css")
        self.cache_dir("libs")
        self.cache_dir("games")

        self.maps = load_map_info()
        self.db = database.ContestDB()

        self.tourn_id = 1

        HTTPServer.__init__(self, *args)

    def cache_file(self, fname, fpath):
        try:
            f = open(fpath, "rb")
            data = f.read()
            f.close()
            log.info("added static %s to cache." % fname)
            self.cache[fname] = data
        except Exception, e:
            log.error("caching %s failed. %s" % (fname, e))

    def cache_dir(self, dir):
        for root, dirs, filenames in os.walk(dir):
            for filename in filenames:
                # fpath is the actual system path.
                fpath = os.path.join(root, filename)
                # fname is the name used by the client.
                fname = '/' + fpath
                fname = fname.replace('\\', '/')
                self.cache_file(fname, fpath)


class ContestHttpHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def __init__(self, *args):
        SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(self, *args)

    def send_head(self, type='text/html'):
        self.send_response(200)
        self.send_header('Content-type', type)
        self.end_headers()

    def header(self, title):
        self.send_head()

        if self.check_auth():
            self.tourns = self.server.db.get_tournaments(
                username=self.username)
        else:
            self.tourns = self.server.db.get_tournaments()

        self.current_tourn = self.server.db.get_tournament_name(
            self.server.tourn_id)

        if self.current_tourn:
            self.tourn_name = self.current_tourn[0][0]
        else:
            self.tourn_name = 'None'

        head = """<!DOCTYPE html><html><head>
        <!--link rel="icon" href='/favicon.ico'-->
        <meta charset="utf-8">
        <meta name="viewport" content="height=device-height,
            width=device-width, user-scalable=no, initial-scale=1.0,
            maximum-scale=1.0">
        <title>""" + title + """</title>
        <link href="http://fonts.googleapis.com/css?family=Arvo"
            rel="stylesheet" type="text/css">
        <link href="http://fonts.googleapis.com/css?family=PT+Sans"
            rel="stylesheet" type="text/css">
        """

        head += """
        </head><body>
        <link rel="stylesheet" href="/libs/semantic-ui/css/semantic.css">
        <link rel="stylesheet" href="/css/styles.css">
        """

        if str(self.server.opts['sort']) == 'True':
            head += """
                <script type="text/javascript"
                    src="/js/jquery.tablesorter.min.js"></script>
                <script
                    src="http://code.jquery.com/ui/1.10.3/jquery-ui.js"></script>
                """

        head += """
        <script type="text/javascript"
            src="/libs/jquery/jquery.js"></script>
        <script type="text/javascript"
            src="/libs/semantic-ui/javascript/semantic.js"></script>
        <script type="text/javascript">
            $(document).ready(function() {
                $('.ui.dropdown.item')
                    .dropdown()
                ;

                $('#tourn_switch').click(function() {
                    $('.ui.dropdown.item')
                        .dropdown('toggle')
                    ;
                });

                $('#logout').click(function() {
                    $.ajax({
                        url: '/logout',
                        success: function() {
                            location.reload();
                        }
                    });
                });
            });
        </script>
        <div class="ui page grid">
            <h1 class="ui icon center aligned header">
                <i class="puzzle piece icon"></i>
                AI Contest
            </h1>
            <div>
                <div class="ui menu">
                    <div class="menu">
                        <div id="tourn_switch" class="ui dropdown item">
                            """ + self.tourn_name + """<i class="icon dropdown"></i>
                            <div class="menu">"""

        for tourn in self.tourns:
            head += "<a class=\"item\" \
                href='switchTourn?tournID=" + str(tourn[0]) + "'>" + tourn[3] + "</a>"

        head += """
                            </div>
                        </div>
                """

        # determine which menu based on the current path
        head += """
                        <a href="/" class="active item">
                            <i class="home icon"></i> Home
                        </a>
        """ if self.path == "/" else """
                        <a href="/" class="item">
                            <i class="home icon"></i> Home
                        </a>
        """
        head += """
                        <a href="/games" class="active item">
                            <i class="gamepad icon"></i> Games
                        </a>
        """ if self.path == "/games" else """
                        <a href="/games" class="item">
                            <i class="gamepad icon"></i> Games
                        </a>
        """
        head += """
                        <a href="/ranks" class="active item">
                            <i class="trophy icon"></i> Rankings
                        </a>
        """ if self.path == "/ranks" else """
                        <a href="/ranks" class="item">
                            <i class="trophy icon"></i> Rankings
                        </a>
        """

        # right menu starts
        head += """
                        <div class="right menu">
        """

        # dashboard
        if (self.check_auth()):
            head += """
            <a href='/user/""" + self.username + """' class="active item">
                <i class="dashboard icon"></i> Dashboard
            </a>
            """ if "/user/" in self.path else """
            <a href='/user/""" + self.username + """' class="item">
                <i class="dashboard icon"></i> Dashboard
            </a>
            """

        # authentication
        if (self.check_auth()):
            head += """
            <a class="item" id="logout">Hi, """ + self.username + """ logout here!</a>
            """
        else:
            head += """
            <div class="item">
                <a href='/login'><i class="unlock icon"></i> Login </a>
            </div>
            <div class="item">
                <a href='/register'><i class="user icon"></i> Register </a>
            </div>
            """

        head += """
                        </div>
                    </div>
                </div>
            </div>
        """

        return head

    def footer_sort(self, id):
        if str(self.server.opts['sort']) == 'True':
            return """
                <script>
                $(document).ready(function() { $("#%s").tablesorter(); });
                </script>
            """ % id
        return ""

    def footer(self):
        apic = "^^^"
        return "<p><br> &nbsp;<a href=#top title='crawl back to the top'>\
            " + apic + "</a>"

    def serve_visualizer(self, match):
        try:
            junk, gid = match.group(0).split('.')
            replaydata = self.server.db.get_replay(self.server.tourn_id, gid)
            game = self.server.db.get_tourn_game(
                self.server.tourn_id)[0]
        except Exception, e:
            self.send_error(500, '%s' % (e,))
            return
        html = """
            <html>
            <head>
                <title>Ant Canvas</title>
                <script type="text/javascript" src="/"""+game[5]+"""">
                </script>
                <script type="text/javascript">
                    window.isFullscreenSupported = function() {
                        return false;
                    };

                    function init() {
                        var options = new Options();
                        options.data_dir = '/games/"""+game[2]+"""/data/';
                        options.embedded = true;
                        var visualizer=new Visualizer(document.body, options);
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
        return """<table id='games' class='ui table segment tablesorter'>
            <thead>
                <tr>
                    <th>Game</th>
                    <th>Players</th>
                    <th>Turns</th>
                    <th>Date</th>
                    <th>Map</th>
                </tr>
            </thead>"""

    def game_line(self, g):
        html = "<tr><td width=10%><a href='/replay." + str(g[0]) + "' \
            title='Run in Visualizer'> Replay " + str(g[0]) + "</a></td><td>"
        for key, value in sorted(
            json.loads(g[2]).iteritems(),
            key=lambda (k, v): (v, k),
            reverse=True
        ):
            html += "<a href='/player/" + str(key) + "' \
                title='"+str(value[1])+"'>"+str(key)+"</a> \
                (" + str(value[0]) + ")"
        html += "</td><td>" + str(g[5]) + "</td>"
        html += "</td><td>" + str(g[3]) + "</td>"
        html += "<td><a href='/map/" + str(g[4]) + "' \
            title='View the map'>" + str(g[4]) + "</a></td>"
        html += "</tr>\n"
        return html

    def rank_head(self):
        return """
        <div class="sixteen wide column">
        <table id='players' class='tablesorter ui table'>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Player</th>
                    <th>Skill</th>
                    <th>Mu</th>
                    <th>Sigma</th>
                    <th>Games</th>
                    <th>Last Seen</th>
                    <th>Delete</th>
                    <th>Status</th>
                </tr>
            </thead>"""

    def page_counter(self, url, nelems):
        if nelems < table_lines:
            return ""
        html = "<table class='tablesorter'><tr><td>Page</td><td>"
        for i in range(min((nelems+table_lines)/table_lines, 10)):
            html += "<a href='"+url+"p"+str(i)+"'>"+str(i)+"</a>"
        html += "</td></tr></table>"
        return html

    def rank_line(self, p):
        html = "<tr>"
        # Bot Rank
        html += "<td>%d</td>" % p[4]
        # Bot Name
        html += "<td><a href='/player/" + str(p[12]) + "'>\
            <b>"+str(p[12])+"</b></a></td>"
        html += "<td>%2.4f</td>" % p[5]
        html += "<td>%2.4f</td>" % p[6]
        html += "<td>%2.4f</td>" % p[7]
        html += "<td>%d</td>" % p[8]
        html += "<td>%s</td>" % p[3]
        html += "<td><a href='/ranks?%s'><b>delete</b></a></td>" % str("delete=" + str(p[2]))
        html += "<td>%s</td>" % p[9]
        html += "</tr>\n"
        return html

    def bots_head(self):
        return """
        <table id='players' class='tablesorter' width='98%'>
            <thead>
                <tr>
                    <th>Bot Name</th>
                    <th>Status</th>
                    <th>Operation</th>
                    <th>Enroll Tournament</th>
                </tr>
            </thead>"""

    def bots_line(self, p, username):
        html = "<tr>"
        # Bot Name
        html += "<td><a href='/player/" + str(p[0]) + "'>\
            <b>"+str(p[0])+" @ " + p[4] + "</b></a></td>"
        if p[1]:
            html += "<td style='color: green;'> Active </td>"
        else:
            html += "<td style='color: red;'> Not-Running </td>"
        html += "<td>\
                <form enctype='multipart/form-data' action='/uploading' method='post'>\
                    <input type='file'  name='file'><input type='submit' name='Upload' value='Upload'>\
                    <input type='submit' name='Terminate' value='Terminate'>\
                    <input type='submit' name='Start' value='Start'></td>\
                    <input type='hidden' name='tID' value=\"" + str(p[3]) + "\">\
                    <input type='hidden' name='botname' value=\"" + str(p[0]) + "\">\
                    <input type='hidden' name='username' value=\"" + username + "\">\
                </form>"
        html += """
        <td>
            <form action="/enrollTourn" method="post">
        """
        for tourn in self.tourns:
            tourn_bots = self.server.db.get_bot_tournaments( tourn[0], p[2] )
            if len(tourn_bots) > 0:
                html += "<input type=\"checkbox\" name=\"tournID\" value=\"" + str(tourn[0]) + "\" checked>" + tourn[3] + "</br>"
            else:
                html += "<input type=\"checkbox\" name=\"tournID\" value=\"" + str(tourn[0]) + "\">" + tourn[3] + "</br>"
        html += """
            <input type="hidden" name="botID" value=""" + str(p[2]) + """>
            <input type='hidden' name='username' value=\"""" + username + """\">
            <input type="submit" value="Enroll Tournament">
            </form>
        </td>
        """
        html += "</tr>\n"
        return html

    # DEPRECATED
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
            <li>Play!</li>
        </ol>
        </ br>
        """
        html += self.footer()
        html += "</body></html>"
        self.wfile.write(html)

    # DEPRECATED
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
        html = self.header("AI Contest Framework")
        html += "<div class=\"sixteen wide column\">"
        html += self.game_head()
        html += "<tbody>"
        offset=0
        if match and (len(match.group(0))>2):
            offset=table_lines * int(match.group(0)[2:])

        for g in self.server.db.get_tourn_games(self.server.tourn_id, offset,table_lines):
            html += self.game_line(g)
        html += "</tbody></table>"
        html += self.page_counter("/", self.server.db.num_tourn_games( self.server.tourn_id ) )
        html += self.footer()
        html += self.footer_sort('games')
        html += "</div></div></body></html>"
        self.wfile.write(html)

    def serve_player(self, match):
        # get player name using match(Regex)
        player = match.group(0).split("/")[2]
        res = self.server.db.get_player(self.server.tourn_id, player)
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
        for g in self.server.db.get_tourn_games_for_player(self.server.tourn_id, offset, table_lines, player):
            html += self.game_line(g)
        html += "</tbody></table>"
        html += self.page_counter("/player/"+player+"/", self.server.db.num_tourn_games_for_player(self.server.tourn_id, player) )
        html += self.footer()
        html += self.footer_sort('games')
        html += "</body></html>"
        self.wfile.write(html)

    def serve_ranking(self, match):
        html = self.header("Rankings")
        html += self.rank_head()

        path2 = urlparse(self.path)
        path3 = parse_qs(path2.query)
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
        for p in self.server.db.get_ranks(self.server.tourn_id, table_lines, offset):
            html += self.rank_line( p )

        html += "</tbody></table>"
        html += self.page_counter("/ranks/", self.server.db.num_players( self.server.tourn_id ) )
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
        html += "</div></body></html>"
        self.wfile.write(html)

    # DEPRECATED
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
        mime = {
            'png':'image/png',
            'jpg':'image/jpeg',
            'jpeg':'image/jpeg',
            'gif':'image/gif',
            'js':'text/javascript',
            'py':'application/python',
            'html':'text/html',
            'css' : 'text/css'
        }
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
        t_id = form.getfirst('tID', '')


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

                existingBot = self.server.db.get_bot( botname )

                if not existingBot:
                    # TODO: change to add bot including username later
                    self.server.db.add_bot( username, botname, language )
                    bot = self.server.db.get_bot( botname )
                    self.server.db.enroll_bot( 1, bot[0][0] )


            html = self.header("File Uploaded")
            html += message + """
            </body></html>
            """
            self.wfile.write(html)

        elif "Terminate" in form:
            # terminate bot
            log.info( 'Terminate Bot' + botname )
            self.server.db.terminate_bot( botname, t_id )
            self.server.db.con.commit()
            self.send_response(301)
            self.send_header("Location", "/user/" + username)
            self.end_headers()

        elif "Start" in form:
            # start bot
            print 'Start Bot' + botname
            self.server.db.start_bot( botname, t_id )
            self.server.db.con.commit()
            self.send_response(301)
            self.send_header("Location", "/user/" + username)
            self.end_headers()

    def serve_uploadGame(self, match):
        # get the form data from the post request
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })

        # A nested FieldStorage instance holds the file
        fileitem = form['file']
        gamename = form.getfirst('gameName', '')
        username = form.getfirst('username', '')

        # Test if the file was uploaded
        if fileitem.filename:

            # strip leading path from file name to avoid directory traversal attacks
            fn = os.path.basename(fileitem.filename)

            # ensure there is a directory before upload the file
            if not os.path.exists('games'):
                os.makedirs('games')
            if not os.path.exists('games/' + gamename):
                os.makedirs('games/'+gamename)

            # upload the bot under /Bots/ Folder as it is
            open('games/' + gamename + '/' + fn, 'wb').write(
                fileitem.file.read()
            )

            # unzip this file
            with zipfile.ZipFile('games/'+gamename+'/'+fn, "r") as z:
                z.extractall('games/'+gamename+'/')

            # traverse the directory to find a few important files
            # 1. main program
            # 2. instruction page
            # 3. visualizer
            files = os.listdir('games/'+gamename+'/')
            count = 0

            for root, dirs, files in os.walk('games/' + gamename + '/'):
                for f in files:
                    if 'main' in f:
                        count += 1
                        main = 'games/'+gamename+'/'+f
                        ext = f.split(".")[1]
                        if ext == 'py':
                            language = 'python'
                        elif ext == 'java':
                            language = 'java'
                        elif ext == 'scala':
                            language = 'scala'
                        elif ext == 'cpp':
                            language = 'c++'
                    elif 'index.html' == f:
                        count += 1
                        instruction = 'games/'+gamename+'/'+f
                    elif 'visualizer.js' == f:
                        count += 1
                        visualizer = root + '/' + f

            if count != 3:
                # error, need all three files
                # remove all the files since it is not valid game
                for root, dirs, files in os.walk('games/'+gamename+'/'):
                    for f in files:
                        os.unlink(os.path.join(root, f))
                    for d in dirs:
                        shutil.rmtree(os.path.join(root, d))
                message = """
                    Game was not created because missing one of these files:
                    <ul>
                        <li><b>main</b> program</li>
                        <li><b>index.html</b> for instruction</li>
                        <li><b>visualizer.html</b> for visualizer</li>
                    </ul>
                """

            self.server.db.add_game(username, gamename, language, instruction, visualizer)

            message = 'The game "' + gamename + '" was created successfully'


        else:
            message = 'No file was uploaded'

        html = self.header("File Uploaded")
        html += "<div class=\"sixteen wide column\">\
            " + message + """
        </div></body></html>
        """
        self.wfile.write(html)

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

    def serve_createTourn(self, match):
        cookie = Cookie.SimpleCookie()

        if "Cookie" in self.headers:
            cookie = Cookie.SimpleCookie(self.headers["Cookie"])

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })

        tName = form.getfirst("tName","")
        password = form.getfirst("password","")
        gamename = form.getfirst("gamename", "")
        message = ""

        print 'gamename:' + gamename

        if tName:
            # all fields are required
                log.info("creating tournament: %s" % tName)
                self.server.db.add_tournament(
                    str(cookie['username'].value),
                    tName,
                    password,
                    gamename
                )
                message = "Tournament: %s successfully created" % tName
        else:
            message = "Please fill out the name"

        html = self.header("Tournament Creation")
        html += message + """
        </body></html>
        """
        self.wfile.write(html)

    def serve_deleteTourn(self, match):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })

        t_id = form.getfirst("tournID","")
        message = ""

        if t_id:
            # all fields are required
                self.server.db.delete_tournament( t_id )
                message = "Tournament: successfully deleted"
        else:
            message = "Please fill out all the fields"

        html = self.header("Tournament Deletion")
        html += message + """
        </body></html>
        """
        self.wfile.write(html)

    def serve_switchTourn(self, match):
        query_params = parse_qs(urlparse(self.path).query)
        print query_params
        t_id = int(query_params["tournID"][0])
        print t_id
        message = ""

        if t_id:
            # all fields are required
                self.server.tourn_id = t_id
                message = "Tournament: successfully switched"
        else:
            message = "Please fill out all the fields"

        self.send_response(301)
        self.send_header('Location', '/')
        self.end_headers()

    def serve_enrollTourn(self, match):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })

        botID = form.getfirst("botID", "")
        t_ids = form.getvalue("tournID")
        username = form.getfirst("username", "")

        message = ""

        if username:
            tourns = self.server.db.get_tournaments( username=username )
        else:
            tourns = self.server.db.get_tournaments()

        if t_ids:
            # all fields are required
            for all_tourn in tourns:
                if str(all_tourn[0]) not in t_ids:
                    self.server.db.disenroll_bot( all_tourn[0], botID )
                else:
                    self.server.db.enroll_bot( all_tourn[0], botID )
            message = "Tournament enrollments: completed"
        else:
            message = "Please fill out all the fields"

        html = self.header("Tournament Enrollment")
        html += message + """
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

        # basic authentication security
        if cookie:

            if str(cookie['username'].value) == str(user):

                html = self.header(user)

                self.user_bots = self.server.db.get_bots(user)

                # Starting of row
                html += "<div class=\"row three column middle aligned\">"

                # step 1 upload a new game
                html += "<div class=\"column\">"
                html += "<div class=\"ui segment\">"
                html += "<h4 class=\"ui header\">Upload New Game"
                html += """
                    <div class="ui sub header">
                        Upload game as <em>.zip</em> file
                    </div>
                </h4>
                """
                html += """
                <form class="ui form" enctype="multipart/form-data"
                    action="/uploadGame" method="post">
                    <div class="field">
                        <label>Game Name</label>
                        <input type="text" name="gameName">
                    </div>
                    <div class="field">
                        <label>Game File</label>
                        <input type="file" name="file"/>
                    </div>
                    <input type="hidden" name="username" value=""" + user + """>
                    <input type="submit" class="ui button submit fluid" value="Upload New Game">
                </form>
                """
                html += "</div></div>"

                # the following section is to add/delete tournament
                # TODO: include a date input here for end date
                html += "<div class=\"column\">"
                html += "<div class=\"ui segment\">"
                html += "<h4 class=\"ui header\">Create Your New Tournament Here"
                html += """
                    <div class="ui sub header">
                        Note: including password will make your tournament private
                    </div>
                </h4>
                """
                html += """
                <form class="ui form" action="/createTourn" method="post">
                    <div class="field">
                        <label>Tournament Name</label>
                        <input type="text" name="tName"></p>
                    </div>
                    <div class="field">
                        <label>Tournament Password</label>
                        <div class="ui labeled input">
                            <input type="password" name="password">
                            <div class="ui corner label">
                                <i class="asterisk icon"></i>
                            </div>
                        </div>
                    </div>
                    <div class="field">
                        <label>Game</label>

                        <div class="ui selection dropdown" id="switch_tourn_game">
                            <input type="hidden" name="gamename">"""

                # get games from the database
                games = self.server.db.get_games()
                # if there is any game being uploaded display them
                if games:
                    html += """
                                <div class="default text">""" + games[0][2] + """</div>
                                <i class="dropdown icon"></i>
                                <div class="menu">
                    """

                    for game in games:
                        html += """
                                    <div class="item" data-value=\"""" + game[2] + """\">
                                        """ + game[2] + """
                                    </div>
                        """
                # else just display no game created yet
                else:
                    html += """
                                <div class="default text">No Game Created Yet</div>
                                <i class="dropdown icon"></i>
                                <div class="menu">
                    """
                html += """
                            </div>
                        </div>

                    </div>
                    <input type="submit" class="ui button submit fluid" value="Create New Tournament">
                </form>
                </div>
                </div>
                """

                # the following section is for uploading new bot
                # note: there is a hidden field include the username field
                html += "<div class=\"column\">"
                html += "<div class=\"ui segment\">"
                html += """
                <h4 class=\"ui header\">
                    Upload Your New Bot Here
                    <div class="sub header">
                        Bot as executable file
                    </div>
                </h4>
                """
                html += """
                <form class="ui form" enctype="multipart/form-data" action="/uploading" method="post">
                    <div class="field">
                        <label>Bot</label>
                        <input type="file" name="file">
                    </div>
                    <input type="submit" class="ui fluid button" value="Upload New Bot" name="Upload">
                    <input type="hidden" name="username" value=""" + user + """>
                </form>
                </div>
                </div>
                """

                # close of row div
                html += "</div>"
                # following section is to show the tournament this user created

                html += "<div class=\"ui divider\"></div>"

                if len(self.user_bots) >= 1:
                    html += """
                    <div class="sixteen wide column">
                        <h3 class="ui header">Your bot(s) are as follow:</h3>
                    """
                    # case if user already has bot(s) running
                    # show all the bot rank table
                    for bot in self.user_bots:
                        html += self.bots_head()
                        html += "<tbody>"
                        html += self.bots_line( bot, user )
                        html += "</tbody></table>"

                self.user_tourns = self.server.db.get_tournaments_user(user)

                if len(self.user_tourns) >= 1:
                    html += "<div class=\"sixteen wide column\">"
                    html += "<h3 class=\"ui header\">Tournaments you've created: </h3>"
                    html += """
                    <table id='players' class='ui table' class='tablesorter'>
                        <tr>
                            <th>Tournament Name</th>
                            <th>Created Date</th>
                            <th>Private</th>
                            <th>Operation</th>
                        </tr>
                    """
                    for tourn in self.user_tourns:
                        html += "<tr>"
                        html += "<td>"
                        html += tourn[3]
                        html += "</td>"
                        html += "<td>"
                        html += tourn[5]
                        html += "</td>"
                        html += "<td>"
                        if tourn[4]:
                            html += "&#10004;"
                        html += "</td>"
                        html += "<td>"
                        html += """
                        <form action="/deleteTourn" method="post">
                            <input type="hidden" name="tournID" value=""" + str(tourn[0]) + """>
                            <input type="submit" value="Delete Tournament">
                        </form>
                        """
                        html += "</td>"
                        html += "</tr>"
                    html += """
                    </table>
                    </div>
                    """

                html += """
                <script>
                    $('#switch_tourn_game')
                        .dropdown()
                    ;
                </script>
                """
                html += "</body></html>"

                self.wfile.write(html)

            else:
                # code 301 for redirect
                self.send_response(301)
                self.send_header("Location", "/login")
                self.end_headers()

        else:
            #todo change this to redirect to login page
            # code 301 for redirect
            self.send_response(301)
            self.send_header("Location", "/login")
            self.end_headers()

    # Main Routing here
    def do_GET(self):

        if self.path == '/':
            self.serve_main(None)
            return

        for regex, func in (
                ('^\/admin', self.serve_admin),
                ('^\/howto', self.serve_howto),
                ('^\/howto', self.serve_howto),
                ('^\/login', self.serve_login),
                ('^\/logout', self.serve_logout),
                ('^\/map(\/.*)', self.serve_map),
                ('^\/maps', self.serve_maps),
                ('^\/p([0-9]?)', self.serve_main),
                ('^\/player\/(.*)', self.serve_player),
                ('^\/ranks', self.serve_ranking),
                ('^\/ranks/p([0-9]?)', self.serve_ranking),
                ('^\/register', self.serve_register),
                ('^\/replay\.([0-9]+)', self.serve_visualizer),
                ('^\/switchTourn', self.serve_switchTourn),
                ('^\/user\/(.*)', self.serve_user),
                ('^\/games\*\*/?(.*)', self.serve_file),
                ('^\/*/?(.*)', self.serve_file),
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
                ('^\/uploadGame', self.serve_uploadGame),
                ('^\/registering', self.serve_registering),
                ('^\/auth', self.serve_auth),
                ('^\/createTourn', self.serve_createTourn),
                ('^\/deleteTourn', self.serve_deleteTourn),
                ('^\/enrollTourn', self.serve_enrollTourn),
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

    web = ContestHttpServer(('', web_port), ContestHttpHandler)
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
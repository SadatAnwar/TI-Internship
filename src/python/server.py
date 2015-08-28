# coding=utf-8
import shutil
import sys
from tempfile import TemporaryFile
import urlparse
import traceback
import threading
import json
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import base64
import cgi
import time

from global_variables import *

log = logging.getLogger(__name__)

try:
    from bbio import *
except ImportError:
    pass

BBIOSERVER_VERSION = "1.2"
log.info('Root folder for application : "%s"' % project_folder)
# modified from the above to make the application of the webserver quicker
ROOT_DIR = os.path.join(project_folder, 'benchDebuggerServer')
PAGES_DIR = os.path.join(ROOT_DIR, "pages")
FOOTER = os.path.join(ROOT_DIR, "src", "footer.html")
INDEX = "%s/index.html" % ROOT_DIR
configModified = None

# Get a hold of the config file
Config = ConfigParser.ConfigParser()

# Change working directory to the BBIOServer library directory,
# otherwise the request handler will try to deliver pages from the
# directory where the program using the library is being run from:
os.chdir(ROOT_DIR)
log.info('Webserver will be hosted in: "%s" folder' % ROOT_DIR)
# This is where we store the function strings indexed by their
# unique ids:
FUNCTIONS = {}


def callFunctionWithParams(function_id, function, paramCount, data):
    parameters = []
    if paramCount == 0:
        try:
            result, function_id = function()
            response = json.dumps({"FunctionName": function_id, "Result": result})
            return response
        except Exception, e:
            response = json.dumps({"FunctionName": function_id, "Result": 'ERROR: %s' % e})
            return response
    else:
        try:
            for i in range(1, paramCount + 1):
                parameters.append(data['param%s' % i][0])
        except AttributeError:
            for i in range(1, paramCount + 1):
                parameters.append(data['param%s' % i].value)
        try:
            result, function_id = function(*parameters)
            response = json.dumps({"FunctionName": function_id, "Result": result})
            return response
        except Exception, e:
            log.error(e)
            response = json.dumps({"FunctionName": function_id, "Result": 'ERROR: %s' % e})
            return response


class BBIORequestHandler(SimpleHTTPRequestHandler, BaseHTTPRequestHandler):
    includePage = '<include-page>'
    includePageEnd = '</include-page>'
    ctype = 'text/html'
    SimpleHTTPRequestHandler.extensions_map.update({
        '.log': 'text/plain', # Default
    })

    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            parts = urlparse.urlsplit(self.path)
            if not parts.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                new_parts = (parts[0], parts[1], parts[2] + '/',
                             parts[3], parts[4])
                new_url = urlparse.urlunsplit(new_parts)
                self.send_header("Location", new_url)
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        self.ctype = self.guess_type(path)
        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None
        return f


    def copyfile(self, source, outputfile):
        """This function is used to copy the file data over the network to the client
        this methos is over ridden to allow the server to read the HTML files to see if there is any include
        statement, and if so then the file requested is injected at that point"""
        try:
            ctype = self.guess_type(source.name)
            self.send_response(200)
            self.send_header("Content-type", ctype)
            fs = os.fstat(source.fileno())
            self.send_header("Content-Length", str(self._calculateFileLength(source)))
            self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
            self.end_headers()
            if source.name.endswith('.html') or source.name.endswith('.htm'):
                self._readHTMLFile(source, outputfile)
            else:
                shutil.copyfileobj(source, outputfile)
        except Exception, e:
            log.error(e)

    def _calculateFileLength(self, source):
        #calculate the length ofthe file so we can send proper headder
        if source.name.endswith('.html') or source.name.endswith('.htm'):
            length = self._calculateHTMLFileLength(source)
        else:
            fs = os.fstat(source.fileno())
            length = fs[6]
        return length

    def _readHTMLFile(self, source, outputfile):
        source.seek(0)
        for line in source:
            if self.includePage in line:
                #get the path of the file to be included
                line = line.replace(self.includePage, '').replace(' ', '').replace(self.includePageEnd, '')
                include = self.translate_path(line).rstrip()
                if os.path.isfile(include):
                    newFile = open(include, 'rb')
                    self._readHTMLFile(newFile, outputfile)
                    newFile.close()
            else:
                outputfile.write(line)
        return

    def _calculateHTMLFileLength(self, source):
        includedFileLength = 0
        opened = False
        try:
            lines = source.readlines()
        except AttributeError:
            source = open(source, 'rb')
            opened = True
            lines = source.readlines()
        for line in lines:
            if self.includePage in line:
                includeLineLength = len(line)
                #get the path of the file to be included
                line = line.replace(self.includePage, '').replace(' ', '').replace(self.includePageEnd, '')
                include = self.translate_path(line).rstrip()
                if os.path.isfile(include):
                    includedFileLength += (self._calculateHTMLFileLength(include) - includeLineLength)
        # now we calculate the total file length
        length = 0
        if type(source) == str:
            with open(source, 'rb') as f:
                fs = os.fstat(f.fileno())
        else:
            fs = os.fstat(source.fileno())
        length += int(fs[6])
        if opened:
            source.close()
        return length + includedFileLength

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm=\"Please enter the Username and Password for the device'
                                             '\n NOT YOUR TI CREDENTIALS \"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        global key, configModified
        if configModified != time.ctime(os.path.getmtime(CONFIG_FILE)):
            log.debug('The congif file has been modified, reading for updated login info')
            Config.read(CONFIG_FILE)
            userName = Config.get("AUTHENTICATION", "UserName")
            password = Config.get("AUTHENTICATION", "Password")
            configModified = time.ctime(os.path.getmtime(CONFIG_FILE))
            key = base64.b64encode("%s:%s" % (userName, password))
        ''' Present frontpage with user authentication. '''
        if self.headers.getheader('Authorization') is None:
            self.do_AUTHHEAD()
            self.wfile.write('no auth header received')
            pass
        elif self.headers.getheader('Authorization') == 'Basic ' + key:
            self.do_GET_AUTH()
            pass
        else:
            self.do_AUTHHEAD()
            self.wfile.write(self.headers.getheader('Authorization'))
            self.wfile.write('not authenticated')
            pass

    def do_GET_AUTH(self):
        """ Overrides SimpleHTTPRequestHandler.do_GET() to handle
PyBBIO function calls. """
        url = self.raw_requestline.split(' ')[1]
        log.debug('Process GET request for %s' % url)
        if '?' in url:
            # We've received a request for a PyBBIO function call,
            # parse out parameters:
            urlParams = url.split('?')[1]
            if urlParams.startswith('_'):
                self.raw_requestline.split(' ')[1] = url.split('?')[0]
                raise
            params = urlparse.parse_qs(urlParams)
            try:
                # try to get the function_id parameter, if its not present, parse the request as a normal request
                # i.e doesnot contain call to a python function
                function_id = params['function_id'][0]
                function = FUNCTIONS.get(function_id)
                # Based on the number of Parameters we will call the functions
                paramCount = len(params) - 1
                log.debug('Received reqest for function %s along with %s parameters' % (function_id, paramCount))
                try:
                    response = callFunctionWithParams(function_id, function, paramCount, params)
                except TypeError, e:
                    log.error('Undefined Function requested: %s' % e.message)
                    log.error(traceback.format_exc())
                    response = json.dumps(
                        {"FunctionName": function_id, "Result": "ERROR:Function not defined at server"})
                except Exception, e:
                    log.error(e.message)
                    log.error(traceback.format_exc())
                    response = json.dumps({"FunctionName": function_id, "Result": "ERROR:%s" % e})

                # Send the HTTP headers:
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                # Our length is simply the length of our function return value:
                self.send_header("Content-length", len(response))
                self.send_header('Server', 'PyBBIO Server')
                self.end_headers()

                # And finally we write the response:
                self.wfile.write(response)
                return
            except Exception, e:
                log.warn(e)
                SimpleHTTPRequestHandler.do_GET(self)
        else:
            # If we get here there's no function id in the request, which
            # means it's a normal page request; let SimpleHTTPRequestHandler
            # handle it the standard way:
            SimpleHTTPRequestHandler.do_GET(self)

    def address_string(self):
        host, port = self.client_address[:2]

    def do_POST(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST',
                     'CONTENT_TYPE': self.headers['Content-Type'],
                     })
        function_id = 'POST_HANDLER'
        try:
            function_id = form['function_id'].value
            function = FUNCTIONS.get(function_id)
            paramCount = len(form) - 1
            response = callFunctionWithParams(function_id, function, paramCount, form)
        except Exception, e:
            log.error('Error handleing POST request: %s' % e.message)
            log.error(traceback.format_exc())
            response = json.dumps({"FunctionName": function_id, "Result": "ERROR:%s" % e})
        # Send the HTTP headers:
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            # Our length is simply the length of our function return value:
            self.send_header("Content-length", len(response))
            self.send_header('Server', 'PyBBIO Server')
            self.end_headers()
            # And finally we write the response:
            self.wfile.write(response)
            return
        except Exception, e:
            log.error(e)
            log.error(traceback.format_exc())


class BBIOHTTPServer(HTTPServer):
    def handle_error(self, request, client_address):
        """ Overrides HTTPServer.handle_error(). """
        # Sometimes when refreshing or navigating away from pages with
        # monitor divs, a Broken pipe exception is thrown on the socket
        # level. By overriding handle_error() we are able to ignore these:
        error = traceback.format_exc()
        if "Broken pipe" in error:
            return

        # Otherwise we want to print the error like normal, except that,
        # because BBIOServer redirects stderr by default, we want it to
        # print to stdout:
        traceback.print_exc(file=sys.stdout)
        print '-' * 40
        print 'Exception happened during processing of request from',
        print client_address
        print '-' * 40


class RequestFilter(object):
    # This acts as a file object, but it doesn't print any messages
    # from the server.
    def write(self, err):
        if not (('GET' in err) or ('404' in err) or ('POST' in err)):
            print err

    def flush(self):
        pass


class BBIOServer(object):
    def __init__(self, port=8000, verbose=False, blocking=True):
        self._server = BBIOHTTPServer(('', port), BBIORequestHandler)
        self.blocking = blocking

        if not (verbose):
            # A log of every request to the server is written to stderr.
            # This makes for a lot of printing when using the monitors.
            # We can avoid this by redirecting stderr to a RequestFilter()
            # instance:
            sys.stderr = RequestFilter()

    def start(self):
        # Start srver in a daemon thread:
        server_thread = threading.Thread(target=self._server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        if self.blocking:
            try:
                while True:
                    time.sleep(10000)
            except KeyboardInterrupt:
                log.debug('Keyboard interrupt, exiting')
                killSystem()
                os._exit(-1)
                sys.exit(-1)

    def stop(self):
        self._server.server_close()

    def registerFunction(self, functionName, function):
        FUNCTIONS[functionName] = function

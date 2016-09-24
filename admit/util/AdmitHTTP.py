"""
   **AdmitHTTP** --- Data browser services module.
   -----------------------------------------------

   This module defines the classes needed to serve ADMIT data
   to the data browser on a localhost port.   These classes are
   subclasses of those provided in the Python library BaseHTTPServer
   module.
"""

import os
import posixpath
import urllib
import sys
import json
import socket
import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

__all__ = ["AdmitHTTPServer", "AdmitHTTPRequestHandler"]

class AdmitHTTPServer(BaseHTTPServer.HTTPServer):
    """This class is identical to BaseHTTPServer.HTTPServer except
        1) It defines a fixed document root instead of using the current
           working directory.
        2) The handler class is fixed to be AdmitHTTPRequestHandler.

       This is accomplished by overriding the constructor and
       BaseServer.finish_request().

       Parameters
       ----------
       server_address : tuple
           The address on which the server is listening.  This is a tuple
           containing a string giving the address, and an integer port
           number: ('127.0.0.1', 80), for example.

       docroot : string
           The document root directory for the local data web server.  Requests
           will be served out of this directory. ** todo: possibly make
           this always localhost**

       postcallback : function
           The external function to call when handling a POST.

       Attributes
       ----------
       _documentRoot : string
           The document root directory for the web server.  Requests will be
           served out of this directory.
    """

    def __init__(self, server_address, docroot, postcallback):
        self._documentRoot=docroot
        self._postCallbackFn = postcallback
        BaseHTTPServer.HTTPServer.__init__(self,server_address, AdmitHTTPRequestHandler)
        self.timeout = None

    def finish_request(self, request, client_address):
        """Finish one http request by instantiating RequestHandlerClass.
           Construction of the handler class calls the methods to process
           the request.
           *overrides:* `BaseServer.finish_request <https://docs.python.org/2/library/socketserver.html#SocketServer.BaseServer.finish_request>`_
        """
        #print "server %s:%d finishing request with handler docroot: %s" % (self.server_address[0], self.server_address[1], self._documentRoot )
        try:
            self.RequestHandlerClass(request, client_address, docroot=self._documentRoot,postcallback=self._postCallbackFn)
        except: 
            self.handle_error(request,client_address)



class AdmitHTTPRequestHandler(SimpleHTTPRequestHandler):
    """And HTTP request handler that allows a fixed document root.
       Python's SimpleHTTPRequestHandler always uses the current
       working directory which is stored globally. Therefore,
       SimpleHTTPRequestHandler cannot be used to spawn off
       http servers in separate threads because they will
       overwrite each other's working directories.
       """
    def __init__(self,request,client_address,docroot,postcallback):
       # Note: documentRoot must be set BEFORE instantiation of SimpleHTTPServer
       # because the __init__ in the base class calls the methods that
       # actually handle the request, including AdmitHTTPServer.finish_request()
       # above.
       self._documentRoot = docroot
       # for now don't log anything; it's too verbose
       self._logging = False
       self._postCallbackFn = postcallback
       try:
           SimpleHTTPRequestHandler.__init__(self, request=request, client_address=client_address, server=None)
       except:
           if self.is_broken_pipe_error(): pass
           else: raise

    def is_broken_pipe_error(self):
        exc_type, exc_value = sys.exc_info()[:2]
        return issubclass(exc_type, socket.error) and exc_value.args[0] == 32

    def handle_error(self, request, client_address):
        if self.is_broken_pipe_error():
            print "- Broken pipe from %s\n" % str(client_address)
            return

    """Override base class log message method to bypass logging."""
    def log_message(self,format,*args):
       if self._logging:
            SimpleHTTPRequestHandler.log_message(self, format, *args)

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.
        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.
        This method is identical to SimpleHTTPRequestHandler.translate_path()
        except it uses the locally stored document root instead of the current
        working directory.

        """
        # abandon query parameters
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        # Always use document root!
        path = self._documentRoot
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        return path

    def do_OPTIONS(self):
        self.send_response(200, "ok")       
        self.send_header('Access-Control-Allow-Origin', '*')                
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, HEAD')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With", "Content-Type") 

    def do_POST(self):
        length = int(self.headers['Content-Length'])
        self.data_string = self.rfile.read(length)
        #print "DATASTRING=%s" % self.data_string
        if self.data_string[0] != "{":
            # Firefox sends extra GETs disguised as POSTs with
            # garbage data.  Need to deal with this.
            # Disabling network prefetch in about:config does not fix it.
            #print "this looks like a bogus GET"
            #self.send_response(200)
            # THE ISSUE HERE IS WHAT RESPONSE TO SEND THAT DOES
            # NOT BREAK THE BROWSER VIEW.  200 will refresh
            # a blank page.  We really just want the button to
            # come unstuck and no refresh of html.
            # The correct answer may be do nothing.
            return
 
        try: 
            data = json.loads(self.data_string)
            #print "GOT JSON: %d \n %s" % (len(data), data)
            #command = data["command"]
            #print "command = %s" % command
            print "User agent: %s " % self.headers['user-agent']
            data["firefox"] = self.isFirefox()
            self._postCallbackFn(data)
            self.send_response(200)
        except Exception, e:
            print "Problem with server/browser connection: ", e
            # This is almost certainly the firefox bug, try sending 200
            # instead of 400
            #print "sending 200 anyway"
            self.send_response(200)

        self.send_header('Content-type','text/html')
        self.end_headers()

        return

    def isFirefox(self):
        """Attempt to detect the Firefox browser. This is because Firefox does
           funny things and we have to workaround it.
           Return True if the user-agent header contains the string 'firefox'  
           (case insensitive)
        """
        return self.headers['user-agent'].lower().find('firefox') != -1


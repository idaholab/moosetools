from RunApp import RunApp
from util import runCommand
import os
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
import threading, cgi

class ICEUpdaterTester(RunApp):

  @staticmethod
  def validParams():
    params = RunApp.validParams()
    params.addRequiredParam('nPosts', "The Number of Expected Posts")
    params.addRequiredParam('port', "The port to listen to")

    return params

  def __init__(self, name=None, params=None):
    RunApp.__init__(self, name, params)
    if params is not None:
       self.nPosts = self.getParam('nPosts')
       self.port = int(self.getParam('port'))

    self.httpServer = SimpleHttpServer("localhost", self.port)
    self.httpServer.start()

  # This method is called prior to running the test.  It can be used to cleanup files
  # or do other preparations before the tester is run
  def prepare(self):
    return

  # This method is called to return the commands (list) used for processing results
  def processResultsCommand(self, moose_dir, options):
    commands = []
    return commands

  # This method should return the executable command that will be executed by the tester
  def getCommand(self, options):
    command = RunApp.getCommand(self, options)
    return command

  # This method will be called to process the results of running the test.  Any post-test
  # processing should happen in this method
  def processResults(self, moose_dir, retcode, options, output):
    if self.httpServer.getNumberOfPosts() != int(self.nPosts):
       return ("ICEUpdater FAILED: DID NOT GET CORRECT NUMBER OF POSTS",
               "Number of Posts was " + str(self.httpServer.getNumberOfPosts()) +
               ", but should have been " + str(self.nPosts))
    else:
       return RunApp.processResults(self, moose_dir, retcode, options, output)

class HTTPRequestHandler(BaseHTTPRequestHandler):
    nPosts = 0
    def do_POST(self):
        length = int(self.headers.getheader('content-length'))
        data = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
        print data
        HTTPRequestHandler.nPosts += 1
        self.send_response(200)
        return

    def getNumberOfPosts(self):
        return self.nPosts

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True

    def shutdown(self):
        self.socket.close()
        HTTPServer.shutdown(self)

    def getNumberOfPosts(self):
        return HTTPRequestHandler.nPosts

class SimpleHttpServer():
    def __init__(self, ip, port):
        self.server = ThreadedHTTPServer((ip, port), HTTPRequestHandler)

    def getNumberOfPosts(self):
        return self.server.getNumberOfPosts()

    def start(self):
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def stop(self):
        self.server.shutdown()

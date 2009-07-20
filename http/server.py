# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2009 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008-2009 David Versmisse <david.versmisse@itaapy.com>
# Copyright (C) 2009 Hervé Cauwelier <herve@itaapy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Import from the Standard Library
from signal import signal, SIGINT
from socket import error as SocketError
from socket import socket as Socket
from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from time import strftime, time

# Import from itools
from exceptions import BadRequest
from request import Request
from response import get_response

# Import from gobject
from gobject import MainLoop, io_add_watch, source_remove, timeout_add
from gobject import IO_IN, IO_OUT, IO_PRI, IO_ERR, IO_HUP, IO_NVAL


# IO masks
IO_RECV = IO_PRI | IO_IN
IO_SEND = IO_OUT
IO_ERRO = IO_ERR | IO_HUP | IO_NVAL

# When the number of connections hits the maximum number of connections
# allowed, new connections will be automatically responded with the
# "503 Service Unavailable" error
MAX_CONNECTIONS = 50

# When a connection is not active for the number of seconds defined here, it
# will be closed.
CONN_TIMEOUT = 10



###########################################################################
# Wrapper around sockets in non-blocking mode that offers a file
# like API
###########################################################################
class SocketWrapper(object):
    """Offers a file-like interface for sockets in non-blocking mode.
    Read only.
    """

    __slots__ = ['socket', 'buffer']

    def __init__(self, socket):
        self.socket = socket
        self.buffer = ''


    def read(self, size):
        buffer = self.buffer
        buffer_size = len(buffer)
        # Check we already have the required data
        if buffer_size >= size:
            data, self.buffer = buffer[:size], buffer[size:]
            return data
        # Try to read the remaining
        try:
            data = self.socket.recv(size - buffer_size)
        except Exception:
            return None
        # This method is supposed to be called only when there is data to be
        # read. So if no data is available, we suppose the data is truncated
        # and we raise the EOFError exception.
        if not data:
            raise EOFError
        buffer += data
        # Check we now have the required data
        if len(buffer) >= size:
            data, self.buffer = buffer[:size], buffer[size:]
            return data
        # Could not read the required data
        self.buffer = buffer
        return None


    def readline(self):
        """This method is like the file object readline method, but not
        exactly.

        Written specifically for the HTTP protocol, it expects the sequence
        '\r\n' to signal line ending.

        This method is supposed to be called only when there is data to be
        read. So if no data is available, we suppose the line is truncated
        and we raise the EOFError exception.

        If the end-of-line sequence was not being received the value None
        is returned, what means: call me again when more data is available.
        """
        # FIXME Try to make it more like the file interface.
        buffer = self.buffer
        # Check if there is already a line in the buffer
        if '\r\n' in buffer:
            line, self.buffer = buffer.split('\r\n', 1)
            return line
        # Read as much as possible
        recv = self.socket.recv
        # FIXME Here we assume that if the call to "recv" fails is because
        # there is no data available, and we should try again later. But
        # the failure maybe for something else. So we must do proper error
        # handling here. Check http://docs.python.org/lib/module-errno.html
        # for a list of the possible errors.
        try:
            data = recv(512)
        except Exception:
            return None
        if not data:
            # Send the data read so far
            raise EOFError, buffer
        while data:
            buffer += data
            # Hit
            if '\r\n' in buffer:
                line, self.buffer = buffer.split('\r\n', 1)
                return line
            # Miss
            if len(data) < 512:
                self.buffer = buffer
                return None
            # FIXME Catch only the relevant exceptions (see note above)
            try:
                data = recv(512)
            except Exception:
                return None


###########################################################################
# The HTTP Server
###########################################################################
class HTTPConnection(object):
    """This class represents a persistent HTTP connection.
    """

    __slots__ = ['conn', 'recv', 'send', 'recv_id', 'send_id', 'erro_id', 'ts']

    def __init__(self, conn):
        # Socket connection
        self.conn = conn

        # Request & Response
        self.recv = (None, None) # (<Request>, request loader)
        self.send = None         # response string

        # Source ids
        self.recv_id = None
        self.send_id = None
        self.erro_id = None

        # Timestamp
        self.ts = time()

        # New request
        self.new_request()


    def new_request(self):
        request = Request()
        loader = request.non_blocking_load(SocketWrapper(self.conn))
        self.recv = (request, loader)



###########################################################################
# The HTTP Server
###########################################################################

class HTTPServer(object):

    def __init__(self, address='', port=8080):
        # The server listens to...
        self.address = address
        self.port = port

        # The connection
        self.ear = None
        self.ear_fileno = 0
        self.ear_id = 0

        # Main Loop
        self.main_loop = MainLoop()

        # The active connections: {fileno: <Connection>}
        self.connections = {}


    def close_connection(self, fileno):
        connection = self.connections.pop(fileno)
        connection.conn.close()
        for id in connection.recv_id, connection.send_id, connection.erro_id:
            if id is not None:
                source_remove(id)

        return False


    def get_connection(self, fileno):
        connection = self.connections[fileno]
        connection.ts = time()
        return connection


    #######################################################################
    # Callbacks
    #######################################################################
    def new_connection(self, fileno, event):
        """Registers the connection to read the new request.
        """
        # Accept the connection
        try:
            conn, client_address = self.ear.accept()
        except SocketError:
            return True

        # Non-blocking mode
        conn.setblocking(0)

        # Watch
        fileno = conn.fileno()
        recv_id = io_add_watch(fileno, IO_RECV, self.recv_callback)
        erro_id = io_add_watch(fileno, IO_ERRO, self.erro_callback)

        # Make the <HTTPConnection> object
        connection = HTTPConnection(conn)
        connection.recv_id = recv_id
        connection.erro_id = erro_id
        self.connections[fileno] = connection

        return True


    def erro_callback(self, fileno, event):
        return self.close_connection(fileno)


    def recv_callback(self, fileno, event):
        """Loads the request, and when it is done, handles it.
        """
        # Read the request
        connection = self.get_connection(fileno)
        request, loader = connection.recv
        try:
            loader.next()
            return True
        except StopIteration:
            response = self.handle_request(request)
        except EOFError:
            return self.close_connection(fileno)
        except BadRequest:
            self.log_error()
            response = get_response(400)
        except Exception:
            self.log_error()
            response = get_response(500)

        # Log access
        self.log_access(connection.conn, request, response)

        # Ready to send response
        connection.send = response.to_str()
        connection.send_id = io_add_watch(fileno, IO_OUT, self.send_callback)

        # Is this the last request
        if request.get_header('connection') == 'close':
            source_remove(connection.recv_id)
            connection.recv = (None, None)
            connection.recv_id = None
            return False
        else:
            connection.new_request()
            return True


    def send_callback(self, fileno, event):
        connection = self.get_connection(fileno)

        # Send the response
        response = connection.send
        try:
            n = connection.conn.send(response)
        except SocketError:
            return self.close_connection(fileno)

        # Continue
        if n < len(response):
            connection.send = response[n:]
            return True

        # Done
        if connection.recv_id is None:
            return self.close_connection()
        return False


    def clean_callback(self):
        now = time()
        for fileno in self.connections.keys():
            connection = self.connections[fileno]
            if (now - connection.ts) > CONN_TIMEOUT:
                self.close_connection(fileno)

        # Quit
        if not self.ear and not self.connections:
            self.stop()
            return False

        # Continue
        return True


    #######################################################################
    # Start & Stop
    #######################################################################
    def start(self):
        # Set up the connection
        ear = self.ear = Socket(AF_INET, SOCK_STREAM)
        # Allow to reuse the address, this solves the bug "icms.py won't
        # close its connection properly". But is probably not the right
        # solution (FIXME).
        ear.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        ear.bind((self.address, self.port))
        ear.listen(5)
        self.ear_fileno = ear.fileno()
        self.ear_id = io_add_watch(self.ear_fileno, IO_IN | IO_PRI,
                                   self.new_connection)

        # Set up the graceful stop
        signal(SIGINT, self.stop_gracefully)

        # Set timeout callback to clean unused connections
        timeout_add(2000, self.clean_callback)

        # Main loop !!
        self.main_loop.run()


    def stop_gracefully(self, signum, frame):
        """Inmediately stop accepting new connections, and quit once there
        are not more ongoing requests.
        """
        # Close the ear
        if self.ear is not None:
            source_remove(self.ear_id)
            self.ear.close()
            self.ear = None
            self.ear_fileno = 0
            self.ear_id = 0

        # Quit
        print 'Shutting down the server (gracefully)...'
        if not self.connections:
            self.stop()


    def stop(self):
        self.main_loop.quit()


    def handle_request(self, request):
        # 503 Service Unavailable
        if len(self.connections) > MAX_CONNECTIONS:
            return get_response(503)

        try:
            return self._handle_request(request)
        except Exception:
            self.log_error()
            return get_response(500)


    #######################################################################
    # Logging
    #######################################################################
    def log_access(self, conn, request, response):
        # Common Log Format
        #  - IP address of the client
        #  - RFC 1413 identity (not available)
        #  - username (XXX not provided right now, should we?)
        #  - time (XXX we use the timezone name, while we should use the
        #    offset, e.g. +0100)
        #  - the request line
        #  - the status code
        #  - content length of the response
        host = request.get_remote_ip()
        if host is None:
            host, port = conn.getpeername()
        ts = strftime('%d/%b/%Y:%H:%M:%S %Z')
        request_line = request.request_line
        status = response.status
        length = response.get_content_length()
        line = '{0} - - [{1}] "{2}" {3} {4}\n'
        line = line.format(host, ts, request_line, status, length)

        self._log_access(line)


    #######################################################################
    # To override by subclasses
    #######################################################################
    def _handle_request(self, request):
        raise NotImplementedError


    def _log_access(self, line):
        pass


    def log_error(self, context=None):
        pass


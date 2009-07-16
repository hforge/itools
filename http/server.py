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
from logging import getLogger
from signal import signal, SIGINT
from socket import error as SocketError
from socket import socket as Socket
from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR

# Import from itools
from exceptions import BadRequest
from request import Request
from response import get_response

# Import from gobject
from gobject import MainLoop, io_add_watch, source_remove
from gobject import IO_IN, IO_OUT, IO_PRI, IO_ERR, IO_HUP


# Used to limit the load of the server
MAX_CONNECTIONS = 50

# Global variables
logger = getLogger('itools.http')


# TODO Add a timeout to connections, so they are closed after a while.
# TODO Then change 'stop_gracefully' so it quits when there are no more
# connections (and remove the 'activity' variable).
# TODO Handle the IO_ERR and IO_HUP events.


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
        except:
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
        except:
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
            except:
                return None


###########################################################################
# The HTTP Server
###########################################################################
class Connection(object):

    __slots__ = ['conn', 'request', 'loader', 'response']

    def __init__(self, conn):
        self.conn = conn
        self.request = None
        self.loader = None
        self.response = None

        # New request
        self.new_request()


    def new_request(self):
        self.request = Request()
        self.loader = self.request.non_blocking_load(SocketWrapper(self.conn))



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
        self.activity = 0


    #######################################################################
    # Callbacks
    #######################################################################
    def new_connection(self, fileno, event):
        """Registers the connection to read the new request.
        """
        # Get the connection and client address
        try:
            conn, client_address = self.ear.accept()
        except SocketError:
            return True

        # Set non-blocking mode
        conn.setblocking(0)
        # Register the connection
        fileno = conn.fileno()
        id = io_add_watch(fileno, IO_PRI | IO_IN, self.load_request)
        # Keep the connection
        self.connections[fileno] = Connection(conn)

        return True


    def load_request(self, fileno, event):
        """Loads the request, and when it is done, handles it.
        """
        # Read the request
        connection = self.connections[fileno]
        try:
            connection.loader.next()
            return True
        except StopIteration:
            self.activity += 1
            response = self.handle_request(connection.request)
        except BadRequest:
            self.activity += 1
            self.log_error()
            response = get_response(400)
        except:
            self.activity += 1
            self.log_error()
            response = get_response(500)

        # Log access
        connection.response = response
        self.log_access(connection)
        connection.response = response.to_str()

        # Ready to send response
        io_add_watch(fileno, IO_OUT, self.send_response)

        # Is this the last request
        if connection.request.get_header('connection') == 'close':
            connection.request = None
            conenection.loader = None
            return False
        else:
            connection.new_request()
            return True


    def send_response(self, fileno, event):
        connection = self.connections[fileno]

        # Send the response
        response = connection.response
        try:
            n = connection.conn.send(response)
        except SocketError:
            connection.conn.close()
            del self.connections[fileno]
            self.activity -= 1
            if self.ear is None and self.activity == 0:
                self.stop()
            return False

        # Continue
        if n < len(response):
            connection.response = response[n:]
            return True

        # Done
        if connection.request is None:
            connection.conn.close()
            del self.connections[fileno]
        self.activity -= 1
        if self.ear is None and self.activity == 0:
            self.stop()
        return False


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
        ear_fileno = self.ear_fileno = ear.fileno()
        ear_id = self.ear_id = io_add_watch(ear_fileno, IO_IN | IO_PRI,
                                            self.new_connection)

        # Set up the graceful stop
        signal(SIGINT, self.stop_gracefully)

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
        if self.activity == 0:
            self.main_loop.quit()


    def stop(self):
        self.main_loop.quit()


    def handle_request(self, request):
        # 503 Service Unavailable
        if len(self.connections) > MAX_CONNECTIONS:
            return get_response(503)

        try:
            return self._handle_request(request)
        except:
            self.log_error()
            return get_response(500)


    #######################################################################
    # To override by subclasses
    #######################################################################
    def _handle_request(self, request):
        raise NotImplementedError


    def log_access(self, connection):
        pass


    def log_error(self, context=None):
        pass


# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA

# Import from the Standard Library
import socket
import thread
import traceback

# Import from itools
from itools.resources import memory
from itools.web.context import Context, get_context, set_context
from itools.web.request import Request



class Pool(object):
    # XXX Right now we only support one handler tree (may use semaphores)

    def __init__(self, root):
        self.lock = thread.allocate_lock()
        self.pool = [root]


    def pop(self):
        self.lock.acquire()
        return self.pool.pop()


    def push(self, root):
        self.pool.append(root)
        self.lock.release()



def handle_request(connection, pool):
    try:
        # Start, init context
        # Read socket
        data = connection.recv(8192)
        # Build request
        resource = memory.File(data)
        request = Request(resource)
        # Build context
        context = Context(request)
        set_context(context)

        # Get the root handler
        root = pool.pop()

        # Get the handler
        context = get_context()
        request, response = context.request, context.response

        path = context.path
        handler = root.get_handler(path)

        # Get the method
        method_name = context.method
        http_method = request.method

        if method_name is None:
            method_name = http_method

        method = getattr(handler, method_name)
##        method = handler.get_method(method_name)

        # Check security
        if method is None:
            method = handler.forbidden_form

        # Call the method
        response_body = method()
        response.set_header('Content-Type', 'text/plain')
        response.set_body(response_body)

        # Free the root object
        pool.push(root)

        # Finish, send back the response
        response = get_context().response
        response = response.to_str()
        connection.send(response)
    except:
        connection.close()
        traceback.print_exc()
    else:
        connection.close()


class Server(object):

    def __init__(self, root, address='127.0.0.1', port=8000):
        # The application's root
        self.pool = Pool(root)
        # The address and port the server will listen to
        self.address = address
        self.port = port


    def start(self):
        ear = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ear.bind((self.address, self.port))
        ear.listen(5)

        while True:
            try:
                connection, client_address = ear.accept()
            except socket.error:
                continue

            thread.start_new_thread(handle_request, (connection, self.pool))


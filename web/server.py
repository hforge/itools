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
import traceback

# Import from itools
from itools.resources import memory
from itools.web.context import Context, get_context, set_context
from itools.web.request import Request
from itools.web import application



class Application(application.Application):

    def __init__(self, root_reference, address='127.0.0.1', port=8000):
        self.root_reference = root_reference
        self.address = address
        self.port = port


    def init_context(self):
        # Read socket
        socket = self.request
        data = socket.recv(8192)
        # Build request
        resource = memory.File(data)
        request = Request(resource)
        # Build context
        context = Context(request)
        set_context(context)


    def send_response(self):
        # Send back the response
        response = get_context().response
        response = response.to_str()
        self.request.send(response)


    def run(self):
        ear = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ear.bind((self.address, self.port))
        ear.listen(5)

        while True:
            try:
                request, client_address = ear.accept()
            except socket.error:
                continue

            self.request = request
            try:
                self.handle_request()
            except:
                request.close()
                # Show error
                traceback.print_exc()
            request.close()



if __name__ == '__main__':
    application = Application('/home/jdavid/test')
    application.run()

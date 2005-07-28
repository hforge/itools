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
import thread

# Import from itools
from itools.handlers import get_handler
from itools.web.context import get_context


roots = {}
roots_lock = thread.allocate_lock()


class Application(object):

    def __init__(self, root_reference):
        # A uri reference to the root resource
        self.root_reference = root_reference


    def handle_request(self):
        # Start, init context
        self.init_context()

        # Get the root handler
        key = (thread.get_ident(), self.root_reference)
        if key in roots:
            root = roots[key]
            if root.is_outdated():
                root.load_state()
        else:
            root = self.get_root_handler()
            # Store in the cache
            roots_lock.acquire()
            try:
                roots[key] = root
            finally:
                roots_lock.release()

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

        # Finish, send response
        return self.send_response()


    def get_root_handler(self):
        return get_handler(self.root_reference)


    def init_context(self):
        raise NotImplementedError


    def send_response(self):
        raise NotImplementedError


    def run(self):
        return self.handle_request()

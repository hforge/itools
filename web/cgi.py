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
from os import environ
from sys import stdin

# Import from itools
from itools import uri
from itools.web.context import Context, get_context, set_context
from itools.web.request import Request
from itools.web import application


class Application(application.Application):

    def init_context(self):
        # Build the request
        request = Request()

        # The request method
        request_method = environ['REQUEST_METHOD']
        request.set_method(request_method)

        # The path
        path = environ.get('PATH_INFO', '')
        request.set_path(path)

        # The referrer
        if 'HTTP_REFERER' in environ:
            request.set_header('Referer', environ['HTTP_REFERER'])

        # The form
        if request_method == 'GET':
            data = environ['QUERY_STRING']
        elif request_method == 'POST':
            content_length = environ['CONTENT_LENGTH']
            data = stdin.read(content_length)
        else:
            raise ValueError, 'method "%s" not yet supported' % request_method

        # Parse the form data
        for parameter in data.split('&'):
            if parameter:
                key, value = parameter.split('=', 1)
                request.state.form[key] = value

        # Cookies
##        environ['HTTP_COOKIE']

        # Build the context
        context = Context(request)
        set_context(context)


##        # The request URI
##        request_uri = 'http://%s:%s/%s' % (environ['HTTP_HOST'],
##                                           environ['SERVER_PORT'],
##                                           environ['REQUEST_URI'])
##        request.set_uri(request_uri)



    def send_response(self):
        response = get_context().response.to_str()
        # Remove status line
        print '\n'.join(response.splitlines()[1:])


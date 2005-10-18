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

# Import from itools
from itools.datatypes import QName
from itools.schemas.registry import get_datatype_by_prefix
from itools.handlers.File import File
from itools.web import headers
from itools.web import entities


status_messages = {
    # Informational
    100: 'Continue',
    101: 'Switching Protocols',
    # Success
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',
    # Redirection
    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    307: 'Temporary Redirect',
    # Client error
    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Request Entity Too Large',
    414: 'Request-URI Too Long',
    415: 'Unsupported Media Type',
    416: 'Requested Range Not Satisfiable',
    417: 'Expectation Failed',
    # Server error
    500: 'Internal error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
    }


class Cookie(object):

    def __init__(self, value, expires=None, domain=None, path=None,
                 max_age=None, comment=None, secure=None):
        self.value = value
        # Parameters
        self.expires = expires
        self.domain = domain
        self.path = path
        self.max_age = max_age
        self.comment = comment
        self.secure = secure



class Response(File):

    def get_skeleton(self, status_code=200, **kw):
        status_message = status_messages[status_code]
        skeleton = ['HTTP/1.1 %s %s\n' % (status_code, status_message)]
        for name in kw:
            skeleton.append('%s: %s\n' % (name, kw[name]))

        skeleton.append('\n')
        skeleton.append('Welcome to itools\n')
        return ''.join(skeleton)


    def _load_state(self, resource):
        state = self.state

        data = resource.read()
        # The status line
        line, data = entities.read_line(data)
        http_version, status_code, status_message = line.split()
        status_code = int(status_code)
        self.set_status(status_code)
        # The headers
        response_headers, data = entities.read_headers(data)
        state.headers = response_headers
        # The body
        state.body = data
        # The cookies
        state.cookies = {}


    def to_str(self):
        state = self.state

        data = []
        # The status
        status_code = state.status
        status_message = status_messages[status_code]
        data.append('HTTP/1.1 %d %s\n' % (status_code, status_message))
        # The header
        for name in state.headers:
            value = state.headers[name]
            type = headers.get_type(name)
            value = type.encode(value)
            data.append('%s: %s\n' % (name, value))
        # Content length
        if 'content-length' not in state.headers:
            data.append('Content-Length: %d\n' % len(state.body))
        # The Cookies
        for name in state.cookies:
            cookie = state.cookies[name]
            # The parameters
            parameters = []
            if cookie.expires is not None:
                parameters.append('; Expires=%s' % cookie.expires)
            if cookie.domain is not None:
                parameters.append('; Domain=%s' % cookie.domain)
            if cookie.path is not None:
                parameters.append('; Path=%s' % cookie.path)
            if cookie.max_age is not None:
                parameters.append('; Max-Age=%s' % cookie.max_age)
            if cookie.comment is not None:
                parameters.append('; Comment=%s' % cookie.comment)
            if cookie.secure is not None:
                parameters.append('; Secure=%s' % cookie.secure)
            # The value
            prefix, local_name = QName.decode(name)
            datatype = get_datatype_by_prefix(prefix, local_name)
            value = datatype.encode(cookie.value)

            data.append(
                'Set-Cookie: %s="%s"%s\n' % (name, value, ''.join(parameters)))
        # A blank line separates the header from the body
        data.append('\n')
        # The body
        data.append(state.body)

        return ''.join(data)


    #########################################################################
    # API
    #########################################################################
    def set_status(self, status):
        self.state.status = status


    def set_body(self, body):
        state = self.state
        if isinstance(body, unicode):
            body = body.encode('UTF-8')
        state.body = body


    def redirect(self, location, status=302):
        self.set_status(status)
        self.set_header('Location', location)


    #########################################################################
    # Headers
    def set_header(self, name, value):
        type = headers.get_type(name)
        self.state.headers[name] = type.decode(value)


    def has_header(self, name):
        return name in self.state.headers


    #########################################################################
    # Cookies
    def set_cookie(self, name, value, **kw):
        self.state.cookies[name] = Cookie(value, **kw)


    def del_cookie(self, name):
        self.set_cookie(name, 'deleted', expires='Wed, 31-Dec-97 23:59:59 GMT',
                        max_age='0')


    def get_cookie(self, name):
        return self.state.cookies.get(name)


    #########################################################################
    # For Zope
    #########################################################################
    __str__ = to_str

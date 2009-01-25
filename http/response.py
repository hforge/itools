# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Hervé Cauwelier <herve@itaapy.com>
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
from datetime import datetime

# Import from itools
from itools.datatypes import HTTPDate
from cookies import Cookie, SetCookieDataType
from headers import get_type
from entities import read_headers
from message import Message


status_messages = {
    # Informational (HTTP 1.1)
    100: 'Continue',
    101: 'Switching Protocols',
    # Success (HTTP 1.0)
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    204: 'No Content',
    # Success (HTTP 1.1)
    203: 'Non-Authoritative Information',
    205: 'Reset Content',
    206: 'Partial Content',
    # Redirection (HTTP 1.0)
    301: 'Moved Permanently',
    302: 'Found',
    304: 'Not Modified',
    # Redirection (HTTP 1.1)
    300: 'Multiple Choices',
    303: 'See Other',
    305: 'Use Proxy',
    307: 'Temporary Redirect',
    # Client error (HTTP 1.0)
    400: 'Bad Request',
    401: 'Unauthorized',
    403: 'Forbidden',
    404: 'Not Found',
    # Client error (HTTP 1.1)
    402: 'Payment Required',
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
    # Client error (WebDAV),
    423: 'Locked',
    # Server error (HTTP 1.0)
    500: 'Internal error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    # Server error (HTTP 1.1)
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
    }


class Response(Message):

    def new(self, status_code=200, **kw):
        self.http_version = '1.1'
        self.status = status_code
        self.headers = kw
        self.body = ''
        self.cookies = {}


    def _load_state_from_file(self, file):
        # The status line
        line = file.readline()
        http_version, status_code, status_message = line.split(' ', 2)
        self.http_version = http_version
        status_code = int(status_code)
        self.set_status(status_code)
        # The headers
        self.headers = read_headers(file)
        # The body
        self.body = file.read()
        # The cookies
        self.cookies = {}


    def to_str(self):
        from itools import __version__
        data = []
        # The status line
        http_version = self.http_version
        status_code = self.status
        status_message = status_messages[status_code]
        data.append('HTTP/%s %d %s\r\n' % (http_version, status_code,
                                           status_message))
        # Headers
        # Date:
        date = datetime.now()
        data.append('Date: %s\r\n' % HTTPDate.encode(date))
        # Server:
        data.append('Server: itools/%s\r\n' % __version__)
        # User defined headers
        for name in self.headers:
            if name not in ['date', 'server']:
                datatype = get_type(name)
                value = self.headers[name]
                value = datatype.encode(value)
                data.append('%s: %s\r\n' % (name.title(), value))
        # Content-Length:
        if not self.has_header('content-length'):
            data.append('Content-Length: %d\r\n' % self.get_content_length())
        # The Cookies (one SetCookie header per cookie)
        for name in self.cookies:
            value = SetCookieDataType.encode({name: self.cookies[name]})
            data.append('Set-Cookie: %s\r\n' % value)
        # A blank line separates the header from the body
        data.append('\r\n')
        # The body
        if self.body is not None:
            data.append(self.body)

        return ''.join(data)


    #########################################################################
    # API
    #########################################################################
    def set_status(self, status):
        self.status = status


    def get_status(self):
        return self.status


    def set_body(self, body):
        if isinstance(body, unicode):
            body = body.encode('UTF-8')
        elif isinstance(body, str):
            pass
        elif body is None:
            pass
        else:
            raise ValueError, 'body of type %s not supported' % type(body)
        self.body = body


    def redirect(self, location, status=302):
        self.set_status(status)
        self.set_header('Location', location)


    #########################################################################
    # Content-Length
    def get_content_length(self):
        body = self.body
        if body is None:
            return 0
        return len(body)


    #########################################################################
    # Cookies
    def set_cookie(self, name, value, **kw):
        self.cookies[name] = Cookie(value, **kw)


    def del_cookie(self, name):
        self.set_cookie(name, 'deleted',
                        expires='Wed, 31-Dec-97 23:59:59 GMT', max_age='0')


    def get_cookie(self, name):
        return self.cookies.get(name)

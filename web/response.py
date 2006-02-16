# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
from datetime import datetime

# Import from itools
from itools.schemas import get_datatype
from itools.web import headers
from itools.web.headers import HTTPDate
from itools.web.message import Message
from itools.web import entities


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
    # Server error (HTTP 1.0)
    500: 'Internal error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    # Server error (HTTP 1.1)
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



class Response(Message):

    def get_skeleton(self, status_code=200, **kw):
        status_message = status_messages[status_code]
        skeleton = ['HTTP/1.1 %s %s' % (status_code, status_message)]
        for name in kw:
            skeleton.append('%s: %s' % (name, kw[name]))

        skeleton.append('')
        return '\r\n'.join(skeleton)


    def _load_state(self, resource):
        state = self.state

        # The status line
        line = resource.readline()
        http_version, status_code, status_message = line.split(' ', 2)
        status_code = int(status_code)
        self.set_status(status_code)
        # The headers
        state.headers = entities.read_headers(resource)
        # The body
        state.body = resource.read()
        # The cookies
        state.cookies = {}


    def to_str(self):
        state = self.state

        data = []
        # The status line
        status_code = state.status
        status_message = status_messages[status_code]
        data.append('HTTP/1.0 %d %s' % (status_code, status_message))
        # Headers
        # Date:
        date = datetime.utcnow()
        data.append('Date: %s' % HTTPDate.encode(date))
        # Server:
        data.append('Server: itools.web')
        # User defined headers
        for name in state.headers:
            if name not in ['date', 'server']:
                datatype = headers.get_type(name)
                value = state.headers[name]
                value = datatype.encode(value)
                data.append('%s: %s' % (name.title(), value))
        # Content-Length:
        if not self.has_header('content-length'):
            data.append('Content-Length: %d' % self.get_content_length())
        # The Cookies
        for name in state.cookies:
            cookie = state.cookies[name]
            # The parameters
            parameters = []
            if cookie.expires is not None:
                parameters.append('; expires=%s' % cookie.expires)
            if cookie.domain is not None:
                parameters.append('; domain=%s' % cookie.domain)
            if cookie.path is not None:
                parameters.append('; path=%s' % cookie.path)
            else:
                parameters.append('; path=/')
            if cookie.max_age is not None:
                parameters.append('; max-age=%s' % cookie.max_age)
            if cookie.comment is not None:
                parameters.append('; comment=%s' % cookie.comment)
            if cookie.secure is not None:
                parameters.append('; secure=%s' % cookie.secure)
            # The value
            datatype = get_datatype(name)
            value = datatype.encode(cookie.value)

            data.append('Set-Cookie: %s="%s"%s' % (name, value,
                                                   ''.join(parameters)))
        # A blank line separates the header from the body
        data.append('')
        # The body
        if state.body is not None:
            data.append(state.body)

        return '\r\n'.join(data)


    #########################################################################
    # API
    #########################################################################
    def set_status(self, status):
        self.state.status = status


    def get_status(self):
        return self.state.status


    def set_body(self, body):
        state = self.state
        if isinstance(body, unicode):
            body = body.encode('UTF-8')
        state.body = body


    def redirect(self, location, status=302):
        self.set_status(status)
        self.set_header('Location', location)


    #########################################################################
    # Content-Length
    def get_content_length(self):
        body = self.state.body
        if body is None:
            return 0
        return len(body)


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

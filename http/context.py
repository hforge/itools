# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from itools
from itools.uri import decode_query, Path
from entities import Entity
from headers import get_type, Cookie, SetCookieDataType


class HTTPContext(object):

    def __init__(self, soup_message, path):
        self.soup_message = soup_message

        # Request method and URI
        self.method = soup_message.get_method()
        self.hostname = soup_message.get_host()
        self.path = path if type(path) is Path else Path(path)
        query = soup_message.get_query()
        self.query = decode_query(query)

        # The URI as it was typed by the client
        xfp = soup_message.get_header('X_FORWARDED_PROTO')
        src_scheme = xfp or 'http'
        xff = soup_message.get_header('X-Forwarded-Host')
        src_host = xff or soup_message.get_header('Host') or self.hostname
        if query:
            self.uri = '%s://%s%s?%s' % (src_scheme, src_host, path, query)
        else:
            self.uri = '%s://%s%s' % (src_scheme, src_host, path)


    #######################################################################
    # Lazy load
    #######################################################################
    def __getattr__(self, name):
        loader = 'load_%s' % name
        loader = getattr(self.__class__, loader, None)

        # Miss
        if not loader:
            msg = "'%s' object has no attribute '%s'"
            raise AttributeError, msg % (self.__class__.__name__, name)

        # Hit
        value = loader(self)
        setattr(self, name, value)
        return value


    def load_form(self):
        # Case 1: nothing
        body = self.soup_message.get_body()
        if not body:
            self.form = {}
            return

        # Case 2: urlencoded
        type, type_parameters = self.get_header('content-type')
        if type == 'application/x-www-form-urlencoded':
            self.form = decode_query(body)
            return

        # Case 3: multipart
        if type.startswith('multipart/'):
            boundary = type_parameters.get('boundary')
            boundary = '--%s' % boundary
            self.form = {}
            for part in body.split(boundary)[1:-1]:
                if part.startswith('\r\n'):
                    part = part[2:]
                elif part.startswith('\n'):
                    part = part[1:]
                # Parse the entity
                entity = Entity()
                entity.load_state_from_string(part)
                # Find out the parameter name
                header = entity.get_header('Content-Disposition')
                value, header_parameters = header
                name = header_parameters['name']
                # Load the value
                body = entity.get_body()
                if 'filename' in header_parameters:
                    filename = header_parameters['filename']
                    if filename:
                        # Strip the path (for IE).
                        filename = filename.split('\\')[-1]
                        # Default content-type, see
                        # http://tools.ietf.org/html/rfc2045#section-5.2
                        if entity.has_header('content-type'):
                            mimetype = entity.get_header('content-type')[0]
                        else:
                            mimetype = 'text/plain'
                        self.form[name] = filename, mimetype, body
                else:
                    if name not in self.form:
                        self.form[name] = body
                    else:
                        if isinstance(self.form[name], list):
                            self.form[name].append(body)
                        else:
                            self.form[name] = [self.form[name], body]
            return

        # Case 4: ?
        self.form = {'body': body}


    #######################################################################
    # Request
    #######################################################################
    def get_header(self, name):
        name = name.lower()
        datatype = get_type(name)
        value = self.soup_message.get_header(name)
        if value is None:
            return datatype.get_default()
        return datatype.decode(value)


    def get_referrer(self):
        return self.soup_message.get_header('referer')


    #######################################################################
    # Response
    #######################################################################
    def set_status(self, status):
        self.soup_message.set_status(status)


    def set_body(self, content_type, body):
        self.soup_message.set_response(content_type, body)


    def set_header(self, name, value):
        name = name.lower()
        datatype = get_type(name)
        value = datatype.encode(value)
        self.soup_message.set_header(name, value)


    def set_response(self, status):
        set_response(self.soup_message, status)


    #######################################################################
    # Cookies
    #######################################################################
    def get_cookie(self, name, datatype=None):
        value = None

        # Read the cookie from the request
        cookies = self.get_header('cookie')
        if cookies:
            cookie = cookies.get(name)
            if cookie:
                value = cookie.value

        if datatype is None:
            return value

        # Deserialize
        if value is None:
            return datatype.get_default()
        value = datatype.decode(value)
        if not datatype.is_valid(value):
            raise ValueError, "Invalid cookie value"
        return value


    def set_cookie(self, name, value, **kw):
        cookie = Cookie(value, **kw)
        cookie = SetCookieDataType.encode({name: cookie})
        self.soup_message.append_header(cookie)


    def del_cookie(self, name):
        expires = 'Wed, 31-Dec-97 23:59:59 GMT'
        self.set_cookie(name, 'deleted', expires=expires, max_age='0')



###########################################################################
# Keep the context globally
###########################################################################
context = None


def set_context(ctx):
    global context
    context = ctx


def get_context():
    return context


def select_language(languages):
    return context.accept_language.select_language(languages)


###########################################################################
# Utility function 'set_response'
###########################################################################
reason_phrases = {
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


def set_response(soup_message, status):
    soup_message.set_status(status)
    body = '{0} {1}'.format(status, reason_phrases[status])
    soup_message.set_response('text/plain', body)


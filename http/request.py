# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006 Nicolas Deram <nicolas@itaapy.com>
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
from urllib import urlencode

# Import from itools
from itools.uri import get_reference, decode_query
from itools.datatypes import QName, String
from itools.handlers import Handler
from cookies import CookieDataType
from entities import Entity, parse_header
from exceptions import BadRequest, NotImplemented
from headers import get_type
from message import Message


class Request(Message):

    def new(self, method='GET', uri='/'):
        version = 'HTTP/1.1'
        self.request_line = '%s %s %s\r\n' % (method, uri, version)
        self.method = method
        self.request_uri = get_reference(uri)
        self.http_version = version
        self.headers = {}
        self.body = {}


    def request_line_to_str(self):
        return '%s %s %s\r\n' % (self.method, self.request_uri,
                                 self.http_version)


    def headers_to_str(self):
        lines = []
        for name in self.headers:
            datatype = get_type(name)
            value = self.headers[name]
            value = datatype.encode(value)
            lines.append('%s: %s\r\n' % (name.title(), value))
        return ''.join(lines)


    def to_str(self):
        data = []
        data.append(self.request_line_to_str())
        data.append(self.headers_to_str())
        # The body (XXX to do)
        return ''.join(data)


    #########################################################################
    # Load
    #########################################################################
    def _load_state_from_file(self, file):
        list(self.non_blocking_load(file))


    def non_blocking_load(self, file):
        """Loads the request state from in non-blocking mode. Aimed at
        sockets, it works for files too.
        """
        # Read the request line
        try:
            line = file.readline()
            while line is None:
                yield None
                line = file.readline()
        except EOFError:
            # FIXME What should we do here?
            msg = 'unable to read the request line, unexpected end-of-file'
            raise BadRequest, msg
        # Parse the request line
        self.request_line = line
        method, request_uri, http_version = line.split()
        self.method = method
        self.request_uri = get_reference(request_uri)
        self.http_version = http_version
        # Check we support the method
        if method not in ['GET', 'HEAD', 'POST', 'PUT', 'LOCK', 'UNLOCK']:
            # Not Implemented (501)
            message = 'request method "%s" not yet implemented'
            raise NotImplemented, message % method

        # Load headers
        headers = self.headers = {}
        while True:
            line = file.readline()
            if line is None:
                yield None
                continue
            # End of headers?
            line = line.strip()
            if not line:
                break
            # Parse the line
            try:
                name, value = parse_header(line)
            except:
                raise BadRequest, 'unexpected header "%s"' % line
            headers[name] = value

        # Cookies
        headers.setdefault('cookie', {})

        # Load the body
        self.body = {}
        # The body
        if 'content-length' in headers and 'content-type' in headers:
            size = headers['content-length']
            try:
                body = file.read(size)
                while body is None:
                    yield None
                    body = file.read(size)
            except EOFError:
                msg = 'unable to read the request content, %s bytes expected'
                raise BadRequest, msg % size

            if body:
                type, type_parameters = self.get_header('content-type')
                if type == 'application/x-www-form-urlencoded':
                    self.body = decode_query(body)
                elif type.startswith('multipart/'):
                    boundary = type_parameters.get('boundary')
                    boundary = '--%s' % boundary
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
                                if not entity.has_header('content-type'):
                                    mimetype = 'text/plain'
                                else:
                                    mimetype = entity.get_header('content-type')[0]
                                self.body[name] = filename, mimetype, body
                        else:
                            if name not in self.body:
                                self.body[name] = body
                            else:
                                if isinstance(self.body[name], list):
                                    self.body[name].append(body)
                                else:
                                    self.body[name] = [self.body[name], body]
                else:
                    self.body['body'] = body


    ########################################################################
    # API
    ########################################################################
    def get_referrer(self):
        return self.headers.get('referer', None)

    referrer = property(get_referrer, None, None, '')


    ########################################################################
    # The Form
    def get_form(self):
        if self.method in ('GET', 'HEAD'):
            return self.request_uri.query
        # XXX What parameters with the fields defined in the query?
        return self.body


    def get_parameter(self, name, default=None, type=None):
        # Default type is String
        if type is None:
            type = String

        # Return the value
        form = self.get_form()
        if name in form:
            return type.decode(form[name])

        # Default
        if default is None:
            return type.default
        return default


    def has_parameter(self, name):
        return name in self.get_form()


    ########################################################################
    # The Cookies
    def set_cookie(self, name, value):
        self.headers['cookie'][name] = value


    def get_cookie(self, name):
        cookies = self.get_header('cookie')
        return cookies.get(name)


    def get_cookies_as_str(self):
        cookies = self.get_header('cookie')
        return CookieDataType.encode(cookies)


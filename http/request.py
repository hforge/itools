# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from urllib import urlencode

# Import from itools
from itools.uri import get_reference
from itools import uri
from itools.datatypes import QName
from itools import schemas
from itools.resources import memory
from itools.handlers.Handler import Handler
from itools.i18n.accept import AcceptLanguage
from exceptions import BadRequest, NotImplemented
import headers
import entities
from message import Message


class Request(Message):

    request_line = None
    headers = None
    body = None


    def new(self, method='GET', uri='/'):
        version = 'HTTP/1.1'
        self.request_line = '%s %s %s\r\n' % (method, uri, version)
        self.method = method
        self.uri = uri.get_reference(request_uri)
        self.http_version = version
        self.headers = {}
        self.body = {}


    def request_line_to_str(self):
        return '%s %s %s\r\n' % (self.method, self.uri, self.http_version)


    def headers_to_str(self):
        lines = []
        for name in self.headers:
            datatype = headers.get_type(name)
            value = self.headers[name]
            value = datatype.encode(value)
            lines.append('%s: %s\r\n' % (name.title(), value))
        return ''.join(lines)


    def to_str(self):
        data = []
        data.append(self.request_line_tostr())
        data.append(self.headers_to_str())
        # The body (XXX to do)
        return ''.join(data)


    def _load_state(self, resource):
        list(self.non_blocking_load(resource.read))


    def non_blocking_load(self, read):
        buffer = ''
        # Read the first line
        while True:
            data = read(512)
            data_size = len(data)
            # Check there is some data, if not we abort the request, something
            # may be wrong.
            if data_size == 0:
                raise BadRequest
            buffer += data
            buffer = buffer.split('\r\n', 1)
            if len(buffer) == 2:
                request_line, buffer = buffer
                break

            buffer = buffer[0]
            # Give control back
            if data_size < 512:
                yield None

        # Parse the request line
        self.request_line = request_line
        method, request_uri, http_version = request_line.split()
        self.method = method
        self.uri = get_reference(request_uri)
        self.http_version = http_version
        # Check we support the method
        if method not in ['GET', 'HEAD', 'POST', 'PUT', 'LOCK', 'UNLOCK']:
            # Not Implemented (501)
            message = u'request method "%s" not yet implemented'
            raise NotImplemented, message % method

        # Load headers
        headers = self.headers = {}
        while True:
            if buffer:
                buffer = buffer.split('\r\n', 1)
                if len(buffer) == 2:
                    line, buffer = buffer
                    if not line:
                        break
                    name, value = entities.parse_header(line)
                    headers[name] = value
                    continue

                buffer = buffer[0]
            if len(data) < 512:
                yield None
            data = read(512)
            buffer += data

        # Cookies
        self.headers.setdefault('cookie', {})

        # Load the body
        self.form = {}
        parameters = {}
        # The body
        if 'content-length' in headers and 'content-type' in headers:
            size = headers['content-length']
            # Read
            remains = size - len(buffer)
            buffer = [buffer]
            while remains > 0:
                data = read(remains)
                buffer.append(data)
                remains = remains - len(data)
                if remains:
                    yield None
            body = ''.join(buffer)

            # The Form
            if body:
                type, type_parameters = self.get_header('content-type')
                if type == 'application/x-www-form-urlencoded':
                    parameters = uri.generic.Query.decode(body)
                elif type.startswith('multipart/'):
                    boundary = type_parameters.get('boundary')
                    boundary = '--%s' % boundary
                    for part in body.split(boundary)[1:-1]:
                        if part.startswith('\r\n'):
                            part = part[2:]
                        elif part.startswith('\n'):
                            part = part[1:]
                        # Parse the entity
                        resource = memory.File(part)
                        entity = entities.Entity(resource)
                        # Find out the parameter name
                        header = entity.get_header('Content-Disposition')
                        value, header_parameters = header
                        name = header_parameters['name']
                        # Load the value
                        body = entity.get_body()
                        if body.endswith('\r\n'):
                            body = body[:-2]
                        elif body.endswith('\n'):
                            body = body[:-1]
                        if 'filename' in header_parameters:
                            filename = header_parameters['filename']
                            if filename:
                                # Strip the path (for IE). XXX Test this.
                                filename = filename.split('\\')[-1]
                                resource = memory.File(body, name=filename)
                                parameters[name] = resource
                        else:
                            parameters[name] = body
                else:
                    resource = memory.File(body)
                    parameters['body'] = resource
        else:
            parameters = self.uri.query

        for name in parameters:
            self._set_parameter(name, parameters[name])


    ########################################################################
    # API
    ########################################################################
    def get_referrer(self):
        return self.headers.get('referer', None)

    referrer = property(get_referrer, None, None, '')


    def get_accept_language(self):
        headers = self.headers
        if 'accept-language' in headers:
            return headers['accept-language']
        return AcceptLanguage('')

    accept_language = property(get_accept_language, None, None, '')


    ########################################################################
    # The Form
    def _set_parameter(self, name, value):
        prefix, local_name = QName.decode(name)
        if prefix is not None:
            datatype = schemas.get_datatype(name)
            value = datatype.decode(value)

        self.form[name] = value


    def get_parameter(self, name, default=None):
        form = self.form
        if name in form:
            return form[name]

        if default is None:
            datatype = schemas.get_datatype(name)
            return datatype.default

        return default


    def has_parameter(self, name):
        return name in self.form


    # XXX Remove? Use "get_parameter" instead?
    def get_form(self):
        return self.form

    form = property(get_form, None, None, '')


    ########################################################################
    # The Cookies
    def set_cookie(self, name, value):
        self.headers['cookie'][name] = value


    def get_cookie(self, name):
        cookies = self.get_header('cookie')
        return cookies.get(name)


    def get_cookies_as_str(self):
        cookies = self.get_header('cookie')
        return '; '.join([ '%s="%s"' % (x, cookies[x]) for x in cookies ])

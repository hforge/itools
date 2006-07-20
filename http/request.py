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
from itools.uri import get_reference, Query
from itools.datatypes import QName
from itools import schemas
##from itools.resources import memory
from itools.handlers.base import Handler
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
        self.uri = get_reference(uri)
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


    #########################################################################
    # Load
    #########################################################################
    def _load_state_from_file(self, file):
        list(self.non_blocking_load(file))


    def non_blocking_load(self, file):
        """
        Loads the request state from in non-blocking mode. Aimed at sockets,
        it works for files too.
        """
        # Read the request line
        line = file.readline()
        while line is None:
            yield None
            line = file.readline()
        # Parse the request line
        self.request_line = line
        method, request_uri, http_version = line.split()
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
            line = file.readline()
            if line is None:
                yield None
                continue
            # End of headers?
            if not line:
                break
            # Parse the line
            name, value = entities.parse_header(line)
            headers[name] = value

        # Cookies
        self.headers.setdefault('cookie', {})

        # Load the body
        self.body = {}
        # The body
        if 'content-length' in headers and 'content-type' in headers:
            size = headers['content-length']
            body = file.read(size)
            while body is None:
                yield None
                body = file.read(size)

            if body:
                type, type_parameters = self.get_header('content-type')
                if type == 'application/x-www-form-urlencoded':
                    self.body = Query.decode(body)
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
                                self.body[name] = resource
                        else:
                            self.body[name] = body
                else:
                    resource = memory.File(body)
                    self.body['body'] = resource


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
        if self.method in ('GET', 'HEAD'):
                return self.uri.query
        # XXX What parameters with the fields defined in the query?
        return self.body

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

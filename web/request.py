# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
from urllib import urlencode

# Import from itools
from itools import uri
from itools.datatypes import QName
from itools import schemas
from itools.resources import memory
from itools.handlers.Handler import Handler
from itools.i18n.accept import AcceptLanguage
from itools.web.exceptions import BadRequest
from itools.web import headers
from itools.web import entities
from itools.web.message import Message


class Request(Message):

    def get_skeleton(self, path='/'):
        return 'GET %s HTTP/1.1' % path


    def _load_state(self, resource):
        state = self.state
        state.form = {}

        # The request line
        line = resource.readline()
        line = line.strip()
        try:
            method, request_uri, http_version = line.split()
        except ValueError:
            raise BadRequest, line
        else:
            state.request_line = line

        self.set_method(method)
        reference = uri.get_reference(request_uri)
        self.set_uri(reference)
        state.http_version = http_version

        # The headers
        state.headers = entities.read_headers(resource)

        # The body
        if self.has_header('content-length'):
            size = self.get_header('content-length')
            body = resource.read(size)
        else:
            body = ''

        # Cookies
        state.headers.setdefault('cookie', {})

        # The Form
        if method in ('GET', 'HEAD'):
            parameters = reference.query
        elif method in ('POST', 'PUT', 'LOCK', 'UNLOCK'):
            parameters = {}
            if self.has_header('content-type'):
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
            message = u'request method "%s" not yet implemented' % method
            raise ValueError, message

        for name in parameters:
            self._set_parameter(name, parameters[name])


    def to_str(self):
        state = self.state

        data = []
        # Request line
        data.append('%s %s %s\n' % (state.method, state.uri,
                                    state.http_version))
        # Headers
        for name in state.headers:
            datatype = headers.get_type(name)
            value = state.headers[name]
            value = datatype.encode(value)
            data.append('%s: %s\n' % (name.title(), value))
        return ''.join(data)


    ########################################################################
    # The Method
    def get_method(self):
        return self.state.method


    def set_method(self, method):
        self.state.method = method


    method = property(get_method, set_method, None, '')


    ########################################################################
    # The Request URI
    def get_uri(self):
        return self.state.uri


    def set_uri(self, reference):
        if not isinstance(reference, uri.Reference):
            reference = uri.get_reference(reference)
        self.state.uri = reference


    uri = property(get_uri, set_uri, None, '')


    ########################################################################
    # API
    ########################################################################
    def get_content_type(self):
        return self.state.headers.get('content-type', None)

    content_type = property(get_content_type, None, None, '')


    def get_referrer(self):
        return self.state.headers.get('referer', None)

    referrer = property(get_referrer, None, None, '')


    def get_accept_language(self):
        headers = self.state.headers
        if 'accept-language' in headers:
            return headers['accept-language']
        return AcceptLanguage('')

    accept_language = property(get_accept_language, None, None, '')


    ########################################################################
    # The Form
    def _set_parameter(self, name, value):
        prefix, local_name = QName.decode(name)
        if prefix is not None:
            # XXX Horrible exception, kept here for backwards compatibility
            # with Zope, until we get the right solution.
            if local_name == 'list':
                name = prefix
                if not isinstance(value, list):
                    value = [value]
            else:
                datatype = schemas.get_datatype(name)
                value = datatype.decode(value)

        self.state.form[name] = value


    def get_parameter(self, name):
        form = self.state.form
        if name in form:
            return form[name]
        datatype = schemas.get_datatype(name)
        return datatype.default


    def has_parameter(self, name):
        return name in self.state.form


    # XXX Remove? Use "get_parameter" instead?
    def get_form(self):
        return self.state.form

    form = property(get_form, None, None, '')


    ########################################################################
    # The Cookies
    def set_cookie(self, name, value):
        self.state.headers['cookie'][name] = value


    def get_cookie(self, name):
        cookies = self.get_header('cookie')
        return cookies.get(name)


    def get_cookies_as_str(self):
        cookies = self.get_header('cookie')
        return '; '.join([ '%s="%s"' % (x, cookies[x]) for x in cookies ])


    ########################################################################
    # High level API
    ########################################################################

    # XXX Move to itools.uri ?
    def build_url(self, url=None, preserve=[], **kw):
        """
        Builds and returns a new url from the one we are now. Preserves only
        the query parameters that start with any of the specified prefixes in
        the 'preserve' argument. The keywords argument is used to add or
        modify query parameters.
        """
        if url is None:
            url = self.uri.path[-1]

        query = []
        # Preserve request parameters that start with any of the prefixes.
        for key, value in self.form.items():
            for prefix in preserve:
                if key.startswith(prefix):
                    query.append((key, value))
                    break

        # Modify the parameters
        for key in kw:
            for i, x in enumerate(query):
                if x is not None and x[0] == key:
                    query[i] = None
        query = [ x for x in query if x is not None ]
        for key, value in kw.items():
            query.append((key, value))

        # Keep the type (XXX use itools schemas)
        new_query = []
        for key, value in query:
            if isinstance(value, str):
                new_query.append((key, value))
            elif isinstance(value, unicode):
                value = value.encode('utf8')
                new_query.append(('%s' % key, value))
            elif isinstance(value, int):
                new_query.append(('%s' % key, str(value)))
            elif isinstance(value, list):
                for x in value:
                    # XXX Should coerce too
                    new_query.append(('%s:list' % key, x))
            else:
                # XXX More types needed!!
                new_query.append((key, str(value)))

        # Re-build the query string
        query_string = urlencode(new_query)

        # Build the new url
        if query_string:
            url = '%s?%s' % (url, query_string)

        return url

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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from itools
from itools import uri
from itools.schemas import get_datatype
from itools.resources import memory
from itools.i18n.accept import AcceptCharset, AcceptLanguage
from itools.web.context import Context, set_context
from itools.web.request import Request
from itools.web.entities import Entity


def init(zope_request):
    environ = zope_request.environ

    # Build the request
    request = Request()

    # The request method
    request_method = environ['REQUEST_METHOD']
    request.set_method(request_method)

    # The query
    query = zope_request.environ.get('QUERY_STRING', '')
    query = uri.generic.Query(query)

    # The path
    path = zope_request.environ['PATH_INFO']
    request.set_path(path)

    # The header
    for name, key in [('Referer', 'HTTP_REFERER'),
                      ('Content-Type', 'CONTENT_TYPE'),
                      ('Host', 'HTTP_X_FORWARDED_HOST'),
                      ('Host', 'HTTP_HOST'),
                      ('Accept-Language', 'HTTP_ACCEPT_LANGUAGE')]:
        if environ.has_key(key):
            value = environ[key]
            request.set_header(name, value)

    # The form
    if request_method in ('GET', 'HEAD'):
        parameters = query
    elif request_method in ('POST', 'PUT', 'LOCK', 'UNLOCK'):
        # Read the standard input
        body = zope_request.stdin.read()
        # Recover the standard input, so Zope can read it again
        zope_request.stdin.seek(0)
        # Load the parameters
        if request.content_type is not None:
            type, type_parameters = request.content_type
        else:
            type = ''
        if type == 'application/x-www-form-urlencoded':
            parameters = uri.generic.Query(body)
        elif type.startswith('multipart/'):
            boundary = type_parameters.get('boundary')
            boundary = '--%s' % boundary
            parameters = {}
            for part in body.split(boundary)[1:-1]:
                if part.startswith('\r\n'):
                    part = part[2:]
                elif part.startswith('\n'):
                    part = part[1:]
                # Parse the entity
                resource = memory.File(part)
                entity = Entity(resource)
                # Find out the parameter name
                header = entity.get_header('Content-Disposition')
                value, header_parameters = header
                name = header_parameters['name']
                # Load the value
                body = entity.get_body()
                if body.endswith('\r\n'):
                    body = body[:-2]
                elif body.endswih('\n'):
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
            parameters = {'BODY': body}
    else:
        message = 'request method "%s" not yet implemented' % request_method
        raise ValueError, message

    for name in parameters:
        value = parameters[name]
        request._set_parameter(name, value)

    # The cookies
    for name in zope_request.cookies:
        value = zope_request.cookies[name]
        datatype = get_datatype(name)
        value = datatype.decode(value)
        request.set_cookie(name, value)

    # Build the context
    context = Context(request)
    set_context(context)

    # The authority
    if 'HTTP_X_FORWARDED_HOST' in environ:
        authority = environ['HTTP_X_FORWARDED_HOST']
    else:
        authority = zope_request['HTTP_HOST']

    # The URI
    if 'REAL_PATH' in query:
        path = query.pop('REAL_PATH')
    request_uri = 'http://%s/%s?%s' % (authority, path, query)
    context.uri = uri.get_reference(request_uri)

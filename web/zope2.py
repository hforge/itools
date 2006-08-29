# -*- coding: UTF-8 -*-
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

    # The request method
    request_method = environ['REQUEST_METHOD']
    # The request uri
    request_uri = zope_request.environ['PATH_INFO']
    query = zope_request.environ.get('QUERY_STRING', '')
    if query:
        request_uri = '%s?%s' % (request_uri, query)
    # The request hqndler
    request = Request(method=request_method, uri=request_uri)

    # The query
    query = uri.generic.Query(query)

    # The header
    # XXX Check header X-Base-Path
    for name, key in [('Referer', 'HTTP_REFERER'),
                      ('Content-Type', 'CONTENT_TYPE'),
                      ('Host', 'HTTP_X_FORWARDED_HOST'),
                      ('Host', 'HTTP_HOST'),
                      ('Accept-Language', 'HTTP_ACCEPT_LANGUAGE'),
                      ('Lock-Token', 'HTTP_LOCK_TOKEN'),
                      ('X-Forwarded-Host', 'HTTP_X_FORWARDED_HOST')]:
        if environ.has_key(key):
            value = environ[key]
            request.set_header(name, value)

    # The form
    if request_method in ('GET', 'HEAD'):
        pass
    elif request_method in ('POST', 'PUT', 'LOCK', 'UNLOCK'):
        # Read the standard input
        body = zope_request.stdin.read()
        # Recover the standard input, so Zope can read it again
        zope_request.stdin.seek(0)
        # Load the parameters
        if request.has_header('content-type'):
            type, type_parameters = request.get_header('content-type')
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

        for name in parameters:
            value = parameters[name]
            request._set_parameter(name, value)
    else:
        message = 'request method "%s" not yet implemented' % request_method
        raise ValueError, message

    # The cookies
    for name in zope_request.cookies:
        value = zope_request.cookies[name]
        datatype = get_datatype(name)
        value = datatype.decode(value)
        request.set_cookie(name, value)

    # Build the context
    context = Context(request)
    set_context(context)

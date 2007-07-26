# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


class HTTPError(Exception):
    """Base class for all errors, client or server side."""


class ClientError(HTTPError):
    """Base class for 4xx responses."""


class BadRequest(ClientError):
    code = 400
    title = 'Bad Request'


class Unauthorized(ClientError):
    code = 401
    title = 'Unauthorized'


class Forbidden(ClientError):
    code = 403
    title = 'Forbidden'


class NotFound(ClientError):
    code = 404
    title = 'NotFound'



class ServerError(HTTPError):
    """Base class for 5xx responses."""


class InternalServerError(ServerError):
    code = 500
    title = 'Internal Server Error'


class NotImplemented(ServerError):
    code = 501
    title = 'Not Implemented'


class BadGateway(ServerError):
    code = 502
    title = 'Bad Gateway'


class ServiceUnavailable(ServerError):
    code = 503
    title = 'Service Unavailable'


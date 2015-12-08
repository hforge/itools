# -*- coding: UTF-8 -*-
# Copyright (C) 2009-2012 J. David Ibáñez <jdavid.ibp@gmail.com>
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
from itools.core import is_prototype, freeze
from itools.gettext import MSG
from messages import ERROR



class HTTPError(StandardError):
    """Base class for all errors, client or server side.
    """


class NotModified(HTTPError):
    code = 304
    title = 'Not Modified'


class ClientError(HTTPError):
    """Base class for 4xx responses.
    """


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
    title = 'Not Found'


class MethodNotAllowed(ClientError):
    code = 405
    title = 'Method Not Allowed'


class Conflict(ClientError):
    code = 409
    title = 'Conflict'


class ServerError(HTTPError):
    """Base class for 5xx responses.
    """


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


class FormError(StandardError):
    """Raised when a form is invalid (missing or invalid fields).
    """

    def __init__(self, message=None, missing=False, invalid=False,
            missings=freeze([]), invalids=freeze([])):
        self.msg = message
        self.missing = missing
        self.invalid = invalid
        self.missings = missings
        self.invalids = invalids


    def get_message(self):
        # Custom message
        value = self.msg
        if value is not None:
            if is_prototype(value, MSG):
                return value
            return ERROR(value)
        # Default message
        msg = u'There are errors... XXX'
        return ERROR(msg)


    def __str__(self):
        return self.get_message().gettext()

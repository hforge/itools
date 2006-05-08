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


class Successful(Exception):
    """Base class for 2xx responses."""


class OK(Successful):
    code = 200


class Created(Successful):
    code = 201


class Accepted(Successful):
    code = 202


class NoContent(Successful):
    code = 204



class Redirection(Exception):
    """Base class for 3xx responses."""


class MultipleChoices(Redirection):
    code = 300


class MovedPermanently(Redirection):
    code = 301


class MovedTemporarily(Redirection):
    code = 302


class NotModified(Redirection):
    code = 304



class ClientError(Exception):
    """Base class for 4xx responses."""


class BadRequest(ClientError):
    code = 400


class Unauthorized(ClientError):
    code = 401


class Forbidden(ClientError):
    code = 403


class NotFound(ClientError):
    code = 404



class ServerError(Exception):
    """Base class for 5xx responses."""


class InternalServerError(ServerError):
    code = 500


class NotImplemented(ServerError):
    code = 501


class BadGateway(ServerError):
    code = 502


class ServiceUnavailable(ServerError):
    code = 503


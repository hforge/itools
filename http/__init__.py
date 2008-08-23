# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from exceptions import HTTPError, ClientError, ServerError
from exceptions import NotModified
from exceptions import BadRequest, Unauthorized, Forbidden, NotFound
from exceptions import (InternalServerError, NotImplemented, BadGateway,
                        ServiceUnavailable)
from request import Request
from response import Response
import vfs


__all__ = [
    # Exceptions
    'HTTPError',
    'NotModified',
    'ClientError',
    'BadRequest',
    'Unauthorized',
    'Forbidden',
    'NotFound',
    'ServerError',
    'InternalServerError',
    'NotImplemented',
    'BadGateway',
    'ServiceUnavailable',
    # Classes
    'Request',
    'Response']

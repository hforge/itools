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
from itools.core import freeze
from itools.gettext import MSG
from messages import ERROR



class HTTPError(StandardError):
    """Base class for all errors, client or server side.
    """

    def to_dict(self):
        return {'code': self.code, 'title': self.title}


    def __str__(self):
        return '[{}] {}'.format(self.code, self.title)



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


class TokenAuthorizationException(Unauthorized):

    code = 401
    message = None
    error = "token_error"

    def to_dict(self):
        return {
            "error": self.error,
            "message": self.message,
            "code": self.code
        }


class InvalidJWTSignatureException(TokenAuthorizationException):

    message = MSG(u"Signature du jeton invalide")
    error = "invalid_token_signature"


class JWTExpiredException(TokenAuthorizationException):

    message = MSG(u"Jeton expiré")
    error = "token_expired"



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
            missings=freeze([]), invalids=freeze([]),
            messages=freeze([]), values=freeze([]), code=400, **kw):
        self.msg = message
        self.missing = missing
        self.invalid = invalid
        self.missings = missings
        self.invalids = invalids
        self.messages = messages
        self.code = code
        self.values = values
        self.kw = kw


    def get_messages(self):
        # Custom message
        final_messages = []
        messages = []
        if self.messages:
            messages = self.messages
        elif self.msg:
            messages = [self.msg]
        else:
            messages = MSG(u'There are errors... XXX')
        for value in messages:
            if isinstance(value, MSG):
                value = value.gettext()
            final_messages.append(value)
        return final_messages


    def get_message(self, mode='html'):
        messages = self.get_messages()
        if mode == 'html':
            msg = '<br/>'.join(messages)
            return ERROR(msg, format='html')
        return ERROR('\n'.join(messages))


    def __str__(self):
        msg = self.get_message(mode='text')
        if isinstance(msg, MSG):
            return msg.gettext()
        return msg


    def to_dict(self):
        namespace = {
            'msg': self.msg,
            'messages': self.messages,
            'missing': self.missing,
            'invalid': self.invalid,
            'missings': self.missings,
            'invalids': self.invalids,
        }
        namespace.update(self.kw)
        return namespace

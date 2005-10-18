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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA

# Import from the Standard Library
import datetime
from thread import get_ident, allocate_lock

# Import from itools
from response import Response


class Context(object):

    def __init__(self, request):
        self.request = request
        self.response = Response()

        # The user, by default it is not authenticated
        self.user = None

        # Split the path into path and method ("a/b/c/;view")
        path = request.path
        self.path = path
        self.method = None
        if path and not path[-1].name:
            self.path = path[:-1]
            self.method = path[-1].param


    ########################################################################
    # API
    ########################################################################
    def redirect(self, reference, status=302):
        reference = self.uri.resolve2(reference)
        self.response.redirect(reference, status)


    ########################################################################
    # API / cookies (client side sessions)
    def get_cookie(self, name):
        request, response = self.request, self.response

        cookie = response.get_cookie(name)
        if cookie is None:
            return request.get_cookie(name)

        # Check expiration time
        expires = cookie.expires
        if expires is not None:
            expires = expires[5:-4]
            expires = strptime(expires, '%d-%b-%y %H:%M:%S')
            year, month, day, hour, minute, second, wday, yday, isdst = expires
            expires = datetime.datetime(year, month, day, hour, minute, second)

            if expires < datetime.datetime.now():
                return None

        return cookie.value


    def has_cookie(self, name):
        return self.get_cookie(name) is not None


    def set_cookie(self, name, value, **kw):
        self.response.set_cookie(name, value, **kw)


    def del_cookie(self, name):
        self.response.del_cookie(name)



contexts = {}
contexts_lock = allocate_lock()


def set_context(context):
    ident = get_ident()

    contexts_lock.acquire()
    try:
        contexts[ident] = context
    finally:
        contexts_lock.release()


def has_context():
    return get_ident() in contexts


def get_context():
    return contexts.get(get_ident())


def del_context():
    ident = get_ident()

    contexts_lock.acquire()
    try:
        del contexts[ident]
    finally:
        contexts_lock.release()

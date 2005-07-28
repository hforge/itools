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


# Server-side sessions
sessions = {}



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
    # Sessions
    def get_session(self):
        # Get session key
        cookies = self.request.cookies
        if cookies.has_key('iSession'):
            key = cookies['iSession']
        else:
            key = datetime.datetime.now().isoformat()
            # XXX Fix path
##            path = request.path.split('/')
##            path = '/'.join(path[:len(request.context)]) or '/'
            path = '/'
            self.response.set_cookie('iSession', key, path=path)

        # Get session
        global sessions
        return sessions.setdefault(key, {})

    session = property(get_session, None, None, "")



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

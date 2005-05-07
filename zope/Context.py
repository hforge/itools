# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from itools
from Request import Request
from Response import Response


# User sessions
sessions = {}


class Context(object):
    """
    The Zope context contains the request, the response, the path to be
    traversed, the authenticated user, the user session, etc.
    """

    def __init__(self, zope_request):
        # The request
        self.request = Request(zope_request)
        # The response
        self.response = Response(zope_request.RESPONSE)
        # The path to be traversed
        self.path = None
        # The authenticated user
        self.user = None


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

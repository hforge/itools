# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


# Import from itools
from itools.zope import get_context


class Response(object):
    """ """

    def __init__(self, zope_response):
        self.zope_response = zope_response


    ########################################################################
    # The body
    def get_body(self):
        """ """
        # Prevent Zope to fuck the base
        self.set_base(None)
        # Return the body
        return self.zope_response.body

    def set_body(self, body):
        self.zope_response.setBody(body)

    body = property(get_body, set_body, None, '')


    ########################################################################
    # Headers
    def has_header(self, name):
        return name in self.zope_response.headers


    def get_header(self, name):
        return self.zope_response.headers[name]


    def set_header(self, name, value):
        self.zope_response.setHeader(name, value)


    ########################################################################
    # Cookies
    def set_cookie(self, name, value, **kw):
        self.zope_response.setCookie(name, value, **kw)


    def del_cookie(self, name):
        # XXX Add the path parameter for some browsers??
        self.zope_response.expireCookie(name)


    ########################################################################
    # 
    def redirect(self, uri):
        self.zope_response.redirect(uri)


    def set_base(self, base):
        self.zope_response.setBase(base)


    def set_status(self, status):
        self.zope_response.setStatus(status)

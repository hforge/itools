# Copyright (C) 2002-2003 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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



# Import from Python
from base64 import decodestring, encodestring
from urllib import quote, unquote

# Import from itools.zope
from __init__ import get_context

# Import from Zope
from Acquisition import aq_base
from AccessControl.PermissionRole import _what_not_even_god_should_do
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SpecialUsers import nobody
from AccessControl.User import BasicUser, BasicUserFolder
from AccessControl.ZopeSecurityPolicy import _noroles



# Cookie name
cname = '__ac'


class User(BasicUser):
    """
    Base class for users.
    """

    def getUserName(self):
        """ """
        raise NotImplementedError


    def _getPassword(self):
        """ """
        raise NotImplementedError


    def getRoles(self):
        """ """
        raise NotImplementedError


    def getDomains(self):
        """ """
        raise NotImplementedError



class UserFolder(BasicUserFolder):
    """
    Provides an 'acl_users' object
    """

    meta_type = 'ikaaro User Folder'

    id = 'acl_users'
    title = ''


    def getUserNames(self):
        """
        Return the list of usernames available.
        """
        return self.aq_parent.get_usernames()


    def getUsers(self):
        """
        Returns the users
        """
        return [ self.getUser(x) for x in self.getUserNames() ]


    def getUser(self, name):
        return self.aq_parent.get_user(name)


    def identify(self, auth=None):
        """ """
        context = get_context()
        request, response = context.request, context.response

        # Sets the unauthorized response
        def unauthorized(request=request, response=response):
            # XXX This redirection only works with an (Apache) rewrite rule
            response.redirect('http://%s/loginForm?referer=%s'
                              % (request.uri.authority, quote(request.uri)))

        response.unauthorized = unauthorized

        username = request.form.get('__ac_name', None)
        password = request.form.get('__ac_password', None)
        if username is not None and password is not None:
            # Do authentication too, needed by ikaaro
            user = self.aq_parent.get_user(username)
            if user is not None and user.authenticate(password):
                cookie = encodestring('%s:%s' % (username, password))
                cookie = quote(cookie)
                expires = request.get('iAuthExpires', None)
                if expires is None:
                    response.set_cookie(cname, cookie)
                else:
                    response.set_cookie(cname, cookie, expires=expires)
                return username, password

            return None, None

        # Cookie auth
        cookie = request.cookies.get(cname, None)
        if cookie is not None:
            cookie = unquote(cookie)
            cookie = decodestring(cookie)
            name, password = cookie.split(':', 1)
            return name, password

        # Basic auth
        if auth and auth.startswith('Basic '):
            try:
                auth = auth.split()[-1]
                auth = decodestring(auth)
                name, password = auth.split(':', 1)
            except:
                raise 'Bad Request', 'Invalid authentication token'

            return name, password

        return None, None



class Auth:
    """
    Mixin class that lets to implement the authentication in the subclasses
    just implementing the methods getUserNames and getUser.
    """

    __allow_groups__ = acl_users = UserFolder()


    def get_usernames(self):
        raise NotImplementedError


    def get_user(self, name):
        raise NotImplementedError


    def logout(self):
        """ """
        # Remove the cookie
        response = get_context().response
        response.del_cookie(cname)

        # Remove the security context
        newSecurityManager(None, nobody)

##        path = self.absolute_url(1)
##        if not path.startswith('/'):
##            path = '/' + path
##        if not path.endswith('/'):
##            path = path + '/'
##        response.expireCookie(cname, path=path)



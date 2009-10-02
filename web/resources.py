# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
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
from itools.uri import Path
from access import AccessControl
from context import get_context
from views import BaseView


class Resource(object):
    """This is the base class for all web resources.
    """

    __hash__ = None

    #######################################################################
    # API / Private
    #######################################################################
    def _get_names(self):
        raise NotImplementedError


    def _get_resource(self, name):
        return None


    #######################################################################
    # API / Tree
    #######################################################################
    def get_abspath(self):
        if self.parent is None:
            return Path('/')
        parent_path = self.parent.get_abspath()

        return parent_path.resolve_name(self.name)


    def get_canonical_path(self):
        context = get_context()
        if context.host is None:
            return self.path
        return '/%s%s' % (context.host, self.path)


    def get_real_resource(self):
        cpath = self.get_canonical_path()
        if cpath == self.get_abspath():
            return self
        return self.get_resource(cpath)


    def get_root(self):
        if self.parent is None:
            return self
        return self.parent.get_root()


    def get_pathto(self, handler):
        return self.get_abspath().get_pathto(handler.get_abspath())


    def get_names(self, path='.'):
        resource = self.get_resource(path)
        return resource._get_names()


    def get_resource(self, path, soft=False):
        path = self.path.resolve2(path)
        return self.context.get_resource(path, soft=soft)


    def get_resources(self, path='.'):
        here = self.get_resource(path)
        for name in here._get_names():
            yield here.get_resource(name)


    def set_resource(self, path, resource):
        raise NotImplementedError


    def del_resource(self, path, soft=False):
        raise NotImplementedError


    def copy_resource(self, source, target):
        raise NotImplementedError


    def move_resource(self, source, target):
        raise NotImplementedError


    def traverse_resources(self):
        raise NotImplementedError


    def __eq__(self, resource):
        if not isinstance(resource, Resource):
            raise TypeError, "cannot compare Resource and %s" % type(resource)
        return self.get_canonical_path() == resource.get_canonical_path()


    def __ne__(self, node):
        return not self.__eq__(node)


    #######################################################################
    # API / Views
    #######################################################################
    default_view_name = None


    def get_default_view_name(self):
        return self.default_view_name


    def get_view(self, name, query=None):
        # To define a default view, override this
        if name is None:
            name = self.get_default_view_name()
            if name is None:
                return None

        # Explicit view, defined by name
        view = getattr(self, name, None)
        if view is None or not isinstance(view, BaseView):
            return None

        return view

    #######################################################################
    # API / Security
    #######################################################################
    def get_access_control(self):
        resource = self
        while resource is not None:
            if isinstance(resource, AccessControl):
                return resource
            resource = resource.get_parent()

        return None



class VirtualRoot(AccessControl, Resource):
    """Also known as site-root, or virtual-host.
    """

    # FIXME Implement a default behaviour for these views.
    http_main = None # Main view, called when everything is ok
    http_unauthorized = None # 401 Unauthorized
    http_forbidden = None # 403 Forbidden
    http_not_found = None # 404 Not Found
    http_method_not_allowed = None # 405 Method Not Allowed
    http_conflict = None # 409 Conflict
    http_internal_server_error = None # 500 Internal Server Error



class Root(VirtualRoot):
    """This represents the absolute or physical root of the resources tree.
    There is one and only one instance of this in any application.
    """

    def get_user(self, username):
        """Return a resource representing the user named after the username,
        or 'None'.  The nature of the resource, the location of the storage
        and the retrieval of the data remain at your discretion. The only
        requirements are the "name" attribute, and the "authenticate" method
        with a "password" parameter.
        """
        return None


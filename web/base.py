# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


class Node(object):
    """A Node is a base object supporting the HTTP protocol and the access
    control API.
    """

    #######################################################################
    # API / Private
    #######################################################################
    def _has_object(self, name):
        """Default implementation, may be overriden for a better performance.
        """
        try:
            self._get_object(name)
        except LookupError:
            return False
        return True


    def _get_names(self):
        raise NotImplementedError


    def _get_object(self, name):
        raise LookupError


    #######################################################################
    # API / Tree
    #######################################################################
    def get_abspath(self):
        if self.parent is None:
            return Path('/')
        parent_path = self.parent.get_abspath()

        return parent_path.resolve2(self.name)

    abspath = property(get_abspath, None, None, '')


    def get_canonical_path(self):
        if self.parent is None:
            return Path('/')
        parent_path = self.parent.get_canonical_path()

        return parent_path.resolve2(self.name)


    def get_real_object(self):
        cpath = self.get_canonical_path()
        if cpath == self.get_abspath():
            return self
        return self.get_object(cpath)


    def get_root(self):
        if self.parent is None:
            return self
        return self.parent.get_root()


    def get_pathto(self, handler):
        return self.get_abspath().get_pathto(handler.get_abspath())


    def has_object(self, path):
        if not isinstance(path, Path):
            path = Path(path)

        # If path is "/" or "."
        if len(path) == 0:
            return True

        path, name = path[:-1], path[-1]
        try:
            container = self.get_object(path)
        except LookupError:
            return False

        return container._has_object(name)


    def get_names(self, path='.'):
        object = self.get_object(path)
        return object._get_names()


    def get_object(self, path):
        if not isinstance(path, Path):
            path = Path(path)

        if path.is_absolute():
            here = self.get_root()
        else:
            here = self

        while path and path[0] == '..':
            here = here.parent
            path = path[1:]

        for name in path:
            object = here._get_object(name)
            object.parent = here
            object.name = name
            here = object

        return here


    def get_objects(self, path='.'):
        here = self.get_object(path)
        for name in here._get_names():
            object = here._get_object(name)
            object.parent = here
            object.name = name
            yield object


    def set_object(self, path, object):
        raise NotImplementedError


    def del_object(self, path):
        raise NotImplementedError


    def copy_object(self, source, target):
        raise NotImplementedError


    def move_object(self, source, target):
        raise NotImplementedError


    def traverse_objects(self):
        raise NotImplementedError


    def __eq__(self, node):
        if not isinstance(node, Node):
            raise TypeError, "cannot compare Node and %s" % type(node)
        return self.get_canonical_path() == node.get_canonical_path()


    #######################################################################
    # API / HTTP
    #######################################################################
    def get_method(self, name):
        return getattr(self, name, None)


    def GET(self, context):
        raise NotImplementedError


    def HEAD(self, context):
        """Note that "HEAD" is tweaked by the default Web server to call "GET"
        and return the length of the body, and None as the body.
        """
        pass


    def POST(self, context):
        raise NotImplementedError


    def PUT(self, context):
        raise NotImplementedError


    def LOCK(self, context):
        raise NotImplementedError


    def UNLOCK(self, context):
        raise NotImplementedError


    #######################################################################
    # API / Security
    #######################################################################
    def get_access_control(self):
        node = self
        while node is not None:
            if isinstance(node, AccessControl):
                return node
            node = node.parent

        return None



class Root(AccessControl, Node):
    """The Root is the main entry point of the Web application.  Responsible
    for traversal, user retrieval, and error pages.  It is a handler of
    type Foldern so check out the Handler and Folder API.
    """

    def init(self, context):
        """Initialize the root for the new context.  Useful for resetting
        attributes, etc."""
        pass


    def get_user(self, username):
        """Return an object representing the user named after the username,
        or 'None'.  The nature of the object, the location of the storage
        and the retrieval of the data remain at your discretion. The only
        requirements are the "name" attribute, and the "authenticate" method
        with a "password" parameter.
        """
        return None


    #######################################################################
    # API / Publishing
    #######################################################################
    def before_traverse(self, context):
        """Pre-publishing process.
        Possible actions are language negotiation, etc.
        """
        pass


    def after_traverse(self, context, body):
        """Post-publishing process.
        Possible actions are wrapping the body into a template, etc."""
        return body


    #######################################################################
    # API / Error Pages
    #######################################################################
    def unauthorized(self, context):
        """Called on status 401 for replacing the body by an error page."""
        return '401 Unauthorized'


    def forbidden(self, context):
        """Called on status 403 for replacing the body by an error page."""
        return '403 Forbidden'


    def not_found(self, context):
        """Called on status 404 for replacing the body by an error page."""
        return '404 Not Found'


    def internal_server_error(self, context):
        """Called on status 500 for replacing the body by an error page."""
        return '500 Internal Server Error'

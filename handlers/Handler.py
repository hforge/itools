# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import datetime

# Import from itools
from itools import uri


class AcquisitionError(LookupError):
    pass




class Handler(object):
    """
    This class represents a resource handler, where a resource can be
    a file, a directory or a link. It is used as a base class for any
    other handler class.
    """

    # By default the handler is a free node (does not belong to a tree, or
    # is the root of a tree).
    parent = None
    name = ''
    # Default for mimetype (XXX revise)
    _mimetype = None


    def load(self):
        self._load()
        self.timestamp = datetime.datetime.now()


    ########################################################################
    # API
    ########################################################################
    def get_mimetype(self):
        return self._mimetype

    def set_mimetype(self, mimetype):
        self._mimetype = mimetype

    mimetype = property(get_mimetype, set_mimetype, None, '')


    ########################################################################
    # Tree
    def get_abspath(self):
        # XXX Should return a uri.Path instance
        if self.parent is None:
            return ''
        return self.parent.get_abspath() + '/' + self.name


    def get_root(self):
        if self.parent is None:
            return self
        return self.parent.get_root()


    def get_pathtoroot(self):
        if self.parent is None:
            return './'
        return self.parent.get_pathtoroot() + '../'


    def get_pathto(self, handler):
        path = uri.Path(self.get_abspath())
        return path.get_pathto(handler.get_abspath())


    def acquire(self, name):
        if self.parent is None:
            raise AcquisitionError, name
        return self.parent.acquire(name)


    ########################################################################
    # Cache
    def is_outdated(self):
        mtime = self.resource.get_mtime()
        return mtime is None or mtime > self.timestamp

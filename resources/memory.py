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
from datetime import datetime

# Import from itools.resources
import base



class Resource(base.Resource):
    """ """



class File(Resource, base.File):
    """ """

    def __init__(self, data):
        self.data = data
        self.ctime = self.mtime = datetime.now()


    def __setitem__(self, index, value):
        data = self.data
        if isinstance(index, slice):
            # XXX So far 'step' is not supported
            start, stop = index.start, index.stop
        else:
            start, stop = index, index + 1
        self.data = data[:start] + value + data[stop:]
        self.mtime = datetime.now()


    def __setslice__(self, start, stop, value):
        self.data = self.data[:start] + value + self.data[stop:]
        self.mtime = datetime.now()


    def append(self, value):
        self.data += value


    def __str__(self):
        return self.data


    def set_data(self, data):
        self.data = data
        self.mtime = datetime.now()


    def get_ctime(self):
        return self.ctime


    def get_mtime(self):
        return self.mtime



class Folder(Resource, base.Folder):
    """ """

    def __init__(self):
        self.resources = {}
        self.ctime = self.mtime = datetime.now()


    def get_mimetype(self):
        # XXX This method should be removed as soon as the Folder class
        # becomes a new style class, because this method is here only
        # to workaround the wrong inheritance algorithm of classic Python
        # classes.
        return base.Folder.get_mimetype(self)


    def get_mtime(self):
        return self.mtime


    def get_ctime(self):
        return self.ctime


    def _get_resources(self):
        return self.resources.keys()


    def _get_resource(self, name):
        return self.resources[name]


    def _has_resource(self, name):
        return name in self.resources


    def _set_file_resource(self, name, resource):
        data = resource.get_data()
        self.resources[name] = File(data)
        self.mtime = datetime.now()


    def _set_folder_resource(self, name, resource):
        self.resources[name] = Folder()
        self.mtime = datetime.now()


    def _del_file_resource(self, name):
        del self.resources[name]
        self.mtime = datetime.now()


    def _del_folder_resource(self, name):
        del self.resources[name]
        self.mtime = datetime.now()

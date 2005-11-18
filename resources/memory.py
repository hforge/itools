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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
from datetime import datetime
from cStringIO import StringIO

# Import from itools.resources
import base



class Resource(base.Resource):

    name = None
    def get_name(self):
        return self.name


    def get_ctime(self):
        return self.ctime


    def get_mtime(self):
        return self.mtime


    def get_atime(self):
        # XXX Should we correctly keep the real access time??
        return self.mtime


    def set_mtime(self, mtime):
        self.mtime = mtime



class File(Resource, base.File):

    def __init__(self, data, name=None):
        self.name = name
        self.data = StringIO()
        self.data.write(data)
        self.ctime = self.mtime = datetime.now()


    def open(self):
        self.data.seek(0)


    def close(self):
        self.data.seek(0)


    def is_open(self):
        return True


    def read(self, size=-1):
        return self.data.read(size)


    def readline(self):
        return self.data.readline()


    def write(self, data):
        self.data.write(data)
        self.mtime = datetime.now()


    def truncate(self, size=None):
        if size is None:
            self.data.truncate()
        else:
            self.data.truncate(size)
        self.mtime = datetime.now()


    ######################################################################
    # API / Direct access
    ######################################################################
    def seek(self, offset, whence=0):
        self.data.seek(offset, whence)


    def __setitem__(self, index, value):
        self.data.seek(index)
        self.data.write(value)
        self.mtime = datetime.now()


    def __setslice__(self, start, stop, value):
        self.data.seek(start)
        self.data.write(value)
        self.mtime = datetime.now()


    def append(self, value):
        self.data.seek(0, 2)
        self.data.write(value)
        self.mtime = datetime.now()



class Folder(Resource, base.Folder):

    def __init__(self, name=None):
        self.name = name
        self.resources = {}
        self.ctime = self.mtime = datetime.now()


    def _get_resource_names(self):
        return self.resources.keys()


    def _get_resource(self, name):
        return self.resources[name]


    def _has_resource(self, name):
        return name in self.resources


    def _set_file_resource(self, name, resource):
        self.resources[name] = File(resource.read(), name=name)
        self.mtime = datetime.now()


    def _set_folder_resource(self, name, resource):
        self.resources[name] = Folder(name=name)
        self.mtime = datetime.now()


    def _del_file_resource(self, name):
        del self.resources[name]
        self.mtime = datetime.now()


    def _del_folder_resource(self, name):
        del self.resources[name]
        self.mtime = datetime.now()

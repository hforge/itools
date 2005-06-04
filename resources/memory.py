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


    def __getitem__(self, i):
        self.data.seek(i)
        return self.data.read(1)


    def __getslice__(self, a, b):
        self.data.seek(a)
        return self.data.read(b-a)


    def __setitem__(self, index, value):
        if isinstance(index, slice):
            index = index.start
        self.data.seek(index)
        self.data.write(value)
        self.mtime = datetime.now()


    def __setslice__(self, start, stop, value):
        rest = self[stop:]
        self.data.seek(start)
        self.data.truncate()
        self.data.write(value)
        self.data.write(rest)
        self.mtime = datetime.now()


    def append(self, value):
        self.data.seek(0, 2)
        self.data.write(value)


    def read(self):
        self.data.seek(0)
        return self.data.read()


    def set_data(self, data):
        self.data.seek(0)
        self.data.truncate()
        self.data.write(data)
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
        data = resource.read()
        self.resources[name] = File(data, name=name)
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

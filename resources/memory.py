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


# Import from itools.resources
import base
import datetime



class Revision(object):
    def __init__(self, data, date=None):
        self.data = data

        if date is None:
            date = datetime.datetime.now()
        self.date = date



class Resource(base.Resource):
    """ """



class File(Resource, base.File):
    """ """

    def __init__(self, data):
        self.revisions = []
        self.set_data(data)


    def __str__(self):
        return self.revisions[-1].data


    def set_data(self, data):
        revision = Revision(data)
        self.revisions.append(revision)


    def get_ctime(self):
        return self.revisions[0].date


    def get_mtime(self):
        return self.revisions[-1].date




class Folder(Resource, base.Folder):
    """ """

    def __init__(self):
        self.resources = {}
        self.ctime = self.mtime = datetime.datetime.now()


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
        self.mtime = datetime.datetime.now()


    def _set_folder_resource(self, name, resource):
        self.resources[name] = Folder()
        self.mtime = datetime.datetime.now()


    def _del_file_resource(self, name):
        del self.resources[name]
        self.mtime = datetime.datetime.now()


    def _del_folder_resource(self, name):
        del self.resources[name]
        self.mtime = datetime.datetime.now()

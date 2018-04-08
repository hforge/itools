# -*- coding: UTF-8 -*-
# Copyright (C) 2007, 2009, 2011-2012 J. David Ibáñez <jdavid.ibp@gmail.com>
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

# Import from the Standard Library
from os.path import abspath, dirname

# Import from itools
from itools.fs import lfs


class LFS2Backend(object):

    def __init__(self, path):
        path = path + '/database'
        self.fs = lfs.open(path)


    def normalize_key(self, path, __root=None):
        return self.fs.normalize_key(path)


    def handler_exists(self, key):
        return self.fs.exists(key)


    def get_handler_names(self, key):
        return self.fs.get_names(key)


    def get_handler_data(self, key):
        if not key:
            return None
        if not self.fs.exists(key):
            return None
        return self.fs.open(key).read()


    def get_handler_mimetype(self, key):
        return self.fs.get_mimetype(key)


    def handler_is_file(self, key):
        return self.fs.is_file(key)


    def handler_is_folder(self, key):
        return self.fs.is_folder(key)


    def get_handler_mtime(self, key):
        return self.fs.get_mtime(key)


    def get_handler_infos(self, key):
        exists = self.handler_exists(key)
        if exists:
            is_folder = self.handler_is_folder(key)
            if is_folder:
                data = None
            else:
                data = self.get_handler_data(key)
        else:
            is_folder = False
            data = None
        return exists, is_folder, data


    def save_handler(self, key, handler):
        # Save the file
        if not self.fs.exists(key):
            f = self.fs.make_file(key)
        else:
            f = self.fs.open(key, 'w')
        try:
            data = handler.to_str()
            # Write and truncate (calls to "_save_state" must be done with the
            # pointer pointing to the beginning)
            f.write(data)
            f.truncate(f.tell())
        finally:
            f.close()


    def traverse_resources(self):
        raise NotImplementedError


    def do_transaction(self, commit_message, data, added, changed, removed, handlers):
        #raise NotImplementedError
        added_and_changed = list(added) + list(changed)
        for key in added_and_changed:
            handler = handlers.get(key)
            parent_path = dirname(key)
            if not self.fs.exists(parent_path):
                self.fs.make_folder(parent_path)
            self.save_handler(key, handler)
        for key in removed:
            self.fs.remove(key)


    def abort_transaction(self):
        #raise NotImplementedError
        pass

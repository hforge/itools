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
from os.path import dirname

# Import from itools
from itools.fs import lfs, WRITE

# Import from here
from .registry import register_backend


class LFSBackend:

    def __init__(self, path, fields, read_only=False):
        if path:
            self.fs = lfs.open(f'{path}/database')
        else:
            self.fs = lfs

    @classmethod
    def init_backend(cls, path, fields, init=False, soft=False):
        lfs.make_folder(f'{path}/database')

    def normalize_key(self, path):
        return self.fs.normalize_key(path)

    def handler_exists(self, key):
        return self.fs.exists(key)

    def get_handler_names(self, key):
        return self.fs.get_names(key)

    def get_handler_data(self, key, text=False):
        if not key:
            return None
        with self.fs.open(key, text=text) as f:
            if isinstance(f, str):
                return f
            else:
                return f.read()

    def get_handler_mimetype(self, key):
        return self.fs.get_mimetype(key)

    def handler_is_file(self, key):
        return self.fs.is_file(key)

    def handler_is_folder(self, key):
        return self.fs.is_folder(key)

    def get_handler_mtime(self, key):
        return self.fs.get_mtime(key)

    def save_handler(self, key, handler):
        data = handler.to_str()
        text = isinstance(data, str)
        # Save the file
        if not self.fs.exists(key):
            with self.fs.make_file(key, text=text) as f:
                f.write(data)
                f.truncate(f.tell())
        else:
            with self.fs.open(key, WRITE, text=text) as f:
                f.write(data)
                f.truncate(f.tell())

    def traverse_resources(self):
        raise NotImplementedError

    def do_transaction(self, commit_message, data, added, changed, removed, handlers):
        # List of Changed
        added_and_changed = list(added) + list(changed)
        # Build the tree from index
        for key in added_and_changed:
            handler = handlers.get(key)
            parent_path = dirname(key)
            if not self.fs.exists(parent_path):
                self.fs.make_folder(parent_path)
            handler.save_state()
        for key in removed:
            self.fs.remove(key)

    def abort_transaction(self):
        # Cannot abort transaction with this backend
        pass

    def close(self):
        self.fs.close()


register_backend('lfs', LFSBackend)

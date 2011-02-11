# -*- coding: UTF-8 -*-
# Copyright (C) 2011 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from pygit2
from pygit2 import Repository

# Import from itools
from itools.fs import lfs
import _git


class WorkTree(_git.WorkTree):

    timestamp = None

    def __init__(self, path):
        self.path = path
        self.repo = Repository('%s/.git' % path)
        self.index_path = '%s/.git/index' % path


    def _get_index(self):
        path = self.index_path

        index = self.repo.index
        if not self.timestamp or self.timestamp < lfs.get_mtime(path):
            index.read()
            self.timestamp = lfs.get_mtime(path)

        return index


    def git_add(self, *args):
        if args:
            index = self._get_index()
            for path in args:
                index.add(path, 0)
            index.write()
            self.timestamp = lfs.get_mtime(self.index_path)

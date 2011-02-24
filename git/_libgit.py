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

# Import from the Standard Library
from datetime import datetime
from os.path import exists

# Import from pygit2
from pygit2 import Repository, GIT_SORT_TIME, GIT_SORT_REVERSE

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
        # TODO Implement first commit with libgit2
        if not exists(self.index_path):
            super(WorkTree, self).git_add(*args)
            return

        if args:
            index = self._get_index()
            for path in args:
                index.add(path, 0)
            index.write()
            self.timestamp = lfs.get_mtime(self.index_path)


    def xgit_log(self, files=None, n=None, author=None, grep=None,
                reverse=False):
        # Not implemented
        if files or author or grep:
            proxy = super(WorkTree, self)
            return proxy.git_log(files, n, author, grep, reverse)

        # Get the sha
        repo_path = '%s/.git' % self.path
        ref = open('%s/HEAD' % repo_path).read().split()[-1]
        sha = open('%s/%s' % (repo_path, ref)).read().strip()

        # Sort
        sort = GIT_SORT_TIME
        if reverse is True:
            sort |= GIT_SORT_REVERSE

        # Go
        commits = []
        for commit in self.repo.walk(sha, GIT_SORT_TIME):
            ts = commit.commit_time
            commits.append(
                {'revision': commit.sha,             # commit
                 'username': commit.author[0],       # author name
                 'date': datetime.fromtimestamp(ts), # author date
                 'message': commit.message_short,    # subject
                })
            if n is not None:
                n -= 1
                if n == 0:
                    break

        # Ok
        return commits

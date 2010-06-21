# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
# Copyright (C) 2007-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from xapian
from xapian import DatabaseOpeningError

# Import from itools
from itools.core import LRUCache, freeze, lazy, send_subprocess
from itools.fs import lfs
from itools.handlers import RODatabase
from itools.uri import Path
from itools.xapian import Catalog
from registry import get_register_fields



class ROGitDatabase(RODatabase):

    def __init__(self, path, size_min=4800, size_max=5200):
        # 1. Keep the path
        if not lfs.is_folder(path):
            error = '"%s" should be a folder, but it is not' % path
            raise ValueError, error

        folder = lfs.open(path)
        self.path = str(folder.path)

        # 2. Keep the path to the data
        self.path_data = '%s/database/' % self.path
        if not lfs.is_folder(self.path_data):
            error = '"%s" should be a folder, but it is not' % self.path_data
            raise ValueError, error

        # 3. Initialize the database, but chrooted
        folder = lfs.open(self.path_data)
        super(ROGitDatabase, self).__init__(size_min, size_max, fs=folder)

        # 4. The git cache
        self.git_cache = LRUCache(900, 1100)


    def normalize_key(self, path, __root=Path('/')):
        # Performance is critical so assume the path is already relative to
        # the repository.
        key = __root.resolve(path)
        if key and key[0] == '.git':
            err = "bad '%s' path, access to the '.git' folder is denied"
            raise ValueError, err % path

        return '/'.join(key)


    def push_phantom(self, key, handler):
        handler.database = self
        handler.key = key


    def is_phantom(self, handler):
        return handler.timestamp is None and handler.dirty is not None


    #######################################################################
    # Git
    #######################################################################
    def send_subprocess(self, cmd):
        return send_subprocess(cmd, path=self.path_data)


    def get_diff(self, revision):
        cmd = ['git', 'show', revision, '--pretty=format:%an%n%at%n%s']
        data = self.send_subprocess(cmd)
        lines = data.splitlines()

        ts = int(lines[1])
        return {
            'author_name': lines[0],
            'author_date': datetime.fromtimestamp(ts),
            'subject': lines[2],
            'diff': '\n'.join(lines[2:])}


    def get_files_affected(self, revisions):
        """Get the unordered set of files affected by a list of revisions.
        """
        cmd = ['git', 'show', '--numstat', '--pretty=format:'] + revisions
        data = self.send_subprocess(cmd)
        lines = data.splitlines()
        files = set()
        for line in lines:
            if not line:
                continue
            before, after, filename = line.split('\t')
            files.add(filename)
        return freeze(files)


    def get_stats(self, from_, to=None, paths=[]):
        if to is None:
            cmd = ['git', 'show', '--pretty=format:', '--stat', from_]
        else:
            cmd = ['git', 'diff', '--stat', from_, to]

        if paths:
            cmd.append('--')
            cmd.extend(paths)
        return self.send_subprocess(cmd)


    def get_diff_between(self, from_, to='HEAD', paths=[]):
        """Get the diff of the given path from the given commit revision to
        HEAD.

        If "stat" is True, get a diff stat only.
        """
        cmd = ['git', 'diff', from_, to]
        if paths:
            cmd.append('--')
            cmd.extend(paths)
        return self.send_subprocess(cmd)


    def get_blob(self, hash, cls):
        if type(hash) is not str:
            raise TypeError, 'get_blob expects a string, %s found' % type(hash)

        if len(hash) != 40:
            raise ValueError, 'a git hash is 40 chars long, not %d' % len(hash)

        if hash in self.git_cache:
            return self.git_cache[hash]

        cmd = ['git', 'show', hash]
        blob = self.send_subprocess(cmd)
        blob = cls(string=blob)
        self.git_cache[hash] = blob
        return blob


    def get_commit_hashs(self, file):
        """Give the hashs for all commit concerning file
        """
        cmd = ['git', 'log', '--reverse', '--pretty=format:%H', file]
        log = self.send_subprocess(cmd)
        return log.splitlines()


    def get_blob_by_revision_and_path(self, revision, path, cls):
        """Get the file contents located at the given path after the given
        commit revision has been committed.
        """
        arg = '%s:%s' % (revision, path)
        cmd = ['git', 'rev-parse', arg]
        hash = self.send_subprocess(cmd)
        hash = hash.rstrip('\n')
        return self.get_blob(hash, cls)


    def get_revisions(self, files, n=None):
        cmd = ['git', 'rev-list', '--pretty=format:%an%n%at%n%s']
        if n is not None:
            cmd = cmd + ['-n', str(n)]
        cmd = cmd + ['HEAD', '--'] + files
        data = self.send_subprocess(cmd)

        # Parse output
        revisions = []
        lines = data.splitlines()
        for idx in range(len(lines) / 4):
            base = idx * 4
            ts = int(lines[base+2])
            revisions.append(
                {'revision': lines[base].split()[1], # commit
                 'username': lines[base+1],          # author name
                 'date': datetime.fromtimestamp(ts), # author date
                 'message': lines[base+3],           # subject
                })
        # Ok
        return revisions


    def get_last_revision(self, files):
        revisions = self.get_revisions(files, 1)
        return revisions[0] if revisions else None


    #######################################################################
    # Catalog
    #######################################################################
    @lazy
    def catalog(self):
        path = '%s/catalog' % self.path
        fields = get_register_fields()
        try:
            return Catalog(path, fields, read_only=True)
        except DatabaseOpeningError:
            return None


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
from os import remove, rmdir, walk
from os.path import exists, isfile
from shutil import copy2
from subprocess import CalledProcessError

# Import from pygit2
from pygit2 import Repository, GIT_SORT_TIME, GIT_SORT_REVERSE, GIT_OBJ_TREE

# Import from itools
from itools.core import lazy, utc
from itools.datatypes import ISODateTime
from itools.fs import lfs
from subprocess_ import send_subprocess


class WorkTree(object):

    timestamp = None

    def __init__(self, path):
        self.path = path
        self.index_path = '%s/.git/index' % path
        self.cache = {} # {sha: object}


    def _send_subprocess(self, cmd):
        return send_subprocess(cmd, path=self.path)


    @lazy
    def repo(self):
        return Repository('%s/.git' % self.path)


    def get_object_by_sha(self, sha):
        cache = self.cache
        if sha not in cache:
            cache[sha] = self.repo[sha]

        return cache[sha]


    def get_object_by_commit_and_path(self, commit, path):
        obj = commit.tree
        for name in path.split('/'):
            if obj.type != GIT_OBJ_TREE:
                return None
            entry = get_tree_entry_by_name(obj, name)
            if entry is None:
                return None
            obj = self.get_object_by_sha(entry.sha)
        return obj


    @property
    def index(self):
        path = self.index_path
        if not exists(path):
            return None

        index = self.repo.index
        if not self.timestamp or self.timestamp < lfs.get_mtime(path):
            index.read()
            self.timestamp = lfs.get_mtime(path)

        return index


    #######################################################################
    # Public API
    #######################################################################
    def git_init(self):
        send_subprocess(['git', 'init', '-q', self.path])


    def git_add(self, *args):
        index = self.index
        if index is None:
            self._send_subprocess(['git', 'add'] + list(args))
            return
        for path in args:
            abspath = '%s/%s' % (self.path, path)
            # 1. File
            if isfile(abspath):
                index.add(path, 0)
                continue
            # 2. Folder
            for root, dirs, files in walk(abspath):
                for name in files:
                    index.add('%s/%s' % (root[n:], name), 0)


    def git_rm(self, *args):
        index = self.index
        n = len(self.path) + 1
        for path in args:
            abspath = '%s/%s' % (self.path, path)
            # 1. File
            if isfile(abspath):
                del index[path]
                remove(abspath)
                continue
            # 2. Folder
            for root, dirs, files in walk(abspath, topdown=False):
                for name in files:
                    del index['%s/%s' % (root[n:], name)]
                    remove('%s/%s' % (root, name))
                for name in dirs:
                    rmdir('%s/%s' % (root, name))


    def git_mv(self, source, target):
        copy2(source, target)
        self.git_rm(source)


    def git_save_index(self):
        self.index.write()
        self.timestamp = lfs.get_mtime(self.index_path)


    def git_cat_file(self, sha):
        if type(sha) is not str:
            raise TypeError, 'expected string, got %s' % type(sha)

        if len(sha) != 40:
            raise ValueError, '"%s" is not an sha' % sha

        return self._send_subprocess(['git', 'cat-file', '-p', sha])


    def git_clean(self):
        self._send_subprocess(['git', 'clean', '-fxdq'])


    def git_commit(self, message, author=None, date=None, quiet=False):
        cmd = ['git', 'commit', '-m', message]
        if author:
            cmd.append('--author=%s' % author)
        if date:
            date = ISODateTime.encode(date)
            cmd.append('--date=%s' % date)
        if quiet:
            cmd.append('-q')

        try:
            self._send_subprocess(cmd)
        except CalledProcessError, excp:
            # Avoid an exception for the 'nothing to commit' case
            # FIXME Not reliable, we may catch other cases
            if excp.returncode != 1:
                raise


    def git_diff(self, expr, paths=None, stat=False):
        cmd = ['git', 'diff', expr]
        if stat:
            cmd.append('--stat')
        if paths:
            cmd.append('--')
            cmd.extend(paths)
        return self._send_subprocess(cmd)


    def _git_log(self, paths=None, n=None, author=None, grep=None,
                 reverse=False, include_files=False):
        # 1. Build the git command
        cmd = ['git', 'log', '--pretty=format:%H%n%an%n%at%n%s']
        if include_files:
            cmd.append('--raw')
            cmd.append('--name-only')
        if n is not None:
            cmd += ['-n', str(n)]
        if author:
            cmd += ['--author=%s' % author]
        if grep:
            cmd += ['--grep=%s' % grep]
        if reverse:
            cmd.append('--reverse')
        if paths:
            cmd.append('--')
            if type(paths) is str:
                cmd.append(paths)
            else:
                cmd.extend(paths)

        # 2. Run
        lines = self._send_subprocess(cmd).splitlines()
        n = len(lines)

        # 3. Parse output
        commits = []
        idx = 0
        while idx < n:
            date = int(lines[idx + 2])
            commits.append({
                'revision': lines[idx],                    # sha
                'username': lines[idx + 1],                # author name
                'date': datetime.fromtimestamp(date, utc), # author date
                'message': lines[idx + 3]})                # message
            idx += 4
            if include_files:
                paths = []
                commits[-1]['paths'] = paths
                while idx < n and lines[idx]:
                    paths.append(lines[idx])
                    idx += 1

        # Ok
        return commits


    def git_log(self, files=None, n=None, author=None, grep=None,
                reverse=False):
        # Not implemented
        if author or grep:
            return self._git_log(files, n, author, grep, reverse)

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
            if files:
                parents = commit.parents
                parent = parents[0] if parents else None
                for path in files:
                    a = self.get_object_by_commit_and_path(commit, path)
                    if parent is None:
                        if a:
                            break
                    else:
                        b = self.get_object_by_commit_and_path(parent, path)
                        if a is not b:
                            break
                else:
                    continue

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


    def git_reset(self):
        # Use a try/except because this fails with new repositories
        try:
            self._send_subprocess(['git', 'reset', '--hard', '-q'])
        except CalledProcessError:
            pass


    def git_show(self, commit, stat=False):
        cmd = ['git', 'show', commit, '--pretty=format:%an%n%at%n%s']
        if stat:
            cmd.append('--stat')
        data = self._send_subprocess(cmd)
        author, date, message, diff = data.split('\n', 3)

        return {
            'author_name': author,
            'author_date': datetime.fromtimestamp(int(date)),
            'subject': message,
            'diff': diff}


    def get_files_changed(self, expr):
        """Get the files that have been changed by a set of commits.
        """
        cmd = ['git', 'show', '--numstat', '--pretty=format:', expr]
        data = self._send_subprocess(cmd)
        lines = data.splitlines()
        return frozenset([ line.split('\t')[-1] for line in lines if line ])


    def get_blob_id(self, commit_id, path):
        cmd = ['git', 'rev-parse', '%s:%s' % (commit_id, path)]
        blob_id = self._send_subprocess(cmd)
        return blob_id.rstrip('\n')



# TODO We implement this function because the equivalent in libgit2/pygit2
# does not work. Investigate the problem and open an issue in github.
def get_tree_entry_by_name(tree, name):
    i = 0
    while i < len(tree):
        entry = tree[i]
        if entry.name == name:
            return entry
        i += 1
    return None

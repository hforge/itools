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
from os import listdir, remove, rmdir, walk
from os.path import abspath, exists, isabs, isfile
from re import search
from shutil import copy2, copytree

# Import from pygit2
from pygit2 import Repository, GitError, init_repository
from pygit2 import GIT_SORT_REVERSE, GIT_SORT_TIME
from pygit2 import GIT_OBJ_COMMIT, GIT_OBJ_TREE

# Import from itools
from itools.core import get_pipe, lazy, utc
from itools.datatypes import ISODateTime
from itools.fs import lfs


class WorkTree(object):

    timestamp = None

    def __init__(self, path):
        self.path = abspath(path) + '/'
        self.index_path = '%s/.git/index' % path
        self.cache = {} # {sha: object}


    def _get_abspath(self, path):
        if isabs(path):
            if path.startswith(self.path):
                return path
            raise ValueError, 'unexpected absolute path "%s"' % path
        if path == '.':
            return self.path
        return '%s%s' % (self.path, path)


    def _send_subprocess(self, cmd):
        return get_pipe(cmd, cwd=self.path)


    def _resolve_reference(self, reference):
        if reference != 'HEAD':
            raise NotImplementedError

        repo_path = '%s/.git' % self.path
        ref = open('%s/HEAD' % repo_path).read().split()[-1]
        return open('%s/%s' % (repo_path, ref)).read().strip()


    @lazy
    def repo(self):
        return Repository('%s/.git' % self.path)


    def lookup(self, sha):
        cache = self.cache
        if sha not in cache:
            cache[sha] = self.repo[sha]

        return cache[sha]


    def _lookup_by_commit_and_path(self, commit, path):
        obj = commit.tree
        for name in path.split('/'):
            if obj.type != GIT_OBJ_TREE:
                return None
            #entry = obj[name] if name in obj else None
            entry = get_tree_entry_by_name(obj, name)
            if entry is None:
                return None
            obj = self.lookup(entry.sha)
        return obj


    @property
    def index(self):
        index = self.repo.index
        # Bare repository
        if index is None:
            raise RuntimeError, 'expected standard repository, not bare'

        path = self.index_path
        if exists(path):
            mtime = lfs.get_mtime(path)
            if not self.timestamp or self.timestamp < mtime:
                index.read()
                self.timestamp = mtime

        return index


    #######################################################################
    # Public API
    #######################################################################
    def git_init(self):
        self.repo = init_repository(self.path, False)


    def git_add(self, *args):
        index = self.index
        n = len(self.path)
        for path in args:
            abspath = self._get_abspath(path)
            # 1. File
            if isfile(abspath):
                index.add(path)
                continue
            # 2. Folder
            for root, dirs, files in walk(abspath):
                for name in files:
                    index.add('%s/%s' % (root[n:], name))


    def git_rm(self, *args):
        index = self.index
        n = len(self.path)
        for path in args:
            abspath = self._get_abspath(path)
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
        source_abs = self._get_abspath(source)
        target = self._get_abspath(target)
        if isfile(source_abs):
            copy2(source_abs, target)
        else:
            copytree(source_abs, target)

        self.git_rm(source)


    def git_clean(self):
        index = self.index
        n = len(self.path)
        for root, dirs, files in walk(self.path, topdown=False):
            for name in files:
                path = '%s/%s' % (root[n:], name)
                if path not in index:
                    remove('%s/%s' % (root, name))
            if not listdir(root):
                rmdir(root)


    def git_commit(self, message, author=None, date=None, quiet=False):
        self.index.write()
        self.timestamp = lfs.get_mtime(self.index_path)

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
        except EnvironmentError, excp:
            # Avoid an exception for the 'nothing to commit' case
            # FIXME Not reliable, we may catch other cases
            if excp.errno != 1:
                raise


    def git_diff(self, expr, paths=None, stat=False):
        cmd = ['git', 'diff', expr]
        if stat:
            cmd.append('--stat')
        if paths:
            cmd.append('--')
            cmd.extend(paths)
        return self._send_subprocess(cmd)


    def git_log(self, files=None, n=None, author=None, grep=None,
                reverse=False):
        # Get the sha
        sha = self._resolve_reference('HEAD')

        # Sort
        sort = GIT_SORT_TIME
        if reverse is True:
            sort |= GIT_SORT_REVERSE

        # Go
        commits = []
        for commit in self.repo.walk(sha, GIT_SORT_TIME):
            # --author=<pattern>
            if author:
                name, email, time = commit.author
                if not search(author, name) and not search(author, email):
                    continue

            # --grep=<pattern>
            if grep:
                if not search(grep, commit.message):
                    continue

            # -- path ...
            if files:
                parents = commit.parents
                parent = parents[0] if parents else None
                for path in files:
                    a = self._lookup_by_commit_and_path(commit, path)
                    if parent is None:
                        if a:
                            break
                    else:
                        b = self._lookup_by_commit_and_path(parent, path)
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
        except EnvironmentError:
            pass


    def git_show(self, sha):
        commit = self.lookup(sha)

        cmd = ['git', 'show', sha, '--pretty=format:']
        diff = self._send_subprocess(cmd)[1:]

        author = commit.author
        return {
            'author_name': author[0],
            'author_date': datetime.fromtimestamp(author[2]),
            'subject': commit.message_short,
            'diff': diff}


    def git_stats(self, commit):
        cmd = ['git', 'show', '--pretty=format:', '--stat', commit]
        data = self._send_subprocess(cmd)
        return data[1:]


    def describe(self, match=None):
        # The command
        command = ['git', 'describe', '--tags', '--long']
        if match:
            command.extend(['--match', match])

        # Call
        try:
            data = self._send_subprocess(command)
        except EnvironmentError:
            return None
        tag, n, commit = data.rsplit('-', 2)
        return tag, int(n), commit


    def get_blob_id(self, commit_id, path):
        commit = self.lookup(commit_id)
        if commit.type != GIT_OBJ_COMMIT:
            raise ValueError, 'XXX'

        blob = self._lookup_by_commit_and_path(commit, path)
        return blob.sha


    def get_branch_name(self):
        """Returns the name of the current branch.
        """
        ref = open('%s/.git/HEAD' % self.path).read().rstrip()
        ref = ref.rsplit('/', 1)
        return ref[1] if len(ref) == 2 else None


    def get_filenames(self):
        """Returns the list of filenames tracked by git.
        """
        index = self.index

        filenames = []
        i = 0
        while i < len(index):
            filenames.append(index[i].path)
            i += 1

        return filenames


    def get_files_changed(self, since, until):
        """Get the files that have been changed by a set of commits.
        """
        expr = '%s..%s' % (since, until)
        cmd = ['git', 'show', '--numstat', '--pretty=format:', expr]
        data = self._send_subprocess(cmd)
        lines = data.splitlines()
        return frozenset([ line.split('\t')[-1] for line in lines if line ])


    def get_metadata(self, reference='HEAD'):
        """Returns some metadata about the given commit reference.

        For now only the commit id and the timestamp are returned.
        """
        sha = self._resolve_reference(reference)
        commit = self.lookup(sha)
        parents = commit.parents
        an, ae, ad = commit.author
        cn, ce, cd = commit.committer

        return {
            'tree': commit.tree.sha,
            'parent': parents[0].sha if parents else None,
            'author': ('%s <%s>' % (an, ae), datetime.fromtimestamp(ad)),
            'committer': ('%s <%s>' % (cn, ce), datetime.fromtimestamp(cd)),
            'message': commit.message}


    def is_available(self):
        """Returns True if we are in a git working directory, False otherwise.
        """
        try:
            self.repo
        except GitError:
            return False
        return True



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

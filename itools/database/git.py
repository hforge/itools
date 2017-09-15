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
from calendar import timegm
from datetime import datetime
from os.path import abspath
from re import search
from subprocess import Popen, PIPE
import time

# Import from pygit2
from pygit2 import Repository, Signature, IndexEntry, init_repository
from pygit2 import GIT_SORT_REVERSE, GIT_SORT_TIME, GIT_OBJ_TREE
from pygit2 import GIT_FILEMODE_TREE,GIT_FILEMODE_BLOB_EXECUTABLE

# Import from itools
from itools.core import LRUCache, lazy
from itools.fs import lfs

class GitBackend(object):

    def __init__(self, path):
        self.path = abspath(path) + '/'
        # Open database
        self.path_data = '%s/database/' % self.path
        if not lfs.is_folder(self.path_data):
            error = '"%s" should be a folder, but it is not' % path
            raise ValueError, error
        # Open repository
        self.repo = Repository(self.path_data)
        # Read index
        try:
            tree = self.repo.head.peel(GIT_OBJ_TREE)
            self.repo.index.read_tree(tree.id)
        except:
            pass
        # 6.The git cache - {sha: object}
        self.git_cache = LRUCache(900, 1100)
        # Check git commiter
        try:
            _, _ = self.username, self.useremail
        except:
            print '========================================='
            print 'ERROR: Please configure GIT commiter via'
            print ' $ git config --global user.name'
            print ' $ git config --global user.email'
            print '========================================='
            raise


    #######################################################################
    # Internal utility functions
    #######################################################################
    def _call(self, command):
        """Interface to cal git.git for functions not yet implemented using
        libgit2.
        """
        popen = Popen(command, stdout=PIPE, stderr=PIPE, cwd=self.path)
        stdoutdata, stderrdata = popen.communicate()
        if popen.returncode != 0:
            raise EnvironmentError, (popen.returncode, stderrdata)
        return stdoutdata


    def _resolve_reference(self, reference):
        """This method returns the SHA the given reference points to. For now
        only HEAD is supported.

        FIXME This is quick & dirty. TODO Implement references in pygit2 and
        use them here.
        """
        # Case 1: SHA
        if len(reference) == 40:
            return reference

        # Case 2: reference
        reference = self.repo.lookup_reference(reference)
        try:
            reference = reference.resolve()
        except KeyError:
            return None

        return reference.target


    #######################################################################
    # External API
    #######################################################################
    def lookup(self, sha):
        """Return the object by the given SHA. We use a cache to warrant that
        two calls with the same SHA will resolve to the same object, so the
        'is' operator will work.
        """
        cache = self.cache
        if sha not in cache:
            cache[sha] = self.repo[sha]

        return cache[sha]


    def lookup_from_commit_by_path(self, commit, path):
        """Return the object (tree or blob) the given path points to from the
        given commit, or None if the given path does not exist.

        TODO Implement Tree.getitem_by_path(path) => TreeEntry in pygit2 to
        speed up things.
        """
        obj = commit.tree
        for name in path.split('/'):
            if obj.type != GIT_OBJ_TREE:
                return None

            if name not in obj:
                return None
            entry = obj[name]
            obj = self.lookup(entry.oid)
        return obj


    @property
    def index(self):
        """Gives access to the index file. Reloads the index file if it has
        been modified in the filesystem.

        TODO An error condition should be raised if the index file has
        been modified both in the filesystem and in memory.
        """
        index = self.repo.index
        # Bare repository
        if index is None:
            raise RuntimeError, 'expected standard repository, not bare'
        return index



    @lazy
    def username(self):
        cmd = ['git', 'config', '--get', 'user.name']
        try:
            username = self._call(cmd).rstrip()
        except EnvironmentError:
            raise ValueError("Please configure 'git config --global user.name'")
        return username


    @lazy
    def useremail(self):
        cmd = ['git', 'config', '--get', 'user.email']
        try:
            useremail = self._call(cmd).rstrip()
        except EnvironmentError:
            raise ValueError("Please configure 'git config --global user.email'")
        return useremail


    def git_tag(self, tag_name, message):
        """Equivalent to 'git tag', we must give the name of the tag and the message
        TODO Implement using libgit2
        """
        if not tag_name or not message:
            raise ValueError('excepted tag name and message')
        cmd = ['git', 'tag', '-a', tag_name, '-m', message]
        return self._call(cmd)


    def git_remove_tag(self, tag_name):
        if not tag_name:
            raise ValueError('excepted tag name')
        cmd = ['git', 'tag', '-d', tag_name]
        return self._call(cmd)


    def git_reset(self, reference):
        """Equivalent to 'git reset --hard', we must provide the reference to reset to
        """
        if not reference:
            raise ValueError('excepted reference to reset')
        cmd = ['git', 'reset', '--hard', '-q', reference]
        return self._call(cmd)


    def git_commit(self, message, author=None, date=None, tree=None):
        """Equivalent to 'git commit', we must give the message and we can
        also give the author and date.
        """
        # Tree
        if tree is None:
            #tree = self.index.write_tree()
            raise ValueError('Please give me a tree')

        # Parent
        parent = self._resolve_reference('HEAD')
        parents = [parent] if parent else []

        # Committer
        when_time = time.time()
        when_offset = - (time.altzone if time.daylight else time.timezone)
        when_offset = when_offset / 60

        name = self.username
        email = self.useremail
        committer = Signature(name, email, when_time, when_offset)

        # Author
        if author is None:
            author = (name, email)

        if date:
            if date.tzinfo:
                from pytz import utc
                when_time = date.astimezone(utc)            # To UTC
                when_time = when_time.timetuple()           # As struct_time
                when_time = timegm(when_time)               # To unix time
                when_offset = date.utcoffset().seconds / 60
            else:
                err = "Worktree.git_commit doesn't support naive datatime yet"
                raise NotImplementedError, err

        author = Signature(author[0], author[1], when_time, when_offset)

        # Create the commit
        return self.repo.create_commit('HEAD', author, committer, message,
                                       tree, parents)


    def git_log(self, paths=None, n=None, author=None, grep=None,
                reverse=False, reference='HEAD'):
        """Equivalent to 'git log', optional keyword parameters are:

          paths   -- return only commits where the given paths have been
                     changed
          n       -- show at most the given number of commits
          author  -- filter out commits whose author does not match the given
                     pattern
          grep    -- filter out commits whose message does not match the
                     given pattern
          reverse -- return results in reverse order
        """
        # Get the sha
        sha = self._resolve_reference(reference)

        # Sort
        sort = GIT_SORT_TIME
        if reverse is True:
            sort |= GIT_SORT_REVERSE

        # Go
        commits = []
        for commit in self.repo.walk(sha, GIT_SORT_TIME):
            # --author=<pattern>
            if author:
                commit_author = commit.author
                if not search(author, commit_author.name) and \
                   not search(author, commit_author.email):
                    continue

            # --grep=<pattern>
            if grep:
                if not search(grep, commit.message):
                    continue

            # -- path ...
            if paths:
                parents = commit.parents
                parent = parents[0] if parents else None
                for path in paths:
                    a = self.lookup_from_commit_by_path(commit, path)
                    if parent is None:
                        if a:
                            break
                    else:
                        b = self.lookup_from_commit_by_path(parent, path)
                        if a is not b:
                            break
                else:
                    continue

            ts = commit.commit_time
            commits.append(
                {'sha': commit.hex,
                 'author_name': commit.author.name,
                 'author_date': datetime.fromtimestamp(ts),
                 'message_short': self.message_short(commit)})
            if n is not None:
                n -= 1
                if n == 0:
                    break

        # Ok
        return commits


    def git_diff(self, since, until=None, paths=None):
        """Return the diff between two commits, eventually reduced to the
        given paths.

        TODO Implement using Python's difflib standard library, to avoid
        calling Git.
        """
        if until is None:
            data = self._call(['git', 'show', since, '--pretty=format:'])
            return data[1:]

        cmd = ['git', 'diff', '%s..%s' % (since, until)]
        if paths:
            cmd.append('--')
            cmd.extend(paths)
        return self._call(cmd)


    def git_stats(self, since, until=None, paths=None):
        """Return statistics of the changes done between two commits,
        eventually reduced to the given paths.

        TODO Implement using libgit2
        """
        if until is None:
            cmd = ['git', 'show', '--pretty=format:', '--stat', since]
            data = self._call(cmd)
            return data[1:]

        cmd = ['git', 'diff', '--stat', '%s..%s' % (since, until)]
        if paths:
            cmd.append('--')
            cmd.extend(paths)
        return self._call(cmd)


    def get_files_changed(self, since, until):
        """Return the files that have been changed between two commits.

        TODO Implement with libgit2
        """
        expr = '%s..%s' % (since, until)
        cmd = ['git', 'show', '--numstat', '--pretty=format:', expr]
        data = self._call(cmd)
        lines = data.splitlines()
        return frozenset([ line.split('\t')[-1] for line in lines if line ])


    def get_metadata(self, reference='HEAD'):
        """Resolves the given reference and returns metadata information
        about the commit in the form of a dict.
        """
        sha = self._resolve_reference(reference)
        commit = self.lookup(sha)
        parents = commit.parents
        author = commit.author
        committer = commit.committer

        # TODO Use the offset for the author/committer time
        return {
            'tree': commit.tree.hex,
            'parent': parents[0].hex if parents else None,
            'author_name': author.name,
            'author_email': author.email,
            'author_date': datetime.fromtimestamp(author.time),
            'committer_name': committer.name,
            'committer_email': committer.email,
            'committer_date': datetime.fromtimestamp(committer.time),
            'message': commit.message,
            'message_short': self.message_short(commit),
            }


    def message_short(self, commit):
        """Helper function to get the subject line of the commit message.

        XXX This code is based on the 'message_short' value that was once
        available in libgit2 (and removed by 5ae2f0c0135). It should be removed
        once libgit2 gets the feature back, see issue #250 for the discussion:

          https://github.com/libgit2/libgit2/pull/250
        """
        message = commit.message
        message = message.split('\n\n')[0]
        message = message.replace('\n', ' ')
        return message.rstrip()

    #######################################################################
    # Data API
    #######################################################################
    def handler_exists(self, key):
        tree = self.repo.head.peel(GIT_OBJ_TREE)
        try:
            tree[key]
        except:
            return False
        return True


    def get_handler_names(self, key):
        try:
            tree = self.repo.head.peel(GIT_OBJ_TREE)
            if key:
                tree_entry = tree[key]
                if tree_entry.type == 'blob':
                    raise ValueError
                tree = self.repo[tree_entry.id]
        except:
            yield None
        else:
            for item in tree:
                yield item.name


    def get_handler_data(self, key):
        tree = self.repo.head.peel(GIT_OBJ_TREE)
        tree_entry = tree[key]
        blob = self.repo[tree_entry.id]
        return blob.data


    def handler_is_file(self, key):
        return not self.handler_is_folder(key)


    def handler_is_folder(self, key):
        repository = self.repo
        if key == '':
            return True
        else:
            tree = repository.head.peel(GIT_OBJ_TREE)
            tree_entry = tree[key]
        return tree_entry.type == 'tree'


    def get_handler_infos(self, key):
        exists = is_folder = False
        data = None
        try:
            tree = self.repo.head.peel(GIT_OBJ_TREE)
            tree_entry = tree[key]
        except:
            pass
        else:
            exists = True
            is_folder = tree_entry.type == 'tree'
            if not is_folder:
                data = self.repo[tree_entry.id].data
        return exists, is_folder, data

    #######################################################################
    # Git
    #######################################################################
    def get_blob(self, sha, cls):
        if sha in self.git_cache:
            return self.git_cache[sha]

        blob = self.worktree.lookup(sha)
        blob = cls(string=blob.data)
        self.git_cache[sha] = blob
        return blob


    def get_blob_by_revision_and_path(self, sha, path, cls):
        """Get the file contents located at the given path after the given
        commit revision has been committed.
        """
        worktree = self.worktree
        commit = worktree.lookup(sha)
        obj = worktree.lookup_from_commit_by_path(commit, path)
        return self.get_blob(obj.sha, cls)


    def traverse_resources(self):
        tree = self.repo.head.peel(GIT_OBJ_TREE)
        yield self.get_resource('/')
        for name in self.get_names(tree):
            if name[-9:] == '.metadata' and name != '.metadata':
                yield self.get_resource('/' + name[:-9])


    def get_names(self, tree, path=''):
        for entry in tree:
            base_path = '{0}/{1}'.format(path, entry.name)
            yield base_path
            if entry.filemode == GIT_FILEMODE_TREE:
                sub_tree = self.repo.get(entry.hex)
                for x in self.get_names(sub_tree, base_path):
                    yield x

    #######################################################################
    # Git
    #######################################################################
    def do_transaction(self, commit_message, data, added, changed, removed, handlers):
        git_author, git_date, git_msg, docs_to_index, docs_to_unindex = data
        git_msg = commit_message or git_msg or 'no comment'
        # List of Changed
        added_and_changed = list(added) + list(changed)
        # Build the tree
        index = self.repo.index
        for key in added_and_changed:
            handler = handlers.get(key)
            blob_id = self.repo.create_blob(handler.to_str())
            entry = IndexEntry(key, blob_id, GIT_FILEMODE_BLOB_EXECUTABLE)
            index.add(entry)
        for key in removed:
            index.remove(key)
        git_tree = index.write_tree()
        # Commit
        self.git_commit(git_msg, git_author, git_date, tree=git_tree)


    def abort_transaction(self):
        # TODO: Remove created blobs
        pass


def init_backend(path, init=False, soft=False):
    init_repository(path, bare=True)

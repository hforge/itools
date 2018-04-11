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
import time
from calendar import timegm
from datetime import datetime
from os.path import abspath
from subprocess import Popen, PIPE

# Import from pygit2
from pygit2 import Repository, IndexEntry, Signature, init_repository
from pygit2 import GIT_OBJ_TREE, GIT_FILEMODE_TREE,GIT_FILEMODE_BLOB_EXECUTABLE

# Import from itools
from itools.core import fixed_offset, lazy
from itools.database.magic_ import magic_from_buffer
from itools.fs import lfs

# Import from here
from registry import register_backend



class GitBareBackend(object):

    nb_transactions = 0

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


    @classmethod
    def init_backend(cls, path, init=False, soft=False):
        init_repository('{0}/database'.format(path), bare=True)


    #######################################################################
    # Internal utility functions
    #######################################################################
    def _call(self, command):
        """Interface to cal git.git for functions not yet implemented using
        libgit2.
        """
        popen = Popen(command, stdout=PIPE, stderr=PIPE, cwd=self.path_data)
        stdoutdata, stderrdata = popen.communicate()
        if popen.returncode != 0:
            raise EnvironmentError, (popen.returncode, stderrdata)
        return stdoutdata



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



    def normalize_key(self, path, __root=None):
        # Performance is critical so assume the path is already relative to
        # the repository.
        key = __root.resolve(path)
        if key and key[0] == '.git':
            err = "bad '{0}' path, access to the '.git' folder is denied"
            raise ValueError(err.format(path))
        return '/'.join(key)


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


    def get_handler_mimetype(self, key):
        data = self.get_handler_data(key)
        return magic_from_buffer(data)


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


    def get_handler_mtime(self, key):
        # FIXME
        return datetime.utcnow().replace(tzinfo=fixed_offset(0))


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


    def do_transaction(self, commit_message, data, added, changed, removed, handlers):
        self.nb_transactions += 1
        # Get informations
        git_author, git_date, git_msg, docs_to_index, docs_to_unindex = data
        git_msg = commit_message or git_msg or 'no comment'
        # List of Changed
        added_and_changed = list(added) + list(changed)
        # Build the tree from index
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


    def abort_transaction(self):
        # TODO: Remove created blobs
        pass



register_backend('git-bare', GitBareBackend)

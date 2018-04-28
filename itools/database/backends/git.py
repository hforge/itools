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
from datetime import datetime
from heapq import heappush, heappop
from os.path import abspath, dirname
from uuid import uuid4

# Import from pygit2
import pygit2
from pygit2 import TreeBuilder, GIT_FILEMODE_TREE, init_repository
from pygit2 import GIT_CHECKOUT_FORCE, GIT_CHECKOUT_REMOVE_UNTRACKED

# Import from itools
from itools.database import Metadata
from itools.database.magic_ import magic_from_buffer
from itools.database.git import open_worktree
from itools.fs import lfs

# Import from here
from registry import register_backend


class Heap(object):
    """
    This object behaves very much like a sorted dict, but for security only a
    subset of the dict API is exposed:

       >>> len(heap)
       >>> heap[path] = value
       >>> value = heap.get(path)
       >>> path, value = heap.popitem()

    The keys are relative paths as used in Git trees, like 'a/b/c' (and '' for
    the root).

    The dictionary is sorted so deeper paths are considered smaller, and so
    returned first by 'popitem'. The order relation between two paths of equal
    depth is undefined.

    This data structure is used by RWDatabase._save_changes to build the tree
    objects before commit.
    """

    def __init__(self):
        self._dict = {}
        self._heap = []


    def __len__(self):
        return len(self._dict)


    def get(self, path):
        return self._dict.get(path)


    def __setitem__(self, path, value):
        if path not in self._dict:
            n = -path.count('/') if path else 1
            heappush(self._heap, (n, path))

        self._dict[path] = value


    def popitem(self):
        key = heappop(self._heap)
        path = key[1]
        return path, self._dict.pop(path)



class GitBackend(object):

    def __init__(self, path):
        self.path = abspath(path) + '/'
        # Open database
        self.path_data = '%s/database/' % self.path
        # Check if is a folder
        self.path_data = '%s/database/' % self.path
        if not lfs.is_folder(self.path_data):
            error = '"{0}" should be a folder, but it is not'.format(self.path_data)
            raise ValueError(error)
        # New interface to Git
        self.worktree = open_worktree(self.path_data)
        # Initialize the database, but chrooted
        self.fs = lfs.open(self.path_data)
        # Static FS
        self.static_fs = lfs.open('{0}/database_static'.format(path))


    @classmethod
    def init_backend(cls, path, init=False, soft=False):
        # Metadata database
        init_repository('{0}/database'.format(path), bare=False)
        # Static database
        lfs.make_folder('{0}/database_static'.format(path))
        lfs.make_folder('{0}/database_static/.history'.format(path))


    #######################################################################
    # Database API
    #######################################################################
    def normalize_key(self, path, __root=None):
        # Performance is critical so assume the path is already relative to
        # the repository.
        key = __root.resolve(path)
        if key and key[0] == '.git':
            err = "bad '{0}' path, access to the '.git' folder is denied"
            raise ValueError(err.format(path))
        return '/'.join(key)


    def handler_exists(self, key):
        fs = self.get_handler_fs_by_key(key)
        return fs.exists(key)


    def get_handler_names(self, key):
        return self.fs.get_names(key)


    def get_handler_data(self, key):
        if not key:
            return None
        fs = self.get_handler_fs_by_key(key)
        return fs.open(key).read()


    def get_handler_mimetype(self, key):
        data = self.get_handler_data(key)
        return magic_from_buffer(data)


    def handler_is_file(self, key):
        fs = self.get_handler_fs_by_key(key)
        return fs.is_file(key)


    def handler_is_folder(self, key):
        fs = self.get_handler_fs_by_key(key)
        return fs.is_folder(key)


    def get_handler_mtime(self, key):
        fs = self.get_handler_fs_by_key(key)
        return fs.get_mtime(key)


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
        fs = self.get_handler_fs(handler)
        if not fs.exists(key):
            f = fs.make_file(key)
        else:
            f = fs.open(key, 'w')
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


    def get_handler_fs(self, handler):
        if isinstance(handler, Metadata):
            return self.fs
        return self.static_fs


    def get_handler_fs_by_key(self, key):
        if key.endswith('metadata'):
            return self.fs
        return self.static_fs


    def add_handler_into_static_history(self, key):
        the_time = datetime.now().strftime('%Y%m%d%H%M%S')
        new_key = '.history/{0}.{1}.{2}'.format(key, the_time, uuid4())
        parent_path = dirname(new_key)
        if not self.static_fs.exists(parent_path):
            self.static_fs.make_folder(parent_path)
        self.static_fs.copy(key, new_key)


    def do_transaction(self, commit_message, data, added, changed, removed, handlers):
        # Synchronize the handlers and the filesystem
        changed_and_removed = list(changed) + list(removed)
        for key in changed_and_removed:
            if not key.endswith('metadata'):
                self.add_handler_into_static_history(key)
        # Added and changed
        added_and_changed = list(added) + list(changed)
        for key in added_and_changed:
            handler = handlers.get(key)
            parent_path = dirname(key)
            fs = self.get_handler_fs(handler)
            if not fs.exists(parent_path):
                fs.make_folder(parent_path)
            self.save_handler(key, handler)
        for key in removed:
            fs = self.get_handler_fs_by_key(key)
            fs.remove(key)
        # Do git transaction for metadata
        self.do_git_transaction(commit_message, data, added, changed, removed, handlers)



    def do_git_transaction(self, commit_message, data, added, changed, removed, handlers):
        worktree = self.worktree
        # 2. Build the 'git commit' command
        git_author, git_date, git_msg, docs_to_index, docs_to_unindex = data
        git_msg = git_msg or 'no comment'

        # 3. Git add
        git_add = list(added) + list(changed)
        git_add = [x for x in git_add if x.endswith('metadata')]
        worktree.git_add(*git_add)

        # 3. Git rm
        git_rm = list(removed)
        git_rm = [x for x in git_rm if x.endswith('metadata')]
        worktree.git_rm(*git_rm)

        # 4. Create the tree
        repo = worktree.repo
        index = repo.index
        try:
            head = repo.revparse_single('HEAD')
        except KeyError:
            git_tree = None
        else:
            root = head.tree
            # Initialize the heap
            heap = Heap()
            heap[''] = repo.TreeBuilder(root)
            for key in git_add:
                entry = index[key]
                heap[key] = (entry.oid, entry.mode)
            for key in removed:
                heap[key] = None

            while heap:
                path, value = heap.popitem()
                # Stop condition
                if path == '':
                    git_tree = value.write()
                    break

                if type(value) is TreeBuilder:
                    if len(value) == 0:
                        value = None
                    else:
                        oid = value.write()
                        value = (oid, GIT_FILEMODE_TREE)

                # Split the path
                if '/' in path:
                    parent, name = path.rsplit('/', 1)
                else:
                    parent = ''
                    name = path

                # Get the tree builder
                tb = heap.get(parent)
                if tb is None:
                    try:
                        tentry = root[parent]
                    except KeyError:
                        tb = repo.TreeBuilder()
                    else:
                        tree = repo[tentry.oid]
                        tb = repo.TreeBuilder(tree)
                    heap[parent] = tb

                # Modify
                if value is None:
                    # Sometimes there are empty folders left in the
                    # filesystem, but not in the tree, then we get a
                    # "Failed to remove entry" error.  Be robust.
                    if tb.get(name) is not None:
                        tb.remove(name)
                else:
                    tb.insert(name, value[0], value[1])

        # 5. Git commit
        worktree.git_commit(git_msg, git_author, git_date, tree=git_tree)


    def abort_transaction(self):
        strategy = GIT_CHECKOUT_FORCE | GIT_CHECKOUT_REMOVE_UNTRACKED
        if pygit2.__version__ >= '0.21.1':
            self.worktree.repo.checkout_head(strategy=strategy)
        else:
            self.worktree.repo.checkout_head(strategy)


register_backend('git', GitBackend)

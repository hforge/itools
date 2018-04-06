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
from heapq import heappush, heappop

# Import from pygit2
import pygit2
from pygit2 import TreeBuilder, GIT_FILEMODE_TREE, init_repository
from pygit2 import GIT_CHECKOUT_FORCE, GIT_CHECKOUT_REMOVE_UNTRACKED

# Import from itools
from itools.database.magic_ import magic_from_buffer
from itools.database.git import open_worktree
from itools.fs import lfs


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
        # 3. Initialize the database, but chrooted
        self.fs = lfs.open(self.path_data)
        # 4. New interface to Git
        self.worktree = open_worktree(self.path_data)


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
        return self.fs.exists(key)


    def get_handler_names(self, key):
        return self.fs.get_names(key)


    def get_handler_data(self, key):
        if not key:
            return None
        return self.fs.open(key).read()


    def get_handler_mimetype(self, key):
        data = self.get_handler_data(key)
        return magic_from_buffer(data)


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
				# If there is an empty folder in the given key, remove it
				#if self.fs.is_folder(key) and not self.fs.get_names(key):
				#		raise ValueError
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
        worktree = self.worktree
        # 1. Synchronize the handlers and the filesystem
        for key in added:
            handler = handlers.get(key)
            if handler and handler.dirty:
                parent_path = dirname(key)
                if not self.fs.exists(parent_path):
                    self.fs.make_folder(parent_path)
                handler.save_state()

        for key in changed:
            handler = handlers[key]
            handler.save_state()

        # 2. Build the 'git commit' command
        git_author, git_date, git_msg, docs_to_index, docs_to_unindex = data
        git_msg = git_msg or 'no comment'

        # 3. Git add
        git_add = list(added) + list(changed)
        worktree.git_add(*git_add)

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



def init_backend(path, init=False, soft=False):
    init_repository(path)

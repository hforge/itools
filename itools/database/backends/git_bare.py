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
from os.path import abspath
from magic_ import magic_from_buffer

# Import from pygit2
from pygit2 import Repository, IndexEntry, init_repository
from pygit2 import GIT_OBJ_TREE, GIT_FILEMODE_TREE,GIT_FILEMODE_BLOB_EXECUTABLE

# Import from itools
from itools.core import fixed_offset
from itools.fs import lfs


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


    def get_handler_mimetype(self):
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


    def abort_transaction(self):
        # TODO: Remove created blobs
        pass



def init_backend(path, init=False, soft=False):
    init_repository(path, bare=True)

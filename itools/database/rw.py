# -*- coding: UTF-8 -*-
# Copyright (C) 2006, 2010 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2007 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2007 Sylvain Taverne <taverne.sylvain@gmail.com>
# Copyright (C) 2007-2008, 2010-2012 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2010 David Versmisse <versmisse@lil.univ-littoral.fr>
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
import fnmatch
from heapq import heappush, heappop
from os.path import dirname

# Import from pygit2
import pygit2
from pygit2 import TreeBuilder, GIT_FILEMODE_TREE
from pygit2 import GIT_CHECKOUT_FORCE, GIT_CHECKOUT_REMOVE_UNTRACKED

# Import from itools
from itools.core import get_pipe
from itools.fs import lfs
from itools.handlers import Folder
from itools.log import log_error
from catalog import make_catalog
from git import open_worktree
from registry import get_register_fields
from ro import RODatabase



MSG_URI_IS_BUSY = 'The "%s" URI is busy.'



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



class RWDatabase(RODatabase):


    read_only = False

    def __init__(self, path, size_min, size_max, catalog=None):
        proxy = super(RWDatabase, self)
        proxy.__init__(path, size_min, size_max, catalog)

        # The "git add" arguments
        self.added = set()
        self.changed = set()
        self.removed = set()
        self.has_changed = False

        # The resources that been added, removed, changed and moved can be
        # represented as a set of two element tuples.  But we implement this
        # with two dictionaries (old2new/new2old), to be able to access any
        # "tuple" by either value.  With the empty tuple we represent the
        # absence of change.
        #
        #  Tuple        Description                Implementation
        #  -----------  -------------------------  -------------------
        #  ()           nothing has been done yet  {}/{}
        #  (None, 'b')  resource 'b' added         {}/{'b':None}
        #  ('b', None)  resource 'b' removed       {'b':None}/{}
        #  ('b', 'b')   resource 'b' changed       {'b':'b'}/{'b':'b'}
        #  ('b', 'c')   resource 'b' moved to 'c'  {'b':'c'}/{'c':'b'}
        #  ???          resource 'b' replaced      {'b':None}/{'b':None}
        #
        # In real life, every value is either None or an absolute path (as a
        # byte stringi).  For the description that follows, we use the tuples
        # as a compact representation.
        #
        # There are four operations:
        #
        #  A(b)   - add "b"
        #  R(b)   - remove "b"
        #  C(b)   - change "b"
        #  M(b,c) - move "b" to "c"
        #
        # Then, the algebra is:
        #
        # ()        -> A(b) -> (None, 'b')
        # (b, None) -> A(b) -> (b, b)
        # (None, b) -> A(b) -> error
        # (b, b)    -> A(b) -> error
        # (b, c)    -> A(b) -> (b, b), (None, c) FIXME Is this correct?
        #
        # TODO Finish
        #
        self.resources_old2new = {}
        self.resources_new2old = {}


    def check_catalog(self):
        """Reindex resources if database wasn't stoped gracefully"""
        lines = self.catalog.logger.get_lines()
        if not lines:
            return
        print("Catalog wasn't stopped gracefully. Reindexation in progress")
        for abspath in set(lines):
            r = self.get_resource(abspath, soft=True)
            if r:
                self.catalog.index_document(r)
            else:
                self.catalog.unindex_document(abspath)
        self.catalog._db.commit_transaction()
        self.catalog._db.flush()
        self.catalog._db.begin_transaction(self.catalog.commit_each_transaction)
        self.catalog.logger.clear()


    def close(self):
        self.abort_changes()
        self.catalog.close()


    #######################################################################
    # Layer 0: handlers
    #######################################################################
    def is_phantom(self, handler):
        # Phantom handlers are "new"
        if handler.timestamp or not handler.dirty:
            return False
        # They are attached to this database, but they are not in the cache
        return handler.database is self and handler.key not in self.cache


    def has_handler(self, key):
        key = self.normalize_key(key)

        # A new file/directory is only in added
        n = len(key)
        for f_key in self.added:
            if f_key[:n] == key and (len(f_key) == n or f_key[n] == '/'):
                return True

        # Normal case
        return super(RWDatabase, self).has_handler(key)


    def _get_handler(self, key, cls=None, soft=False):
        # A hook to handle the new directories
        base = key + '/'
        n = len(base)
        for f_key in self.added:
            if f_key[:n] == base:
                return Folder(key, database=self)

        # The other files
        return super(RWDatabase, self)._get_handler(key, cls, soft)


    def set_handler(self, key, handler):
        if type(handler) is Folder:
            raise ValueError, 'unexpected folder (only files can be "set")'

        if handler.key is not None:
            raise ValueError, 'only new files can be added, try to clone first'

        key = self.normalize_key(key)
        if self._get_handler(key, soft=True) is not None:
            raise RuntimeError, MSG_URI_IS_BUSY % key

        self.push_handler(key, handler)
        self.added.add(key)
        # Changed
        self.removed.discard(key)
        self.has_changed = True


    def del_handler(self, key):
        key = self.normalize_key(key)

        # Case 1: file
        handler = self._get_handler(key)
        if type(handler) is not Folder:
            self._discard_handler(key)
            if key in self.added:
                self.added.remove(key)
            else:
                self.changed.discard(key)
                self.worktree.git_rm(key)
            # Changed
            self.removed.add(key)
            self.has_changed = True
            return

        # Case 2: folder
        base = key + '/'
        for k in self.added.copy():
            if k.startswith(base):
                self._discard_handler(k)
                self.added.discard(k)

        for k in self.changed.copy():
            if k.startswith(base):
                self._discard_handler(k)
                self.changed.discard(k)

        # Remove file
        if self.fs.exists(key):
            self.worktree.git_rm(key)

        # Changed
        self.removed.add(key)
        self.has_changed = True


    def touch_handler(self, key, handler=None):
        key = self.normalize_key(key)

        # Useful for the phantoms
        if handler is None:
            handler = self._get_handler(key)

        # The phantoms become real files
        if self.is_phantom(handler):
            self.cache[key] = handler
            self.added.add(key)
            self.removed.discard(key)
            self.has_changed = True
            return

        if handler.dirty is None:
            # Load the handler if needed
            if handler.timestamp is None:
                handler.load_state()
            # Mark the handler as dirty
            handler.dirty = datetime.now()
            # Update database state (XXX Should we do this?)
            self.changed.add(key)
            # Changed
            self.removed.discard(key)
            self.has_changed = True


    def get_handler_names(self, key):
        key = self.normalize_key(key)

        # On the filesystem
        names = super(RWDatabase, self).get_handler_names(key)
        names = set(names)

        # In added
        base = key + '/'
        n = len(base)
        for f_key in self.added:
            if f_key[:n] == base:
                name = f_key[n:].split('/', 1)[0]
                names.add(name)

        # Remove .git
        if key == "":
            names.discard('.git')

        return list(names)


    def copy_handler(self, source, target, exclude_patterns=None):
        source = self.normalize_key(source)
        target = self.normalize_key(target)

        # The trivial case
        if source == target:
            return

        # Ignore copy of some handlers
        if exclude_patterns is None:
            exclude_patterns = []
        for exclude_pattern in exclude_patterns:
            if fnmatch.fnmatch(source, exclude_pattern):
                return

        # Check the target is free
        if self._get_handler(target, soft=True) is not None:
            raise RuntimeError, MSG_URI_IS_BUSY % target

        handler = self._get_handler(source)

        # Folder
        if type(handler) is Folder:
            fs = self.fs
            for name in handler.get_handler_names():
                self.copy_handler(fs.resolve2(source, name),
                                  fs.resolve2(target, name),
                                  exclude_patterns)
        # File
        else:
            handler = handler.clone()
            self.push_handler(target, handler)
            self.added.add(target)

        # Changed
        self.removed.discard(target)
        self.has_changed = True


    def move_handler(self, source, target):
        source = self.normalize_key(source)
        target = self.normalize_key(target)

        # The trivial case
        if source == target:
            return

        # Check the target is free
        if self._get_handler(target, soft=True) is not None:
            raise RuntimeError, MSG_URI_IS_BUSY % target

        # Go
        fs = self.fs
        cache = self.cache

        # Case 1: file
        handler = self._get_handler(source)
        if type(handler) is not Folder:
            if fs.exists(source):
                self.worktree.git_mv(source, target, add=False)

            # Remove source
            self.added.discard(source)
            self.changed.discard(source)
            del self.cache[source]

            # Add target
            self.push_handler(target, handler)
            self.added.add(target)

            # Changed
            self.removed.add(source)
            self.removed.discard(target)
            self.has_changed = True
            return

        # In target in cache
        self.added.add(target)
        self.push_handler(target, handler)

        # Case 2: Folder
        n = len(source)
        base = source + '/'
        for key in self.added.copy():
            if key.startswith(base):
                new_key = '%s%s' % (target, key[n:])
                handler = cache.pop(key)
                self.push_handler(new_key, handler)
                self.added.remove(key)
                self.added.add(new_key)

        for key in self.changed.copy():
            if key.startswith(base):
                new_key = '%s%s' % (target, key[n:])
                handler = cache.pop(key)
                self.push_handler(new_key, handler)
                self.changed.remove(key)

        if fs.exists(source):
            self.worktree.git_mv(source, target, add=False)

        # Changed
        self.removed.add(source)
        self.removed.discard(target)
        self.has_changed = True


    #######################################################################
    # Layer 1: resources
    #######################################################################
    def remove_resource(self, resource):
        old2new = self.resources_old2new
        new2old = self.resources_new2old

        for x in resource.traverse_resources():
            path = str(x.abspath)
            old2new[path] = None
            new2old.pop(path, None)


    def add_resource(self, resource):
        old2new = self.resources_old2new
        new2old = self.resources_new2old

        # Catalog
        for x in resource.traverse_resources():
            path = str(x.abspath)
            new2old[path] = None


    def change_resource(self, resource):
        old2new = self.resources_old2new
        new2old = self.resources_new2old

        # Case 1: added, moved in-here or already changed
        path = str(resource.abspath)
        if path in new2old:
            return

        # Case 2: removed or moved away
        if path in old2new and not old2new[path]:
            raise ValueError, 'cannot change a resource that has been removed'

        # Case 3: not yet touched
        old2new[path] = path
        new2old[path] = path


    def is_changed(self, resource):
        """We use for this function only the 2 dicts old2new and new2old.
        """

        old2new = self.resources_old2new
        new2old = self.resources_new2old

        path = str(resource.abspath)
        return path in old2new or path in new2old


    def move_resource(self, source, new_path):
        old2new = self.resources_old2new
        new2old = self.resources_new2old

        old_path = source.abspath
        for x in source.traverse_resources():
            source_path = x.abspath
            target_path = new_path.resolve2(old_path.get_pathto(source_path))

            source_path = str(source_path)
            target_path = str(target_path)
            if source_path in old2new and not old2new[source_path]:
                err = 'cannot move a resource that has been removed'
                raise ValueError, err

            source_path = new2old.pop(source_path, source_path)
            if source_path:
                old2new[source_path] = target_path
            new2old[target_path] = source_path


    #######################################################################
    # Transactions
    #######################################################################
    def _cleanup(self):
        super(RWDatabase, self)._cleanup()
        self.has_changed = False


    def _abort_changes(self):
        # 1. Handlers
        cache = self.cache
        for key in self.added:
            self._discard_handler(key)
        for key in self.changed:
            cache[key].abort_changes()

        # 2. Git
        strategy = GIT_CHECKOUT_FORCE | GIT_CHECKOUT_REMOVE_UNTRACKED
        if pygit2.__version__ >= '0.21.1':
            self.worktree.repo.checkout_head(strategy=strategy)
        else:
            self.worktree.repo.checkout_head(strategy)

        # Reset state
        self.added.clear()
        self.changed.clear()
        self.removed.clear()

        # 2. Catalog
        self.catalog.abort_changes()

        # 3. Resources
        self.resources_old2new.clear()
        self.resources_new2old.clear()


    def abort_changes(self):
        if not self.has_changed:
            return

        self._abort_changes()
        self._cleanup()


    def _before_commit(self):
        """This method is called before 'save_changes', and gives a chance
        to the database to check for preconditions, if an error occurs here
        the transaction will be aborted.

        The value returned by this method will be passed to '_save_changes',
        so it can be used to pre-calculate whatever data is needed.
        """
        return None, None, None, [], []


    def _save_changes(self, data):
        worktree = self.worktree

        # 1. Synchronize the handlers and the filesystem
        added = self.added
        for key in added:
            handler = self.cache.get(key)
            if handler and handler.dirty:
                parent_path = dirname(key)
                if not self.fs.exists(parent_path):
                    self.fs.make_folder(parent_path)
                handler.save_state()

        changed = self.changed
        for key in changed:
            handler = self.cache[key]
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
            for key in self.removed:
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

        # 6. Clear state
        changed.clear()
        added.clear()
        self.removed.clear()

        # 7. Catalog
        catalog = self.catalog
        for path in docs_to_unindex:
            catalog.unindex_document(path)
        for resource, values in docs_to_index:
            catalog.index_document(values)
        catalog.save_changes()


    def save_changes(self):
        if not self.has_changed:
            return

        # Prepare for commit, do here the most you can, if something fails
        # the transaction will be aborted
        try:
            data = self._before_commit()
        except Exception:
            log_error('Transaction failed', domain='itools.database')
            try:
                self._abort_changes()
            except Exception:
                log_error('Aborting failed', domain='itools.database')
            self._cleanup()
            raise

        # Commit
        try:
            self._save_changes(data)
        except Exception:
            log_error('Transaction failed', domain='itools.database')
            try:
                self._abort_changes()
            except Exception:
                log_error('Aborting failed', domain='itools.database')
            raise
        finally:
            self._cleanup()


    def create_tag(self, tag_name, message=None):
        worktree = self.worktree
        if message is None:
            message = tag_name
        worktree.git_tag(tag_name, message)


    def reset_to_tag(self, tag_name):
        worktree = self.worktree
        try:
            # Reset the tree to the given tag name
            worktree.git_reset(tag_name)
            # Remove the tag
            worktree.git_remove_tag(tag_name)
        except Exception:
            log_error('Transaction failed', domain='itools.database')
            try:
                self._abort_changes()
            except Exception:
                log_error('Aborting failed', domain='itools.database')
            raise


    def reindex_catalog(self, base_abspath, recursif=True):
        """Reindex the catalog & return nb resources re-indexed
        """
        catalog = self.catalog
        base_resource = self.get_resource(base_abspath, soft=True)
        if base_resource is None:
            return 0
        n = 0
        # Recursif ?
        if recursif:
            for item in base_resource.traverse_resources():
                catalog.index_document(item)
                n += 1
        else:
            # Reindex resource
            catalog.index_document(base_resource)
            n = 1
        # Save catalog if has changes
        if n > 0:
            catalog.save_changes()
        # Ok
        return n


def make_git_database(path, size_min, size_max, fields=None):
    """Create a new empty Git database if the given path does not exists or
    is a folder.

    If the given path is a folder with content, the Git archive will be
    initialized and the content of the folder will be added to it in a first
    commit.
    """
    path = lfs.get_absolute_path(path)
    # Git init
    open_worktree('%s/database' % path, init=True)
    # The catalog
    if fields is None:
        fields = get_register_fields()
    catalog = make_catalog('%s/catalog' % path, fields)
    # Ok
    database = RWDatabase(path, size_min, size_max, catalog=catalog)
    return database



def check_database(target):
    """This function checks whether the database is in a consisitent state,
    this is to say whether a transaction was not brutally aborted and left
    the working directory with changes not committed.

    This is meant to be used by scripts, like 'icms-start.py'
    """
    print('Checking database...')
    cwd = '%s/database' % target

    # Check modifications to the working tree not yet in the index.
    command = ['git', 'ls-files', '-m', '-d', '-o']
    data1 = get_pipe(command, cwd=cwd)

    # Check changes in the index not yet committed.
    command = ['git', 'diff-index', '--cached', '--name-only', 'HEAD']
    data2 = get_pipe(command, cwd=cwd)

    # Everything looks fine
    if len(data1) == 0 and len(data2) == 0:
        return True

    # Something went wrong
    print('The database is not in a consistent state.  Fix it manually with')
    print('the help of Git:')
    print('')
    print('  $ cd %s/database' % target)
    print('  $ git clean -fxd')
    print('  $ git checkout -f')
    print('')
    return False

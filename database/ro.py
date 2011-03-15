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
from sys import getrefcount

# Import from xapian
from xapian import DatabaseError, DatabaseOpeningError

# Import from itools
from itools.core import LRUCache, lazy
from itools.fs import lfs
from itools.git import open_worktree
from itools.handlers import Folder, get_handler_class_by_mimetype
from itools.log import log_warning
from itools.uri import Path
from catalog import Catalog
from registry import get_register_fields



class ReadonlyError(StandardError):
    pass



class ROGitDatabase(object):

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
        self.fs = lfs.open(self.path_data)

        # 4. New interface to Git
        self.worktree = open_worktree(self.path_data)

        # 5. A mapping from key to handler
        self.cache = LRUCache(size_min, size_max, automatic=False)

        # 6. The git cache
        self.git_cache = LRUCache(900, 1100)


    #######################################################################
    # Private API
    #######################################################################
    def _sync_filesystem(self, key):
        """This method checks the state of the key in the cache against the
        filesystem. Synchronizes the state if needed by discarding the
        handler, or raises an error if there is a conflict.

        Returns the handler for the given key if it is still in the cache
        after all the tests, or None otherwise.
        """
        # If the key is not in the cache nothing can be wrong
        handler = self.cache.get(key)
        if handler is None:
            return None

        # (1) Not yet loaded
        if handler.timestamp is None and handler.dirty is None:
            # Removed from the filesystem
            if not self.fs.exists(key):
                self._discard_handler(key)
                return None
            # Everything looks fine
            # FIXME There will be a bug if the file in the filesystem has
            # changed to a different type, so the handler class may not match.
            return handler

        # (2) New handler
        if handler.timestamp is None and handler.dirty is not None:
            # Everything looks fine
            if not self.fs.exists(key):
                return handler
            # Conflict
            error = 'new file in the filesystem and new handler in the cache'
            raise RuntimeError, error

        # (3) Loaded but not changed
        if handler.timestamp is not None and handler.dirty is None:
            # Removed from the filesystem
            if not self.fs.exists(key):
                self._discard_handler(key)
                return None
            # Modified in the filesystem
            mtime = self.fs.get_mtime(key)
            if mtime > handler.timestamp:
                self._discard_handler(key)
                return None
            # Everything looks fine
            return handler

        # (4) Loaded and changed
        if handler.timestamp is not None and handler.dirty is not None:
            # Removed from the filesystem
            if not self.fs.exists(key):
                error = 'a modified handler was removed from the filesystem'
                raise RuntimeError, error
            # Modified in the filesystem
            mtime = self.fs.get_mtime(key)
            if mtime > handler.timestamp:
                error = 'modified in the cache and in the filesystem'
                raise RuntimeError, error
            # Everything looks fine
            return handler


    def _discard_handler(self, key):
        """Unconditionally remove the handler identified by the given key from
        the cache, and invalidate it (and free memory at the same time).
        """
        handler = self.cache.pop(key)
        # Invalidate the handler
        handler.__dict__.clear()


    def _abort_changes(self):
        """To be called to abandon the transaction.
        """
        raise ReadonlyError


    def _cleanup(self):
        """For maintenance operations, this method is automatically called
        after a transaction is committed or aborted.
        """
#       import gc
#       from itools.core import vmsize
#       print 'RODatabase._cleanup (0): % 4d %s' % (len(self.cache), vmsize())
#       print gc.get_count()
        self.make_room()
#       print 'RODatabase._cleanup (1): % 4d %s' % (len(self.cache), vmsize())
#       print gc.get_count()


    #######################################################################
    # Public API
    #######################################################################
    def normalize_key(self, path, __root=Path('/')):
        # Performance is critical so assume the path is already relative to
        # the repository.
        key = __root.resolve(path)
        if key and key[0] == '.git':
            err = "bad '%s' path, access to the '.git' folder is denied"
            raise ValueError, err % path

        return '/'.join(key)


    def push_handler(self, key, handler):
        """Adds the given resource to the cache.
        """
        handler.database = self
        handler.key = key
        # Folders are not stored in the cache
        if isinstance(handler, Folder):
            return
        # Store in the cache
        self.cache[key] = handler


    def make_room(self):
        """Remove handlers from the cache until it fits the defined size.

        Use with caution. If the handlers we are about to discard are still
        used outside the database, and one of them (or more) are modified, then
        there will be an error.
        """
        # Find out how many handlers should be removed
        size = len(self.cache)
        if size < self.cache.size_max:
            return

        # Discard as many handlers as needed
        n = size - self.cache.size_min
        for key, handler in self.cache.iteritems():
            # Skip externally referenced handlers (refcount should be 3:
            # one for the cache, one for the local variable and one for
            # the argument passed to getrefcount).
            refcount = getrefcount(handler)
            if refcount > 3:
                continue
            # Skip modified (not new) handlers
            if handler.dirty is not None:
                continue
            # Discard this handler
            self._discard_handler(key)
            # Check whether we are done
            n -= 1
            if n == 0:
                return


    def has_handler(self, key):
        key = self.normalize_key(key)

        # Synchronize
        handler = self._sync_filesystem(key)
        if handler is not None:
            return True

        # Ask vfs
        return self.fs.exists(key)


    def get_handler_names(self, key):
        key = self.normalize_key(key)

        if self.fs.exists(key):
            names = self.fs.get_names(key)
            return list(names)

        return []


    def get_handler_class(self, key):
        fs = self.fs
        mimetype = fs.get_mimetype(key)

        try:
            return get_handler_class_by_mimetype(mimetype)
        except ValueError:
            log_warning('unknown handler class "{0}"'.format(mimetype))
            if fs.is_file(key):
                from itools.handlers import File
                return File
            elif fs.is_folder(key):
                from itools.handlers import Folder
                return Folder

        raise ValueError


    def _get_handler(self, key, cls=None, soft=False):
        # Synchronize
        handler = self._sync_filesystem(key)
        if handler is not None:
            # Check the class matches
            if cls is not None and not isinstance(handler, cls):
                error = "expected '%s' class, '%s' found"
                raise LookupError, error % (cls, handler.__class__)
            # Cache hit
            self.cache.touch(key)
            return handler

        # Check the resource exists
        if not self.fs.exists(key):
            if soft:
                return None
            raise LookupError, 'the resource "%s" does not exist' % key

        # Folders are not cached
        if self.fs.is_folder(key):
            if cls is None:
                cls = Folder
            folder = cls(key, database=self)
            return folder

        # Cache miss
        if cls is None:
            cls = self.get_handler_class(key)
        # Build the handler and update the cache
        handler = object.__new__(cls)
        self.push_handler(key, handler)

        return handler


    def get_handler(self, key, cls=None, soft=False):
        key = self.normalize_key(key)
        return self._get_handler(key, cls, soft)


    def get_handlers(self, key):
        base = self.normalize_key(key)
        for name in self.get_handler_names(base):
            key = self.fs.resolve2(base, name)
            yield self._get_handler(key)


    def touch_handler(self, key, handler=None):
        """Report a modification of the key/handler to the database.  We must
        pass the handler because of phantoms.
        """
        raise ReadonlyError, 'cannot set handler'


    def set_handler(self, key, handler):
        raise ReadonlyError, 'cannot set handler'


    def del_handler(self, key):
        raise ReadonlyError, 'cannot del handler'


    def copy_handler(self, source, target):
        raise ReadonlyError, 'cannot copy handler'


    def move_handler(self, source, target):
        raise ReadonlyError, 'cannot move handler'


    #######################################################################
    # Layer 1: resources
    #######################################################################
    def remove_resource(self, resource):
         raise ReadonlyError


    def add_resource(self, resource):
         raise ReadonlyError


    def change_resource(self, resource):
         raise ReadonlyError


    def move_resource(self, source, new_path):
         raise ReadonlyError


    def save_changes(self):
        return


    def abort_changes(self):
        return


    def push_phantom(self, key, handler):
        handler.database = self
        handler.key = key


    def is_phantom(self, handler):
        return handler.timestamp is None and handler.dirty is not None


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


    #######################################################################
    # Catalog
    #######################################################################
    @lazy
    def catalog(self):
        path = '%s/catalog' % self.path
        fields = get_register_fields()
        try:
            return Catalog(path, fields, read_only=True)
        except (DatabaseError, DatabaseOpeningError):
            return None

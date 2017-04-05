# -*- coding: UTF-8 -*-
# Copyright (C) 2006, 2011 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2007 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2007 Sylvain Taverne <taverne.sylvain@gmail.com>
# Copyright (C) 2007-2008, 2010-2011 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2010-2011 David Versmisse <versmisse@lil.univ-littoral.fr>
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

# Import from other libraries
from xapian import DatabaseError, DatabaseOpeningError

# Import from itools
from itools.core import LRUCache, lazy
from itools.fs import lfs
from itools.handlers import Folder, get_handler_class_by_mimetype
from itools.log import log_warning
from itools.uri import Path
from catalog import Catalog, _get_xquery, SearchResults
from git import open_worktree
from magic_ import magic_from_file
from metadata import Metadata
from registry import get_register_fields




class ReadonlyError(StandardError):
    pass



class RODatabase(object):

    def __init__(self, path, size_min=4800, size_max=5200, catalog=None):
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
        # 7. Get the catalog
        if catalog:
            self.catalog = catalog
        else:
            self.catalog = self.get_catalog()


    def check_catalog(self):
        lines = self.catalog.logger.get_lines()
        if lines:
            raise ValueError('Catalog should be reindexed')


    def close(self):
        self.catalog.close()

    #######################################################################
    # Private API
    #######################################################################
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
        if type(handler) is Folder:
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
        handler = self.cache.get(key)
        if handler is not None:
            return True

        # Ask vfs
        return self.fs.exists(key)


    def get_handler_names(self, key):
        key = self.normalize_key(key)
        return self.fs.get_names(key)


    def get_mimetype(self, key):
        fs = self.fs
        abspath = fs._resolve_path(key)
        return magic_from_file(abspath)


    def get_handler_class(self, key):
        mimetype = self.get_mimetype(key)
        try:
            return get_handler_class_by_mimetype(mimetype)
        except ValueError:
            log_warning('unknown handler class "{0}"'.format(mimetype))
            if self.fs.is_file(key):
                from itools.handlers import File
                return File
            elif self.fs.is_folder(key):
                from itools.handlers import Folder
                return Folder
        raise ValueError


    def _get_handler(self, key, cls=None, soft=False):
        # Synchronize
        handler = self.cache.get(key)
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
            return Folder(key, database=self)

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


    def copy_handler(self, source, target, exclude_patterns=None):
        raise ReadonlyError, 'cannot copy handler'


    def move_handler(self, source, target):
        raise ReadonlyError, 'cannot move handler'


    #######################################################################
    # Layer 1: resources
    #######################################################################
    _resources_registry = {}

    @classmethod
    def register_resource_class(self, resource_class, format=None):
        if format is None:
            format = resource_class.class_id
        self._resources_registry[format] = resource_class


    @classmethod
    def unregister_resource_class(self, resource_class):
        registry = self._resources_registry
        for class_id, cls in registry.items():
            if resource_class is cls:
                del registry[class_id]


    def get_resource_class(self, class_id):
        if type(class_id) is not str:
            raise TypeError, 'expected byte string, got %s' % class_id

        # Check dynamic models are not broken
        registry = self._resources_registry
        if class_id[0] == '/':
            model = self.get_resource(class_id, soft=True)
            if model is None:
                registry.pop(class_id, None)
                err = 'the resource "%s" does not exist' % class_id
                raise LookupError, err

        # Cache hit
        cls = registry.get(class_id)
        if cls:
            return cls

        # Cache miss: dynamic model
        if class_id[0] == '/':
            cls = model.build_resource_class()
            registry[class_id] = cls
            return cls

        # Cache miss: fallback on mimetype
        if '/' in class_id:
            class_id = class_id.split('/')[0]
            cls = registry.get(class_id)
            if cls:
                return cls

        # Default
        return self._resources_registry['application/octet-stream']


    def get_resource_classes(self):
        registry = self._resources_registry
        for class_id, cls in self._resources_registry.items():
            if class_id[0] == '/':
                model = self.get_resource(class_id, soft=True)
                if model is None:
                    registry.pop(class_id, None)
                    continue

            yield cls


    def get_metadata(self, abspath, soft=False):
        if type(abspath) is str:
            path = abspath[1:]
            abspath = Path(abspath)
        else:
            path = str(abspath)[1:]
        path_to_metadata = '%s.metadata' % path
        return self.get_handler(path_to_metadata, Metadata, soft=soft)


    def get_cls(self, class_id):
        cls = self.get_resource_class(class_id)
        return cls or self.get_resource_class('application/octet-stream')


    def get_resource(self, abspath, soft=False):
        abspath = Path(abspath)
        # Get metadata
        metadata = self.get_metadata(abspath, soft)
        if metadata is None:
            return None
        # Get associated class
        class_id = metadata.format
        cls = self.get_cls(class_id)
        # Ok
        return cls(abspath=abspath, database=self, metadata=metadata)


    def get_resource_from_brain(self, brain):
        cls = self.get_cls(brain.format)
        return cls(abspath=Path(brain.abspath), database=self, brain=brain)


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


    def create_tag(self, tag_name, message=None):
        raise ReadonlyError


    def reset_to_tag(self, tag_name):
        raise ReadonlyError


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
    # Search
    #######################################################################
    def get_catalog(self):
        path = '%s/catalog' % self.path
        fields = get_register_fields()
        return Catalog(path, fields, read_only=True)


    def search(self, query=None, **kw):
        """Launch a search in the catalog.
        """
        xquery = _get_xquery(self.catalog, query, **kw)
        return SearchResults(self, xquery)


    def reindex_catalog(self, base_abspath, recursif=True):
        raise ReadonlyError

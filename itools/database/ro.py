# Copyright (C) 2006, 2011 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2007 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2007-2017 Sylvain Taverne <taverne.sylvain@gmail.com>
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

import datetime
from os.path import splitext
from sys import getrefcount
from fnmatch import fnmatch

# Import from itools
from itools.core import LRUCache
from itools.handlers import File, Folder, get_handler_class_by_mimetype
from itools.uri import Path

# Import from itools.database
from .backends import backends_registry
from .exceptions import ReadonlyError
from .metadata import Metadata
from .registry import get_register_fields


class SearchResults:

    def __init__(self, database, results):
        self.database = database
        self.results = results

    def __len__(self):
        return len(self.results)

    def search(self, query=None, **kw):
        results = self.results.search(query, **kw)
        return SearchResults(self.database, results)

    def get_documents(self, sort_by=None, reverse=False, start=0, size=0):
        return self.results.get_documents(sort_by, reverse, start, size)

    def get_resources(self, sort_by=None, reverse=False, start=0, size=0):
        brains = list(self.get_documents(sort_by, reverse, start, size))
        for brain in brains:
            yield self.database.get_resource_from_brain(brain)


class RODatabase:

    read_only = True
    backend_cls = None

    def __init__(self, path=None, size_min=4800, size_max=5200, backend='lfs'):
        # Init path
        self.path = path
        # Init backend
        self.backend_cls = backends_registry[backend]
        # The "git add" arguments
        self.added = set()
        self.changed = set()
        self.removed = set()
        self.has_changed = False
        # Fields
        self.fields = get_register_fields()
        # init backend
        self.init_backend()
        # A mapping from key to handler
        self.cache = LRUCache(size_min, size_max, automatic=False)

    def init_backend(self):
        self.backend = self.backend_cls(self.path, self.fields, self.read_only)

    @property
    def catalog(self):
        # WARNING: Uses of context.database.catalog is obsolete
        return self.backend.catalog

    def close(self):
        self.backend.close()

    def check_database(self):
        """This function checks whether the database is in a consisitent state,
        this is to say whether a transaction was not brutally aborted and left
        the working directory with changes not committed.

        This is meant to be used by scripts, like 'icms-start.py'
        """
        return True

    #######################################################################
    # With statement
    #######################################################################

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    #######################################################################
    # Private API
    #######################################################################
    def _sync_filesystem(self, key):
        """This method checks the state of the key in the cache against the
        filesystem. Synchronizes the state if needed by discarding the
        handler.
        , or raises an error if there is a conflict.
        Returns the handler for the given key if it is still in the cache
        after all the tests, or None otherwise.
        """
        # If the key is not in the cache nothing can be wrong
        handler = self.cache.get(key)
        if handler is None:
            return None
        # Modified in the filesystem ?
        mtime = self.get_handler_mtime(key)
        if mtime > handler.timestamp:
            # Remove from cache
            self._discard_handler(key)
            return None
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
        #import gc
        #from itools.core import vmsize
        #print 'RODatabase._cleanup (0): % 4d %s' % (len(self.cache), vmsize())
        #print gc.get_count()
        self.make_room()
        #print 'RODatabase._cleanup (1): % 4d %s' % (len(self.cache), vmsize())
        #print gc.get_count()

    #######################################################################
    # Public API
    #######################################################################
    def normalize_key(self, path):
        return self.backend.normalize_key(path)

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
        n = len(self.cache) - self.cache.size_min
        for key, handler in self.cache.items():
            # Stop condition
            if n <= 0:
                break

            # Skip modified (not new) handlers
            if handler.dirty is not None:
                continue

            # Skip externally referenced handlers (refcount should be 3:
            # one for the cache, one for the local variable and one for
            # the argument passed to getrefcount).
            refcount = getrefcount(handler)
            if refcount > 3:
                continue

            # FIXME Do not remove handler from cache if the associated
            # resource is in cache (else we cannot move resource)
            if not key.endswith('.metadata'):
                metadata_key = splitext(key)[0] + '.metadata'
                if metadata_key in self.cache:
                    continue

            # Discard this handler
            n -= 1
            self._discard_handler(key)

    def has_handler(self, key):
        key = self.normalize_key(key)

        # Synchronize
        handler = self._sync_filesystem(key)
        if handler is not None:
            return True

        # Ask backend
        return self.backend.handler_exists(key)

    def save_handler(self, key, handler):
        self.backend.save_handler(key, handler)

    def get_handler_names(self, key):
        key = self.normalize_key(key)
        return self.backend.get_handler_names(key)

    def get_handler_data(self, key, text=False):
        return self.backend.get_handler_data(key, text=text)

    def get_handler_mtime(self, key):
        return self.backend.get_handler_mtime(key)

    def get_mimetype(self, key):
        return self.backend.get_handler_mimetype(key)

    def get_handler_class(self, key):
        mimetype = self.get_mimetype(key)
        cls = get_handler_class_by_mimetype(mimetype, soft=True)
        return cls or File

    def _get_handler(self, key, cls=None, soft=False):
        # Get resource
        if key in self.removed:
            return None
        # Folders are not cached
        if cls is Folder:
            return Folder(key, database=self)
        # Synchronize
        handler = self._sync_filesystem(key)
        if handler is not None:
            # Check the class matches
            if cls is not None and not isinstance(handler, cls):
                raise LookupError(f"expected '{cls}' class, '{handler.__class__}' found")
            # Cache hit
            return handler

        # Check the resource exists
        try:
            data = self.backend.get_handler_data(key)
        except Exception:
            # Do not exists
            if soft:
                return None
            raise LookupError(f'the resource "{key}" does not exist')

        # Cache miss
        if cls is None:
            cls = self.get_handler_class(key)
        # Build the handler and update the cache
        handler = object.__new__(cls)
        # Put handler in cache
        self.push_handler(key, handler)
        self.make_room()
        # Load handler data
        # FIXME We should reset handler state on errors
        try:
            handler.load_state_from_string(data)
            handler.timestamp = self.backend.get_handler_mtime(key)
        except Exception:
            # Remove handler from cache if cannot load it
            self._discard_handler(key)
            raise

        # Ok
        return handler

    def traverse_resources(self):
        return self.backend.traverse_resources()

    def get_nb_metadatas(self):
        # Return how many metadatas files there's in the database
        count = 0
        for file in self.backend.fs.traverse():
            if fnmatch(file, '*.metadata'):
                count += 1
        return count

    def get_handler(self, key, cls=None, soft=False):
        key = self.normalize_key(key)
        return self._get_handler(key, cls, soft)

    def get_handlers(self, key):
        base = self.normalize_key(key)
        for name in self.get_handler_names(base):
            yield self._get_handler(base + '/' + name)

    def touch_handler(self, key, handler):
        """Report a modification of the key/handler to the database.
        """
        assert handler is not None

        # FIXME touch_handler is called at handler loading
        # ro_database is also a rw_database, so it can save data
        key = self.normalize_key(key)
        # Mark the handler as dirty
        handler.dirty = datetime.datetime.now()
        # Do some checks
        if key in self.removed:
            raise ValueError
        # Set database has changed
        self.has_changed = True
        # Set in changed list
        self.changed.add(key)

    def set_handler(self, key, handler):
        raise ReadonlyError('cannot set handler')

    def del_handler(self, key):
        raise ReadonlyError('cannot del handler')

    def copy_handler(self, source, target, exclude_patterns=None):
        raise ReadonlyError('cannot copy handler')

    def move_handler(self, source, target):
        raise ReadonlyError('cannot move handler')

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
        for class_id, cls in list(registry.items()):
            if resource_class is cls:
                del registry[class_id]

    def get_resource_class(self, class_id):
        if type(class_id) is not str:
            raise TypeError(f'expected string, got {class_id}')

        # Check dynamic models are not broken
        registry = self._resources_registry
        if class_id[0] == '/':
            model = self.get_resource(class_id, soft=True)
            if model is None:
                registry.pop(class_id, None)
                raise LookupError(f"the resource '{class_id}' does not exist")

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
        for class_id, cls in list(self._resources_registry.items()):
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
        path_to_metadata = f'{path}.metadata'
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

    #######################################################################
    # API for path
    #######################################################################
    @staticmethod
    def get_basename(path):
        if type(path) is not Path:
            path = Path(path)
        return path.get_name()

    @staticmethod
    def get_path(path):
        if type(path) is not Path:
            path = Path(path)
        return str(path)

    @staticmethod
    def resolve(base, path):
        if type(base) is not Path:
            base = Path(base)
        path = base.resolve(path)
        return str(path)

    @staticmethod
    def resolve2(base, path):
        if type(base) is not Path:
            base = Path(base)
        path = base.resolve2(path)
        return str(path)

    #######################################################################
    # Search
    #######################################################################
    def search(self, query=None, **kw):
        results = self.backend.search(query, **kw)
        return SearchResults(database=self, results=results)

    def reindex_catalog(self, base_abspath, recursif=True):
        raise ReadonlyError


ro_database = RODatabase()

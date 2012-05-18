# -*- coding: UTF-8 -*-
# Copyright (C) 2006, 2009-2010 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2007 Sylvain Taverne <taverne.sylvain@gmail.com>
# Copyright (C) 2007, 2010 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2007-2011 J. David Ibáñez <jdavid.ibp@gmail.com>
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
from sys import getrefcount

# Import from itools
from itools.core import LRUCache
from itools.fs import vfs
from folder import Folder
import messages
from registry import get_handler_class_by_mimetype


class RODatabase(object):
    """The read-only database works as a cache for file handlers.  This is
    the base class for any other handler database.
    """

    # Flag to know whether to commit or not.  This is to avoid superfluos
    # actions by the 'save' and 'abort' methods.
    has_changed = False


    def __init__(self, size_min=4800, size_max=5200, fs=None):
        # A mapping from key to handler
        self.cache = LRUCache(size_min, size_max, automatic=False)
        self.fs = fs or vfs


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
        raise NotImplementedError


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
    def normalize_key(self, key):
        """Resolves and returns the given key to be unique.
        """
        return self.fs.normalize_key(key)


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


    def get_mimetype(self, key):
        return self.fs.get_mimetype(key)


    def get_handler_class(self, key):
        mimetype = self.get_mimetype(key)

        try:
            return get_handler_class_by_mimetype(mimetype)
        except ValueError:
            fs = self.fs
            if fs.is_file(key):
                from file import File
                return File
            elif fs.is_folder(key):
                from folder import Folder
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
        raise NotImplementedError, 'cannot set handler'


    def set_handler(self, key, handler):
        raise NotImplementedError, 'cannot set handler'


    def del_handler(self, key):
        raise NotImplementedError, 'cannot del handler'


    def copy_handler(self, source, target):
        raise NotImplementedError, 'cannot copy handler'


    def move_handler(self, source, target):
        raise NotImplementedError, 'cannot move handler'


    def save_changes(self):
        raise NotImplementedError


    def abort_changes(self):
        if not self.has_changed:
            return

        self._abort_changes()
        self._cleanup()



class RWDatabase(RODatabase):
    """Add write operations and in-memory transactions.
    """

    def __init__(self, size_min=4800, size_max=5200, fs=None):
        super(RWDatabase, self).__init__(size_min, size_max, fs=fs)
        # The state, for transactions
        self.handlers_old2new = {}
        self.handlers_new2old = {}


    def has_handler(self, key):
        key = self.normalize_key(key)

        # Check the state
        if key in self.handlers_new2old:
            return True
        if key in self.handlers_old2new:
            return False

        return super(RWDatabase, self).has_handler(key)


    def get_handler_names(self, key):
        names = super(RWDatabase, self).get_handler_names(key)
        names = set(names)
        fs = self.fs

        # The State
        base = self.normalize_key(key)
        # Removed
        for key in self.handlers_old2new:
            name = fs.get_basename(key)
            if fs.resolve2(base, name) == key:
                names.discard(name)
        # Added
        for key in self.handlers_new2old:
            name = fs.get_basename(key)
            if fs.resolve2(base, name) == key:
                names.add(name)

        # Ok
        return list(names)


    def _get_handler(self, key, cls=None, soft=False):
        # Check state
        if key in self.handlers_new2old:
            handler = self.cache[key]
            # cls is good?
            if cls is not None and not isinstance(handler, cls):
                raise LookupError, ('conflict with a handler of type "%s"' %
                                     handler.__class__)
            return handler

        if key in self.handlers_old2new:
            if soft:
                return None
            raise LookupError, 'the resource "%s" does not exist' % key

        # Ok
        return super(RWDatabase, self)._get_handler(key, cls, soft)


    def set_handler(self, key, handler):
        if type(handler) is Folder:
            raise ValueError, 'unexpected folder (only files can be "set")'

        if handler.key is not None:
            raise ValueError, 'only new files can be added, try to clone first'

        key = self.normalize_key(key)
        if self._get_handler(key, soft=True) is not None:
            raise RuntimeError, messages.MSG_URI_IS_BUSY % key

        self.push_handler(key, handler)
        self.handlers_new2old[key] = None


    def del_handler(self, key):
        key = self.normalize_key(key)

        # Check the handler has been added
        hit = False
        n = len(key)
        for k in self.handlers_new2old.keys():
            if k.startswith(key) and (len(k) == n or k[n] == '/'):
                hit = True
                self._discard_handler(k)
                k = self.handlers_new2old.pop(k)
                if k:
                    self.handlers_old2new[k] = None
        if hit:
            return

        # Check the handler has been removed
        if key in self.handlers_old2new:
            raise LookupError, 'resource already removed'

        # Synchronize
        self._sync_filesystem(key)
        if not self.fs.exists(key):
            raise LookupError, 'resource does not exist'

        # Clean the cache
        if key in self.cache:
            self._discard_handler(key)

        # Mark for removal
        self.handlers_old2new[key] = None


    def touch_handler(self, key, handler=None):
        key = self.normalize_key(key)
        handler = self._get_handler(key)

        if handler.dirty is None:
            # Load the handler if needed
            if handler.timestamp is None:
                handler.load_state()
            # Mark the handler as dirty
            handler.dirty = datetime.now()
            # Update database state
            self.handlers_new2old[key] = key
            self.handlers_old2new[key] = key


    def copy_handler(self, source, target):
        source = self.normalize_key(source)
        target = self.normalize_key(target)
        if source == target:
            return

        # Check the target is free
        if self._get_handler(target, soft=True) is not None:
            raise RuntimeError, messages.MSG_URI_IS_BUSY % target

        handler = self._get_handler(source)
        # Case 1: folder
        if type(handler) is Folder:
            fs = self.fs
            for name in handler.get_handler_names():
                self.copy_handler(fs.resolve2(source, name),
                                  fs.resolve2(target, name))
            return

        # Case 2: file
        handler = handler.clone()
        # Update the state
        self.push_handler(target, handler)
        self.handlers_new2old[target] = None


    def move_handler(self, source, target):
        # TODO This method can be optimized further
        source = self.normalize_key(source)
        target = self.normalize_key(target)
        if source == target:
            return

        # Check the target is free
        if self._get_handler(target, soft=True) is not None:
            raise RuntimeError, messages.MSG_URI_IS_BUSY % target

        handler = self._get_handler(source)
        if type(handler) is Folder:
            # Folder
            fs = self.fs
            for name in handler.get_handler_names():
                self.move_handler(fs.resolve2(source, name),
                                  fs.resolve2(target, name))
            # Update double dict
            self.handlers_old2new[source] = None
        else:
            # Load if needed
            if handler.timestamp is None and handler.dirty is None:
                handler.load_state()
            # File
            handler = self.cache.pop(source)
            self.push_handler(target, handler)
            handler.timestamp = None
            handler.dirty = datetime.now()
            # Update double dict
            source = self.handlers_new2old.pop(source, source)
            if source:
                self.handlers_old2new[source] = target
            self.handlers_new2old[target] = source


    #######################################################################
    # API / Transactions
    @property
    def has_changed(self):
        return bool(self.handlers_old2new) or bool(self.handlers_new2old)


    def _abort_changes(self):
        cache = self.cache
        for target, source in self.handlers_new2old.iteritems():
            # Case 1: changed
            if source == target:
                cache[target].abort_changes()
            # Case 2: added or moved
            else:
                self._discard_handler(target)

        # Reset state
        self.handlers_old2new.clear()
        self.handlers_new2old.clear()


    def _save_changes(self):
        cache = self.cache

        sources = self.handlers_old2new.keys()
        sources.sort(reverse=True)
        while True:
            something = False
            retry = []
            for source in sources:
                target = self.handlers_old2new[source]
                # Case 1: removed
                if target is None:
                    self.fs.remove(source)
                    something = True
                # Case 2: changed
                elif source == target:
                    # Save the handler's state
                    handler = cache[source]
                    handler.save_state()
                    # Update timestamp
                    handler.timestamp = self.fs.get_mtime(source)
                    handler.dirty = None
                    something = True
                # Case 3: moved (TODO Optimize)
                else:
                    handler = cache[target]
                    try:
                        # Only save_state_to can raise an OSError
                        # So we try to save the handler before remove it.
                        # Add
                        handler.save_state_to(target)
                    except OSError:
                        retry.append(source)
                    else:
                        # Remove
                        self.fs.remove(source)
                        # Update timestamp
                        handler.timestamp = self.fs.get_mtime(target)
                        handler.dirty = None
                        something = True

            # Case 1: done
            if not retry:
                break

            # Case 2: Try again
            if something:
                sources = retry
                continue

            # Error
            error = 'unable to complete _save_changes'
            raise RuntimeError, error

        # Case 4: added
        for target, source in self.handlers_new2old.iteritems():
            if source is None:
                handler = cache[target]
                handler.save_state_to(target)
                # Update timestamp
                handler.timestamp = self.fs.get_mtime(target)
                handler.dirty = None

        # Reset the state
        self.handlers_old2new.clear()
        self.handlers_new2old.clear()


    def save_changes(self):
        if not self.has_changed:
            return

        # Commit
        try:
            self._save_changes()
        except Exception:
            self._abort_changes()
            raise
        finally:
            self._cleanup()



# A built-in database for handler operations
ro_database = RODatabase()

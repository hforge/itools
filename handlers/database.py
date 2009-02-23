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
from datetime import datetime
from logging import getLogger
from os import fdopen
from sys import getrefcount
from tempfile import mkstemp
from thread import allocate_lock, get_ident

# Import from itools
from itools.uri import get_reference, get_absolute_reference, Path
from itools.vfs import vfs
from itools.vfs import cwd, READ, WRITE, READ_WRITE, APPEND
from folder import Folder
import messages
from registry import get_handler_class


logger = getLogger('data')


###########################################################################
# Doubly-linked list, used to build a LRU (Least Recently Used) Cache
# http://en.wikipedia.org/wiki/Cache_algorithms
# TODO Implement in C with the Glib
###########################################################################

class DNode(object):
    __slots__ = ['prev', 'next', 'data']

    def __init__(self, data):
        self.data = data


class DList(object):
    __slots__ = ['first', 'last', 'size']

    def __init__(self):
        self.first = None
        self.last = None
        self.size = 0


    def append(self, data):
        # The node
        node = DNode(data)
        node.prev = self.last
        node.next = None

        if self.first is None:
            # size = 0
            self.first = node
        else:
            # size > 0
            self.last.next = node

        self.last = node

        # Ok
        self.size += 1
        return node


    def remove(self, node):
        if node.prev is None:
            self.first = node.next
        else:
            node.prev.next = node.next

        if node.next is None:
            self.last = node.prev
        else:
            node.next.prev = node.prev

        # Ok
        self.size -= 1


    def __len__(self):
        return self.size


    def __iter__(self):
        node = self.first
        while node is not None:
            yield node.data
            node = node.next


###########################################################################
# Exceptions
###########################################################################
class ReadOnlyError(RuntimeError):
    pass


###########################################################################
# Abstract database (defines the API)
###########################################################################

class BaseDatabase(object):

    def _before_commit(self):
        """This method is called before 'save_changes', and gives a chance
        to the database to check for preconditions, if an error occurs here
        the transaction will be aborted.

        The value returned by this method will be passed to '_save_changes',
        so it can be used to pre-calculate whatever data is needed.
        """
        return None


    def _save_changes(self, data):
        raise NotImplementedError


    def _abort_changes(self):
        raise NotImplementedError


    def _cleanup(self):
        """For maintenance operations, this method is automatically called
        after a transaction is commited or aborted.
        """


    #######################################################################
    # Public API
    def save_changes(self):
        # Prepare for commit, do here the most you can, if something fails
        # the transaction will be aborted
        try:
            data = self._before_commit()
        except:
            database.abort_changes()
            raise

        # Commit for real
        self._save_changes(data)
        self._cleanup()


    def abort_changes(self):
        self._abort_changes()
        self._cleanup()



###########################################################################
# Read Only Database
###########################################################################

class RODatabase(BaseDatabase):
    """The read-only database works as a cache for file handlers.
    """

    def __init__(self, size=5000):
        # A mapping from URI to handler
        self.cache = {}
        # The maximum desired size for the cache
        self.size = size
        # The list of URIs sorted by access time to the associated handler
        self.queue = DList()
        self.queue_idx = {}


    #######################################################################
    # Cache API
    def _discard_handler(self, uri):
        """Unconditionally remove the handler identified by the given URI from
        the cache, and invalidate it (and free memory at the same time).
        """
        handler = self.cache.pop(uri)
        node = self.queue_idx.pop(uri)
        self.queue.remove(node)
        # Invalidate the handler
        handler.__dict__.clear()


    def _sync_filesystem(self, uri):
        """This method checks the state of the uri in the cache against the
        filesystem.  Synchronizes the state if needed by discarding the
        handler, or raises an error if there is a conflict.

        Returns the handler for the given uri if it is still in the cache
        after all the tests, or None otherwise.
        """
        # If the uri is not in the cache nothing can be wrong
        handler = self.cache.get(uri)
        if handler is None:
            return None

        # (1) Not yet loaded
        if handler.timestamp is None and handler.dirty is None:
            # Removed from the filesystem
            if not vfs.exists(uri):
                self._discard_handler(uri)
                return None
            # Everything looks fine
            # FIXME There will be a bug if the file in the filesystem has
            # changed to a different type, so the handler class may not match.
            return handler

        # (2) New handler
        if handler.timestamp is None and handler.dirty is not None:
            # Everything looks fine
            if not vfs.exists(uri):
                return handler
            # Conflict
            error = 'new file in the filesystem and new handler in the cache'
            raise RuntimeError, error

        # (3) Loaded but not changed
        if handler.timestamp is not None and handler.dirty is None:
            # Removed from the filesystem
            if not vfs.exists(uri):
                self._discard_handler(uri)
                return None
            # Modified in the filesystem
            mtime = vfs.get_mtime(uri)
            if mtime > handler.timestamp:
                self._discard_handler(uri)
                return None
            # Everything looks fine
            return handler

        # (4) Loaded and changed
        if handler.timestamp is not None and handler.dirty is not None:
            # Removed from the filesystem
            if not vfs.exists(uri):
                error = 'a modified handler was removed from the filesystem'
                raise RuntimeError, error
            # Modified in the filesystem
            mtime = vfs.get_mtime(uri)
            if mtime > handler.timestamp:
                error = 'modified in the cache and in the filesystem'
                raise RuntimeError, error
            # Everything looks fine
            return handler


    def discard_handler(self, uri):
        """Removes the handler identified by the given uri from the cache.
        If the handler has been modified, an exception is raised.
        """
        # Check the handler has not been modified
        handler = self.cache[uri]
        if handler.dirty is not None:
            raise RuntimeError, 'cannot discard a modified handler'
        # Discard the handler
        self._discard_handler(uri)


    def touch_handler(self, uri):
        """Put the handler at the top of the queue.
        """
        queue = self.queue
        # Remove
        node = self.queue_idx[uri]
        queue.remove(node)
        # Add
        node = queue.append(uri)
        self.queue_idx[uri] = node


    def push_handler(self, uri, handler):
        """Adds the given resource to the cache.
        """
        handler.database = self
        handler.uri = uri
        # Folders are not stored in the cache
        if isinstance(handler, Folder):
            return
        # Store in the cache
        self.cache[uri] = handler
        node = self.queue.append(uri)
        self.queue_idx[uri] = node


    def make_room(self):
        """Remove handlers from the cache until it fits the defined size.

        Use with caution.  If the handlers we are about to discard are still
        used outside the database, and one of them (or more) are modified,
        then there will be an error.
        """
        # Find out how many handlers should be removed
        queue = self.queue
        n = len(queue) - self.size
        if n <= 0:
            return

        # Discard as many handlers as needed
        cache = self.cache
        for uri in queue:
            handler = cache[uri]
            # Skip externally referenced handlers (refcount should be 3:
            # one for the cache, one for the local variable and one for
            # the argument passed to getrefcount).
            refcount = getrefcount(handler)
            if refcount > 3:
                continue
            # Skip modified handlers
            if handler.dirty is not None:
                continue
            # Discard this handler
            self._discard_handler(uri)
            # Check whether we are done
            n -= 1
            if n == 0:
                return


    #######################################################################
    # Database API
    def has_handler(self, reference):
        uri = cwd.get_reference(reference)

        # Syncrhonize
        handler = self._sync_filesystem(uri)
        if handler is not None:
            return True

        # Check the file system
        if not vfs.exists(uri):
            return False

        # Empty folders do not exist
        if vfs.is_folder(uri):
            return bool(vfs.get_names(uri))

        return True


    def get_handler_names(self, reference):
        uri = cwd.get_reference(reference)

        if vfs.exists(uri):
            names = vfs.get_names(uri)
            return list(names)

        return []


    def get_handler(self, reference, cls=None):
        uri = cwd.get_reference(reference)

        # Syncrhonize
        handler = self._sync_filesystem(uri)
        if handler is not None:
            # Check the class matches
            if cls is not None and not isinstance(handler, cls):
                error = "expected '%s' class, '%s' found"
                raise LookupError, error % (cls, handler.__class__)
            # Cache hit
            self.touch_handler(uri)
            return handler

        # Check the resource exists
        if not vfs.exists(uri):
            raise LookupError, 'the resource "%s" does not exist' % uri

        # Folders are not cached
        if vfs.is_folder(uri):
            if cls is None:
                cls = Folder
            folder = cls(uri)
            folder.database = self
            return folder

        # Cache miss
        if cls is None:
            cls = get_handler_class(uri)
        # Build the handler and update the cache
        handler = object.__new__(cls)
        self.push_handler(uri, handler)

        return handler


    def get_handlers(self, reference):
        reference = cwd.get_reference(reference)
        for name in vfs.get_names(reference):
            ref = reference.resolve2(name)
            yield self.get_handler(ref)


    #######################################################################
    # Write API
    def set_handler(self, reference, handler):
        raise ReadOnlyError, 'cannot set handler'


    def del_handler(self, reference):
        raise ReadOnlyError, 'cannot del handler'


    def copy_handler(self, source, target):
        raise ReadOnlyError, 'cannot copy handler'


    def move_handler(self, source, target):
        raise ReadOnlyError, 'cannot move handler'


    def safe_make_file(self, reference):
        raise ReadOnlyError, 'cannot make file'


    def safe_make_folder(self, reference):
        raise ReadOnlyError, 'cannot make folder'


    def safe_remove(self, reference):
        raise ReadOnlyError, 'cannot remove'


    def safe_open(self, reference, mode=None):
        if mode in (WRITE, READ_WRITE, APPEND):
            raise ReadOnlyError, 'cannot open file for writing'

        return vfs.open(reference, READ)


    def _cleanup(self):
        self.make_room()


###########################################################################
# Read/Write Database (in memory transactions)
###########################################################################
class RWDatabase(RODatabase):

    def __init__(self):
        RODatabase.__init__(self)
        # The state, for transactions
        self.changed = set()
        self.added = set()
        self.removed = set()


    def has_handler(self, reference):
        reference = cwd.get_reference(reference)
        # Check the state
        if reference in self.added:
            return True
        if reference in self.removed:
            return False

        return RODatabase.has_handler(self, reference)


    def get_handler_names(self, reference):
        names = RODatabase.get_handler_names(self, reference)

        # The State
        uri = cwd.get_reference(reference)
        names = set(names)
        removed = [ str(x.path[-1]) for x in self.removed
                    if uri.resolve2(str(x.path[-1])) == x ]
        added = [ str(x.path[-1]) for x in self.added
                  if uri.resolve2(str(x.path[-1])) == x ]
        names = names - set(removed) | set(added)

        # Ok
        return list(names)


    def get_handler(self, reference, cls=None):
        reference = cwd.get_reference(reference)

        # Check state
        if reference in self.added:
            handler = self.cache[reference]
            # cls is good?
            if cls is not None and not isinstance(handler, cls):
                raise LookupError, ('conflict with a handler of type "%s"' %
                                     handler.__class__)
            return handler

        if reference in self.removed:
            raise LookupError, 'the resource "%s" does not exist' % reference

        # Ok
        return RODatabase.get_handler(self, reference, cls=cls)


    def set_handler(self, reference, handler):
        if isinstance(handler, Folder):
            raise ValueError, 'unexpected folder (only files can be "set")'

        if handler.uri is not None:
            raise ValueError, ('only new files can be added, '
                               'try to clone first')

        if self.has_handler(reference):
            raise RuntimeError, messages.MSG_URI_IS_BUSY % reference

        reference = get_absolute_reference(reference)
        self.push_handler(reference, handler)
        self.added.add(reference)


    def del_handler(self, reference):
        reference = cwd.get_reference(reference)

        if reference in self.added:
            self._discard_handler(reference)
            self.added.remove(reference)
            return

        # Check the handler actually exists
        if reference in self.removed:
            raise LookupError, 'resource already removed'
        if not vfs.exists(reference):
            raise LookupError, 'resource does not exist'

        # Clean the cache
        if reference in self.cache:
            self._discard_handler(reference)

        # Mark for removal
        self.removed.add(reference)


    def copy_handler(self, source, target):
        source = get_absolute_reference(source)
        target = get_absolute_reference(target)
        if source == target:
            return

        # Check the target is free
        if self.has_handler(target):
            raise RuntimeError, messages.MSG_URI_IS_BUSY % target

        handler = self.get_handler(source)
        if isinstance(handler, Folder):
            # Folder
            for name in handler.get_handler_names():
                self.copy_handler(source.resolve2(name),
                                  target.resolve2(name))
        else:
            # File
            handler = handler.clone()
            # Update the state
            self.push_handler(target, handler)
            self.added.add(target)


    def move_handler(self, source, target):
        # TODO This method can be optimized further
        source = get_absolute_reference(source)
        target = get_absolute_reference(target)
        if source == target:
            return

        # Check the target is free
        if self.has_handler(target):
            raise RuntimeError, messages.MSG_URI_IS_BUSY % target

        handler = self.get_handler(source)
        if isinstance(handler, Folder):
            # Folder
            for name in handler.get_handler_names():
                self.move_handler(source.resolve2(name),
                                  target.resolve2(name))
        else:
            # Load if needed
            if handler.timestamp is None and handler.dirty is None:
                handler.load_state()
            # File
            handler = self.cache.pop(uri)
            node = self.queue_idx.pop(uri)
            self.queue.remove(node)
            self.push_handler(target, handler)
            handler.timestamp = None
            handler.dirty = datetime.now()
            # Add to target
            self.added.add(target)
            if source in self.added:
                self.added.remove(source)
            elif source in self.changed:
                self.changed.remove(source)
                self.removed.add(source)
            else:
                self.removed.add(source)


    #######################################################################
    # API / Safe VFS operations (not really safe)
    def safe_make_file(self, reference):
        return vfs.make_file(reference)


    def safe_make_folder(self, reference):
        return vfs.make_folder(reference)


    def safe_remove(self, reference):
        return vfs.remove(reference)


    def safe_open(self, reference, mode=None):
        return vfs.open(reference, mode)


    #######################################################################
    # API / Transactions
    def _abort_changes(self):
        cache = self.cache
        # Added handlers
        for uri in self.added:
            self._discard_handler(uri)
        # Changed handlers
        for uri in self.changed:
            cache[uri].abort_changes()
        # Reset state
        self.changed.clear()
        self.added.clear()
        self.removed.clear()


    def _save_changes(self, data):
        cache = self.cache
        try:
            # Save changed handlers
            for uri in self.changed:
                # Save the handler's state
                handler = cache[uri]
                handler.save_state()
                # Update timestamp
                handler.timestamp = vfs.get_mtime(uri)
                handler.dirty = None
            # Remove handlers
            for uri in self.removed:
                self.safe_remove(uri)
            # Add new handlers
            for uri in self.added:
                handler = cache[uri]
                handler.save_state_to(uri)
                # Update timestamp
                handler.timestamp = vfs.get_mtime(uri)
                handler.dirty = None
        except:
            # Rollback
            self.abort_changes()
            raise

        # Reset the state
        self.changed.clear()
        self.added.clear()
        self.removed.clear()



###########################################################################
# The Solid Database (bullet-proof transactions)
###########################################################################

# The database states
READY = 0
TRANSACTION_PHASE1 = 1
TRANSACTION_PHASE2 = 2

# Map from handler path to temporal file
thread_lock = allocate_lock()
_tmp_maps = {}

def get_tmp_map():
    ident = get_ident()
    thread_lock.acquire()
    try:
        tmp_map = _tmp_maps.setdefault(ident, {})
    finally:
        thread_lock.release()

    return tmp_map


class SolidDatabase(RWDatabase):

    def __init__(self, commit):
        RWDatabase.__init__(self)
        # The commit, for safe transactions
        if not isinstance(commit, Path):
            commit = Path(commit)
        self.commit = str(commit)
        self.commit_log = str(commit.resolve2('log'))


    #######################################################################
    # API / Safe VFS operations
    def safe_make_file(self, reference):
        tmp_map = get_tmp_map()
        if reference in tmp_map:
            tmp_path = tmp_map[reference]
            return vfs.open(tmp_path, WRITE)

        tmp_file, tmp_path = mkstemp(dir=self.commit)
        tmp_path = get_reference(tmp_path)
        log = open(self.commit_log, 'a+b')
        try:
            log.write('+%s#%s\n' % (reference, tmp_path))
        finally:
            log.close()
        return fdopen(tmp_file, 'w')


    def safe_make_folder(self, reference):
        log = open(self.commit_log, 'a+b')
        try:
            log.write('+%s\n' % reference)
        finally:
            log.close()

        return vfs.make_folder(reference)


    def safe_remove(self, reference):
        log = open(self.commit_log, 'a+b')
        try:
            log.write('-%s\n' % reference)
        finally:
            log.close()


    def safe_open(self, reference, mode=None):
        if mode == WRITE:
            tmp_map = get_tmp_map()
            if reference in tmp_map:
                tmp_path = tmp_map[reference]
                return vfs.open(tmp_path, mode)

            tmp_file, tmp_path = mkstemp(dir=self.commit)
            tmp_path = get_reference(tmp_path)
            tmp_map[reference] = tmp_path
            log = open(self.commit_log, 'a+b')
            try:
                log.write('~%s#%s\n' % (reference, tmp_path))
            finally:
                log.close()
            return fdopen(tmp_file, 'w')
        elif mode == READ_WRITE:
            raise NotImplementedError
        elif mode == APPEND:
            tmp_map = get_tmp_map()
            if reference in tmp_map:
                tmp_path = tmp_map[reference]
                return vfs.open(tmp_path, mode)

            tmp_file, tmp_path = mkstemp(dir=self.commit)
            tmp_path = get_reference(tmp_path)
            tmp_map[reference] = tmp_path
            log = open(self.commit_log, 'a+b')
            try:
                log.write('>%s#%s\n' % (reference, tmp_path))
            finally:
                log.close()
            return fdopen(tmp_file, 'w')
        # READ by default
        return vfs.open(reference, mode)


    #######################################################################
    # API / Transactions
    def get_state(self):
        commit = self.commit
        if vfs.exists(commit):
            if vfs.exists('%s/done' % commit):
                return TRANSACTION_PHASE2
            return TRANSACTION_PHASE1

        return READY


    def _save_changes(self, data):
        # 1. Start
        vfs.make_file(self.commit_log)

        # State
        changed = self.changed
        added = self.added
        removed = self.removed

        # Write changes to disk
        cache = self.cache
        try:
            # Save changed handlers
            for uri in changed:
                # Save the handler's state
                handler = cache[uri]
                handler.save_state()
            # Remove handlers
            for uri in removed:
                self.safe_remove(uri)
            # Add new handlers
            for uri in added:
                handler = cache[uri]
                handler.save_state_to(uri)
        except:
            # Rollback the changes in memory
            self.abort_changes()
            # Rollback the changes in disk
            self.rollback()
            get_tmp_map().clear()
            # Log
            logger.error('Transaction failed.')
            raise
        else:
            get_tmp_map().clear()

        # Reset the state
        self.changed = set()
        self.added = set()
        self.removed = set()

        # 2. Transaction commited successfully.
        # Once we pass this point, we will save the changes permanently,
        # whatever happens (e.g. if there is a current failover we will
        # continue this process to finish the work).
        vfs.make_file('%s/done' % self.commit)
        self.save_changes_forever()

        # 3. Update timestamps
        for uri in changed:
            handler = cache[uri]
            handler.timestamp = vfs.get_mtime(uri)
            handler.dirty = None
        for uri in added:
            handler = cache[uri]
            handler.timestamp = vfs.get_mtime(uri)
            handler.dirty = None

        # 4. Log
        logger.info('Transaction done.')


    def rollback(self):
        """This method is to be called when something bad happens while we
        are saving the changes to disk. For example if somebody pushes the
        reset button of the computer.

        This method will remove the changes done so far and restore the
        database state before the transaction started.
        """
        vfs.remove(self.commit)


    def save_changes_forever(self):
        """This method makes the transaction changes permanent.

        If it fails, for example if the computer crashes, it must be
        safe call this method again so it finishes the work.
        """
        # Save the transaction
        log = open(self.commit_log)
        try:
            for line in log.readlines():
                if line[-1] == '\n':
                    line = line[:-1]
                else:
                    raise RuntimeError, 'log file corrupted'
                action, line = line[0], line[1:]
                if action == '-':
                    if vfs.exists(line):
                        vfs.remove(line)
                elif action == '+':
                    dst, src = line.rsplit('#', 1)
                    vfs.move(src, dst)
                elif action == '~':
                    dst, src = line.rsplit('#', 1)
                    if vfs.exists(src):
                        vfs.remove(dst)
                        vfs.move(src, dst)
                elif action == '>':
                    dst, src = line.rsplit('#', 1)
                    data = vfs.open(src).read()
                    file = vfs.open(dst, APPEND)
                    try:
                        file.write(data)
                    finally:
                        file.close()
                else:
                    raise RuntimeError, 'log file corrupted'
        finally:
            log.close()

        # We are done. Remove the commit.
        vfs.remove(self.commit)


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
from os.path import dirname
from subprocess import CalledProcessError
from sys import getrefcount

# Import from itools
from itools.core import LRUCache, send_subprocess, freeze
from itools.fs import vfs, lfs
from itools.uri import Path
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


    def _rollback(self):
        """To be called when something goes wrong while saving the changes.
        """
        raise NotImplementedError


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
            if fs.is_file(key):
                from file import File
                return File
            elif fs.is_folder(key):
                from folder import Folder
                return Folder

        raise ValueError


    def get_handler(self, key, cls=None):
        key = self.normalize_key(key)

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


    def get_handlers(self, key):
        base = self.normalize_key(key)
        for name in self.get_handler_names(base):
            key = self.fs.resolve2(base, name)
            yield self.get_handler(key)


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
        if not self.has_changed:
            return

        # Prepare for commit, do here the most you can, if something fails
        # the transaction will be aborted
        try:
            data = self._before_commit()
        except:
            self._abort_changes()
            self._cleanup()
            raise

        # Commit
        try:
            self._save_changes(data)
        except Exception:
            self._rollback()
            self._abort_changes()
            raise
        finally:
            self._cleanup()


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


    def get_handler(self, key, cls=None):
        key = self.normalize_key(key)

        # Check state
        if key in self.handlers_new2old:
            handler = self.cache[key]
            # cls is good?
            if cls is not None and not isinstance(handler, cls):
                raise LookupError, ('conflict with a handler of type "%s"' %
                                     handler.__class__)
            return handler

        if key in self.handlers_old2new:
            raise LookupError, 'the resource "%s" does not exist' % key

        # Ok
        return super(RWDatabase, self).get_handler(key, cls=cls)


    def set_handler(self, key, handler):
        if isinstance(handler, Folder):
            raise ValueError, 'unexpected folder (only files can be "set")'

        if handler.key is not None:
            raise ValueError, 'only new files can be added, try to clone first'

        key = self.normalize_key(key)
        if self.has_handler(key):
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
        handler = self.get_handler(key)

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
        if self.has_handler(target):
            raise RuntimeError, messages.MSG_URI_IS_BUSY % target

        handler = self.get_handler(source)
        if isinstance(handler, Folder):
            # Folder
            fs = self.fs
            for name in handler.get_handler_names():
                self.copy_handler(fs.resolve2(source, name),
                                  fs.resolve2(target, name))
        else:
            # File
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
        if self.has_handler(target):
            raise RuntimeError, messages.MSG_URI_IS_BUSY % target

        handler = self.get_handler(source)
        if isinstance(handler, Folder):
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


    def _save_changes(self, data):
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



###########################################################################
# The Git Database
###########################################################################
class ROGitDatabase(RODatabase):

    def __init__(self, path, size_min=4800, size_max=5200):
        if not lfs.is_folder(path):
            raise ValueError, '"%s" should be a folder, but it is not' % path

        # Initialize the database, but chrooted
        fs = lfs.open(path)
        super(ROGitDatabase, self).__init__(size_min, size_max, fs=fs)

        # Keep the path close, to be used by 'send_subprocess'
        self.path = '%s/' % fs.path


    def normalize_key(self, path, __root=Path('/')):
        # Performance is critical so assume the path is already relative to
        # the repository.
        key = __root.resolve(path)
        if key and key[0] == '.git':
            err = "bad '%s' path, access to the '.git' folder is denied"
            raise ValueError, err % path

        return '/'.join(key)


    def push_phantom(self, key, handler):
        handler.database = self
        handler.key = key


    def is_phantom(self, handler):
        return handler.timestamp is None and handler.dirty is not None


    def get_diff(self, revision):
        cmd = ['git', 'show', revision, '--pretty=format:%an%n%at%n%s']
        data = send_subprocess(cmd, path=self.path)
        lines = data.splitlines()

        ts = int(lines[1])
        return {
            'author_name': lines[0],
            'author_date': datetime.fromtimestamp(ts),
            'subject': lines[2],
            'diff': '\n'.join(lines[2:])}


    def get_files_affected(self, revisions):
        """Get the unordered set of files affected by a list of revisions.
        """
        cmd = ['git', 'show', '--numstat', '--pretty=format:'] + revisions
        data = send_subprocess(cmd, path=self.path)
        lines = data.splitlines()
        files = set()
        for line in lines:
            if not line:
                continue
            before, after, filename = line.split('\t')
            files.add(filename)
        return freeze(files)


    def get_stats(self, from_, to=None, paths=[]):
        if to is None:
            cmd = ['git', 'show', '--pretty=format:', '--stat', from_]
        else:
            cmd = ['git', 'diff', '--stat', from_, to]

        if paths:
            cmd.append('--')
            cmd.extend(paths)
        return send_subprocess(cmd, path=self.path)


    def get_diff_between(self, from_, to='HEAD', paths=[]):
        """Get the diff of the given path from the given commit revision to
        HEAD.

        If "stat" is True, get a diff stat only.
        """
        cmd = ['git', 'diff', from_, to]
        if paths:
            cmd.append('--')
            cmd.extend(paths)
        return send_subprocess(cmd, path=self.path)


    def get_blob(self, revision, path):
        """Get the file contents located at the given path after the given
        commit revision has been committed.
        """
        cmd = ['git', 'show', '%s:%s' % (revision, path)]
        return send_subprocess(cmd, path=self.path)



class GitDatabase(ROGitDatabase):

    def __init__(self, path, size_min, size_max):
        super(GitDatabase, self).__init__(path, size_min, size_max)

        # The "git add" arguments
        self.added = set()
        self.changed = set()
        self.has_changed = False


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
        return self.fs.exists(key)


    def get_handler(self, key, cls=None):
        key = self.normalize_key(key)

        # A hook to handle the new directories
        base = key + '/'
        n = len(base)
        for f_key in self.added:
            if f_key[:n] == base:
                if cls is None:
                    cls = Folder
                return cls(key, database=self)

        # The other files
        return super(GitDatabase, self).get_handler(key, cls)


    def set_handler(self, key, handler):
        if isinstance(handler, Folder):
            raise ValueError, 'unexpected folder (only files can be "set")'

        if handler.key is not None:
            raise ValueError, 'only new files can be added, try to clone first'

        key = self.normalize_key(key)
        if self.has_handler(key):
            raise RuntimeError, messages.MSG_URI_IS_BUSY % key

        self.push_handler(key, handler)
        self.added.add(key)
        # Changed
        self.has_changed = True


    def del_handler(self, key):
        key = self.normalize_key(key)

        # Case 1: file
        handler = self.get_handler(key)
        if not isinstance(handler, Folder):
            self._discard_handler(key)
            if key in self.added:
                self.added.remove(key)
            else:
                self.changed.discard(key)
                self.fs.remove(key)
            # Changed
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

        if self.fs.exists(key):
            self.fs.remove(key)

        # Changed
        self.has_changed = True


    def touch_handler(self, key, handler=None):
        key = self.normalize_key(key)

        # Useful for the phantoms
        if handler is None:
            handler = self.get_handler(key)

        # The phantoms become real files
        if self.is_phantom(handler):
            self.cache[key] = handler
            self.added.add(key)
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
            self.has_changed = True


    def get_handler_names(self, key):
        key = self.normalize_key(key)

        # On the filesystem
        names = super(GitDatabase, self).get_handler_names(key)
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


    def copy_handler(self, source, target):
        source = self.normalize_key(source)
        target = self.normalize_key(target)

        # The trivial case
        if source == target:
            return

        # Check the target is free
        if self.has_handler(target):
            raise RuntimeError, messages.MSG_URI_IS_BUSY % target

        handler = self.get_handler(source)

        # Folder
        if isinstance(handler, Folder):
            fs = self.fs
            for name in handler.get_handler_names():
                self.copy_handler(fs.resolve2(source, name),
                                  fs.resolve2(target, name))
        # File
        else:
            handler = handler.clone()
            self.push_handler(target, handler)
            self.added.add(target)

        # Changed
        self.has_changed = True


    def move_handler(self, source, target):
        source = self.normalize_key(source)
        target = self.normalize_key(target)

        # The trivial case
        if source == target:
            return

        # Check the target is free
        if self.has_handler(target):
            raise RuntimeError, messages.MSG_URI_IS_BUSY % target

        # Go
        fs = self.fs
        cache = self.cache

        # Case 1: file
        handler = self.get_handler(source)
        if not isinstance(handler, Folder):
            if source in self.added:
                self.added.remove(source)
            else:
                fs.move(source, target)
                if source in self.changed:
                    self.changed.remove(source)

            # Update the cache
            del cache[source]
            self.push_handler(target, handler)
            self.added.add(target)
            # Changed
            self.has_changed = True
            return

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
            fs.move(source, target)
        for path in fs.traverse(target):
            if not fs.is_folder(path):
                path = fs.get_relative_path(path)
                self.added.add(path)

        # Changed
        self.has_changed = True


    #######################################################################
    # API / Transactions
    def _cleanup(self):
        super(GitDatabase, self)._cleanup()
        self.has_changed = False


    def _abort_changes(self):
        cache = self.cache
        # Added handlers
        for key in self.added:
            self._discard_handler(key)
        # Changed handlers
        for key in self.changed:
            cache[key].abort_changes()

        # And now, clean the filesystem
        try:
            # In a try/except to avoid a problem with new repositories
            send_subprocess(['git', 'reset', '--hard', '-q'], path=self.path)
        except CalledProcessError:
            pass
        if self.added:
            send_subprocess(['git', 'clean', '-fxdq'], path=self.path)

        # Reset state
        self.added.clear()
        self.changed.clear()


    def _rollback(self):
        pass


    def _save_changes(self, data):
        # Synchronize eventually the handlers and the filesystem
        for key in self.added:
            handler = self.cache.get(key)
            if handler is not None:
                parent_path = dirname(key)
                if not self.fs.exists(parent_path):
                    self.fs.make_folder(parent_path)
                handler.save_state()

        for key in self.changed:
            handler = self.cache[key]
            handler.save_state()

        self.changed.clear()

        # Call a "git add" eventually for new and/or moved files
        if self.added:
            send_subprocess(['git', 'add'] + list(self.added), path=self.path)
            self.added.clear()

        # Commit
        command = ['git', 'commit', '-aq']
        if data is None:
            command.extend(['-m', 'no comment'])
        else:
            git_author, git_message = data
            command.extend(['--author=%s' % git_author, '-m', git_message])
        try:
            send_subprocess(command, path=self.path)
        except CalledProcessError, excp:
            # Avoid an exception for the 'nothing to commit' case
            # FIXME Not reliable, we may catch other cases
            if excp.returncode != 1:
                raise



def make_git_database(path, size_min, size_max):
    """Create a new empty Git database if the given path does not exists or
    is a folder.

    If the given path is a folder with content, the Git archive will be
    initialized and the content of the folder will be added to it in a first
    commit.
    """
    path = lfs.get_absolute_path(path)
    if not lfs.exists(path):
        lfs.make_folder(path)

    # Init
    send_subprocess(['git', 'init', '-q'], path=path)

    # Add
    send_subprocess(['git', 'add', '.'], path=path)

    # Commit or not ?
    try:
        send_subprocess(['git', 'commit', '-q', '-m', 'Initial commit'],
                        path=path)
    except CalledProcessError:
        pass

    # Ok
    return GitDatabase(path, size_min, size_max)


# A built-in database for handler operations
ro_database = RODatabase()


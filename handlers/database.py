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
from os import mkdir
from subprocess import call, PIPE
from sys import getrefcount

# Import from itools
from itools.core import LRUCache, call_subprocess, read_subprocess
from itools.uri import get_reference, get_uri_name, get_uri_path, resolve_uri2
from itools import vfs
from itools.vfs import cwd, READ, WRITE, READ_WRITE, APPEND
from folder import Folder
import messages
from registry import get_handler_class


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
        after a transaction is commited or aborted.
        """


    def _has_changed(self):
        """Returns whethere there is something that has changed or not.
        This is to avoid superfluos actions by the 'save' and 'abort'
        methods.
        """
        raise NotImplementedError


    #######################################################################
    # Public API
    def save_changes(self):
        if self._has_changed() is False:
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
        except:
            self._rollback()
            self._abort_changes()
            raise
        finally:
            self._cleanup()


    def abort_changes(self):
        if self._has_changed() is False:
            return

        self._abort_changes()
        self._cleanup()



###########################################################################
# Read Only Database
###########################################################################

class RODatabase(BaseDatabase):
    """The read-only database works as a cache for file handlers.
    """

    def __init__(self, cache_size=5000):
        # A mapping from URI to handler
        self.cache = LRUCache(cache_size, automatic=False)


    def _resolve_reference(self, reference):
        """Resolves and returns the given reference.
        """
        return cwd.get_uri(reference)


    def _resolve_reference_for_writing(self, reference):
        raise NotImplementedError


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


    #######################################################################
    # Cache API
    def _discard_handler(self, uri):
        """Unconditionally remove the handler identified by the given URI from
        the cache, and invalidate it (and free memory at the same time).
        """
        handler = self.cache.pop(uri)
        # Invalidate the handler
        handler.__dict__.clear()


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


    def make_room(self):
        """Remove handlers from the cache until it fits the defined size.

        Use with caution.  If the handlers we are about to discard are still
        used outside the database, and one of them (or more) are modified,
        then there will be an error.
        """
        # Find out how many handlers should be removed
        n = len(self.cache) - self.cache.size
        if n <= 0:
            return

        # Discard as many handlers as needed
        for uri, handler in self.cache.iteritems():
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
        uri = self._resolve_reference(reference)

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
        uri = self._resolve_reference(reference)

        if vfs.exists(uri):
            names = vfs.get_names(uri)
            return list(names)

        return []


    def get_handler(self, reference, cls=None):
        uri = self._resolve_reference(reference)

        # Syncrhonize
        handler = self._sync_filesystem(uri)
        if handler is not None:
            # Check the class matches
            if cls is not None and not isinstance(handler, cls):
                error = "expected '%s' class, '%s' found"
                raise LookupError, error % (cls, handler.__class__)
            # Cache hit
            self.cache.touch(uri)
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
        base = self._resolve_reference(reference)
        for name in vfs.get_names(uri):
            ref = resolve_uri2(base, name)
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


    def safe_remove(self, reference):
        raise ReadOnlyError, 'cannot remove'


    def safe_open(self, reference, mode=None):
        if mode in (WRITE, READ_WRITE, APPEND):
            raise ReadOnlyError, 'cannot open file for writing'

        return vfs.open(reference, READ)


    def _cleanup(self):
#       import gc
#       from itools.core import vmsize
#       print 'RODatabase._cleanup (0): % 4d %s' % (len(self.cache), vmsize())
#       print gc.get_count()
        self.make_room()
#       print 'RODatabase._cleanup (1): % 4d %s' % (len(self.cache), vmsize())
#       print gc.get_count()


###########################################################################
# Read/Write Database (in memory transactions)
###########################################################################
class RWDatabase(RODatabase):

    def __init__(self, cache_size):
        RODatabase.__init__(self, cache_size)
        # The state, for transactions
        self.changed = set()
        self.added = set()
        self.removed = set()


    def _resolve_reference_for_writing(self, reference):
        """Resolves and returns the given reference.
        """
        return cwd.get_uri(reference)


    def has_handler(self, reference):
        uri = self._resolve_reference(reference)

        # Check the state
        if uri in self.added:
            return True
        if uri in self.removed:
            return False

        return RODatabase.has_handler(self, uri)


    def get_handler_names(self, reference):
        names = RODatabase.get_handler_names(self, reference)

        # The State
        base = self._resolve_reference(reference)
        # Removed
        removed = set()
        for uri in self.removed:
            name = get_uri_name(uri)
            if resolve_uri2(base, name) == uri:
                removed.add(name)
        # Added
        added = set()
        for uri in self.added:
            name = get_uri_name(uri)
            if resolve_uri2(base, name) == uri:
                added.add(name)
        names = set(names) - removed | added

        # Ok
        return list(names)


    def get_handler(self, reference, cls=None):
        uri = self._resolve_reference(reference)

        # Check state
        if uri in self.added:
            handler = self.cache[uri]
            # cls is good?
            if cls is not None and not isinstance(handler, cls):
                raise LookupError, ('conflict with a handler of type "%s"' %
                                     handler.__class__)
            return handler

        if uri in self.removed:
            raise LookupError, 'the resource "%s" does not exist' % uri

        # Ok
        return RODatabase.get_handler(self, uri, cls=cls)


    def set_handler(self, reference, handler):
        if isinstance(handler, Folder):
            raise ValueError, 'unexpected folder (only files can be "set")'

        if handler.uri is not None:
            raise ValueError, ('only new files can be added, '
                               'try to clone first')

        if self.has_handler(reference):
            raise RuntimeError, messages.MSG_URI_IS_BUSY % reference

        uri = self._resolve_reference_for_writing(reference)
        self.push_handler(uri, handler)
        self.added.add(uri)


    def del_handler(self, reference):
        uri = self._resolve_reference_for_writing(reference)

        # Check the handler has been added
        if uri in self.added:
            self._discard_handler(uri)
            self.added.remove(uri)
            return

        # Check the handler has been removed
        if uri in self.removed:
            raise LookupError, 'resource already removed'

        # Check for phantom handlers
        handler = self.cache.get(uri)
        if handler and not handler.timestamp and handler.dirty:
            self._discard_handler(uri)
            return

        # Syncrhonize
        handler = self._sync_filesystem(uri)
        if not vfs.exists(uri):
            raise LookupError, 'resource does not exist'

        # Clean the cache
        if uri in self.cache:
            self._discard_handler(uri)

        # Mark for removal
        self.removed.add(uri)


    def copy_handler(self, source, target):
        source = self._resolve_reference(source)
        target = self._resolve_reference_for_writing(target)
        if source == target:
            return

        # Check the target is free
        if self.has_handler(target):
            raise RuntimeError, messages.MSG_URI_IS_BUSY % target

        handler = self.get_handler(source)
        if isinstance(handler, Folder):
            # Folder
            for name in handler.get_handler_names():
                self.copy_handler(resolve_uri2(source, name),
                                  resolve_uri2(target, name))
        else:
            # File
            handler = handler.clone()
            # Update the state
            self.push_handler(target, handler)
            self.added.add(target)


    def move_handler(self, source, target):
        # TODO This method can be optimized further
        source = self._resolve_reference_for_writing(source)
        target = self._resolve_reference_for_writing(target)
        if source == target:
            return

        # Check the target is free
        if self.has_handler(target):
            raise RuntimeError, messages.MSG_URI_IS_BUSY % target

        handler = self.get_handler(source)
        if isinstance(handler, Folder):
            # Folder
            for name in handler.get_handler_names():
                self.move_handler(resolve_uri2(source, name),
                                  resolve_uri2(target, name))
        else:
            # Load if needed
            if handler.timestamp is None and handler.dirty is None:
                handler.load_state()
            # File
            handler = self.cache.pop(source)
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
        uri = self._resolve_reference_for_writing(reference)
        return vfs.make_file(uri)


    def safe_remove(self, reference):
        uri = self._resolve_reference_for_writing(reference)
        return vfs.remove(uri)


    def safe_open(self, reference, mode=None):
        uri = self._resolve_reference_for_writing(reference)
        return vfs.open(uri, mode)


    #######################################################################
    # API / Transactions
    def _has_changed(self):
        return bool(self.added) or bool(self.changed) or bool(self.removed)


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

        # Reset the state
        self.changed.clear()
        self.added.clear()
        self.removed.clear()


###########################################################################
# The Git Database
###########################################################################
class ROGitDatabase(RODatabase):

    def __init__(self, path, cache_size=5000):
        RODatabase.__init__(self, cache_size)
        uri = cwd.get_uri(path)
        uri = get_reference(uri)
        if uri.scheme != 'file':
            raise ValueError, 'unexpected "%s" path' % path
        self.path = str(uri.path)
        if self.path[-1] != '/':
            self.path += '/'


    def get_revisions_metadata(self, files, n=None):
        cmd = ['git', 'rev-list', '--pretty=format:%an%n%at%n%s']
        if n is not None:
            cmd = cmd + ['-n', str(n)]
        cmd = cmd + ['HEAD', '--'] + files
        cmd = cmd + files
        errno, data = read_subprocess(cmd)

        revisions = []
        lines = data.splitlines()
        for idx in range(len(lines) / 4):
            base = idx * 4
            ts = lines[base+2]
            revisions.append(
                {'commit': lines[base].split()[1],
                 'author_name': lines[base+1].rstrip(),
                 'author_date': datetime.fromtimestamp(int(ts)),
                 'subject': lines[base+3].rstrip()})

        return revisions


    def get_diff(self, revision):
        cmd = ['git', 'show', revision, '--pretty=format:%an%n%at%n%s']
        errno, data = read_subprocess(cmd)
        lines = data.splitlines()

        ts = int(lines[1])
        return {
            'author_name': lines[0],
            'author_date': datetime.fromtimestamp(ts),
            'subject': lines[2],
            'diff': '\n'.join(lines[2:])}



class GitDatabase(RWDatabase, ROGitDatabase):

    def __init__(self, path, cache_size):
        RWDatabase.__init__(self, cache_size)
        ROGitDatabase.__init__(self, path, cache_size)


    def _resolve_reference_for_writing(self, reference):
        """Check whether the given reference is within the git path.  If it
        is, return the resolved reference as an string.
        """
        # Resolve the reference
        uri = cwd.get_uri(reference)
        uri_ = get_reference(uri)
        # Security check
        if uri_.scheme != 'file':
            raise ValueError, 'unexpected "%s" reference' % reference
        path = str(uri_.path)
        if not path.startswith(self.path):
            raise ValueError, 'unexpected "%s" reference' % reference
        if path.startswith('%s.git' % self.path):
            raise ValueError, 'unexpected "%s" reference' % reference
        # Ok
        return uri


    def _rollback(self):
        call_subprocess(['git', 'checkout', '-f'])
        call_subprocess(['git', 'clean', '-fxdq'])


    def _save_changes(self, data):
        # Figure out the files to add
        git_files = [ get_uri_path(x) for x in self.added ]

        # Save
        RWDatabase._save_changes(self, data)

        # Add
        git_files = [ x for x in git_files if vfs.exists(x) ]
        if git_files:
            call_subprocess(['git', 'add'] + git_files)

        # Commit
        command = ['git', 'commit', '-aq']
        if data is None:
            command.extend(['-m', 'no comment'])
        else:
            git_author, git_message = data
            command.extend(['--author=%s' % git_author, '-m', git_message])
        call_subprocess(command)



def make_git_database(path, size):
    """Create a new empty Git database if the given path does not exists or
    is a folder.

    If the given path is a folder with content, the Git archive will be
    initialized and the content of the folder will be added to it in a first
    commit.
    """
    if not vfs.exists(path):
        mkdir(path)
    # Init
    command = ['git', 'init', '-q']
    call(command, cwd=path, stdout=PIPE)
    # Add
    command = ['git', 'add', '.']
    error = call(command, cwd=path, stdout=PIPE, stderr=PIPE)
    # Commit
    if error == 0:
        command = ['git', 'commit', '-q', '-m', 'Initial commit']
        call(command, cwd=path, stdout=PIPE)

    # Ok
    return GitDatabase(path, size)

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
from subprocess import call, PIPE, CalledProcessError
from sys import getrefcount

# Import from itools
from itools.core import LRUCache, send_subprocess, freeze
from itools.fs import vfs, lfs, READ, WRITE, READ_WRITE, APPEND
from folder import Folder
import messages
from registry import get_handler_class_by_mimetype


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
        after a transaction is committed or aborted.
        """


    def _has_changed(self):
        """Returns whether there is something that has changed or not.
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
        except Exception:
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

    def __init__(self, size_min=4800, size_max=5200, fs=None):
        # A mapping from key to handler
        self.cache = LRUCache(size_min, size_max, automatic=False)
        self.fs = fs or vfs


    def resolve_key(self, key):
        """Resolves and returns the given key to be unique.
        """
        return self.fs.resolve_key(key)


    def resolve_key_for_writing(self, key):
        raise NotImplementedError


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


    #######################################################################
    # Cache API
    def _discard_handler(self, key):
        """Unconditionally remove the handler identified by the given key from
        the cache, and invalidate it (and free memory at the same time).
        """
        handler = self.cache.pop(key)
        # Invalidate the handler
        handler.__dict__.clear()


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


    def push_phantom(self, key, handler):
        handler.database = self
        handler.key = key


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


    def _has_changed(self):
        return False


    #######################################################################
    # Database API
    def is_phantom(self, handler):
        return handler.timestamp is None and handler.dirty is not None


    def has_handler(self, key):
        key = self.resolve_key(key)

        # Synchronize
        handler = self._sync_filesystem(key)
        if handler is not None:
            return True

        # Ask vfs
        return self.fs.exists(key)


    def get_handler_names(self, key):
        key = self.resolve_key(key)

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
        key = self.resolve_key(key)

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
        base = self.resolve_key(key)
        fs = self.fs
        for name in fs.get_names(base):
            key = fs.resolve2(base, name)
            yield self.get_handler(key)


    #######################################################################
    # Write API
    def set_handler(self, key, handler):
        raise ReadOnlyError, 'cannot set handler'


    def del_handler(self, key):
        raise ReadOnlyError, 'cannot del handler'


    def copy_handler(self, source, target):
        raise ReadOnlyError, 'cannot copy handler'


    def move_handler(self, source, target):
        raise ReadOnlyError, 'cannot move handler'


    def safe_make_file(self, key):
        raise ReadOnlyError, 'cannot make file'


    def safe_remove(self, key):
        raise ReadOnlyError, 'cannot remove'


    def safe_open(self, key, mode=None):
        if mode in (WRITE, READ_WRITE, APPEND):
            raise ReadOnlyError, 'cannot open file for writing'

        return self.fs.open(key, READ)


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

    def __init__(self, size_min=4800, size_max=5200, fs=None):
        RODatabase.__init__(self, size_min=size_min, size_max=size_max,
                fs=fs)
        # The state, for transactions
        self.handlers_old2new = {}
        self.handlers_new2old = {}


    def resolve_key_for_writing(self, key):
        """Resolves and returns the given key.
        """
        return self.fs.resolve_key(key)


    def is_phantom(self, handler):
        # Phantom handlers are "new"
        if handler.timestamp or not handler.dirty:
            return False
        # They are attached to this database, but they are not in the cache
        return handler.database is self and handler.key not in self.cache


    def has_handler(self, key):
        key = self.resolve_key(key)

        # Check the state
        if key in self.handlers_new2old:
            return True
        if key in self.handlers_old2new:
            return False

        return RODatabase.has_handler(self, key)


    def get_handler_names(self, key):
        names = RODatabase.get_handler_names(self, key)
        names = set(names)
        fs = self.fs

        # The State
        base = self.resolve_key(key)
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
        key = self.resolve_key(key)

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
        return RODatabase.get_handler(self, key, cls=cls)


    def set_handler(self, key, handler):
        if isinstance(handler, Folder):
            raise ValueError, 'unexpected folder (only files can be "set")'

        if handler.key is not None:
            raise ValueError, ('only new files can be added, '
                               'try to clone first')

        if self.has_handler(key):
            raise RuntimeError, messages.MSG_URI_IS_BUSY % key

        key = self.resolve_key_for_writing(key)
        self.push_handler(key, handler)
        self.handlers_new2old[key] = None


    def del_handler(self, key):
        key = self.resolve_key_for_writing(key)

        # Check the handler has been added
        if key in self.handlers_new2old:
            self._discard_handler(key)
            key = self.handlers_new2old.pop(key)
            if key:
                self.handlers_old2new[key] = None
            return

        # Check the handler has been removed
        if key in self.handlers_old2new:
            raise LookupError, 'resource already removed'

        # Synchronize
        handler = self._sync_filesystem(key)
        if not self.fs.exists(key):
            raise LookupError, 'resource does not exist'

        # Clean the cache
        if key in self.cache:
            self._discard_handler(key)

        # Mark for removal
        self.handlers_old2new[key] = None


    def copy_handler(self, source, target):
        source = self.resolve_key(source)
        target = self.resolve_key_for_writing(target)
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
        source = self.resolve_key_for_writing(source)
        target = self.resolve_key_for_writing(target)
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
    # API / Safe VFS operations (not really safe)
    def safe_make_file(self, key):
        key = self.resolve_key_for_writing(key)

        # Remove empty folder first
        fs = self.fs
        if fs.is_folder(key):
            for x in fs.traverse(key):
                if fs.is_file(x):
                    break
            else:
                fs.remove(key)

        return fs.make_file(key)


    def safe_remove(self, key):
        key = self.resolve_key_for_writing(key)
        return self.fs.remove(key)


    def safe_open(self, key, mode=None):
        key = self.resolve_key_for_writing(key)
        return self.fs.open(key, mode)


    #######################################################################
    # API / Transactions
    def _has_changed(self):
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
                    self.safe_remove(source)
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
                        self.safe_remove(source)
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
        # Restrict to local fs
        RODatabase.__init__(self, size_min, size_max, fs=lfs)
        path = self.fs.get_absolute_path(path)
        if not self.fs.exists(path):
            raise ValueError, 'unexpected "%s" path' % path
        if path[-1] != '/':
            path += '/'
        self.path = path


    def resolve_key(self, path):
        return self.fs.get_absolute_path(path)


    def get_diff(self, revision):
        cmd = ['git', 'show', revision, '--pretty=format:%an%n%at%n%s']
        data = send_subprocess(cmd)
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
        data = send_subprocess(cmd)
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
        return send_subprocess(cmd)


    def get_diff_between(self, from_, to='HEAD', paths=[]):
        """Get the diff of the given path from the given commit revision to
        HEAD.

        If "stat" is True, get a diff stat only.
        """
        cmd = ['git', 'diff', from_, to]
        if paths:
            cmd.append('--')
            cmd.extend(paths)
        return send_subprocess(cmd)


    def get_blob(self, revision, path):
        """Get the file contents located at the given path after the given
        commit revision has been committed.
        """
        cmd = ['git', 'show', '%s:%s' % (revision, path)]
        return send_subprocess(cmd)



class GitDatabase(RWDatabase, ROGitDatabase):

    def __init__(self, path, size_min, size_max):
        RWDatabase.__init__(self, size_min, size_max)
        ROGitDatabase.__init__(self, path, size_min, size_max)


    def resolve_key_for_writing(self, path):
        """Check whether the given path is within the git path. If it is,
        return the absolute path.
        """
        # Resolve the path
        path = self.fs.get_absolute_path(path)
        # Security check
        if not path.startswith(self.path):
            raise ValueError, 'unexpected "%s" path' % path
        if path.startswith('%s.git' % self.path):
            raise ValueError, 'unexpected "%s" path' % path
        # Ok
        return path


    def _rollback(self):
        send_subprocess(['git', 'checkout', '-f'])
        send_subprocess(['git', 'clean', '-fxdq'])


    def _save_changes(self, data):
        # Figure out the files to add
        git_files = [ x for x in self.handlers_new2old ]

        # Save
        RWDatabase._save_changes(self, data)

        # Add
        fs = self.fs
        git_files = [ x for x in git_files if fs.exists(x) ]
        if git_files:
            send_subprocess(['git', 'add'] + git_files)

        # Commit
        command = ['git', 'commit', '-aq']
        if data is None:
            command.extend(['-m', 'no comment'])
        else:
            git_author, git_message = data
            command.extend(['--author=%s' % git_author, '-m', git_message])
        try:
            send_subprocess(command)
        except CalledProcessError, excp:
            # Avoid an exception for the 'nothing to commit' case
            # FIXME Not reliable, we may catch other cases
            if excp.returncode != 1:
                raise


    def get_handler_names(self, key):
        # TODO Use this method not only for GitDatabase, but for any database
        # that uses lfs.
        names = RODatabase.get_handler_names(self, key)
        names = set(names)

        # The State
        base = self.resolve_key(key) + '/'
        n = len(base)
        # Removed
        for key in self.handlers_old2new:
            if key[:n] == base:
                name = key[n:]
                if '/' not in name:
                    names.discard(name)
        # Added
        for key in self.handlers_new2old:
            if key[:n] == base:
                name = key[n:]
                if '/' not in name:
                    names.add(name)

        # Ok
        return list(names)



def make_git_database(path, size_min, size_max):
    """Create a new empty Git database if the given path does not exists or
    is a folder.

    If the given path is a folder with content, the Git archive will be
    initialized and the content of the folder will be added to it in a first
    commit.
    """
    if not lfs.exists(path):
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
    return GitDatabase(path, size_min, size_max)


# A built-in database for handler operations
ro_database = RODatabase()


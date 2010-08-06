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
from sys import getrefcount

# Import from xapian
from xapian import DatabaseOpeningError

# Import from itools
from itools.core import LRUCache, freeze, lazy, send_subprocess
from itools.fs import lfs
from itools.handlers import Folder, get_handler_class_by_mimetype
from itools.uri import Path
from catalog import Catalog
from registry import get_register_fields



class ROGitDatabase(object):

    # Flag to know whether to commit or not.  This is to avoid superfluos
    # actions by the 'save' and 'abort' methods.
    has_changed = False

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

        # 4. A mapping from key to handler
        self.cache = LRUCache(size_min, size_max, automatic=False)

        # 5. The git cache
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


    def push_phantom(self, key, handler):
        handler.database = self
        handler.key = key


    def is_phantom(self, handler):
        return handler.timestamp is None and handler.dirty is not None


    #######################################################################
    # Git
    #######################################################################
    def send_subprocess(self, cmd):
        return send_subprocess(cmd, path=self.path_data)


    def get_diff(self, revision):
        cmd = ['git', 'show', revision, '--pretty=format:%an%n%at%n%s']
        data = self.send_subprocess(cmd)
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
        data = self.send_subprocess(cmd)
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
        return self.send_subprocess(cmd)


    def get_diff_between(self, from_, to='HEAD', paths=[]):
        """Get the diff of the given path from the given commit revision to
        HEAD.

        If "stat" is True, get a diff stat only.
        """
        cmd = ['git', 'diff', from_, to]
        if paths:
            cmd.append('--')
            cmd.extend(paths)
        return self.send_subprocess(cmd)


    def get_blob(self, hash, cls):
        if type(hash) is not str:
            raise TypeError, 'get_blob expects a string, %s found' % type(hash)

        if len(hash) != 40:
            raise ValueError, 'a git hash is 40 chars long, not %d' % len(hash)

        if hash in self.git_cache:
            return self.git_cache[hash]

        cmd = ['git', 'show', hash]
        blob = self.send_subprocess(cmd)
        blob = cls(string=blob)
        self.git_cache[hash] = blob
        return blob


    def get_commit_hashs(self, file):
        """Give the hashs for all commit concerning file
        """
        cmd = ['git', 'log', '--reverse', '--pretty=format:%H', file]
        log = self.send_subprocess(cmd)
        return log.splitlines()


    def get_blob_by_revision_and_path(self, revision, path, cls):
        """Get the file contents located at the given path after the given
        commit revision has been committed.
        """
        arg = '%s:%s' % (revision, path)
        cmd = ['git', 'rev-parse', arg]
        hash = self.send_subprocess(cmd)
        hash = hash.rstrip('\n')
        return self.get_blob(hash, cls)


    def get_revisions(self, files, n=None):
        cmd = ['git', 'rev-list', '--pretty=format:%an%n%at%n%s']
        if n is not None:
            cmd = cmd + ['-n', str(n)]
        cmd = cmd + ['HEAD', '--'] + files
        data = self.send_subprocess(cmd)

        # Parse output
        revisions = []
        lines = data.splitlines()
        for idx in range(len(lines) / 4):
            base = idx * 4
            ts = int(lines[base+2])
            revisions.append(
                {'revision': lines[base].split()[1], # commit
                 'username': lines[base+1],          # author name
                 'date': datetime.fromtimestamp(ts), # author date
                 'message': lines[base+3],           # subject
                })
        # Ok
        return revisions


    def get_last_revision(self, files):
        revisions = self.get_revisions(files, 1)
        return revisions[0] if revisions else None


    #######################################################################
    # Catalog
    #######################################################################
    @lazy
    def catalog(self):
        path = '%s/catalog' % self.path
        fields = get_register_fields()
        try:
            return Catalog(path, fields, read_only=True)
        except DatabaseOpeningError:
            return None


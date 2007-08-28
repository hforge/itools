# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the future
from __future__ import with_statement

# Import from the Standard Library
from os import fdopen
from tempfile import mkstemp
from thread import allocate_lock, get_ident

# Import from itools
from itools.uri import get_reference, get_absolute_reference, Path
from itools.vfs import vfs
from itools.vfs import cwd, READ, WRITE, APPEND
from registry import get_handler_class
from folder import Folder



# The database states
READY = 0
TRANSACTION_PHASE1 = 1
TRANSACTION_PHASE2 = 2


###########################################################################
# Map from handler path to temporal file
###########################################################################
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



###########################################################################
# The database
###########################################################################
class Database(object):

    def __init__(self, commit=None):
        # The cache
        self.cache = {}
        # The state, for transactions
        self.changed = set()
        self.added = set()
        self.removed = set()
        # The commit, for safe transactions
        if commit is None:
            self.commit = None
            self.log = None
        else:
            if not isinstance(commit, Path):
                commit = Path(commit)
            self.commit = str(commit)
            self.log = str(commit.resolve2('log'))


    #######################################################################
    # API
    #######################################################################
    def has_handler(self, reference):
        fs, reference = cwd.get_fs_and_reference(reference)

        if reference in self.added:
            return True
        if reference in self.removed:
            return False
        return fs.exists(reference)


    def get_handler(self, reference, cls=None):
        fs, reference = cwd.get_fs_and_reference(reference)

        cache = self.cache
        # Check state
        if reference in self.added:
            return cache[reference]

        if reference in self.removed:
            raise LookupError, 'the resource "%s" does not exist' % reference

        # Verify the resource exists
        if not fs.exists(reference):
            # Check errors
            if reference in self.changed:
                raise RuntimeError, MSG_CONFLICT
            # Clean the cache
            if reference in cache:
                del cache[reference]
            raise LookupError, 'the resource "%s" does not exist' % reference

        # Folders are not cached
        if fs.is_folder(reference):
            # Check errors
            if reference in self.changed:
                raise RuntimeError, MSG_CONFLICT
            # Clean the cache
            if reference in cache:
                del cache[reference]
            folder = object.__new__(Folder)
            folder.database = self
            folder.uri = reference
            return folder

        # Lookup the cache
        if reference in cache:
            # Cache hit
            handler = cache[reference]
            if handler.timestamp is None:
                return handler
            # Check the timestamp
            mtime = fs.get_mtime(reference)
            if mtime < handler.timestamp:
                raise RuntimeError, 'XXX'
            elif mtime == handler.timestamp:
                return handler

        # Cache miss
        if cls is None:
            cls = get_handler_class(reference)
        # Build the handler
        handler = object.__new__(cls)
        handler.database = self
        handler.uri = reference
        handler.dirty = False
        # Update the cache
        cache[reference] = handler

        return handler


    def set_handler(self, reference, handler):
        if self.has_handler(reference):
            raise IOError, 'XXX'

        reference = get_absolute_reference(reference)
        handler.database = self
        handler.uri = reference
        if isinstance(handler, Folder):
            if handler.cache is None:
                raise NotImplementedError
            else:
                for name, subhandler in handler.cache.items():
                    self.set_handler(reference.resolve2(name), subhandler)
        else:
            self.cache[reference] = handler
            self.added.add(reference)


    def del_handler(self, reference):
        fs, reference = cwd.get_fs_and_reference(reference)

        if reference in self.added:
            del self.cache[reference]
            self.added.remove(reference)
            return

        # Check the handler actually exists
        if reference in self.removed:
            raise LookupError, 'resource already removed'
        if not fs.exists(reference):
            raise LookupError, 'resource does not exist'

        # Clean the cache
        if reference in self.cache:
            del self.cache[reference]

        # Mark for removal
        self.removed.add(reference)


    def copy_handler(self, source, target):
        source = get_absolute_reference(source)
        target = get_absolute_reference(target)

        handler = self.get_handler(source)
        if isinstance(handler, Folder):
            # Folder
            for name in handler.get_names():
                self.copy(source.resolve2(name), target.resolve2(name))
        else:
            # File
            handler = handler.clone()
            handler.database = self
            handler.uri = target
            # Update the state 
            self.cache[target] = handler
            self.added.add(target)


    def move_handler(self, source, target):
        # XXX Not efficient implementation
        self.copy(source, target)
        self.remove(source)


    #######################################################################
    # API / Safe VFS operations
    #######################################################################
    def safe_make_file(self, reference):
        # Not safe
        if self.log is None:
            return vfs.make_file(reference)

        # Safe
        with open(self.log, 'a+b') as log:
            log.write('+%s\n' % reference)

        return vfs.make_file(reference)


    def safe_make_folder(self, reference):
        # Not safe
        if self.log is None:
            return vfs.make_folder(reference)

        # Safe
        with open(self.log, 'a+b') as log:
            log.write('+%s\n' % reference)

        return vfs.make_folder(reference)


    def safe_remove(self, reference):
        # Not safe
        if self.log is None:
            return vfs.remove(reference)

        # Safe
        with open(self.log, 'a+b') as log:
            log.write('-%s\n' % reference)


    def safe_open(self, reference, mode=None):
        # Not safe
        if self.log is None:
            return vfs.open(reference, mode)

        # Safe
        if mode == WRITE:
            tmp_map = get_tmp_map()
            if reference in tmp_map:
                tmp_path = tmp_map[reference]
                return vfs.open(tmp_path, mode)

            tmp_file, tmp_path = mkstemp(dir=self.commit)
            tmp_path = get_reference(tmp_path)
            tmp_map[reference] = tmp_path
            with open(self.log, 'a+b') as log:
                log.write('~%s#%s\n' % (reference, tmp_path))
            return fdopen(tmp_file, 'w')
        elif mode == APPEND:
            tmp_map = get_tmp_map()
            if reference in tmp_map:
                tmp_path = tmp_map[reference]
                return vfs.open(tmp_path, mode)

            tmp_file, tmp_path = mkstemp(dir=self.commit)
            tmp_path = get_reference(tmp_path)
            tmp_map[reference] = tmp_path
            with open(self.log, 'a+b') as log:
                log.write('>%s#%s\n' % (reference, tmp_path))
            return fdopen(tmp_file, 'w')

        return vfs.open(reference, mode)


    #######################################################################
    # API / Transactions
    #######################################################################
    def get_state(self):
        commit = self.commit
        if vfs.exists(commit):
            if vfs.exists('%s/done' % commit):
                return TRANSACTION_PHASE2
            return TRANSACTION_PHASE1

        return READY


    def abort_changes(self):
        cache = self.cache
        # Added handlers
        for uri in self.added:
            del cache[uri]
        # Changed handlers
        for uri in self.changed:
            cache[uri].abort_changes()
        # Reset state
        self.changed.clear()
        self.added.clear()
        self.removed.clear()


    def save_changes(self):
        # 1. Start
        if self.log is not None:
            vfs.make_file(self.log)

        # Write changes to disk
        cache = self.cache
        try:
            # Save changed handlers
            for uri in self.changed:
                # Save the handler's state
                handler = cache[uri]
                handler.save_state()
                # Update the handler's timestamp
                handler.timestamp = vfs.get_mtime(uri)
                handler.dirty = False
            # Remove handlers
            for uri in self.removed:
                self.safe_remove(uri)
            # Add new handlers
            for uri in self.added:
                handler = cache[uri]
                handler.save_state_to(uri)
                # Update the handler's timestamp
                handler.timestamp = vfs.get_mtime(uri)
                handler.dirty = False
        except:
            # Rollback the changes in memory
            self.abort_changes()
            # Rollback the changes in disk
            if self.log is not None:
                self.rollback()
            raise
        finally:
            if self.log is not None:
                get_tmp_map().clear()

        # Reset the state
        self.changed.clear()
        self.added.clear()
        self.removed.clear()

        # 2. Transaction commited successfully.
        if self.log is not None:
            # Once we pass this point, we will save the changes permanently,
            # whatever happens (e.g. if there is a current failover we will
            # continue this process to finish the work).
            vfs.make_file('%s/done' % self.commit)

            self.save_changes_forever()


    def rollback(self):
        """
        This method is to be called when something bad happens while we
        are saving the changes to disk. For example if somebody pushes
        the reset button of the computer.

        This method will remove the changes done so far and restore the
        database state before the transaction started.
        """
        # The data
        with open(self.log) as log:
            for line in log.readlines():
                if line[-1] == '\n':
                    line = line[:-1]
                else:
                    raise RuntimeError, 'log file corrupted'
                action, line = line[0], line[1:]
                if action == '-':
                    pass
                elif action == '+':
                    if vfs.exists(line):
                        vfs.remove(line)
                elif action == '~':
                    pass
                elif action == '>':
                    pass
                else:
                    raise RuntimeError, 'log file corrupted'

        # We are done. Remove the commit.
        vfs.remove(self.commit)


    def save_changes_forever(self):
        """
        This method makes the transaction changes permanent.

        If it fails, for example if the computer crashes, it must be
        safe call this method again so it finishes the work.
        """
        # Save the transaction
        with open(self.log) as log:
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
                    pass
                elif action == '~':
                    dst, src = line.rsplit('#', 1)
                    if vfs.exists(src):
                        vfs.remove(dst)
                        vfs.move(src, dst)
                elif action == '>':
                    dst, src = line.rsplit('#', 1)
                    data = open(src, READ).read()
                    with vfs.open(dst, APPEND) as file:
                        file.write(data)
                else:
                    raise RuntimeError, 'log file corrupted'

        # We are done. Remove the commit.
        vfs.remove(self.commit)


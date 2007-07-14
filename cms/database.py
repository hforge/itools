# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
#               2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from datetime import datetime
import os
from tempfile import mkstemp
import thread

# Import from itools
from itools.uri import get_reference, Path
from itools import vfs
from itools.vfs import FileFS, register_file_system, READ, WRITE, APPEND
from itools.handlers import get_handler_class, get_transaction
from catalog import get_to_index, get_to_unindex



# The database states
READY = 0
TRANSACTION_PHASE1 = 1
TRANSACTION_PHASE2 = 2


###########################################################################
# Methods to find out the database path from a URI reference
###########################################################################
def get_log(reference):
    path = reference.path
    for i, name in enumerate(path):
        if name == 'database':
            log = path[:i].resolve2('database.commit/log')
            return str(log)

    raise RuntimeError, 'path "%s" is not a database path' % reference


def get_commit_and_log(reference):
    path = reference.path
    for i, name in enumerate(path):
        if name == 'database':
            path = path[:i]
            commit = path.resolve2('database.commit')
            log = commit.resolve2('log')
            return str(commit), str(log)

    raise RuntimeError, 'path "%s" is not a database path' % reference


###########################################################################
# Map from handler path to temporal file
###########################################################################
thread_lock = thread.allocate_lock()
_tmp_maps = {}


def get_tmp_map():
    ident = thread.get_ident()
    thread_lock.acquire()
    try:
        tmp_map = _tmp_maps.setdefault(ident, {})
    finally:
        thread_lock.release()

    return tmp_map



###########################################################################
# The database instance and VFS layer
###########################################################################
class DatabaseFS(FileFS):

    def __init__(self, path, cls=None):
        if not isinstance(path, Path):
            path = Path(path)

        self._database = path.resolve2('database')
        self._commit = path.resolve2('database.commit')
        log = path.resolve2('database.commit/log')
        self._log = str(log)

        # Build the root handler
        root_path = str(self._database)
        if cls is None:
            cls = get_handler_class(root_path)

        root = cls(root_path)
        root.uri.scheme = 'database'
        self.root = root


    #######################################################################
    # Override FileFS methods
    #######################################################################
    @staticmethod
    def make_file(reference):
        # Update the log
        log = get_log(reference)
        with open(log, 'a+') as log:
            log.write('+%s\n' % reference.path)

        # Create the file
        return FileFS.make_file(reference)


    @staticmethod
    def make_folder(reference):
        # Update the log
        log = get_log(reference)
        with open(log, 'a+') as log:
            log.write('+%s\n' % reference.path)

        # Create the folder
        return FileFS.make_folder(reference)


    @staticmethod
    def remove(reference):
        # Update the log
        log = get_log(reference)
        with open(log, 'a+') as log:
            log.write('-%s\n' % reference.path)


    @staticmethod
    def open(reference, mode=None):
        if mode == WRITE:
            tmp_map = get_tmp_map()
            if reference.path in tmp_map:
                tmp_path = tmp_map[reference.path]
                return FileFS.open(tmp_path, mode)

            commit, log = get_commit_and_log(reference)
            tmp_file, tmp_path = mkstemp(dir=commit)
            tmp_path = get_reference(tmp_path)
            tmp_map[reference.path] = tmp_path
            with open(log, 'a+') as log:
                log.write('~%s#%s\n' % (reference.path, tmp_path))
            return os.fdopen(tmp_file, 'w')
        elif mode == APPEND:
            tmp_map = get_tmp_map()
            if reference.path in tmp_map:
                tmp_path = tmp_map[reference.path]
                return FileFS.open(tmp_path, mode)

            commit, log = get_commit_and_log(reference)
            tmp_file, tmp_path = mkstemp(dir=commit)
            tmp_path = get_reference(tmp_path)
            tmp_map[reference.path] = tmp_path
            with open(log, 'a+') as log:
                log.write('>%s#%s\n' % (reference.path, tmp_path))
            return os.fdopen(tmp_file, 'w')

        return FileFS.open(reference, mode)


    #######################################################################
    # API
    #######################################################################
    def get_state(self):
        commit = self._commit
        commit = str(commit)
        if vfs.exists(commit):
            if vfs.exists('%s/done' % commit):
                return TRANSACTION_PHASE2
            return TRANSACTION_PHASE1

        return READY


    def commit(self):
        # 1. Start
        vfs.make_file(self._log)

        # Write changes to disk
        transaction = get_transaction()
        try:
            for handler in transaction:
                mtime = vfs.get_mtime(handler.uri)
                if mtime is not None:
                    handler.save_state()
        except:
            # Rollback the changes in memory
            for handler in transaction:
                # XXX Should we call to "handler.abort_changes()" instead?
                handler.timestamp = datetime(1900, 1, 1)
            # Rollback the changes in disk
            self.rollback()
            raise
        finally:
            # Clear
            transaction.clear()
            get_tmp_map().clear()

        # 2. Transaction commited successfully.
        # Once we pass this point, we will save the changes permanently,
        # whatever happens (e.g. if there is a current failover we will
        # continue this process to finish the work).
        done = self._commit.resolve2('done')
        done = str(done)
        vfs.make_file(done)

        self.save_changes_forever()


    def abort(self):
        """
        This method aborts the current transaction. It is assumed nothin
        has been written to disk yet.

        This method is to be used by the programmer whe he changes his
        mind and decides not to commit.
        """
        # Clean the index/unindex queues (XXX This may not should be here
        # as of 0.17)
        get_to_index().clear()
        get_to_unindex().clear()

        # Clean the transaction
        transaction = get_transaction()
        for handler in transaction:
            handler.abort_changes()
        transaction.clear()


    def rollback(self):
        """
        This method is to be called when something bad happens while we
        are saving the changes to disk. For example if somebody pushes
        the reset button of the computer.

        This method will remove the changes done so far and restore the
        database state before the transaction started.
        """
        # The data
        with open(self._log) as log:
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
        commit = str(self._commit)
        vfs.remove(commit)


    def save_changes_forever(self):
        """
        This method makes the transaction changes permanent.

        If it fails, for example if the computer crashes, it must be
        safe call this method again so it finish the work.
        """
        # Save the transaction
        with open(self._log) as log:
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
                        vfs.move(src, dst)
                elif action == '>':
                    dst, src = line.rsplit('#', 1)
                    data = vfs.open(src, READ).read()
                    with vfs.open(dst, APPEND) as file:
                        file.write(data)
                else:
                    raise RuntimeError, 'log file corrupted'

        # We are done. Remove the commit.
        commit = str(self._commit)
        vfs.remove(commit)



register_file_system('database', DatabaseFS)

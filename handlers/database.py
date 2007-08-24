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
from itools.uri import get_reference, Path
from itools.vfs import vfs
from itools.vfs import READ, WRITE, APPEND
from registry import get_handler_class



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
# The database instance and VFS layer
###########################################################################
class Database(object):

    def __init__(self, commit=None):
        self.changed = set()
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
    # Override FileFS methods
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
    # API
    #######################################################################
    def get_state(self):
        commit = self.commit
        if vfs.exists(commit):
            if vfs.exists('%s/done' % commit):
                return TRANSACTION_PHASE2
            return TRANSACTION_PHASE1

        return READY


    def save_changes(self):
        # 1. Start
        vfs.make_file(self.log)

        # Write changes to disk
        transaction = self.changed
        try:
            for handler in transaction:
                mtime = vfs.get_mtime(handler.uri)
                if mtime is not None:
                    handler.save_state()
        except:
            # Rollback the changes in memory
            for handler in transaction:
                handler.abort_changes()
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
        vfs.make_file('%s/done' % self.commit)

        self.save_changes_forever()


    def abort(self):
        """
        This method aborts the current transaction. It is assumed nothing
        has been written to disk yet.

        This method is to be used by the programmer whe he changes his
        mind and decides not to commit.
        """
        # Clean the transaction
        transaction = self.changed
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
        safe call this method again so it finish the work.
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


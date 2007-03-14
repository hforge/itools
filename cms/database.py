# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the future
from __future__ import with_statement

# Import from the Standard Library
from os import remove, rename
from subprocess import call
from tempfile import mkstemp
import thread

# Import from itools
from itools.uri import get_reference
from itools import vfs
from itools.vfs.file import FileFS
from itools.vfs.registry import register_file_system


def split_path(reference):
    path = reference.path
    for i, segment in enumerate(path):
        if segment.name == 'database':
            return path[:i].resolve2('~database'), path[i+1:]

    raise RuntimeError, 'path "%s" is not a database path' % reference



thread_lock = thread.allocate_lock()
_transactions = {}


def get_transaction():
    ident = thread.get_ident()
    thread_lock.acquire()
    try:
        transaction = _transactions.setdefault(ident, {})
    finally:
        thread_lock.release()

    return transaction



class DatabaseFS(FileFS):

    @staticmethod
    def make_file(reference):
        # The catalog has its own backup
        if '.catalog' in reference.path:
            return FileFS.make_file(reference)

        # Update the log
        commit, path = split_path(reference)
        with open('%s/log' % commit, 'a+') as log:
            log.write('+%s\n' % reference.path)

        # Create the file
        return FileFS.make_file(reference)


    @staticmethod
    def make_folder(reference):
        # The catalog has its own backup
        if '.catalog' in reference.path:
            return FileFS.make_folder(reference)

        # Update the log
        commit, path = split_path(reference)
        with open('%s/log' % commit, 'a+') as log:
            log.write('+%s\n' % reference.path)

        # Create the folder
        return FileFS.make_folder(reference)


    @staticmethod
    def remove(reference):
        # The catalog has its own backup
        if '.catalog' in reference.path:
            return FileFS.remove(reference)

        # Update the log
        commit, path = split_path(reference)
        with open('%s/log' % commit, 'a+') as log:
            log.write('-%s\n' % reference.path)


    @staticmethod
    def open(reference, mode=None):
        # The catalog has its own backup
        if '.catalog' in reference.path:
            return FileFS.open(reference, mode)

        if mode == 'w':
            transaction = get_transaction()
            if reference.path in transaction:
                tmp_path = transaction[reference.path]
            else:
                commit, path = split_path(reference)
                commit = str(commit)
                tmp_file, tmp_path = mkstemp(dir=commit)
                tmp_path = get_reference(tmp_path)
                transaction[reference.path] = tmp_path
                with open('%s/log' % commit, 'a+') as log:
                    log.write('~%s#%s\n' % (reference.path, tmp_path))

            return FileFS.open(tmp_path, mode)

        return FileFS.open(reference, mode)


    @staticmethod
    def commit_transaction(database):
        # The data
        transaction = database.path
        transaction = transaction.resolve2('../~database')
        log = transaction.resolve2('log')
        log = str(log)
        with open(log) as log:
            for line in log.readlines():
                if line[-1] == '\n':
                    line = line[:-1]
                else:
                    raise RuntimeError, 'log file corrupted'
                action, line = line[0], line[1:]
                if action == '-':
                    vfs.remove(line)
                elif action == '+':
                    pass
                elif action == '~':
                    dst, src = line.rsplit('#', 1)
                    vfs.move(src, dst)
                else:
                    raise RuntimeError, 'log file corrupted'

        # Clean transaction
        vfs.remove(transaction)
        get_transaction().clear()

        # The catalog
        src = str(database.path.resolve2('.catalog/'))
        dst = str(database.path.resolve2('.catalog.bak'))
        call(['rsync', '-a', '--delete', src, dst])


    @staticmethod
    def rollback_transaction(database):
        # The data
        transaction = database.path
        transaction = transaction.resolve2('../~database')
        log = transaction.resolve2('log')
        log = str(log)
        with open(log) as log:
            for line in log.readlines():
                if line[-1] == '\n':
                    line = line[:-1]
                else:
                    raise RuntimeError, 'log file corrupted'
                action, line = line[0], line[1:]
                if action == '-':
                    pass
                elif action == '+':
                    vfs.remove(line)
                elif action == '~':
                    pass
                else:
                    raise RuntimeError, 'log file corrupted'

        # Clean transaction
        vfs.remove(transaction)
        get_transaction().clear()

        # The catalog
        src = str(database.path.resolve2('.catalog.bak/'))
        dst = str(database.path.resolve2('.catalog'))
        call(['rsync', '-a', '--delete', src, dst])



register_file_system('database', DatabaseFS)

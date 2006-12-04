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

# Import from the Standard Library
import thread
from os import remove, rename
from subprocess import call

# Import from itools
from file import FileFS
from registry import register_file_system


def get_reference_on_change(reference):
    backup = '~' + reference.path[-1].name + '.tmp'
    return reference.resolve(backup)


def get_reference_on_add(reference):
    backup = '~' + reference.path[-1].name + '.add'
    return reference.resolve(backup)


def get_reference_on_remove(reference):
    backup = '~' + reference.path[-1].name + '.del'
    return reference.resolve(backup)



thread_lock = thread.allocate_lock()
_transactions = {}


def get_transaction():
    ident = thread.get_ident()
    thread_lock.acquire()
    try:
        transaction = _transactions.setdefault(ident, set())
    finally:
        thread_lock.release()

    return transaction



class DatabaseFS(FileFS):

    @staticmethod
    def make_file(reference):
        # The catalog has its own backup
        if '.catalog' in reference.path:
            return FileFS.make_file(reference)

        marker = get_reference_on_add(reference)
        FileFS.make_file(marker)
        get_transaction().add(marker)
        return FileFS.make_file(reference)


    @staticmethod
    def make_folder(reference):
        # The catalog has its own backup
        if '.catalog' in reference.path:
            return FileFS.make_folder(reference)

        marker = get_reference_on_add(reference)
        FileFS.make_file(marker)
        get_transaction().add(marker)
        return FileFS.make_folder(reference)


    @staticmethod
    def remove(reference):
        # The catalog has its own backup
        if '.catalog' in reference.path:
            return FileFS.remove(reference)

        src = str(reference.path)
        reference = get_reference_on_remove(reference)
        get_transaction().add(reference)
        dst = str(reference.path)
        rename(src, dst)


    @staticmethod
    def open(reference, mode=None):
        # The catalog has its own backup
        if '.catalog' in reference.path:
            return FileFS.open(reference, mode)

        if mode == 'w':
            reference = get_reference_on_change(reference)
            if FileFS.exists(reference):
                return FileFS.open(reference, mode)
            get_transaction().add(reference)
            return FileFS.make_file(reference)

        return FileFS.open(reference, mode)


    @staticmethod
    def commit(database):
        transaction = get_transaction()
        for reference in transaction:
            path = reference.path
            filename = path[-1].name
            marker = filename[-3:]
            original = str(path.resolve(filename[1:-4]))
            if marker == 'tmp':
                remove(original)
                backup = str(path)
                rename(backup, original)
            elif marker == 'add' or marker == 'del':
                FileFS.remove(reference)
        transaction.clear()
        src = str(database.path.resolve2('.catalog/'))
        dst = str(database.path.resolve2('.catalog.bak'))
        call(['rsync', '-a', '--delete', src, dst])


    @staticmethod
    def rollback(database):
        transaction = get_transaction()
        for reference in transaction:
            path = reference.path
            filename = path[-1].name
            marker = filename[-3:]
            original = path.resolve(filename[1:-4])
            backup = str(path)
            if marker == 'tmp':
                remove(backup)
            elif marker == 'add':
                FileFS.remove(original)
                remove(backup)
            elif marker == 'del':
                original = str(original)
                rename(backup, original)
        transaction.clear()
        src = str(database.path.resolve2('.catalog.bak/'))
        dst = str(database.path.resolve2('.catalog'))
        call(['rsync', '-a', '--delete', src, dst])



register_file_system('database', DatabaseFS)

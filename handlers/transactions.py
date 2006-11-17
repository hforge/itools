# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
import datetime
import thread

# Import from itools
from itools.vfs import api as vfs


thread_lock = thread.allocate_lock()


class Transaction(set):

    def rollback(self):
        if not self:
            return

        # Reset handlers
        for handler in self:
            handler.timestamp = datetime.datetime(1900, 1, 1)


    def commit(self, username='', note=''):
        if not self:
            return

        self.lock()
        try:
            # Errors should not happen in this stage.
            for handler in self:
                mtime = vfs.get_mtime(handler.uri)
                if mtime is not None:
                    handler.save_state()
        except:
            # Rollback the transaction, so handlers state will be consistent.
            # Note that the resource layer maybe incosistent anyway, true
            # ACID support must be implemented in a layer above.
            self.rollback()
            self.release()
            raise
        else:
            # Release the thread lock
            self.release()


    def lock(self):
        thread_lock.acquire()


    def release(self):
        thread_lock.release()



_transactions = {}

def get_transaction():
    ident = thread.get_ident()

    thread_lock.acquire()
    try:
        transaction = _transactions.setdefault(ident, Transaction())
    finally:
        thread_lock.release()

    return transaction


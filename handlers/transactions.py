# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA

# Import from the Standard Library
import datetime
from sets import Set
import thread


thread_lock = thread.allocate_lock()


class Transaction(Set):

    def rollback(self):
        for handler in self:
            handler.timestamp = datetime.datetime(1900, 1, 1)
        self.clear()


    def commit(self):
        # Event: before commit
        try:
            for handler in list(self):
                if hasattr(handler, 'before_commit'):
                    handler.before_commit()
        except:
            self.rollback()
            raise

        thread_lock.acquire()
        try:
            # Errors should not happen in this stage.
            try:
                for handler in self:
                    if handler.resource.get_mtime() is not None:
                        handler._save_state(handler.resource)
                        handler.timestamp = handler.resource.get_mtime()
            except:
                # XXX Right now we just rollback the transaction, so handlers
                # state will be consistent.
                #
                # However, it may happen something worse, the resource layer
                # may be left into an inconsistent state.
                self.rollback()
                raise
            self.clear()
        finally:
            thread_lock.release()


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


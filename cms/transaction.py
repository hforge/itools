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
from __future__ import with_statement
import datetime
import thread

# Import from itools
from itools import vfs
from itools.catalog.catalog import Catalog
from itools.handlers.File import File
from itools.handlers.Folder import Folder
from itools.handlers.transactions import (register_transaction_class,
        Transaction as BaseTransaction)


def save_file_state(handler):
    """ Duplicate of handlers.File.File.save_state but save to a temporary
    file.
    """
    temp = handler.uri.resolve('~%s.tmp' % handler.name)
    with vfs.make_file(temp) as file:
        handler.save_state_to_file(file)
    # Update the timestamp
    handler.timestamp = vfs.get_mtime(temp)



def save_folder_state(handler):
    """ Duplicate of handlers.Folder.Folder.save_state but save to
    temporary files.
    """
    cache = handler.cache
    base = handler.uri

    # Remove
    folder = vfs.open(base)
    for name in handler.removed_handlers:
        temp = '~%s.del' % name
        folder.move(name, temp)
    handler.removed_handlers = set()

    # Add
    for name in handler.added_handlers:
        temp = '~%s.add' % name if name != '.catalog' else name
        if folder.exists(temp):
            folder.remove(temp)
        # Add the handler
        target = base.resolve2(temp)
        handler = cache[name]
        # Add the handler
        handler.save_state_to(target)
        # Clean the cache (the most simple and robust option)
        cache[name] = None
    handler.added_handlers = set()

    # Update the timestamp
    handler.timestamp = vfs.get_mtime(handler.uri)



class Transaction(BaseTransaction):

    def commit(self, username='', note=''):
        """Copy of handlers.transactions.Transaction.commit
        but save to temporary files and directories.
        """
        if not self:
            return

        self.lock()
        try:
            # Errors should not happen in this stage.
            for handler in self:
                mtime = vfs.get_mtime(handler.uri)
                if mtime is not None:
                    if isinstance(handler, Catalog):
                        handler.save_state()
                    elif isinstance(handler, File):
                        save_file_state(handler)
                    else:
                        save_folder_state(handler)
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


register_transaction_class(Transaction)

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from optparse import OptionParser

# Import from itools
import itools
from itools import vfs
from itools.handlers import (Database, READY, TRANSACTION_PHASE1,
    TRANSACTION_PHASE2)
from itools.cms.server import ask_confirmation


def restore(parser, options, target):
    database = Database('%s/database.commit' % target)

    state = database.get_state()
    if state == READY:
        print 'Everything seems fine.'
    elif state == TRANSACTION_PHASE1:
        msg = 'The latest transaction failed. Clean up database (y/N)? '
        if ask_confirmation(msg) is True:
            print '  * Cleaning...'
            database.rollback()
            print 'DONE'
    elif state == TRANSACTION_PHASE2:
        msg = 'The latest transaction was not saved. Finish now (y/N)?'
        if ask_confirmation(msg) is True:
            print '  * Saving transaction...'
            database.save_changes_forever()
            print 'DONE'
    else:
        raise ValueError, 'unknown database state'



if __name__ == '__main__':
    # The command line parser
    usage = '%prog TARGET'
    version = 'itools %s' % itools.__version__
    description = ('Restore the TARGET itools.cms instance if broken. To be'
                   ' used after a crash.')
    parser = OptionParser(usage, version=version, description=description)

    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error('incorrect number of arguments')

    target = args[0]

    # Action!
    restore(parser, options, target)

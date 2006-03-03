#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2006 J. David Ibáñez <jdavid@itaapy.com>
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

# Import from itools
import itools


if __name__ == '__main__':
    print 'Welcome to: itools %s' % itools.__version__
    print
    print 'Type:'
    print
    print '  igettext-extract <source file>...'
    print '  - To build a message catalog (POT file) with the translatable'
    print '    messages from the given source files.'
    print
    print '  igettext-merge <POT file> <PO file>'
    print '  - To build a new message catalog, result of merging the messages'
    print '    in the given files.'
    print
    print '  igettext-build <source file> <PO file>'
    print '  - To build a new file from the source file, but replacing the'
    print '    translatable messages by the translations found in the PO file.'
    print
    print 'For more help on any command type: "igettext-<command> --help"'
    print

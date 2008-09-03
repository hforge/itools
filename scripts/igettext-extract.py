#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
# Copyright (C) 2008 Wynand Winterbach <wynand.winterbach@gmail.com>
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
import sys

# Import from itools
import itools
from itools.handlers import get_handler
from itools.gettext import POFile, POUnit
import itools.html
import itools.stl
import itools.odf
import itools.srx



if __name__ == '__main__':
    version = 'itools %s' % itools.__version__
    description = ('Extracts the translatable messages from the given source'
                   ' files. Builds a PO file with these messages, and prints'
                   ' to the standard output.')
    parser = OptionParser('%prog [OPTIONS] [<file>...]',
                          version=version, description=description)

    parser.add_option('-s', '--srx',
                      help='Use an other SRX file than the default one.')


    parser.add_option('-o', '--output',
                      help="The output will be written to the given file,"
                           " instead of printed to the standard output.")

    options, args = parser.parse_args()

    # Source files
    if len(args) == 0:
        parser.error('Needs at least one source file.')

    # The SRX file
    if options.srx is not None:
        srx_handler = get_handler(options.srx)
    else:
        srx_handler = None

    # Output
    if options.output is None:
        output = sys.stdout
    else:
        output = open(options.output, 'w')

    try:
        po = POFile()
        for filename in args:
            handler = get_handler(filename)
            try:
                get_units = handler.get_units
            except AttributeError:
                message = 'ERROR: The file "%s" could not be processed\n'
                sys.stderr.write(message % filename)
                continue
            # Extract the messages
            for value, line in get_units(srx_handler=srx_handler):
                message = POUnit([], [value], [u''], {filename: [line]})
                po.set_message(message)

        # XXX Should omit the header?
        output.write(po.to_str())
    finally:
        if options.output is not None:
            output.close()

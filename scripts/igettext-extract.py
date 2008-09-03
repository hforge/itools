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
from itools.gettext import POFile
import itools.html
import itools.stl
import itools.odf
import itools.srx
from itools.xliff import XLIFF



if __name__ == '__main__':
    usage = '%prog [OPTIONS] [<file>...]'
    version = 'itools %s' % itools.__version__
    description = ('Extracts the translatable messages from the given source'
                   ' files. Builds a PO file with these messages, and prints'
                   ' to the standard output.')
    parser = OptionParser(usage, version=version, description=description)
    parser.add_option('-f', '--format', default='po', help='Use the given '
        'output format.  The available options are "po" (default) and '
        ' "xliff".')
    parser.add_option('-o', '--output', help='Write the output to the given '
        'file (instead of to the standard output).')
    parser.add_option('-s', '--srx', help='Use an other SRX file than the '
        'default one.')

    # Source files
    options, args = parser.parse_args()
    if len(args) == 0:
        parser.error('Needs at least one source file.')

    # Format
    if options.format == 'po':
        cls = POFile
    elif options.format == 'xliff':
        cls = XLIFF
    else:
        parser.error("Available output formats: 'po' (default) and 'xliff'.")

    # The SRX file
    if options.srx is None:
        srx_handler = None
    else:
        srx_handler = get_handler(options.srx)

    # Make the output handler
    out_handler = cls()
    for filename in args:
        handler = get_handler(filename)
        try:
            get_units = handler.get_units
        except AttributeError:
            message = 'ERROR: The file "%s" could not be processed\n'
            sys.stderr.write(message % filename)
            continue
        # Extract the messages
        for source, line in get_units(srx_handler=srx_handler):
            out_handler.add_unit(filename, source, line)
    data = out_handler.to_str()

    # Output
    if options.output is None:
        print data
    else:
        open(options.output, 'w').write(data)

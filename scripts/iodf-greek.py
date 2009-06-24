#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from sys import stdout

# Import from itools
import itools
from itools.handlers import get_handler
from itools.odf import ODFFile



if __name__ == '__main__':
    # Build the command line parser
    usage = '%prog [OPTIONS] <ODF file>'
    version = 'itools %s' % itools.__version__
    description = (
        'Anonymizes and ODF file, replacing text by latin boilerplate and '
        'images by other dumb images.')
    parser = OptionParser(usage, version=version, description=description)
    parser.add_option('-o', '--output', help='The output will be written to'
        ' the given file, instead of printed to the standard output.')

    # Parse the command line
    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error('incorrect number of arguments')

    # Load the ODF handler
    filename = args[0]
    handler = get_handler(filename)
    if not isinstance(handler, ODFFile):
        parser.error('the given file is not an ODF file')

    # Anonymize
    data = handler.greek()

    # Save
    if options.output is None:
        stdout.write(data)
    else:
        with open(options.output, 'w') as file_out:
            file_out.write(data)



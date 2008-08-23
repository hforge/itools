#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from os import popen
from os.path import exists
import sys

# Import from itools
import itools



if __name__ == '__main__':
    version = 'itools %s' % itools.__version__
    description = ('Merges the given POT file into the PO file. Preserves'
                   ' the translations already present in the PO file.')
    parser = OptionParser('%prog [OPTIONS] <POT file> <PO file>',
                          version=version, description=description)

    parser.add_option('-o', '--output',
                      help="The output will be written to the given file,"
                           " instead of printed to the standard output.")

    options, args = parser.parse_args()

    if len(args) != 2:
        parser.error('incorrect number of arguments')

    if options.output is None:
        output = sys.stdout
    else:
        output = open(options.output, 'w')

    try:
        pot, po = args
        if exists(po):
            # a .po file already exist, merge it with locale.pot
            output.write(popen('msgmerge -s %s %s' % (po, pot)).read())
        else:
            # po doesn't exist, just copy locale.pot
            output.write(open(pot).read())
    finally:
        if options.output is not None:
            output.close()

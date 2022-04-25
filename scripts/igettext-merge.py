# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2009, 2011 J. David Ibáñez <jdavid.ibp@gmail.com>
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
from os.path import exists
from shutil import copyfile
from sys import stdout

# Import from itools
import itools
from itools.core import get_pipe



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

    pot, po = args
    # Case 1: a PO file already exist, merge it with locale.pot
    if exists(po):
        command = ['msgmerge', '-s', po, pot]
        if options.output:
            if options.output == po:
                command.append('-U')
            else:
                command.extend(['-o', options.output])
        data = get_pipe(command)
    # Case 2: PO doesn't exist, just copy locale.pot
    else:
        if options.output:
            copyfile(pot, options.output)
        else:
            data = open(pot).read()

    # Stdout
    if not options.output:
        stdout.write(data)

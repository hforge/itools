#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from subprocess import call
from tempfile import TemporaryFile

# Import from itools
import itools
from itools import git


def analyse(filenames):
    # Cumulative statistics
    lines = 0
    too_long = 0
    trailing_whites = 0
    tabs = 0

    # Analyse
    files = []
    for filename in filenames:
        f_lines = 0
        f_too_long = 0
        f_trailing_whites = 0
        f_tabs = 0
        for line in open(filename).readlines():
            f_lines += 1
            # Strip trailing newline
            line = line[:-1]
            length = len(line)
            # Maximum line length is 79
            if length > 79:
                f_too_long += 1
            # Trailing whitespaces are a bad thing
            if len(line.rstrip()) < length:
                f_trailing_whites += 1
            # Lines with tabs
            if '\t' in line:
                f_tabs += 1
        # File
        weight = f_too_long + f_trailing_whites + f_tabs
        files.append((weight, filename))
        # Cumulative
        lines += f_lines
        too_long += f_too_long
        trailing_whites += f_trailing_whites
        tabs += f_tabs

    # Show quality summary
    print 'Total number of lines: %d' % lines
    print
    too_long = (too_long*100.0)/lines
    print ' - longer than 79 characters: %.02f%%' % too_long
    trailing_whites = (trailing_whites*100.0)/lines
    print ' - with trailing whitespaces: %.02f%%' % trailing_whites
    tabs = (tabs*100.0)/lines
    print ' - with tabulators          : %.02f%%' % tabs
    print
    # Show list of worse files
    print 'Worse files:'
    print
    files.sort()
    files.reverse()
    files = files[:3]
    for weight, filename in files:
        print ' - %s' % filename
    print



def fix(filenames):
    for filename in filenames:
        lines = [ x.rstrip() + '\n' for x in open(filename).readlines() ]
        open(filename, 'w').write(''.join(lines))



if __name__ == '__main__':
    # The command line parser
    usage = '%prog [OPTIONS] [FILES]'
    version = 'itools %s' % itools.__version__
    description = (
        'Shows some statistics about the quality of the Python code.')
    parser = OptionParser(usage, version=version, description=description)
    parser.add_option(
        '-f', '--fix', action='store_true', dest='fix',
        help="makes some small improvements to the source code "
             "(MAKE A BACKUP FIRST)")
    options, args = parser.parse_args()

    if args:
        filenames = args
    elif git.is_available():
        filenames = git.get_filenames()
        filenames = [ x for x in filenames if x.endswith('.py') ]
    else:
        file = TemporaryFile()
        call(['find', '-name', '*.py'], stdout=file)
        file.seek(0)
        filenames = [ x.strip() for x in file.readlines() ]
        file.close()

    # Analyse
    analyse(filenames)
    # Fix
    if options.fix is True:
        print 'FIXING...'
        fix(filenames)
        print 'DONE'
        analyse(filenames)

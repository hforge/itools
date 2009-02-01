#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Gautier Hayoun <gautier.hayoun@itaapy.com>
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from Standard Library
from getpass import getpass
from optparse import OptionParser
from subprocess import call
from sys import executable

# Import from itools
from itools import __version__
from itools.pkg import DEFAULT_REPOSITORY
from itools.vfs import exists


def release(repository):
    # Check 'setup.py' exists
    if not exists('setup.py'):
        print ('setup.py not found, please execute isetup-release.py from '
               'the package directory')
        return

    # Prepare the arguments
    baseargs = [executable, 'setup.py']

    # Read the password
    password = getpass('Password: ')
    if not password:
        print 'Error: no password given, aborting.'
        return

    # Arguments list
    args = ['-p', password, '-r', repository]

    # Call iregister
    ret = call(baseargs + ['iregister'] + args)
    if ret != 0:
        print "Error: command iregister failed."
        return

    # Call iupload
    ret = call(baseargs + ['sdist', 'iupload'] + args)
    if ret != 0:
        print "Error: command iupload failed."
        return


if __name__ == '__main__':
    # Define the command line parser
    usage = '%prog REPOSITORY'
    version = 'itools %s' % __version__
    description = 'Upload a new package version to the given repository.'
    parser = OptionParser(usage, version=version, description=description)

    # Parse the command line
    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error('incorrect number of arguments')

    repository = args[0]

    # Action
    release(repository)

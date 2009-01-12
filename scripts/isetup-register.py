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
from urllib import urlencode
from urllib2 import urlopen

# Import from itools
from itools import __version__
from itools.pkg import DEFAULT_REPOSITORY


def register_user(username, options):
    repository = options.repository or DEFAULT_REPOSITORY

    # Password
    password = getpass('Password: ')
    if not password:
        print 'Error: no password was given, aborting.'
        return
    confirm = getpass('Confirm password: ')
    if password != confirm:
        print "Error: password and confirm don't match, aborting."
        return

    # Email
    email = raw_input('EMail: ')

    # Add the new user
    data = {':action': 'user',
            'name': username,
            'password': password,
            'confirm': confirm,
            'email': email}
    try:
        resp = urlopen(repository, urlencode(data))
    except Exception, exception:
        print 'Server error: [%s]: %s' % (exception.__class__, str(exception))
        return

    # Result
    if resp.code != 200:
        print 'Server error (%s)' % resp.code
        return

    print ('Your are now registered, unless the server admin set up a'
           ' email-confirmation system.\n'
           'In this case check your emails, and follow instructions'
           '\n'
           '"Execute isetup-release.py again to register package')



if __name__ == '__main__':
    # Define the command line parser
    usage = '%prog [OPTIONS] username'
    version = 'itools %s' % __version__
    description = 'Registers a new user into the server.'
    parser = OptionParser(usage, version=version, description=description)
    parser.add_option(
        '-r', '--repository', dest='repository', default=None,
        help='url to the package server [default: %s]' % DEFAULT_REPOSITORY)

    # Parse the command line
    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error('incorrect number of arguments')
    username = args[0]

    # Action
    register_user(username, options)

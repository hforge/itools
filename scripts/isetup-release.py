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
from sys import executable, exit
from urllib import urlencode
from urllib2 import urlopen

# Import from itools
from itools import __version__
from itools.utils import DEFAULT_REPOSITORY
from itools.vfs import exists


def add_user(options):
    repository = options.repository or DEFAULT_REPOSITORY

    username = options.username
    if username:
        msg = "Do you want to register user '%s'? (y/n) " % options.username
    else:
        msg = "Do you want to register a new user? (y/n) "
    if raw_input(msg).lower() not in ('y', 'yes'):
        exit()

    # Get the data
    while not username:
        username = raw_input('Username: ')

    password = email = ''
    confirm = None
    while password != confirm:
        while not password:
            password = getpass('Password: ')
        while not confirm:
            confirm = getpass('Confirm password: ')
        if password != confirm:
            password = ''
            confirm = None
            print "Password and confirm don't match!"
    while not email:
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
        exit()

    # Result
    if resp.code != 200:
        print 'Server error (%s)' % resp.code
        exit()
    else:
        print ('Your are now registered, unless the server admin set up a'
               ' email-confirmation system.\n'
               'In this case check your emails, and follow instructions'
               '\n'
               '"Execute isetup-release.py again to register package')
        exit()


def release(options):
    # Get setup.py file
    if not exists('setup.py'):
        print ('setup.py not found, please execute isetup-release.py from '
               'the package directory')
        exit()

    # Prepare the arguments
    baseargs = [executable, 'setup.py']


    args = []

    password = None
    while not password:
        password = getpass('Password: ')
    args.extend(['-p', password])

    if options.username is not None:
        args.extend(['-u', options.username])

    if options.repository is not None:
        args.extend(['-r', options.repository])

    # Call iregister
    ret = call(baseargs + ['iregister'] + args)
    if ret != 0:
        print "Stopping: command iregister failed"
        exit(ret)

    # Call iupload
    ret = call(baseargs + ['sdist', 'iupload'] + args)
    if ret != 0:
        print "Stopping: command iupload failed"
        exit(ret)


if __name__ == '__main__':
    # command line parsing
    version = 'itools %s' % __version__
    description = ('Automate the release process work (register, upload)')
    parser = OptionParser('%prog', version=version, description=description)

    parser.add_option('-u', '--username',
                  dest='username', default=None,
                  help='username used to log in the server')

    parser.add_option('-r', '--repository',
                  dest='repository', default=None,
                  help='url to the package server [default: %s]' %
                          DEFAULT_REPOSITORY)

    parser.add_option('-a', '--add', dest='add', default=False,
                      action="store_true",
                      help='set this option to add a new user')

    options, args = parser.parse_args()


    # No more options
    if len(args) != 0:
        parser.error('bag argument, please try --help')

    # Mode "Release" or "Add user"?
    if options.add:
        add_user(options)
    else:
        release(options)


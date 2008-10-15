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


if __name__ == "__main__":
    # command line parsing
    version = 'itools %s' % __version__
    description = ("Automate the release process work (register, upload)")
    parser = OptionParser('%prog', version=version, description=description)

    parser.add_option("-u", "--username",
                  dest="username", default=None,
                  help="username used to log in the server")

    parser.add_option("-r", "--repository",
                  dest="repository", default=None,
                  help="url to the package server [default: %s]" %
                          DEFAULT_REPOSITORY)

    (options, args) = parser.parse_args()

    # get setup.py file
    if not exists('setup.py'):
        msg = ('setup.py not found, please executre isetup-release.py from '
               'the package directory')
        parser.error(msg)

    baseargs = [executable, 'setup.py']

    password = None
    while not password:
        password = getpass('Password: ')

    passwordargs = ['-p', password]

    optionalargs = []
    if options.username is not None:
        optionalargs.extend(['-u', options.username])

    if options.repository is not None:
        optionalargs.extend(['-r', options.repository])

    # Call iregister
    ret = call(baseargs + ['iregister'] + passwordargs + optionalargs)
    if ret == 2:
        repository = options.repository or DEFAULT_REPOSITORY
        print "Unable to log in to %s" % repository

        username = options.username
        if username:
            msg = "Do you want to register user '%s'? (y/n)" % options.username
        else:
            msg = "Do you want to register a new user?"
        if raw_input(msg).lower() not in ('y', 'yes'):
            exit(ret)

        while not username:
            username = raw_input('Username: ')

        password = password
        email = confirm = ''
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

        data = {':action': 'user',
                'name': username,
                'password': password,
                'confirm': confirm,
                'email': email}
        resp = urlopen(repository, urlencode(data))

        if resp.code != 200:
            print 'Server response (%s): %s' % (resp.code, result)
            exit(ret)
        else:
            print ('Your are now registred, unless the server admin set up a'
                   ' email-confirmation system.\n'
                   'In this case check your emails, and follow instructions'
                   '\n'
                   '"Execute isetup-release.py again to register package')
            exit(0)
    elif ret != 0:
        print "Stopping: command iregister failed"
        exit(ret)

    # Call iupload
    ret = call(baseargs + ['sdist', 'iupload'] + passwordargs + optionalargs)
    if ret != 0:
        print "Stopping: command iregister failed"
        exit(ret)

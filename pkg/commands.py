# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 Gautier Hayoun <gautier.hayoun@itaapy.com>
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
from distutils.command.register import register
from distutils.command.upload import upload
from distutils.errors import DistutilsOptionError
from getpass import getpass
from sys import exit
from urllib2 import HTTPPasswordMgr

# Import from itools
from itools.uri import get_reference
from handlers import SetupConf


DEFAULT_REPOSITORY = 'http://pypi.python.org/pypi'


class iupload(upload):

    user_options = [
        ('password=', 'p', 'password'),
        ('repository=', 'r',
         "url of repository [default: %s]" % DEFAULT_REPOSITORY),
        ]
    boolean_options = []


    def initialize_options(self):
        self.password = ''
        self.repository = ''
        self.show_response = 0
        self.sign = False
        self.identity = None


    def finalize_options(self):
        config = SetupConf('setup.conf')

        if self.repository == DEFAULT_REPOSITORY:
            if config.has_value('repository'):
                self.repository = config.get_value('repository')
        elif self.repository is None:
            self.repository = DEFAULT_REPOSITORY
        # Get the password
        while not self.password:
            self.password = getpass('Password: ')



class iregister(register):

    user_options = [
        ('repository=', 'r',
            "url of repository [default: %s]" % DEFAULT_REPOSITORY),
        ('password=', 'p', 'password'),
        ]

    boolean_options = []

    def send_metadata(self):
        # Get the password
        while not self.password:
            self.password = getpass('Password: ')
        # set up the authentication
        auth = HTTPPasswordMgr()
        host = get_reference(self.repository).authority
        auth.add_password('pypi', host, self.username, self.password)

        # send the info to the server and report the result
        data = self.build_post_data('submit')
        code, result = self.post_to_server(data, auth)

        if code == 200:
            print 'The package has been successfully register to repository'
        else:
            print 'There has been an error while registring the package.'
            print 'Server responded (%s): %s' % (code, result)
            if code == 401:
                if result == 'Unauthorized':
                    print 'Perhaps your username/password is wrong.'
                    print 'Are you registered with "ipkg-register.py"?'
                exit(2)
            else:
                exit(3)


    def initialize_options(self):
        self.show_response = False
        self.list_classifiers = []

        self.repository = None
        self.password = ''


    def finalize_options(self):
        config = SetupConf('setup.conf')
        if self.repository == DEFAULT_REPOSITORY:
            if config.has_value('repository'):
                self.repository = config.get_value('repository')
        elif self.repository is None:
            self.repository = DEFAULT_REPOSITORY


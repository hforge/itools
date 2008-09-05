# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from distutils import core
from distutils.command.build_py import build_py
from distutils.command.register import register
from distutils.command.upload import upload
from getpass import getpass
from os import getcwd
from os.path import exists, join as join_path, sep, splitdrive
from re import search
from sys import _getframe, platform
from urllib2 import HTTPPasswordMgr
import sys

# Import from itools
import git

if platform[:3] == 'win':
    from utils_win import vmsize, get_time_spent
else:
    from utils_unix import vmsize, get_time_spent



def get_abspath(local_path, mname=None):
    """Returns the absolute path to the required file.
    """
    if mname is None:
        mname = _getframe(1).f_globals.get('__name__')

    if mname == '__main__' or mname == '__init__':
        mpath = getcwd()
    else:
        module = sys.modules[mname]
        if hasattr(module, '__path__'):
            mpath = module.__path__[0]
        elif '.' in mname:
            mpath = sys.modules[mname[:mname.rfind('.')]].__path__[0]
        else:
            mpath = mname

    drive, mpath = splitdrive(mpath)
    mpath = drive + join_path(mpath, local_path)

    # Make it working with Windows. Internally we use always the "/".
    if sep == '\\':
        mpath = mpath.replace(sep, '/')

    return mpath




############################################################################
# Our all powerful setup
############################################################################
def get_version(mname=None):
    if mname is None:
        mname = _getframe(1).f_globals.get('__name__')

    path = get_abspath('version.txt', mname=mname)
    if exists(path):
        return open(path).read().strip()
    return None



def setup(ext_modules=[]):
    mname = _getframe(1).f_globals.get('__name__')
    version = get_version(mname)
    try:
        from itools.datatypes import MultiLinesTokens, URI, Email, String
        from itools.datatypes import Tokens
        from itools.handlers import ConfigFile
        from itools.uri import get_reference
    except ImportError:
        # Are we trying to install itools?
        # FIXME Should use relative imports, by they don't work well yet (see
        # http://bugs.python.org/issue1510172).  This issue is solved with
        # Python 2.6, so we will remove this code once we raise the required
        # Python version to 2.6.
        # And move next few def/class before setup()
        start_local_import()
        from datatypes import MultiLinesTokens
        from datatypes import String, URI, Email, Tokens
        from handlers import ConfigFile
        from uri import get_reference
        end_local_import()

    class SetupConf(ConfigFile):
        schema = {'name': String,
                  'title': String,
                  'url': URI,
                  'author_name': String,
                  'author_email': Email,
                  'license': String,
                  'description': String,
                  'classifiers': MultiLinesTokens(default=()),
                  'packages': Tokens(default=()),
                  'requires': Tokens(default=()),
                  'provides': Tokens(default=()),
                  'scripts': Tokens(default=()),
                  'source_language': String,
                  'target_language': String,
                  'repository': URI,
                  'username': String}


    def get_setupconf_repo():
        repository = ''
        username = ''
        password = ''

        config = SetupConf('setup.conf')

        if not config.has_value('repository'):
            print "Please fill the 'repository' option in setup.conf"
            sys.exit(0)
        repository = str(config.get_value('repository'))

        if config.has_value('username'):
            username = config.get_value('username')
        while not username:
            username = raw_input('Username: ')

        while not password:
            password = getpass('Password (for user %s): ' % username)

        return (repository, username, password)


    class iupload(upload):

        def finalize_options(self):
            # From disutils
            if self.identity and not self.sign:
                raise DistutilsOptionError(
                    "Must use --sign for --identity to have meaning"
                )

            if 'repository_options' in globals().keys():
                self.repository = repository_options['repository']
                self.username = repository_options['username']
                self.password = repository_options['password']
                return

            self.repository, self.username, self.password = get_setupconf_repo()


    class iregister(register):

        def send_metadata(self):
            # set up the authentication
            auth = HTTPPasswordMgr()
            host = str(get_reference(self.repository).authority)
            auth.add_password('pypi', host, self.username, self.password)

            # send the info to the server and report the result
            data = self.build_post_data('submit')
            code, result = self.post_to_server(data, auth)

            if code == 200:
                print ('The package has been successfully register to'
                       ' repository')
            else:
                print 'There has been an error while registring the package.'
                print 'Server responded (%s): %s' % (code, result)


        def initialize_options(self):
            self.repository = None
            self.show_response = 0
            self.list_classifiers = 0

            self.repository = ''
            self.username = ''
            self.password = ''


        def finalize_options(self):
            global repository_options
            repository_options = {}

            self.repository, self.username, self.password = get_setupconf_repo()

            repository_options = {'username': self.username,
                                  'password': self.password,
                                  'repository': self.repository}


    config = SetupConf('setup.conf')

    # Initialize variables
    package_name = config.get_value('name')
    packages = [package_name]
    package_data = {package_name: []}

    # The sub-packages
    if config.has_value('packages'):
        subpackages = config.get_value('packages')
        for subpackage_name in subpackages:
            packages.append('%s.%s' % (package_name, subpackage_name))
    else:
        subpackages = []

    # Write the manifest file if it does not exist
    if exists('MANIFEST'):
        filenames = [ x.strip() for x in open('MANIFEST').readlines() ]
    else:
        filenames = git.get_filenames()
        lines = [ x + '\n' for x in filenames ]
        open('MANIFEST', 'w').write(''.join(lines))

    # Python files are included by default
    filenames = [ x for x in filenames if not x.endswith('.py') ]

    # The data files
    for line in filenames:
        path = line.split('/')
        n = len(path)
        if path[0] in subpackages:
            subpackage = '%s.%s' % (package_name, path[0])
            files = package_data.setdefault(subpackage, [])
            files.append(join_path(*path[1:]))
        elif path[0] not in ('scripts', 'test'):
            package_data[package_name].append(line)

    # The scripts
    if config.has_value('scripts'):
        scripts = config.get_value('scripts')
        scripts = [ join_path(*['scripts', x]) for x in scripts ]
    else:
        scripts = []

    author_name = config.get_value('author_name')
    # XXX Workaround buggy distutils ("sdist" don't likes unicode strings,
    # and "register" don't likes normal strings).
    if 'register' in sys.argv or 'iregister' in sys.argv:
        author_name = unicode(author_name, 'utf-8')
    core.setup(name = package_name,
               version = version,
               # Metadata
               author = author_name,
               author_email = config.get_value('author_email'),
               license = config.get_value('license'),
               url = config.get_value('url'),
               description = config.get_value('title'),
               long_description = config.get_value('description'),
               classifiers = config.get_value('classifiers'),
               # Packages
               package_dir = {package_name: ''},
               packages = packages,
               package_data = package_data,
               # Requires
               requires = config.get_value('requires'),
               # Provides
               provides = config.get_value('provides'),
               # Scripts
               scripts = scripts,
               cmdclass = {'iupload': iupload,
                           'iregister': iregister},
               # C extensions
               ext_modules=ext_modules)



############################################################################
# XXX Work-around the fact that Python does not implements (yet) relative
# imports (see PEP 328).
############################################################################

pythons_import = __import__

def local_import(name, globals={}, locals={}, fromlist=[]):
    if name.startswith('itools.'):
        name = name[7:]
    return pythons_import(name, globals, locals, fromlist)


def start_local_import():
    __builtins__['__import__'] = local_import


def end_local_import():
    __builtins__['__import__'] = pythons_import



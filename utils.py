# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from os import getcwd, getpid
from os.path import exists, join as join_path, sep, splitdrive
import sys

# Import from itools
import git

if sys.platform[:3] == 'win':
    from utils_win import vmsize, get_time_spent
else:
    from utils_unix import vmsize, get_time_spent



def get_abspath(globals_namespace, local_path):
    """Returns the absolute path to the required file.
    """
    mname = globals_namespace['__name__']

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
# XXX To be removed once distutils works again:
# http://bugs.python.org/issue1183712
class build_py_fixed(build_py):

    def get_data_files(self):
        """Generate list of '(package,src_dir,build_dir,filenames)' tuples.
        """
        data = []
        if not self.packages:
            return data
        for package in self.packages:
            # Locate package source directory
            src_dir = self.get_package_dir(package)

            # Compute package build directory
            build_dir = join_path(*([self.build_lib] + package.split('.')))

            # Length of path to strip from found files
            if src_dir:
                plen = len(src_dir)+1
            else:
                plen = 0

            # Strip directory from globbed filenames
            filenames = [
                file[plen:] for file in self.find_data_files(package, src_dir)
                ]
            data.append((package, src_dir, build_dir, filenames))
        return data



############################################################################
# Our all powerful setup
############################################################################
def get_version(namespace):
    path = get_abspath(namespace, 'version.txt')
    if exists(path):
        return open(path).read().strip()
    return None



def setup(namespace, classifiers=[], ext_modules=[]):
    version = get_version(namespace)
    try:
        from itools.handlers import ConfigFile
    except ImportError:
        # Are we trying to install itools?
        # XXX Should use relative imports, by they don't work well yet, see
        # http://bugs.python.org/issue1510172
        start_local_import()
        from handlers import ConfigFile
        end_local_import()

    config = ConfigFile('setup.conf')

    # Initialize variables
    package_name = config.get_value('name')
    packages = [package_name]
    package_data = {package_name: []}
    provided_packages = []
    required_packages = []

    # The sub-packages
    if config.has_value('packages'):
        subpackages = config.get_value('packages').split()
        for subpackage_name in subpackages:
            packages.append('%s.%s' % (package_name, subpackage_name))
    else:
        subpackages = []

    # The provided packages
    if config.has_value('provides'):
        for provided_package_name in config.get_value('provides').split():
            provided_packages.append(provided_package_name)

    # The required packages
    if config.has_value('requires'):
        for required_package_name in config.get_value('requires').split():
            required_packages.append(required_package_name)

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
        scripts = config.get_value('scripts').split()
        scripts = [ join_path(*['scripts', x]) for x in scripts ]
    else:
        scripts = []

    author_name = config.get_value('author_name')
    # XXX Workaround buggy distutils ("sdist" don't likes unicode strings,
    # and "register" don't likes normal strings).
    if sys.argv == ['setup.py', 'register']:
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
               classifiers = classifiers,
               # Packages
               package_dir = {package_name: ''},
               packages = packages,
               package_data = package_data,
               # Requires
               requires = required_packages,
               # Provides
               provides = provided_packages,
               # Scripts
               scripts = scripts,
               # C extensions
               ext_modules=ext_modules,
               # XXX broken distutils
               cmdclass={'build_py': build_py_fixed})



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



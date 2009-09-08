# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from distutils.core import Extension
from distutils.command.build_ext import build_ext
from distutils.errors import LinkError
from os.path import exists, join as join_path
from os import popen
from sys import _getframe, argv

# Import from itools
from itools.core import freeze, get_pipe, get_version
from itools import git
from handlers import SetupConf


class OptionalExtension(Extension):
    """An Optional Extension is a C extension that complements the package
    without being mandatory. It typically depends on external libraries. If the
    libraries are not available, the package will be installed without this
    extra module. Build errors will still be reported. Developers are
    responsible for testing the availability of the package, e.g. try/except
    ImportError.

    Simply Use OptionalExtension instead of Extension in your setup.
    """



class OptionalBuildExt(build_ext):
    """Internal class to support OptionalExtension.
    """

    def build_extension(self, ext):
        if not isinstance(ext, OptionalExtension):
            return build_ext.build_extension(self, ext)
        try:
            build_ext.build_extension(self, ext)
        except LinkError:
            print ""
            print "  '%s' module will not be available." % ext.name
            print "  Make sure the following libraries are installed:",
            print ", ".join(ext.libraries)
            print "  This error is not fatal, continuing build..."
            print ""



def get_compile_flags(command):
    include_dirs = []
    extra_compile_args = []
    library_dirs = []
    libraries = []

    if isinstance(command, str):
        command = command.split()
    data = get_pipe(command)

    for line in data.splitlines():
        for token in line.split():
            flag, value = token[:2], token[2:]
            if flag == '-I':
                include_dirs.append(value)
            elif flag == '-f':
                extra_compile_args.append(token)
            elif flag == '-L':
                library_dirs.append(value)
            elif flag == '-l':
                libraries.append(value)

    return {'include_dirs': include_dirs,
            'extra_compile_args': extra_compile_args,
            'library_dirs': library_dirs,
            'libraries': libraries}



def get_manifest():
    if git.is_available():
        return git.get_filenames()

    # No git: find out source files
    config = SetupConf('setup.conf')
    target_languages = config.get_value('target_languages', default='').split()
    cmd = (
        'find -type f|grep -Ev "^./(build|dist)"|grep -Ev "*.(~|pyc|%s)"'
        % '|'.join(target_languages))
    return [ x.strip() for x in popen(cmd).readlines() ]



def setup(ext_modules=freeze([])):
    mname = _getframe(1).f_globals.get('__name__')
    version = get_version(mname)

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
        filenames = get_manifest()
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
    if 'register' in argv:
        author_name = unicode(author_name, 'utf-8')
    classifiers = [ x for x in config.get_value('classifiers') if x ]
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
               # Requires / Provides
               requires = config.get_value('requires'),
               provides = config.get_value('provides'),
               # Scripts
               scripts = scripts,
               cmdclass = {'build_ext': OptionalBuildExt},
               # C extensions
               ext_modules=ext_modules)

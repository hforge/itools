# Copyright (C) 2006-2011 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2009 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2009-2011 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2010 Sylvain Taverne <taverne.sylvain@gmail.com>
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

import setuptools

from os.path import exists, join as join_path
from sys import argv
import codecs

# Requirements
from pip._internal.req import parse_requirements

# Import from itools
from itools.core import get_pipe

# Import from itools.pkg
from .build import build, get_package_version
from .handlers import SetupConf


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


def get_config():
    return SetupConf('setup.conf')


def setup(path, ext_modules=None):
    ext_modules = ext_modules or []
    config = get_config()
    package_root = config.get_value('package_root')
    # Guess environment
    if "--development" in argv:
        environment = 'development'
        argv.remove("--development")
    else:
        environment = 'production'
    # Build
    if any(x in argv for x in ('build', 'install', 'sdist', 'egg_info')):
        version = build(path, config, environment)
    else:
        version = get_package_version(package_root)

    # Initialize variables
    package_name = config.get_value('package_name')
    if not package_name:
        package_name = config.get_value('name')
    packages = [package_name]
    package_data = {package_name: []}

    # The sub-packages
    if config.has_value('packages'):
        subpackages = config.get_value('packages')
        for subpackage_name in subpackages:
            packages.append(f'{package_name}.{subpackage_name}')
    else:
        subpackages = []

    # Python files are included by default
    filenames = [x.strip() for x in open(path + 'MANIFEST').readlines()]
    filenames = [x for x in filenames if not x.endswith('.py')]

    # The data files
    prefix = '' if package_root == '.' else package_root + '/'
    prefix_n = len(prefix)
    for line in filenames:
        if not line.startswith(prefix):
            continue
        line = line[prefix_n:]

        path = line.split('/')
        if path[0] in subpackages:
            subpackage = f'{package_name}.{path[0]}'
            files = package_data.setdefault(subpackage, [])
            files.append(join_path(*path[1:]))
        elif path[0] not in ('archive', 'docs', 'scripts', 'test'):
            package_data[package_name].append(line)

    # The scripts
    if config.has_value('scripts'):
        scripts = config.get_value('scripts')
        scripts = [join_path('scripts', x) for x in scripts]
    else:
        scripts = []

    data_files = []
    if config.has_value('bin'):
        paths = [join_path('bin', x) for x in config.get_value('bin')]
        data_files.append(('bin', paths))
        print('XXX DATA FILES', data_files)

    # Long description
    if exists('README.rst'):
        with codecs.open('README.rst', 'r', 'utf-8') as readme:
            long_description = readme.read()
    else:
        long_description = config.get_value('description')

    author_name = config.get_value('author_name')
    # Requires
    install_requires = []

    if exists('requirements.txt'):
        install_requires = parse_requirements('requirements.txt', session='xxx')
        install_requires = [
            str(ir.requirement) for ir in install_requires
            if not str(ir.requirement).startswith("git")
        ]
    classifiers = [x for x in config.get_value('classifiers') if x]
    setuptools.setup(
        name=package_name,
        version=version,
        # Metadata
        author=author_name,
        author_email=config.get_value('author_email'),
        license=config.get_value('license'),
        url=config.get_value('url'),
        description=config.get_value('title'),
        long_description=long_description,
        classifiers=classifiers,
        # Packages
        package_dir={package_name: package_root},
        packages=packages,
        package_data=package_data,
        # Requires / Provides
        install_requires=install_requires,
        # Scripts
        scripts=scripts,
        data_files=data_files,
        # C extensions
        ext_modules=ext_modules,
    )

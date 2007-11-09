#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
# Copyright (C) 2007 Luis Arturo Belmar-Letelier <luis@itaapy.com>
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
from datetime import date
from optparse import OptionParser
from os import environ, getcwd
from os.path import exists, basename, dirname, join, sep, islink, realpath
from string import Template
from sys import executable

# Import from itools
import itools
from itools import vfs


def make(parser, options, target):
    if exists(target):
        parser.error("Directory '%s' already existing" % target)
    if len(target.split(sep)) > 1:
        parser.error("%s is not a corect directory name" % target)

    # Find out the name of the package_name
    package_name, package_path = target, getcwd()

    python_bin_path = python_bin_realpath = executable
    if islink(python_bin_path):
        python_bin_realpath = realpath(python_bin_path)

    python_bin_realpath = python_bin_realpath.rsplit(sep, 1)[0]
    python_bin_path= python_bin_path.rsplit(sep, 1)[0]

    # Build the namespace
    namespace = {}
    namespace['YEAR'] = date.today().year
    namespace['PACKAGE_NAME'] = package_name
    namespace['PACKAGE_PATH'] = package_path
    namespace['PACKAGE'] = '%s/%s' % (package_path, package_name)
    namespace['PYTHON_BIN_PATH'] = python_bin_path
    namespace['PYTHON_BIN_REALPATH'] = python_bin_realpath

    scripts = ('isetup-build.py', 'icms-start.py', 'icms-stop.py',
               'icms-init.py', 'icms-update-catalog.py', 'python')
    for s in scripts:
        script_fn = '%s/%s' % (python_bin_path, s)
        if not exists(script_fn):
            script_fn = '%s/%s' % (python_bin_realpath, s)
        script = s.split('.py', 1)[0].upper().replace('-', '_')
        namespace[script] = script_fn
    if 'GIT_AUTHOR_NAME' in environ:
        namespace['AUTHOR_NAME'] = environ['GIT_AUTHOR_NAME']
    if 'GIT_AUTHOR_EMAIL' in environ:
        namespace['AUTHOR_EMAIL'] = environ['GIT_AUTHOR_EMAIL']

    # Create the target folder
    vfs.make_folder(target)
    folder = vfs.open(target)

    # Copy source files
    path_prefix = 'cms/skeleton/%s/' % options.type
    path_prefix_n = len(path_prefix)

    itools_path = dirname(itools.__file__)
    manifest = join(itools_path, 'MANIFEST')
    for path in open(manifest).readlines():
        if not path.startswith(path_prefix):
            continue
        path = path.strip()
        # Read and process the data
        source = join(itools_path, path)
        source = open(source).read()
        data = Template(source).safe_substitute(**namespace)
        # Create the target file
        file = folder.make_file(path[path_prefix_n:])
        try:
            file.write(data)
        finally:
            file.close()

    # Print a helpful message
    print '*'
    print '* Package "%s" created' % package_name
    print '*'
    print '* To install it type:'
    print '*'
    print '*   $ cd %s' % namespace['PACKAGE_NAME']
    print '*   $ %s' % namespace['ISETUP_BUILD']
    print '*   ...'
    print '*   $ %s setup.py install' % namespace['PYTHON']
    print '*'
    if options.type == 'quickstart':
        print '* Follow %s/README' % package_name


if __name__ == '__main__':
    # The command line parser
    usage = '%prog TARGET'
    version = 'itools %s' % itools.__version__
    description = 'Creates a new Python package for itools.cms of name TARGET.'
    parser = OptionParser(usage, version=version, description=description)
    help=('Choose the type of package to make: --type=quickstart or '
          '--type=bare [default]. "bare" is an empty package, "quickstart" is'
          ' a kind of tutorial')
    parser.add_option('-t', '--type', type="string", default="bare", help=help)

    # Get the name of the package to build
    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error('incorrect number of arguments')

    target = args[0]

    # Action!
    make(parser, options, target)

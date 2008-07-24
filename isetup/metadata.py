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
from distutils.versionpredicate import split_provision
from os.path import join, isfile

# Import from itools
from itools.vfs import get_names



# Note : some .egg-info are directories and not files
def egg_info(data):
    """Return a dict containing information from PKG-INFO formated data
    like .egg-info files.

    >>> filename = '/usr/lib/python2.5/site-packages/pexpect-2.1.egg-info'
    >>> egg_info(open(filename).read())
    {'Author': 'Noah Spurrier', 'Author-email': 'noah@noah.org', ...}
    """
    attributes = {}
    last_line_key = None
    for line in data.splitlines():
        if ': ' in line:
            (key, val) = line.split(': ', 1)
            # Don't record useless attribute
            if val != 'UNKNOWN':
                # Comma separated string for lists
                if key in attributes.keys():
                    attributes[key] += ',' + val
                else:
                    attributes[key] = val
                last_line_key = key
        elif last_line_key is not None:
            attributes[last_line_key] += '\n'+line
    return attributes


def list_eggs_info(dir, module_name='', check_import=True):
    """For every .egg-info in a directory, return its informations and test if
    import is possible.
    """
    eggs = []
    # sort the files
    eggs_info = [egg for egg in get_names(dir) if egg.endswith('.egg-info')]
    eggs_info.sort(lambda a, b: cmp(a.upper(),b.upper()))

    for egg in eggs_info:
        if isfile(join(dir, egg)):
            infos = egg_info(open(join(dir, egg)).read())
        else:
            infos = {}
        # for the time being only file .egg-info are supported
        if not isfile(join(dir, egg)) or\
           module_name.upper() not in infos['Name'].upper():
            continue

        if check_import:
            # try the import
            # if the project filled Provides field use this one
            if 'Provides' in infos:
                try:
                    for provided_module in infos['Provides'].split(','):
                        provided_module = split_provision(provided_module)
                        provided_module_name = provided_module[0]
                        provided_module_ver = provided_module[1]
                        __import__(provided_module_name)
                except:
                    is_imported = False
                else:
                    is_imported = True
            else:
                # We can try the name if the project has not filled Provides
                # field
                try:
                    __import__(infos['Name'])
                except:
                    is_imported = False
                else:
                    is_imported = True

            infos['is_imported'] = is_imported
        eggs.append(infos)
    return eggs



# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
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
from distutils.core import Extension
from subprocess import Popen, PIPE
from sys import exit

# Import from itools
from utils import setup

def hlib_dirs():
    # Try to launch pkg_config
    proc = Popen(['pkg-config', '--libs', '--cflags', 'hlib'], stdout=PIPE)
    if proc.wait() != 0:
        exit()

    # Analyze the results
    cmd_mapping = {'l': 'libraries', 'L': 'library_dirs', 'I': 'include_dirs'}
    result = {'libraries': [], 'library_dirs': [], 'include_dirs': []}
    for token in proc.stdout.read().split():
            result[cmd_mapping[token[1]]].append(token[2:])
    result['runtime_library_dirs'] = result['library_dirs']

    return result


if __name__ == '__main__':
    cparser = Extension('itools.xml.parser', sources=['xml/parser.c'],
                        **hlib_dirs())

    setup(ext_modules=[cparser])

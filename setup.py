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
from imp import load_module, PKG_DIRECTORY
from os import getcwd

# Import local itools first, otherwise installing the first time won't work.
load_module('itools', None, getcwd(), ('', '', PKG_DIRECTORY))

# Import from itools
from pkg import setup, get_compile_flags


if __name__ == '__main__':
    flags = get_compile_flags('pkg-config --cflags --libs glib-2.0')
    cparser = Extension('itools.xml.parser',
                        sources=['xml/parser.c', 'xml/doctype.c',
                                 'xml/arp.c', 'xml/pyparser.c'],
                        **flags)

    setup(ext_modules=[cparser])

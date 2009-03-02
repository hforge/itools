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
from sys import stderr, exit

# Import local itools first, otherwise installing the first time won't work.
load_module('itools', None, getcwd(), ('', '', PKG_DIRECTORY))

# Import from itools
from pkg import setup, get_compile_flags


if __name__ == '__main__':
    ext_modules = []

    # XML Parser
    try:
        flags = get_compile_flags('pkg-config --cflags --libs glib-2.0')
    except OSError:
        print >> stderr, 'Error: the command "pkg-config" is not found.'
        print >> stderr, 'Install pkg-config before installing itools.'
        exit(1)
    except EnvironmentError:
        print >> stderr, 'Error: Glib 2.0 library or headers not found.'
        raise
    else:
        sources = ['xml/parser.c', 'xml/doctype.c', 'xml/arp.c',
                   'xml/pyparser.c']
        extension = Extension('itools.xml.parser', sources, **flags)
        ext_modules.append(extension)

    # PDF indexation
    try:
        flags = get_compile_flags('pkg-config --cflags --libs poppler')
    except EnvironmentError:
        print >> stderr, 'Warning: poppler headers are not found.'
        print >> stderr, 'PDF indexation will not be available'
    else:
        sources = ['pdf/pdftotext.cc']
        extension = Extension('itools.pdf.pdftotext', sources, **flags)
        ext_modules.append(extension)

    # DOC indexation
    try:
        flags = get_compile_flags('wv2-config --cflags --libs')
    except EnvironmentError:
        print >> stderr, 'Warning: wv2 library is not found.'
        print >> stderr, 'DOC indexation will not be available'
    else:
        sources = ['office/doctotext.cc']
        extension = Extension('itools.office.doctotext', sources, **flags)
        ext_modules.append(extension)

    # Ok
    setup(ext_modules=ext_modules)

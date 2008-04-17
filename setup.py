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

# Import from itools
from utils import setup


if __name__ == '__main__':
    libs = ['glib-2.0']
    extensions = [
        # The Graph Structured Stack
        ('itools.abnf.gss', ['abnf/gss.c']),
        # The XML Parser
        ('itools.xml.parser',
         ['xml/parser.c', 'xml/doctype.c', 'xml/arp.c', 'xml/pyparser.c']),
        ]

    extensions = [
        Extension(name, sources=sources, libraries=libs)
        for name, sources in extensions ]

    # Setup
    setup(ext_modules=extensions)

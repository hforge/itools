# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2012 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2008 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2009 Hervé Cauwelier <herve@oursours.net>
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
from sys import stderr

# Import from itools
from itools.pkg import setup, get_compile_flags


if __name__ == '__main__':
    ext_modules = []

    # XML Parser
    try:
        flags = get_compile_flags('pkg-config --cflags --libs glib-2.0')
    except OSError:
        print >> stderr, "[ERROR] 'pkg-config' not found, aborting..."
        raise
    except EnvironmentError:
        err = '[ERROR] Glib 2.0 library or headers not found, aborting...'
        print >> stderr, err
        raise
    else:
        sources = [
            'itools/xml/parser.c', 'itools/xml/doctype.c', 'itools/xml/arp.c',
            'itools/xml/pyparser.c']
        extension = Extension('itools.xml.parser', sources, **flags)
        ext_modules.append(extension)

    # PDF indexation
    try:
        flags = get_compile_flags(
            'pkg-config --cflags --atleast-version=0.20.0 --libs poppler fontconfig')
    except EnvironmentError:
        err = "[WARNING] poppler headers not found, PDF indexation won't work"
        print >> stderr, err
    else:
        sources = ['itools/pdf/pdftotext.cc']
        extension = Extension('itools.pdf.pdftotext', sources, **flags)
        ext_modules.append(extension)

    # DOC indexation
    try:
        flags = get_compile_flags('wv2-config --cflags --libs')
    except EnvironmentError:
        err = "[WARNING] wv2 not found, DOC indexation won't work"
        print >> stderr, err
    else:
        sources = ['itools/office/doctotext.cc']
        extension = Extension('itools.office.doctotext', sources, **flags)
        ext_modules.append(extension)

    # libsoup wrapper
    line = 'pkg-config --cflags --libs gthread-2.0 pygobject-2.0 libsoup-2.4'
    try:
        flags = get_compile_flags(line)
    except EnvironmentError:
        err = "[WARNING] libsoup not found, itools.web won't work"
        print >> stderr, err
    else:
        for include in flags['include_dirs']:
            if include.endswith('/libsoup-2.4'):
                flags['include_dirs'].append('%s/libsoup' % include)
                break
        sources = ['itools/web/soup.c']
        extension = Extension('itools.web.soup', sources, **flags)
        ext_modules.append(extension)

    # Ok
    setup(ext_modules=ext_modules)

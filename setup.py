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


# FIXME Information to be moved to setup.conf
classifiers = ['Development Status :: 3 - Alpha',
               'Intended Audience :: Developers',
               'License :: OSI Approved :: GNU General Public License (GPL)',
               'Programming Language :: Python',
               'Topic :: Internet',
               'Topic :: Internet :: WWW/HTTP',
               'Topic :: Software Development',
               'Topic :: Software Development :: Internationalization',
               'Topic :: Software Development :: Libraries',
               'Topic :: Software Development :: Libraries :: Python Modules',
               'Topic :: Software Development :: Localization',
               'Topic :: Text Processing',
               'Topic :: Text Processing :: Markup',
               'Topic :: Text Processing :: Markup :: XML']



if __name__ == '__main__':
    cparser = Extension('itools.xml.parser',
                        sources=['xml/parser.c', 'xml/doctype.c',
                                 'xml/arp.c', 'xml/pyparser.c'],
                        libraries=['glib-2.0'])

    setup(classifiers=classifiers, ext_modules=[cparser])

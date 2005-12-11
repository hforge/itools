# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
from distutils.core import setup
from distutils.command.build_py import build_py
from os.path import join

# Import from itools
from itools import build_py_fixed



setup(
    name = "portal1",
    version = "0.1",
    author = u"Luis Belmar-Letelier",
    author_email = "luis@itaapy.com",
    license = "GNU General Public License",
    url = "http://www.ikaaro.org",
    description="Portal 1 (example of itools.cms)",
    package_dir = {'portal1': ''},
    packages = ['portal1'],
    classifiers = ['Development Status :: 3 - Alpha',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: GNU General Public License (GPL)',
                   'Programming Language :: Python',
                   'Topic :: Internet'],
    package_data = {'portal1': ['README', join('ui', 'portal', '*.x*ml')]},
    cmdclass={'build_py': build_py_fixed},
    )

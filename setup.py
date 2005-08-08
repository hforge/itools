# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2002-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#                    2005 Luis Belmar Leteliet <luis@itaapy.com>
#                    2005 Hervé Cauwelier <herve@oursours.net>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA

"""
This script can be tested with the folowing::

  make clean 
  python setup.py -q clean sdist
  cd dist
  tar xzf itools-0.7.1.tar.gz
  cd itools-0.7.1
  sudo python setup.py -q install

Make sure the following files are shipped:
  - Changelog
  - Makefile
  - i18n/languages.txt

Note the path separator may vary on your platform.
"""


# Import Python modules
from distutils.core import setup
from distutils.command.install_data import install_data
import os


# XXX make data installed as Python modules
# In Python 2.4, the new package_data makes it damn easier.
#
class install_module_data(install_data):
    def finalize_options (self):
        self.set_undefined_options('install',
                                   ('install_purelib', 'install_dir'),
                                   ('root', 'root'),
                                   ('force', 'force'),
                                   )


description = """itools is a Python library, it groups a number of packages
into a single meta-package for easier development and deployment. The packages
included are:

 - itools.catalog
 - itools.datatypes
 - itools.gettext
 - itools.handlers
 - itools.html
 - itools.i18n
 - itools.ical
 - itools.resources
 - itools.rss
 - itools.schemas
 - itools.tmx
 - itools.uri
 - itools.web
 - itools.workflow
 - itools.xhtml
 - itools.xliff
 - itools.xml
"""

setup(name = "itools",
      version = "0.10.0",
      author = "J. David Ibáñez",
      author_email = "jdavid@itaapy.com",
      license = "GNU Lesser General Public License",
      url = "http://www.ikaaro.org",
      description="Misc. tools: uri, resources, handlers, i18n, workflow",
      long_description=description,
      package_dir = {'itools': ''},
      packages = ['itools',
                  'itools.catalog',
                  'itools.datatypes',
                  'itools.handlers',
                  'itools.gettext',
                  'itools.html',
                  'itools.i18n',
                  'itools.ical',
                  'itools.resources',
                  'itools.rss',
                  'itools.schemas',
                  'itools.tmx',
                  'itools.uri',
                  'itools.web',
                  'itools.workflow',
                  'itools.xhtml',
                  'itools.xliff',
                  'itools.xml'],
      classifiers = ['Development Status :: 3 - Alpha',
                     'Intended Audience :: Developers',
                     ('License :: OSI Approved :: GNU Library or Lesser General'
                      ' Public License (LGPL)'),
                     'Programming Language :: Python',
                     'Topic :: Internet',
                     'Topic :: Internet :: WWW/HTTP',
                     'Topic :: Software Development',
                     'Topic :: Software Development :: Internationalization',
                     'Topic :: Software Development :: Libraries',
                     ('Topic :: Software Development :: Libraries :: Python'
                      ' Modules'),
                     'Topic :: Software Development :: Localization',
                     'Topic :: Text Processing',
                     'Topic :: Text Processing :: Markup',
                     'Topic :: Text Processing :: Markup :: XML'],
      data_files=[('itools', ['Changelog']),
                  (os.path.join('itools', 'i18n'),
                   [os.path.join('i18n', 'languages.txt')])],
      scripts = [os.path.join('scripts', 'igettext.py')],
      cmdclass={'install_data': install_module_data},
      )

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
  - zope/localroles.dtml

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


# XXX itools.zope.zmi shouldn't be a Python package, but this is the
# quickest workaround I found to install this directory.
description = """Itools is a Python package that encapsulates several Python
tools developed by the Itaapy company and other developers. The provided
tools are:

 * itools.uri -- an API to manage URIs, to identify and locate resources.

 * itools.types -- several type marshalers for basic types (integer, date,
   etc.) and not so basic types (filenames, XML qualified names, etc.)

 * itools.resources -- an abstraction layer over resources that let to
   manage them with a consistent API, independently of where they are stored.

 * itools.handlers -- resource handlers infrastructure (resource
   handlers are non persistent classes that add specific semantics to
   resources). This package also includes several handlers out of the
   box.

 * itools.gettext -- resource handlers for PO and MO files.

 * itools.xml -- includes an intuitive event driven XML parser, a handler
   for XML documents, and the Simple Template Language.

 * itools.xhtml -- resource handlers for XHTML documents.

 * itools.html -- resource handlers for HTML documents.

 * itools.i18n -- tools for language negotiation and text segmentation.

 * itools.workflow -- represent workflows as automatons, objects can move
   from one state to another through transitions, classes can add specific
   semantics to states and transitions.

 * itools.catalog -- An Index & Search engine.
"""

setup(name = "itools",
      version = "0.8.1",
      author = "J. David Ibáñez",
      author_email = "jdavid@itaapy.com",
      license = "GNU Lesser General Public License",
      url = "http://www.ikaaro.org",
      description="Misc. tools: uri, resources, handlers, i18n, workflow",
      long_description=description,
      package_dir = {'itools': ''},
      packages = ['itools',
                  'itools.uri',
                  'itools.types',
                  'itools.resources',
                  'itools.handlers',
                  'itools.gettext',
                  'itools.catalog',
                  'itools.i18n',
                  'itools.workflow',
                  'itools.xml',
                  'itools.xhtml',
                  'itools.html',
                  'itools.zope'],
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
                  (os.path.join('itools', 'zope'),
                   [os.path.join('zope', 'localroles.dtml')]),
                  (os.path.join('itools', 'i18n'),
                   [os.path.join('i18n', 'languages.txt')])],
      scripts = [os.path.join('i18n', 'igettext.py')],
      cmdclass={'install_data': install_module_data},
      )

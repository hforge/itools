# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2002-2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#                    2005 Luis Belmar Leteliet <luis@itaapy.com>
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

  sudo rm -r /usr/lib/python2.3/site-packages/itools
  sudo make clean 
  python setup.py -q clean sdist
  cd dist
  tar xzf itools-0.6.4.tar.gz
  cd itools-0.6.4
  sudo python setup.py -q install

We test the fact that Changelog, txt and dtml file are in site-packages::

  ls -lah /usr/lib/python2.3/site-packages/itools/Changelog
  find /usr/lib/python2.3/site-packages/itools/ -name "*.dtml"
  find /usr/lib/python2.3/site-packages/itools/ -name "*.txt"
"""


# Import Python modules
from distutils.command import build_py
from distutils.core import setup
from glob import glob
import os, sys
import string


distutils_path = sys.modules['distutils'].__path__[0]
python_path, trash = os.path.split(distutils_path)
itools_path = os.path.join(python_path, 'site-packages', 'itools')


# XXX itools.zope.zmi shouldn't be a Python package, but this is the
# quickest workaround I found to install this directory.
description = """Itools is a Python package that encapsulates several Python
tools developed by the Itaapy company and other developers. The provided
tools are:

 * itools.uri -- an API to manage URIs, to identify and locate resources.

 * itools.resources -- an abstraction layer over resources that let to
   manage them with a consistent API, independently of where they are stored.

 * itools.handlers -- resource handlers infrastructure (resource
   handlers are non persistent classes that add specific semantics to
   resources). This package also includes several handlers out of the
   box.

 * itools.xml -- XML infrastructure, includes resource handlers for XML,
   XHTML and HTML documents. Plus the Simple Template Language.

 * itools.i18n -- tools for language negotiation and text segmentation.

 * itools.workflow -- represent workflows as automatons, objects can move
   from one state to another through transitions, classes can add specific
   semantics to states and transitions.

 * itools.catalog -- An Index & Search engine.
"""

setup(name = "itools",
      version = "0.7.0",
      author = "J. David Ibáñez",
      author_email = "jdavid@itaapy.com",
      license = "GNU Lesser General Public License",
      url = "http://www.ikaaro.org",
      description="Misc. tools: uri, resources, handlers, i18n, workflow",
      long_description=description,
      package_dir = {'itools': ''},
      packages = ['itools', 'itools.catalog', 'itools.handlers', 'itools.i18n',
                  'itools.resources', 'itools.workflow', 'itools.xml',
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
        data_files = [(itools_path, ['Changelog']), 
                      (os.path.join(itools_path, ('zope')), 
                       ['zope/localroles.dtml']),
                      (os.path.join(itools_path, ('i18n')), 
                       ['i18n/languages.txt']), 
                     ],
      scripts = ['i18n/igettext.py'],
      )

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
  tar xzf itools-0.11.0.tar.gz
  cd itools-0.11.0
  sudo python setup.py -q install

Make sure the following files are shipped:
  - Changelog
  - Makefile
  - i18n/languages.txt

Note the path separator may vary on your platform.
"""


# Import from the Standard Library
from distutils.core import setup
from distutils.command.build_py import build_py
import os

class build_py_fixed(build_py):
    """http://sourceforge.net/tracker/index.php?func=detail&aid=1183712&group_id=5470&atid=305470"""
    def get_data_files(self):
        """Generate list of '(package,src_dir,build_dir,filenames)' tuples"""
        data = []
        if not self.packages:
            return data
        for package in self.packages:
            # Locate package source directory
            src_dir = self.get_package_dir(package)

            # Compute package build directory
            build_dir = os.path.join(*([self.build_lib] + package.split('.')))

            # Length of path to strip from found files
            if src_dir:
                plen = len(src_dir)+1
            else:
                plen = 0

            # Strip directory from globbed filenames
            filenames = [
                file[plen:] for file in self.find_data_files(package, src_dir)
                ]
            data.append((package, src_dir, build_dir, filenames))
        return data


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
      version = "0.11.0",
      author = u"J. David Ibáñez",
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
      package_data = {'itools': ['Changelog'],
                      'itools.catalog': [os.path.join('tests', '*.txt')],
                      'itools.i18n': ['languages.txt'],
                      'itools.resources': [os.path.join('tests', 'index.html.en')],
                      'itools.rss': ['*.html', '*.rss', '*.xml'],
                      'itools.tmx': ['localizermsgs.tmx'],
                      'itools.workflow': ['HOWTO.txt', 'TODO.txt'],
                      'itools.xliff': ['gettext_en_es.xlf'],
                      'itools.xml': ['bench_parser.xml']},
      scripts = [os.path.join('scripts', 'igettext.py')],
      cmdclass={'build_py': build_py_fixed},
      )

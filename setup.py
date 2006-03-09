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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

"""
This script can be tested with the folowing::

  make clean
  python setup.py -q clean sdist
  cd dist
  tar xzf itools-0.12.3.tar.gz
  cd itools-0.12.3
  sudo python setup.py -q install

Make sure the following files are shipped:
  - Changelog
  - Makefile
  - i18n/languages.txt

Note the path separator may vary on your platform.
"""


# Import from the Standard Library
from distutils.core import setup
from os.path import join

# Import from itools
from __init__ import build_py_fixed, __version__



description = """itools is a Python library, it groups a number of packages
into a single meta-package for easier development and deployment. The packages
included are:

 - itools.catalog
 - itools.cms
 - itools.csv
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

setup(
    name = "itools",
    version = __version__,
    # XXX Broken distutils, "sdist" don't likes unicode strings, and "register"
    # don't likes normal strings.
    author = u"J. David Ibáñez".encode('UTF-8'),
    author_email = "jdavid@itaapy.com",
    license = "GNU Lesser General Public License",
    url = "http://www.ikaaro.org",
    description="A Python library which provides a wide range of capabilities",
    long_description=description,
    package_dir = {'itools': ''},
    packages = ['itools',
                'itools.catalog',
                'itools.cms',
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
                'itools.xml',
                'itools.csv'],
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
    package_data = {
    'itools': ['version.txt'],
    'itools.cms': [
    join('locale', '*.po'),
    join('locale', '*.mo'),
    join('locale', 'locale.pot'),
    join('ui', '*.x*ml.??'),
    join('ui', '*.js'),
    join('ui', '*.css'),
    join('ui', '*.xml'),
    join('ui', 'calendar', '*.js'),
    join('ui', 'calendar', '*.css'),
    join('ui', 'calendar', 'README'),
    join('ui', 'calendar', 'lang', '*.js'),
    join('ui', 'classic', '*.css'),
    join('ui', 'classic', '*.x*ml.??'),
    join('ui', 'classic', 'images', '*.png'),
    join('ui', 'images', '*.png'),
    join('ui', 'images', '*.gif'),
    join('ui', 'images', 'epoz', '*.gif'),
    join('ui', 'surf', '*.css'),
    join('ui', 'surf', '*.x*ml.??'),
    join('ui', 'surf', 'images', '*.gif'),
    join('ui', 'surf', 'images', '*.jpg'),
    join('ui', 'surf', 'images', '*.png'),
    join('ui', 'aruni', '*.css'),
    join('ui', 'aruni', '*.js'),
    join('ui', 'aruni', '*.x*ml.??'),
    join('ui', 'aruni', 'ie7', '*.gif'),
    join('ui', 'aruni', 'ie7', '*.htc'),
    join('ui', 'aruni', 'ie7', '*.js'),
    join('ui', 'aruni', 'ie7', '*.txt'),
    join('ui', 'aruni', 'images', '*.png'),
    join('ui', 'aruni', 'images', '*.jpg'),
    join('ui', 'web_site_templates', 'community', '*.x*ml.??'),
    join('ui', 'web_site_templates', 'community', '*.jpg'),
    join('ui', 'web_site_templates', 'community', '*.png'),
    join('ui', 'web_site_templates', 'community', 'skin', '*.x*ml.??'),
    join('ui', 'web_site_templates', 'community', 'skin', '*.css'),
    join('ui', 'web_site_templates', 'community', 'skin', '*.png'),
    join('zmi', '*.dtml'),
    join('zmi', '*.png'),
    join('zmi', '*.xml'),
    ],
    'itools.catalog': [join('tests', '*.txt')],
    'itools.i18n': ['languages.txt'],
    'itools.resources': [join('tests', 'index.html.en')],
    'itools.rss': ['*.html', '*.rss', '*.xml'],
    'itools.tmx': ['localizermsgs.tmx'],
    'itools.workflow': ['HOWTO.txt', 'TODO.txt'],
    'itools.xliff': ['gettext_en_es.xlf'],
    'itools.xml': ['bench_parser.xml'],
    'itools.csv': ['*.csv']},
    scripts = [join('scripts', 'igettext.py'),
               join('scripts', 'icms.py'),
               join('scripts', 'igraph.py'),],
    cmdclass={'build_py': build_py_fixed},
    )

# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2002-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#                    2005 Luis Belmar Leteliet <luis@itaapy.com>
#                    2005 Hervé Cauwelier <herve@oursours.net>
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
import os

# Import from itools
from __init__ import __version__
from utils import start_local_import, end_local_import, build_py_fixed
############################################################################
# START HACK
start_local_import()
from resources import get_resource
from handlers.config import Config
end_local_import()
# END HACK
############################################################################



config = Config(get_resource('config'))


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


# The package name
package_name = config.get_value('name')

# The list of sub-packages
subpackages = config.get_value('packages').split()

# The data in the packages
packages = [package_name]
package_data = {package_name: []}
for subpackage_name in subpackages:
    packages.append('%s.%s' % (package_name, subpackage_name))


if not os.path.exists('MANIFEST'):
    os.system('git-ls-files > MANIFEST')

for line in open('MANIFEST').readlines():
    line = line.strip()
    # Python files are included by default
    if line.endswith('.py'):
        continue

    path = line.split('/')
    n = len(path)
    if n == 1:
        package_data[package_name].append(line)
    elif path[0] == 'locale':
        package_data[package_name].append(line)
    elif path[0] in subpackages:
        files = package_data.setdefault('%s.%s' % (package_name, path[0]), [])
        files.append(os.path.join(*path[1:]))

# The scripts
scripts = config.get_value('scripts').split()
scripts = [ os.path.join(*['scripts', x]) for x in scripts ]


setup(name = package_name,
      version = __version__,
      # Metadata
      # XXX Broken distutils, "sdist" don't likes unicode strings, and
      # "register" don't likes normal strings.
      author = config.get_value('author_name'),
      author_email = config.get_value('author_email'),
      license = config.get_value('license'),
      url = config.get_value('url'),
      description = config.get_value('description'),
      long_description = description,
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
                     'Topic :: Text Processing :: Markup :: XML'],
      # Packages
      package_dir = {package_name: ''},
      packages = packages,
      package_data = package_data,
      # Scripts
      scripts = scripts,
      # XXX broken distutils
      cmdclass={'build_py': build_py_fixed},
      )

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2006, 2010 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2006-2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2007-2008, 2010 Sylvain Taverne <taverne.sylvain@gmail.com>
# Copyright (C) 2008 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2008 Wynand Winterbach <wynand.winterbach@gmail.com>
# Copyright (C) 2009 Dumont Sébastien <sebastien.dumont@itaapy.com>
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
from optparse import OptionParser
from os import sep
from subprocess import call
import sys

# Import from itools
import itools
from itools.gettext import POFile
from itools.handlers import register_handler_class, ro_database
import itools.html
import itools.python
import itools.stl
import itools.pdf
from itools.pkg import get_config
import itools.srx
from itools.stl import STLFile
from itools.uri import Path
from itools.fs import lfs, WRITE


# FIXME We register STLFile to override get_units of XHTMLFile handler
# (See bug #864)
register_handler_class(STLFile)


def write(text):
    sys.stdout.write(text)
    sys.stdout.flush()



if __name__ == '__main__':
    # The command line parser
    version = 'itools %s' % itools.__version__
    description = ('Updates the message catalogs (POT and PO files) in the'
                   ' "locale" directory, with the messages found in the'
                   ' source.')
    parser = OptionParser('%prog', version=version, description=description)

    parser.add_option('-s', '--srx',
                      help='Use an other SRX file than the default one.')

    options, args = parser.parse_args()
    if len(args) != 0:
        parser.error('incorrect number of arguments')

    # Read configuration for languages
    config = get_config()
    src_language = config.get_value('source_language', default='en')

    # The SRX file
    if options.srx is not None:
        srx_handler = ro_database.get_handler(options.srx)
    else:
        srx_handler = None

    # Initialize message catalog
    po = POFile()
    lines = []
    for line in open('MANIFEST').readlines():
        line = line.strip()
        if line.split(sep)[0] not in ('archive', 'docs', 'skeleton', 'test'):
            lines.append(line)

    # Process Python and HTML files
    write('* Extract text strings')
    extensions = ['.py', '.xhtml.%s' % src_language, '.xml.%s' % src_language]

    for path in lines:
        # Filter files
        for extension in extensions:
            if path.endswith(extension):
                break
        else:
            continue
        # Get the units
        write('.')
        handler = ro_database.get_handler(path)
        try:
            units = handler.get_units(srx_handler=srx_handler)
            units = list(units)
        except Exception:
            print
            print '*'
            print '* Error:', path
            print '*'
            raise

        relative_path = Path('..').resolve2(path)
        for source, context, line in units:
            po.add_unit(relative_path, source, context, line)
    print

    # Check if package is pip compatible or non
    package_root = config.get_value('package_root')
    if lfs.exists(package_root):
        locale_folder = lfs.open('{0}/locale'.format(package_root))
    else:
        locale_folder = lfs.open('locale/')

    write('* Update PO template ')
    data = po.to_str()

    # Write the po into the locale.pot
    try:
        locale_pot = locale_folder.open('locale.pot', WRITE)
    except IOError:
        # The locale.pot file does not exist create and open
        locale_pot = locale_folder.make_file('locale.pot')
    else:
        with locale_pot:
            locale_pot.write(data)

    # Update PO files
    filenames = set([ x for x in locale_folder.get_names() if x[-3:] == '.po' ])
    filenames.add('%s.po' % src_language)
    for language in config.get_value('target_languages'):
        filenames.add('%s.po' % language)
    filenames = list(filenames)
    filenames.sort()

    print '* Update PO files:'
    locale_pot_path = locale_folder.get_absolute_path('locale.pot')
    for filename in filenames:
        if locale_folder.exists(filename):
            write('  %s ' % filename)
            file_path = locale_folder.get_absolute_path(filename)
            call(['msgmerge', '-U', '-s', file_path, locale_pot_path])
        else:
            print '  %s (new)' % filename
            lfs.copy(locale_pot_path, filename)
    print

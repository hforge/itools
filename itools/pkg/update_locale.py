#!/usr/bin/env python
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
from subprocess import call
import sys

# Import from itools
from itools.gettext import POFile
from itools.handlers import register_handler_class
from itools.database.ro import ro_database
from itools.stl import STLFile
from itools.python import Python
from itools.uri import Path
from itools.fs import lfs, WRITE

# Import from here
from .utils import get_config


# FIXME We register STLFile to override get_units of XHTMLFile handler
# (See bug #864)
register_handler_class(STLFile)
register_handler_class(Python)


def write(text):
    sys.stdout.write(text)
    sys.stdout.flush()


def update_locale(srx_handler, exclude_folders, no_wrap=False):
    # Read configuration for languages
    config = get_config()
    src_language = config.get_value('source_language', default='en')

    # Get local folder
    package_root = config.get_value('package_root')
    if lfs.exists(package_root):
        locale_folder_path = Path(f'{package_root}/locale')
    else:
        locale_folder_path = Path('locale/')
    locale_folder = lfs.open(locale_folder_path)

    # Initialize message catalog
    po = POFile()
    lines = []
    for line in open('MANIFEST').readlines():
        line = line.strip()
        exclude_folder = False
        for x in exclude_folders:
            if line.startswith(x):
                exclude_folder = True
                break
        if exclude_folder is False:
            lines.append(line)

    # Process Python and HTML files
    write('* Extract text strings')
    extensions = [
        '.py',
        '.js',
        f'.xhtml.{src_language}',
        f'.xml.{src_language}',
        f'.html.{src_language}']

    for path in lines:
        # Filter files
        for extension in extensions:
            if path.endswith(extension):
                break
        else:
            continue
        # Get the units
        write('.')
        try:
            handler = ro_database.get_handler(path)
        except Exception:
            print("*")
            print(f"* Error: {path}")
            print("*")
            raise
        try:
            units = handler.get_units(srx_handler=srx_handler)
            units = list(units)
        except Exception:
            print("*")
            print(f"* Error: {path}")
            print("*")
            raise

        relative_path = locale_folder_path.get_pathto(path)
        for source, context, line in units:
            po.add_unit(relative_path, source, context, line)

    write('* Update PO template ')
    data = po.to_str()

    # Write the po into the locale.pot
    try:
        locale_pot = locale_folder.open('locale.pot', WRITE, text=True)
    except OSError:
        # The locale.pot file does not exist create and open
        locale_pot = locale_folder.make_file('locale.pot')
    else:
        with locale_pot:
            locale_pot.write(data)

    # Update PO files
    filenames = { x for x in locale_folder.get_names() if x[-3:] == '.po' }
    filenames.add(f'{src_language}.po')
    for language in config.get_value('target_languages'):
        filenames.add(f'{language}.po')
    filenames = list(filenames)
    filenames.sort()

    print("* Update PO files:")
    locale_pot_path = locale_folder.get_absolute_path('locale.pot')
    for filename in filenames:
        if locale_folder.exists(filename):
            write(f'  {filename} ')
            file_path = locale_folder.get_absolute_path(filename)
            if no_wrap:
                call(['msgmerge', '--no-wrap', '-U', '-s', file_path, locale_pot_path])
            else:
                call(['msgmerge', '-U', '-s', file_path, locale_pot_path])
        else:
            print(f"  {filename} (new)")
            file_path = locale_folder.get_absolute_path(filename)
            lfs.copy(locale_pot_path, file_path)

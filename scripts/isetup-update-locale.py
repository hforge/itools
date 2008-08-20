#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
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
from os import system, sep
from os.path import basename
import sys

# Import from itools
import itools
from itools.datatypes import FileName
from itools.gettext import Message, POFile
from itools.handlers import Python, ConfigFile
from itools.html import XHTMLFile
import itools.stl
from itools import vfs
from itools.vfs import WRITE


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

    options, args = parser.parse_args()
    if len(args) != 0:
        parser.error('incorrect number of arguments')

    # Read configuration for languages
    config = ConfigFile('setup.conf')
    source_language = config.get_value('source_language', default='en')

    # Initialize message catalog
    po = POFile()
    lines = []
    for line in open('MANIFEST').readlines():
        line = line.strip()
        if line.split(sep)[0] not in ('skeleton', 'test'):
            lines.append(line)

    # Process Python files
    write('* Extract text strings from Python files')
    for path in lines:
        if path.endswith('.py') and path != 'utils.py':
            write('.')
            handler = Python(path)
            for value, references in handler.get_units():
                message = Message([], [value], [u''], references)
                if len(message.msgid[0]) > 2:
                    po.set_message(message)
    print

    # Process XHTML files
    paths = []
    for path in lines:
        name = basename(path)
        name, extension, language = FileName.decode(name)
        if extension in ('xhtml', 'xml') and language == source_language:
            paths.append(path)
    if paths:
        write('* Extract text strings from XHTML files')
        for path in paths:
            write('.')
            handler = XHTMLFile(path)
            try:
                messages = handler.get_units()
                messages = list(messages)
            except:
                print
                print '*'
                print '* Error:', path
                print '*'
                raise
            for value, references in messages:
                message = Message([], [value], [u''], references)
                if len(message.msgid[0]) > 1:
                    po.set_message(message)
        print

    # Update locale.pot
    if not vfs.exists('locale/locale.pot'):
        vfs.make_file('locale/locale.pot')

    write('* Update PO template ')
    data = po.to_str()
    file = vfs.open('locale/locale.pot', WRITE)
    try:
        file.write(data)
    finally:
        file.close()
    print

    # Update PO files
    folder = vfs.open('locale')
    filenames = set([ x for x in folder.get_names() if x[-3:] == '.po' ])
    filenames.add('%s.po' % source_language)
    for language in config.get_value('target_languages', default='').split():
        filenames.add('%s.po' % language)
    filenames = list(filenames)
    filenames.sort()

    print '* Update PO files:'
    for filename in filenames:
        if folder.exists(filename):
            write('  %s ' % filename)
            system('msgmerge -U -s locale/%s locale/locale.pot' % filename)
        else:
            print '  %s (new)' % filename
            folder.copy('locale.pot', filename)
    print

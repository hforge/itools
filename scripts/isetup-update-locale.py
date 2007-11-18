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
import os
import sys

# Import from itools
import itools
from itools.gettext import PO
from itools.handlers import Python, ConfigFile
from itools.html import XHTMLFile
import itools.stl
from itools import vfs



if __name__ == '__main__':
    # The command line parser
    version = 'itools %s' % itools.__version__
    description = ('Updates the message catalogs (POT and PO files) in the'
                   ' "locale" directory, with the messages found in the'
                   ' source.')
    parser = OptionParser('%prog',
                          version=version, description=description)

    options, args = parser.parse_args()
    if len(args) != 0:
        parser.error('incorrect number of arguments')

    # Read configuration for languages
    config = ConfigFile('setup.conf')
    source_language = config.get_value('source_language', default='en')

    # Initialize message catalog
    po = PO()

    # Process Python files
    print '(1) Processing Python files',
    sys.stdout.flush()
    for line in open('MANIFEST').readlines():
        path = line.strip()
        if (not path.endswith('.py') or 'test_' in path or
                path == 'utils.py' or path.startswith('skeleton')):
            continue
        sys.stdout.write('.')
        sys.stdout.flush()
        handler = Python(path)
        for msgid, line_number in handler.get_messages():
            if len(msgid) > 2:
                po.set_message(msgid, references={path: [line_number]})
    print ' OK'

    # Process XHTML files
    print '(2) Processing XHTML files',
    sys.stdout.flush()
    for line in open('MANIFEST').readlines():
        path = line.strip()
        if (not (path.endswith('.xhtml.' + source_language) or
                path.endswith('.xml.' + source_language)) or
                path.startswith('skeleton')):
            continue
        sys.stdout.write('.')
        sys.stdout.flush()
        handler = XHTMLFile(path)
        messages = handler.get_messages()
        try:
            messages = list(messages)
        except:
            print
            print
            print 'ERROR:', path
            print
            raise
        for msgid, line_number in messages:
            if len(msgid) > 1:
                po.set_message(msgid, references={path: [line_number]})
    print ' OK'

    # Update locale.pot
    print '(3) Updating "locale/locale.pot"',
    sys.stdout.flush()
    open('locale/locale.pot', 'w').write(po.to_str())
    print 'OK'

    # Update language files
    print '(4) Updating language files:'
    print '',
    sys.stdout.flush()
    folder = vfs.open('locale')
    for filename in folder.get_names():
        if not filename.endswith('.po'):
            continue
        print filename,
        sys.stdout.flush()
        os.system('msgmerge -U -s locale/%s locale/locale.pot' % filename)

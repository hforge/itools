# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2002-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#               2005 Nicolas Oyez <noyez@itaapy.com>
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
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

# Import from the Standard Library
import logging
import logging.config
import os

# Import from itools
from itools import get_abspath
from itools.gettext import domains

# Import from itools
import Root
from Folder import Folder
import Document
import File
import csv
import flash
import html
import images
import msoffice
import openoffice
import pdf
import text



#############################################################################
# Logging facilities
#############################################################################
filename = get_abspath(globals(), 'logging.conf')
logging.config.fileConfig(filename)


###########################################################################
# Register
###########################################################################
Folder.register_document_type(Folder)
Folder.register_document_type(File.File)
Folder.register_document_type(text.Text)
Folder.register_document_type(Document.HTML)

# Register domain (i18n)
domains.register_domain('ikaaro', get_abspath(globals(), 'locale'))


###########################################################################
# Check for required software
###########################################################################
cmds = ['xlhtml', 'pdftotext', 'catdoc', 'ppthtml', 'iconv', 'links',
        'unzip', 'pdftohtml', 'wvHtml']

paths = os.getenv('PATH').split(':')
all_names = set()
for path in paths:
    path = path.strip()
    try:
        names = os.listdir(path)
    except OSError:
        pass
    else:
        all_names = all_names.union(names)

for name in cmds:
    if name not in all_names:
        print 'You need to install the command "%s".' % name

# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2005 Nicolas Oyez <nicoyez@gmail.com>
# Copyright (C) 2006 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2007 Hervé Cauwelier <herve@itaapy.com>
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
import os

# Import from itools
from itools import get_abspath
from itools.gettext import register_domain

# Import from itools.cms
import root
from folder import Folder
from file import File
import binary
import csv
import handlers
import html
from html import XHTMLFile as Document
import ical
import text
from forum import Forum
from tracker import Tracker
try:
    import wiki
except ImportError:
    wiki = None



###########################################################################
# Register
###########################################################################
Folder.register_document_type(Folder)
Folder.register_document_type(File)
Folder.register_document_type(text.Text)
Folder.register_document_type(html.XHTMLFile)
Folder.register_document_type(ical.Calendar)
Folder.register_document_type(ical.CalendarTable)
Folder.register_document_type(Forum)
Folder.register_document_type(Tracker)
if wiki is not None:
    Folder.register_document_type(wiki.WikiFolder)


###########################################################################
# Check for required software
###########################################################################
cmds = ['wvText', 'xlhtml', 'ppthtml', 'pdftotext', 'unrtf']

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

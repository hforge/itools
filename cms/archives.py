# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
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
from zipfile import ZipFile
from tarfile import TarFile
from cStringIO import StringIO

# Import from itools
from itools.handlers.archive import (Archive as iArchive, ZipArchive as
                                     iZipArchive, TarArchive as iTarArchive,
                                     BZ2Proxy)
from itools.stl import stl

# Import from itools.cms
from File import File
from registry import register_object_class


class Archive(File, iArchive):

    class_id = 'Archive'
    class_icon16 = 'images/Archive16.png'
    class_icon48 = 'images/Archive48.png'


    #######################################################################
    # View
    view__access__ = 'is_allowed_to_view'
    view__label__ = u'View'
    view__sublabel__ = u'View'
    def view(self, context):
        namespace = {}
        contents = self.get_contents()
        namespace['contents'] = '\n'.join(contents)

        handler = self.get_handler('/ui/Archive_view.xml')
        return stl(handler, namespace)



register_object_class(Archive)

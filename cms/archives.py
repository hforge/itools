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
    class_version = '20060518'
    class_icon16 = 'images/Archive16.png'
    class_icon48 = 'images/Archive48.png'


    #######################################################################
    # View
    view__access__ = 'is_allowed_to_view'
    view__label__ = u'View'
    view__sublabel__ = u'View'
    def view(self):
        namespace = {}

        contents = self.get_contents()
        namespace['contents'] = '\n'.join(contents)

        handler = self.get_handler('/ui/Archive_view.xml')

        return stl(handler, namespace)



register_object_class(Archive)



class ZipArchive(Archive, iZipArchive):

    class_id = 'application/zip'
    class_title = u"Zip Archive"

    def get_contents(self):
        archive = self.resource
        archive.open()
        zip = ZipFile(archive)
        contents = zip.namelist()
        zip.close()
        archive.close()

        return contents


register_object_class(ZipArchive)



class TarArchive(Archive, iTarArchive):

    class_id = 'application/x-tar'
    class_title = u"Tar Archive"

    def get_contents(self):
        name = self.name.encode('UTF-8')
        archive = StringIO(self.to_str())
        if name.endswith('gz'):
            # try gzip support
            import gzip
            mode = 'r|gz'
        elif name.endswith('.bz2'):
            # try bz2 support
            import bz2
            mode = 'r|'
            archive = BZ2Proxy(archive, 'r')
        else:
            mode = 'r|'
        tar = TarFile.open(name=name, mode=mode, fileobj=archive)
        contents = tar.getnames()
        tar.close()

        return contents


register_object_class(TarArchive)

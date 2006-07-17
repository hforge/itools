# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#               2006 Hervé Cauwelier <herve@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
from cStringIO import StringIO
import mimetypes
import os
from tarfile import TarFile
import tempfile
from zipfile import ZipFile, BadZipfile

# Import from itools
from itools.resources import memory
from itools.handlers.Image import Image as iImage
from itools.handlers.archive import (Archive as iArchive, ZipArchive as
                                     iZipArchive, TarArchive as iTarArchive,
                                     BZ2Proxy)
from itools.xml import XML
from itools.html import HTML
from itools.stl import stl
from itools.web.context import get_context
from File import File
from text import Text
from registry import register_object_class


###########################################################################
# Images, Video & Flash
###########################################################################
class Image(File, iImage):

    class_id = 'image'
    class_title = u'Image'
    class_version = '20040625'
    class_icon16 = 'images/Image16.png'
    class_views = [['view'],
                   ['externaledit'],
                   ['edit_metadata_form']]


    # XXX Temporal, until icon's API is fixed
    def icons_path(self):
        return ';icon48?width=144&height=144'


    icon48__access__ = True
    def icon48(self, context):
        width = context.get_form_value('width', 48)
        height = context.get_form_value('height', 48)

        width, height = int(width), int(height)

        if not hasattr(self, '_icon'):
            self._icon = {}

        if (width, height) not in self._icon:
            thumbnail = self.get_thumbnail(width, height)
            if thumbnail is None:
                data = self.get_handler('/ui/images/Image48.png').to_str()
                self._icon[(width, height)] = data, 'png'
            else:
                self._icon[(width, height)] = thumbnail

        data, format = self._icon[(width, height)]
        response = context.response
        response.set_header('Content-Type', 'image/%s' % format)
        return data


    view__access__ = 'is_allowed_to_view'
    view__label__ = u'View'
    view__sublabel__ = u'View'
    def view(self, context):
        handler = self.get_handler('/ui/Image_view.xml')
        return handler.to_str()



class Video(File):

    class_id = 'video'
    class_title = u'Video'
    class_description = u'Video'
    class_icon48 = 'images/Flash48.png'
    class_icon16 = 'images/Flash16.png'


    view__access__ = 'is_allowed_to_view'
    view__label__ = u'View'
    view__sublabel__ = u'View'
    def view(self):
        namespace = {}
        namespace['format'] = self.get_mimetype()

        handler = self.get_handler('/ui/Video_view.xml')
        return stl(handler, namespace)



class Flash(File):

    class_id = 'application/x-shockwave-flash'
    class_title = u'Flash'
    class_description = u'Document Flash'
    class_icon48 = 'images/Flash48.png'
    class_icon16 = 'images/Flash16.png'


    view__label__ = u'View'
    view__sublabel__ = u'View'
    view__access__ = 'is_allowed_to_view'
    def view(self, context):
        handler = self.get_handler('/ui/Flash_view.xml')
        return stl(handler)


###########################################################################
# Office Documents
###########################################################################
class TempDir(object):

    def __init__(self, handler):
        self.handler = handler
        self.filename = str(handler.name)

        self.path = tempfile.mkdtemp('itools')
        file_path = os.path.join(self.path, self.filename)
        open(file_path, 'w').write(handler.to_str())


    def convert(self, cmdline, outfile=None):
        here = os.getcwd()
        os.chdir(self.path)

        cmdline = cmdline % self.filename
        cmdline = cmdline + " >stdout 2>stderr"
        os.system(cmdline)

        if outfile is None:
            self.stdout = open('stdout').read()
        else:
            self.stdout = open(outfile).read()
        self.stderr = open('stderr').read()

        os.system('rm -fr %s' % self.path)
        os.chdir(here)



class OfficeDocument(File):

    __text_output__ = None
    __html_output__ = None

    source_encoding = 'UTF-8'

    def to_text(self):
        if self.__text_output__ is not None:
            return self.__text_output__

        html = self.to_html().encode('UTF-8')
        resource = memory.File(html)
        try:
            handler = HTML.Document(resource)
            text = handler.to_text()
        except ValueError:
            context = get_context()
            context.server.log_error()
            text = u''

        self.__text_output__ = text

        return text


    def to_html(self, outfile=None):
        if self.__html_output__ is not None:
            return self.__html_output__

        temp = TempDir(self)
        temp.convert(self.source_converter, outfile=outfile)
        stdout = temp.stdout
        stderr = temp.stderr

        if stderr != "":
            text = u''
        else:
            try:
                text = unicode(stdout, self.source_encoding)
            except UnicodeDecodeError:
                encoding = Text.guess_encoding(stdout)
                text = unicode(stdout, encoding)
        self.__html_output__ = text

        return text


    def clear_cache(self):
        self.__text_output__ = None
        self.__html_output__ = None


    def upload(self, file=None, **kw):
        File.upload(self, file=file, **kw)
        self.clear_cache()


    ########################################################################
    # User interface
    view__access__ = 'is_allowed_to_view'
    view__label__ = u'View'
    view__sublabel__ = u'Preview'
    def view(self, context):
        return self.to_html()



class MSWord(OfficeDocument):

    class_id = 'application/msword'
    class_title = u'Word'
    class_description = u'Document Word'
    class_icon16 = 'images/Word16.png'
    class_icon48 = 'images/Word48.png'

    source_converter = 'wvHtml --charset=UTF-8 "%s" out.doc'

    def to_html(self):
        return OfficeDocument.to_html(self, outfile='out.doc')



class MSExcel(OfficeDocument):

    class_id = 'application/vnd.ms-excel'
    class_title = u'Excel'
    class_description = u'Document Excel'
    class_icon16 = 'images/Excel16.png'
    class_icon48 = 'images/Excel48.png'
    class_extension = '.xls'
    
    source_converter = 'xlhtml -nh "%s"'
    source_encoding='windows-1252'



class MSPowerPoint(OfficeDocument):

    class_id = 'application/vnd.ms-powerpoint'
    class_title = u'PowerPoint'
    class_description = u'Document PowerPoint'
    class_icon16 = 'images/PowerPoint16.png'
    class_icon48 = 'images/PowerPoint48.png'
    class_extension = '.ppt'

    source_converter = 'ppthtml "%s"'



class OOffice(OfficeDocument):

    def to_text(self):
        if self.__text_output__ is not None:
            return self.__text_output__

        resource = memory.File(self.to_str())
        try:
            archive = ZipFile(resource)
            content = archive.read('content.xml')
            resource = memory.File(content)
            handler = XML.Document(resource)
            text = handler.to_text()
        except BadZipfile:
            context = get_context()
            context.server.log_error()
            text = u''

        self.__text_output__ = text

        return text


    def view(self, context):
        namespace = {}
        pgraphs = self.to_text()
        pgraphs = [ l for l in pgraphs.split('\n') if l and len(l) > 1 ]
        namespace['pgraphs'] = pgraphs

        handler = self.get_handler('/ui/OOffice_view.xml')
        return stl(handler, namespace)



class OOWriter(OOffice):

    class_id = 'application/vnd.sun.xml.writer'
    class_title = u'OOo Writer'
    class_description = u'OpenOffice.org Document'
    class_icon16 = 'images/OOWriter16.png'
    class_icon48 = 'images/OOWriter48.png'
    class_extension = '.sxw'



class OOCalc(OOffice):

    class_id = 'application/vnd.sun.xml.calc'
    class_title = u'OOo Calc'
    class_description = u'OpenOffice.org Spreadsheet'
    class_icon16 = 'images/OOCalc16.png'
    class_icon48 = 'images/OOCalc48.png'
    class_extension = '.sxc'



class OOImpress(OOffice):

    class_id = 'application/vnd.sun.xml.impress'
    class_title = u'OOo Impress'
    class_description = u'OpenOffice.org Presentation'
    class_icon16 = 'images/OOImpress16.png'
    class_icon48 = 'images/OOImpress48.png'
    class_extension = '.sxi'



class PDF(OfficeDocument):

    class_id = 'application/pdf'
    class_title = u'PDF'
    class_description = u'Document PDF'
    class_icon16 = 'images/Pdf16.png'
    class_icon48 = 'images/Pdf48.png'
    class_extension = '.pdf'

    source_converter = 'pdftohtml -enc UTF-8 -p -noframes -stdout "%s"'



###########################################################################
# Archive (zip, tar)
###########################################################################
class Archive(File, iArchive):

    class_id = 'Archive'
    class_icon16 = 'images/Archive16.png'
    class_icon48 = 'images/Archive48.png'


    view__access__ = 'is_allowed_to_view'
    view__label__ = u'View'
    view__sublabel__ = u'View'
    def view(self, context):
        namespace = {}
        contents = self.get_contents()
        namespace['contents'] = '\n'.join(contents)

        handler = self.get_handler('/ui/Archive_view.xml')
        return stl(handler, namespace)



###########################################################################
# Register
###########################################################################
mimetypes.add_type('application/vnd.sun.xml.writer', '.sxw')
mimetypes.add_type('application/vnd.sun.xml.calc', '.sxc')
mimetypes.add_type('application/vnd.sun.xml.impress', '.sxi')

register_object_class(Image)
register_object_class(Video)
register_object_class(Flash)
register_object_class(MSWord)
register_object_class(MSExcel)
register_object_class(MSPowerPoint)
register_object_class(OOWriter)
register_object_class(OOCalc)
register_object_class(OOImpress)
register_object_class(PDF)
register_object_class(Archive)

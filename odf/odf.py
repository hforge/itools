# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
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
import mimetypes
from zipfile import ZipFile
from cStringIO import StringIO

# Import from itools
from itools.handlers import register_handler_class
from itools.xml.i18n import get_messages
from itools.xml import (xml_to_text, translate, OfficeDocument, stream_to_str,
                        START_ELEMENT, TEXT, stream_text_and_comment_to_unicode)

# Import
import definition
import w3


class OpenOfficeDocument(OfficeDocument):
    """
    SuperClass of OpenDocumentFormat 1.0 & 2.0
    """
    def to_text(self):
        file = StringIO(self.data)
        zip = ZipFile(file)
        content = zip.read('content.xml')
        zip.close()
        return xml_to_text(content)



class OdfDocument(OpenOfficeDocument):
    """
    Format ODF : OpenDocumentFormat 2.0
    """
    namespace = 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'

    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler',
                 'data']


    def new(self, title=''):
        self.data = None 
   

    def _load_state_from_file(self, file):
        self.data = file.read()


    def to_text(self):
        file = StringIO(self.data)
        zip = ZipFile(file)
        content = zip.read('content.xml')
        zip.close()
        return xml_to_text(content)


    def to_str(self, encoding='UTF-8'):
        return self.data


    def get_meta(self):
        """
        Return the meta informations of an ODF Document
        """
        meta = {}
        meta_tags = ['title', 'description', 'subject', 'initial-creator',
                     'creation-date', 'creator', 'date', 'keyword', 'language']
        meta_events = self.get_events('meta.xml')
        previous_tag_name = None
        for type, value, line in meta_events:
            if type == START_ELEMENT:
                tag_uri, tag_name, attributes = value
                previous_tag_name = tag_name
            elif type == TEXT:
                if previous_tag_name in meta_tags:
                    if meta.has_key(previous_tag_name):
                        meta[previous_tag_name] = '%s\n%s' % (
                                                meta[previous_tag_name], value)                                                 
                    else:
                        meta[previous_tag_name] = value
        return meta


    def get_events(self, file_name):
        zip = ZipFile(StringIO(self.data))
        content = zip.read(file_name)
        return stream_text_and_comment_to_unicode(content) 
        

    def get_messages(self):
        return get_messages(self.get_events('content.xml'))


    def translate(self, catalog):
        """
        Translate the document
        and reconstruct an odt document
        """
        content_events = self.get_events('content.xml')
        translation = translate(content_events, catalog)
        translation = stream_to_str(translation)
        # Reconstruct an Odt
        file = StringIO()
        outzip = ZipFile(file, 'w')
        zip = ZipFile(StringIO(self.data))
        for f in zip.infolist():
            if f.filename == 'content.xml':
                outzip.writestr('content.xml', translation)
            else:
                outzip.writestr(f, zip.read(f.filename))
        outzip.close()
        content = file.getvalue()
        file.close()
        return content



class ODT(OdfDocument):
    
    class_mimetypes = ['application/vnd.oasis.opendocument.text']
    class_extension = 'odt'
    namespace = 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'

    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler',
                 'data']


class ODS(OdfDocument):
  
    class_mimetypes = ['application/vnd.oasis.opendocument.spreadsheet']
    class_extension = 'ods'
    namespace = 'urn:oasis:names:tc:opendocument:xmlns:spreadsheet:1.0'

    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler',
                 'data']


class ODP(OdfDocument):

    class_mimetypes = ['application/vnd.oasis.opendocument.presentation']
    class_extension = 'odp'
    namespace = 'urn:oasis:names:tc:opendocument:xmlns:presentation:1.0'

    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler',
                 'data']


# Register handler and mimetypes
handlers = [ODT, ODS, ODP]
for handler in handlers:
    mimetypes.add_type(handler.class_mimetypes[0],
                       '.%s' %handler.class_extension)
    register_handler_class(handler)


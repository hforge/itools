# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007-2008 Sylvain Taverne <sylvain@itaapy.com>
# Copyright (C) 2008 Romain Gauthier <romain.gauthier@itaapy.com>
# Copyright (C) 2008 Wynand Winterbach <wynand.winterbach@gmail.com>
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
from zipfile import ZipFile
from cStringIO import StringIO

# Import from itools
from itools.core import add_type
from itools.stl import stl
from itools.handlers import register_handler_class, ZIPFile
from itools.xml import XMLParser, XML_DECL, START_ELEMENT, TEXT
from itools.xml import stream_to_str
from itools.xmlfile import get_units, translate


def stl_to_odt(model_odt, namespace):
    # Get the content of content.xml
    events = list(model_odt.get_events('content.xml'))
    # Apply the stl
    xml_content = stl(namespace=namespace, events=events, mode='xml')
    # Reconstruct an Odt
    file = StringIO()
    outzip = ZipFile(file, 'w')
    zip = ZipFile(StringIO(model_odt.data))
    for f in zip.infolist():
        if f.filename == 'content.xml':
            outzip.writestr('content.xml', xml_content)
        else:
            outzip.writestr(f, zip.read(f.filename))
    outzip.close()
    content = file.getvalue()
    file.close()
    return content



class OOFile(ZIPFile):
    """SuperClass of OpenDocumentFormat 1.0 & 2.0
    """

    def to_text(self):
        file = self.get_file('content.xml')
        encoding = 'utf-8'
        text = []
        for event, value, line in XMLParser(file):
            # TODO Extract some attribute values
            if event == TEXT:
                text.append(value)
            elif event == XML_DECL:
                encoding = value[1]
        return unicode(' '.join(text), encoding)



class ODFFile(OOFile):
    """Format ODF : OpenDocumentFormat 2.0
    """

    namespace = 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'

    def get_meta(self):
        """Return the meta informations of an ODF Document.
        """
        meta = {}
        meta_tags = ['title', 'description', 'subject', 'initial-creator',
                     'creation-date', 'creator', 'date', 'keyword',
                     'language']

        meta_events = self.get_events('meta.xml')
        previous_tag_name = None
        for type, value, line in meta_events:
            if type == START_ELEMENT:
                tag_uri, tag_name, attributes = value
                previous_tag_name = tag_name
            elif type == TEXT:
                if previous_tag_name in meta_tags:
                    if previous_tag_name in meta:
                        meta[previous_tag_name] = '%s\n%s' % (
                                              meta[previous_tag_name], value)
                    else:
                        meta[previous_tag_name] = value
        return meta


    def get_events(self, filename):
        content = self.get_file(filename)
        for event in XMLParser(content):
            if event == XML_DECL:
                pass
            else:
                yield event


    def get_units(self, srx_handler=None):
        for filename in ['content.xml', 'meta.xml', 'styles.xml']:
            events = self.get_events(filename)
            for message in get_units(events, srx_handler):
                # FIXME the line number has no sense here
                yield message


    def translate(self, catalog, srx_handler=None):
        """Translate the document and reconstruct an odt document.
        """
        content_events = self.get_events('content.xml')
        translation = translate(content_events, catalog, srx_handler)
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


    def greek(self):
        """Anonymize the ODF file.
        """
        class Catalog(object):
            @staticmethod
            def gettext(unit, context):
                new_unit = []
                for x, s in unit:
                    if type(s) in (str, unicode):
                        s = [ 'x' if not c.isspace() else c for c in s ]
                        s = ''.join(s)
                    new_unit.append((x, s))
                return new_unit

        return self.translate(Catalog)



class ODTFile(ODFFile):

    class_mimetypes = ['application/vnd.oasis.opendocument.text']
    class_extension = 'odt'
    namespace = 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'



class ODSFile(ODFFile):

    class_mimetypes = ['application/vnd.oasis.opendocument.spreadsheet']
    class_extension = 'ods'
    namespace = 'urn:oasis:names:tc:opendocument:xmlns:spreadsheet:1.0'



class ODPFile(ODFFile):

    class_mimetypes = ['application/vnd.oasis.opendocument.presentation']
    class_extension = 'odp'
    namespace = 'urn:oasis:names:tc:opendocument:xmlns:presentation:1.0'



# Register handler and mimetypes
for handler in [ODTFile, ODSFile, ODPFile]:
    add_type(handler.class_mimetypes[0], '.%s' % handler.class_extension)
    register_handler_class(handler)

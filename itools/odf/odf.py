# Copyright (C) 2007-2008 Sylvain Taverne <taverne.sylvain@gmail.com>
# Copyright (C) 2007-2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2008 Romain Gauthier <romain.gauthier@itaapy.com>
# Copyright (C) 2008 Wynand Winterbach <wynand.winterbach@gmail.com>
# Copyright (C) 2008-2009 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2009 Aurélien Ansel <camumus@gmail.com>
# Copyright (C) 2009 Hervé Cauwelier <herve@oursours.net>
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
from io import StringIO, BytesIO
from os.path import splitext
from random import choice
from zipfile import ZipFile

# Import from itools
from itools.core import add_type, get_abspath
from itools.fs import lfs
from itools.handlers import register_handler_class, ZIPFile
from itools.stl import stl
from itools.xml import XMLParser, XML_DECL, START_ELEMENT, TEXT
from itools.xml import stream_to_str, xml_to_text
from itools.xmlfile import get_units, translate

# Import from the Python Image Library
try:
    from PIL import Image as PILImage, ImageDraw as PILImageDraw
except ImportError:
    PILImage = None


def zip_data(source, modified_files):
    assert isinstance(source, bytes)
    inzip = ZipFile(BytesIO(source))

    file = BytesIO()
    with ZipFile(file, 'w') as outzip:
        for info in inzip.infolist():
            # Replace the data from the map
            if info.filename in modified_files:
                data = modified_files[info.filename]
                if data is None:
                    continue
            else:
                data = inzip.read(info.filename)

            # Section 17.4 says the mimetype file shall not include an extra
            # field.  So we remove it even if present in the source.
            if info.filename == 'mimetype':
                info.extra = b''

            # Ok
            outzip.writestr(info, data)

    # Ok
    content = file.getvalue()
    file.close()
    return content


def stl_to_odt(model_odt, namespace):
    # STL
    events = list(model_odt.get_events('content.xml'))
    xml_content = stl(namespace=namespace, events=events, mode='xml')
    modified_files = {'content.xml': xml_content}
    # Zip
    return zip_data(model_odt.data, modified_files)


class GreekCatalog:
    """A stupid translator.
    """

    # This table is derived from the Times New Roman font 12px
    table = [
        # 6-14
        'ijlt', 'frI', 'sJ', 'acez', 'bdghknopquvxy', 'FPS', 'ELTZ', 'BCR',
        'wADGHKNOQUVXY',
        # 16
        'm',
        # 18+19
        'MW']

    @classmethod
    def gettext(cls, unit, context):
        table = {}
        for chars in cls.table:
            for c in chars:
                table[c] = chars

        def f(c):
            if c.isspace():
                return c
            if c in table:
                return choice(table[c])
            return 'x'

        new_unit = []
        for x, s in unit:
            if type(s) is str:
                s = ''.join([f(c) for c in s])
            new_unit.append((x, s))
        return new_unit


class OOFile(ZIPFile):
    """SuperClass of OpenDocumentFormat 1.0 & 2.0
    """

    def to_text(self):
        content = self.get_file('content.xml')
        return xml_to_text(content)


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
                        meta[previous_tag_name] = f'{meta[previous_tag_name]}\n{value}'
                    else:
                        meta[previous_tag_name] = value
        return meta

    def get_events(self, filename):
        content = self.get_file(filename)
        if isinstance(content, bytes):
            content = content.decode("utf-8")

        for event in XMLParser(content):
            if event == XML_DECL:
                pass
            else:
                yield event

    def get_units(self, srx_handler=None):
        for filename in ['content.xml', 'meta.xml', 'styles.xml']:
            events = self.get_events(filename)
            yield from get_units(events, srx_handler)


    def translate(self, catalog, srx_handler=None):
        """Translate the document and reconstruct an odt document.
        """
        # Translate
        modified_files = {}
        for filename in ['content.xml', 'meta.xml', 'styles.xml']:
            events = self.get_events(filename)
            translation = translate(events, catalog, srx_handler)
            modified_files[filename] = stream_to_str(translation)

        # Zip
        return zip_data(self.data, modified_files)

    def greek(self):
        """Anonymize the ODF file.
        """
        # Verify PIL is installed
        if PILImage is None:
            err = 'The greeking feature requires the Python Imaging Library'
            raise ImportError(err)

        folder = lfs.open(get_abspath('.'))
        err = 'Unexpected "%s" file will be omitted from the greeked document'

        modified_files = {}
        for filename in self.get_contents():
            extension = splitext(filename)[1]
            startswith = filename.startswith
            # Files to keep as they are
            # TODO the manifest.xml file should be properly updated
            keep = ['mimetype', 'settings.xml', 'META-INF/manifest.xml']
            if filename in keep:
                pass

            # Content, metadata and style
            elif filename in ['content.xml', 'meta.xml', 'styles.xml']:
                events = self.get_events(filename)
                translation = translate(events, GreekCatalog)
                modified_files[filename] = stream_to_str(translation)

            # Thumbnails
            elif startswith('Thumbnails'):
                if extension == '.pdf':
                    modified_files[filename] = folder.open('thumb.pdf').read()
                elif extension == '.png':
                    modified_files[filename] = folder.open('thumb.png').read()
                else:
                    # Unexpected (TODO use the logging system)
                    modified_files[filename] = None
                    print(err % filename)

            # SVM files (usually they are in the Pictures folder)
            elif extension == '.svm':
                modified_files[filename] = folder.open('square.svm').read()

            # Pictures
            elif startswith('Pictures') or startswith('media'):
                # Try with PIL
                file = self.get_file(filename)
                file = StringIO(file)
                image = PILImage.open(file)
                format = image.format
                image = image.convert('RGB')
                image.filename = filename
                draw = PILImageDraw.Draw(image)

                # Make a cross
                h, l = image.size
                draw.rectangle((0, 0, h-1, l-1), fill="grey", outline="black")
                draw.line((0, 0, h-1, l-1), fill="black")
                draw.line((0, l-1, h-1, 0), fill="black")

                # Save
                data = StringIO()
                image.save(data, format)
                modified_files[filename] = data.getvalue()

            # Unexpected (TODO use the logging system)
            else:
                modified_files[filename] = None
                print(err % filename)

        return zip_data(self.data, modified_files)


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
    add_type(handler.class_mimetypes[0], f'.{handler.class_extension}')
    register_handler_class(handler)

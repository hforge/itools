# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Nicolas OYEZ <noyez@itaapy.com>
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

# Import from itools
from itools.handlers import Text
from itools.xml import (Parser, DOCUMENT_TYPE, START_ELEMENT, END_ELEMENT, 
                        COMMENT, TEXT)



def protect_content(s):
    return s.replace('<','&lt;').replace('>','&gt;')



class Note(object):

    def __init__(self, attributes):
        self.text = None
        self.attributes = attributes


    def to_str(self):
        s = []
        if self.attributes != {}:
            att = ['%s="%s"' % (k, self.attributes[k]) 
                  for k in self.attributes.keys() if k != 'lang']
            s.append('<note %s ' % ' '.join(att))
            if 'lang' in self.attributes.keys():
                s.append('xml:lang="%s"' % self.attributes['lang'])
            s.append('>')
        else:
            s.append('<note>')
            
        s.append(self.text)
        s.append('</note>\n')
        return ''.join(s)



class Translation(object):

    def __init__(self, attributes):
        self.source = None
        self.target = None
        self.attributes = attributes
        self.notes = []


    def to_str(self):
        s = []
        if self.attributes != {}:
            att = ['%s="%s"' % (k, self.attributes[k]) 
                  for k in self.attributes.keys() if k != 'space']
            s.append('<trans-unit %s ' % '\n'.join(att))
            if 'space' in self.attributes.keys():
                s.append('xml:space="%s"' % self.attributes['space'])
            s.append('>\n')
        else:
            s.append('<trans-unit>\n')

        if self.source:
            s.append(' <source>%s</source>\n' % protect_content(self.source))

        if self.target:
            s.append(' <target>%s</target>\n' % protect_content(self.target))

        for l in self.notes:
            s.append(l.to_str())

        s.append('</trans-unit>\n')
        return ''.join(s)



class File(object):

    def __init__(self, attributes):
        self.body = {}
        self.attributes = attributes
        self.header = []


    def to_str(self):
        s = []

        # Opent tag
        if self.attributes != {}:
            att = [' %s="%s"' % (k, self.attributes[k]) 
                  for k in self.attributes.keys() if k != 'space']
            s.append('<file %s' % '\n'.join(att))
            if 'space' in self.attributes.keys():
                s.append('xml:space="%s"' % self.attributes['space'])
            s.append('>\n')
        else:
            s.append('<file>\n')
        # The header
        if self.header:
            s.append('<header>\n')
            for l in self.header:
                s.append(l.to_str())
            s.append('</header>\n')
        # The body
        s.append('<body>\n')
        if self.body:
            mkeys = self.body.keys()
            mkeys.sort()
            msgs = '\n'.join([ self.body[m].to_str() for m in mkeys ])
            s.append(msgs)
        s.append('</body>\n')
        # Close tag
        s.append('</file>\n')

        return ''.join(s)



class XLIFF(Text):

    class_mimetypes = ['application/x-xliff']
    class_extension = 'xlf'

    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler',
                 'document_type', 'version', 'lang', 'files']


    def new(self):
        self.document_type = (
            'xliff',
            'http://www.oasis-open.org/committees/xliff/documents/xliff.dtd',
            None, False)
        self.version = '1.0'
        self.lang = None
        self.files = []


    #######################################################################
    # Load
    def _load_state_from_file(self, file):
        self.files = []
        for event, value, line_number in Parser(file.read()):
            if event == DOCUMENT_TYPE:
                self.document_type = value
            elif event == START_ELEMENT:
                namespace, local_name, attributes = value
                # Attributes, get rid of the namespace uri (XXX bad)
                aux = {}
                for attr_key in attributes:
                    attr_name = attr_key[1]
                    aux[attr_name] = attributes[attr_key]
                attributes = aux

                if local_name == 'xliff':
                    self.version = attributes['version']
                    self.lang = attributes.get('lang', None)
                elif local_name == 'file':
                    file = File(attributes)
                elif local_name == 'header':
                    notes = []
                elif local_name == 'trans-unit':
                    translation = Translation(attributes)
                    notes = []
                elif local_name == 'note':
                    note = Note(attributes)
            elif event == END_ELEMENT:
                namespace, local_name = value

                if local_name == 'file':
                    self.files.append(file)
                elif local_name == 'header':
                    file.header = notes
                elif local_name == 'trans-unit':
                    translation.notes = notes
                    file.body[translation.source] = translation
                elif local_name == 'source':
                    translation.source = text
                elif local_name == 'target':
                    translation.target = text
                elif local_name == 'note':
                    note.text = text
                    notes.append(note)
            elif event == COMMENT:
                pass
            elif event == TEXT:
                text = unicode(value, 'UTF-8')


    #######################################################################
    # Save
    #######################################################################
    def xml_header_to_str(self, encoding='UTF-8'):
        s = ['<?xml version="1.0" encoding="%s"?>\n' % encoding]
        # The document type
        if self.document_type is not None:
            s.append('<!DOCTYPE %s SYSTEM "%s">\n' % self.document_type[:2])
        return ''.join(s)


    def header_to_str(self, encoding='UTF-8'):
        s = []
        s.append('<xliff')
        if self.version:
            s.append('version="%s"' % self.version)
        if self.lang:
            s.append('xml:lang="%s"' % self.lang)
        s.append('>\n') 

        return ' '.join(s)


    def to_str(self, encoding=None):
        s = [self.xml_header_to_str(), self.header_to_str()]
        for file in self.files:
            s.append(file.to_str())
        s.append('</xliff>')

        return '\n'.join(s)


    #######################################################################
    # API
    #######################################################################
    def build(self, xml_header, version, files):
        self.document_type = xml_header['document_type']
        self.files = files
        self.version = version


    def get_languages(self):
        files_id, sources, targets = [], [], []
        for file in self.files:
            file_id = file.attributes['original']
            source = file.attributes['source-language']
            target = file.attributes.get('target-language', '')

            if file_id not in files_id:
                files_id.append(file_id)
            if source not in sources:
                sources.append(source)
            if target not in targets:
                targets.append(target)

        return ((files_id, sources, targets))

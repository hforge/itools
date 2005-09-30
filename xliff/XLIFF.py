# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Nicolas OYEZ <noyez@itaapy.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA

#import from itools
from itools.handlers.Text import Text
from itools.xml import parser



def protect_content(s):
    return s.replace('<','&lt;').replace('>','&gt;')



class Note(object):

    def __init__(self, attributes):
        self.text = None
        self.attributes = attributes


    def to_unicode(self):
        s = []
        if self.attributes != {}:
            att = [u'%s="%s"' % (k, self.attributes[k]) 
                  for k in self.attributes.keys() if k != 'lang']
            s.append(u'<note %s ' % u' '.join(att))
            if 'lang' in self.attributes.keys():
                s.append('xml:lang="%s"' % self.attributes['lang'])
            s.append(u'>')
        else:
            s.append(u'<note>')
            
        s.append(self.text)
        s.append(u'</note>\n')
        return u''.join(s)



class Translation(object):

    def __init__(self, attributes):
        self.source = None
        self.target = None
        self.attributes = attributes
        self.notes = []


    def to_unicode(self):
        s = []
        if self.attributes != {}:
            att = [u'%s="%s"' % (k, self.attributes[k]) 
                  for k in self.attributes.keys() if k != 'space']
            s.append(u'<trans-unit %s ' % u'\n'.join(att))
            if 'space' in self.attributes.keys():
                s.append('xml:space="%s"' % self.attributes['space'])
            s.append(u'>\n')
        else:
            s.append(u'<trans-unit>\n')

        if self.source:
            s.append(u' <source>%s</source>\n' % protect_content(self.source))

        if self.target:
            s.append(u' <target>%s</target>\n' % protect_content(self.target))

        for l in self.notes:
            s.append(l.to_unicode())

        s.append(u'</trans-unit>\n')
        return u''.join(s)



class File(object):

    def __init__(self, attributes):
        self.body = {}
        self.attributes = attributes
        self.header = []


    def to_unicode(self):
        s = []

        # Opent tag
        if self.attributes != {}:
            att = [u' %s="%s"' % (k, self.attributes[k]) 
                  for k in self.attributes.keys() if k != 'space']
            s.append(u'<file %s' % u'\n'.join(att))
            if 'space' in self.attributes.keys():
                s.append('xml:space="%s"' % self.attributes['space'])
            s.append(u'>\n')
        else:
            s.append(u'<file>\n')
        # The header
        if self.header:
            s.append(u'<header>\n')
            for l in self.header:
                s.append(l.to_unicode())
            s.append(u'</header>\n')
        # The body
        s.append(u'<body>\n')
        if self.body:
            mkeys = self.body.keys()
            mkeys.sort()
            msgs = u'\n'.join([ self.body[m].to_unicode() for m in mkeys ])
            s.append(msgs)
        s.append(u'</body>\n')
        # Close tag
        s.append(u'</file>\n')

        return u''.join(s)



class XLIFF(Text):

    def get_skeleton(self):
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<!DOCTYPE xliff SYSTEM "http://www.oasis-open.org/'
                'committees/xliff/documents/xliff.dtd">\n'
                '<xliff version="1.0">\n'
                '  <file original="/nothing" datatype="plaintext"\n'
                '        source-language="en">\n'
                '    <body>\n'
                '      <trans-unit id="1">\n'
                '        <source>nothing</source>\n'
                '      </trans-unit>\n'
                '    </body>\n'
                '  </file>\n'
                '</xliff>\n')


    #######################################################################
    # Load
    #######################################################################
    def _load_state(self, resource):
        state = self.state
        state.files = []
        for event, value, line_number in parser.parse(resource.read()):
            if event == parser.DOCUMENT_TYPE:
                state.document_type = value
            elif event == parser.START_ELEMENT:
                namespace, local_name, attributes = value
                # Attributes, get rid of the namespace uri (XXX bad)
                aux = {}
                for attr_key in attributes:
                    attr_name = attr_key[1]
                    aux[attr_name] = attributes[attr_key]
                attributes = aux

                if local_name == 'xliff':
                    state.version = attributes['version']
                    state.lang = attributes.get('lang', None)
                elif local_name == 'file':
                    file = File(attributes)
                elif local_name == 'header':
                    notes = []
                elif local_name == 'trans-unit':
                    translation = Translation(attributes)
                    notes = []
                elif local_name == 'note':
                    note = Note(attributes)
            elif event == parser.END_ELEMENT:
                namespace, local_name = value

                if local_name == 'file':
                    state.files.append(file)
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
            elif event == parser.COMMENT:
                pass
            elif event == parser.TEXT:
                text = unicode(value, 'UTF-8')


    #######################################################################
    # Save
    #######################################################################
    def xml_header_to_unicode(self, encoding='UTF-8'):
        state = self.state
        s = [u'<?xml version="1.0" encoding="%s"?>\n' % encoding]
        # The document type
        if state.document_type is not None:
            s.append(u'<!DOCTYPE %s SYSTEM "%s">\n' % state.document_type[:2])
        return u''.join(s)


    def header_to_unicode(self, encoding='UTF-8'):
        state = self.state
        s = []
        s.append(u'<xliff')
        if state.version:
            s.append(u'version="%s"' % state.version)
        if state.lang:
            s.append(u'xml:lang="%s"' % state.lang)
        s.append(u'>\n') 

        return u' '.join(s)


    def to_unicode(self, encoding=None):
        s = [self.xml_header_to_unicode(),
             self.header_to_unicode()]
        for file in self.state.files:
            s.append(file.to_unicode())
        s.append(u'</xliff>')

        return u'\n'.join(s)


    #######################################################################
    # API
    #######################################################################
    def build(self, xml_header, version, files):
        state = self.state
        state.document_type = xml_header['document_type']
        state.files = files
        state.version = version


    def get_languages(self):
        state = self.state

        files_id, sources, targets = [], [], []
        for file in state.files:
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

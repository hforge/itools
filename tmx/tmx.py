# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Nicolas Oyez <nicoyez@gmail.com>
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
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

# Import from itools
from itools.datatypes import XMLContent, XMLAttribute
from itools.handlers import TextFile, register_handler_class
from itools.xml import XMLParser, START_ELEMENT, END_ELEMENT, COMMENT, TEXT



# FIXME TMXNote and XLFNote are the same
class TMXNote(object):

    def __init__(self, text='', attributes=None):
        if attributes is None:
            attributes = {}

        self.text = text
        self.attributes = attributes


    def to_str(self):
        # Attributes
        attributes = []
        for attr_name in self.attributes:
            attr_value = self.attributes[attr_name]
            attr_value = XMLContent.encode(attr_value)
            if attr_name == 'lang':
                attr_name = 'xml:lang'
            attributes.append(' %s="%s"' % (attr_name, attr_value))
        attributes = ''.join(attributes)
        # Ok
        return '<note%s>%s</note>\n' % (attributes, self.text)



class Sentence(object):

    def __init__(self, attributes):
        self.attributes = attributes
        self.text = ''
        self.notes = []


    def to_str(self):
        s = []
        attributes = ['xml:lang="%s"' % self.attributes['lang']]
        for attr_name in self.attributes:
            if attr_name != 'lang':
                attributes.append('%s="%s"' % (attr_name,
                                               self.attributes[attr_name]))
        s.append('  <tuv %s>\n' % ' '.join(attributes))

        for note in self.notes:
            s.append(note.to_str())

        s.append('  <seg>%s</seg>\n' % XMLContent.encode(self.text))
        s.append('  </tuv>\n')
        return ''.join(s)



class TMXUnit(object):

    def __init__(self, attributes):
        self.attributes = attributes
        self.msgstr = {}
        self.notes = []


    def to_str(self):
        s = []
        if self.attributes != {}:
            att = [' %s="%s"' %(k, self.attributes[k])
                  for k in self.attributes.keys()]
            s.append('<tu%s>\n' % ''.join(att))
        else:
            s.append('<tu>\n')

        if self.notes:
            for l in self.notes:
                s.append(l.to_str())

        languages = self.msgstr.keys()
        languages.sort()
        for language in languages:
            s.append(self.msgstr[language].to_str())

        s.append('</tu>\n')
        return ''.join(s)



class TMXFile(TextFile):

    class_mimetypes = ['application/x-tmx']
    class_extension = 'tmx'


    def new(self):
        self.version = '1.4'
        self.header = {'o-encoding': 'utf-8', 'srclang': 'en'}
        self.header_notes = {}
        self.messages = {}


    #######################################################################
    # Load
    def _load_state_from_file(self, file):
        self.header = {}
        messages = {}
        self.header_notes = {}
        for event, value, line_number in XMLParser(file.read()):
            if event == START_ELEMENT:
                namespace, local_name, attributes = value
                # Attributes, get rid of the namespace uri (XXX bad)
                aux = {}
                for attr_key in attributes:
                    attr_name = attr_key[1]
                    aux[attr_name] = attributes[attr_key]
                attributes = aux

                if local_name == 'tmx':
                    self.version = attributes['version']
                elif local_name == 'header':
                    self.header = attributes
                    default_srclang = attributes['srclang']
                    notes = []
                elif local_name == 'note':
                    note = TMXNote(attributes=attributes)
                elif local_name == 'tu':
                    tu = TMXUnit(attributes)
                    notes = []
                elif local_name == 'tuv':
                    tuv = Sentence(attributes)
                    notes = []
                    segment = None
            elif event == END_ELEMENT:
                namespace, local_name = value
                if local_name == 'header':
                    self.header_notes = notes
                elif local_name == 'note':
                    note.text = text
                    notes.append(note)
                elif local_name == 'tu':
                    tu.notes = notes
                    srclang = tu.attributes.get('srclang', default_srclang)
                    if srclang == '*all*':
                        raise NotImplementedError, \
                              'no support for "*all*" in srclang attribute.'
                    msgid = tu.msgstr[srclang].text
                    messages[msgid] = tu
                elif local_name == 'tuv':
                    if segment is not None:
                        tuv.notes = notes
                        tuv.text = segment
                        tu.msgstr[tuv.attributes['lang']] = tuv
                elif local_name == 'seg':
                    segment = text
            elif event == COMMENT:
                pass
            elif event == TEXT:
                text = unicode(value, 'UTF-8')

        self.messages = messages


    #######################################################################
    # Save
    def to_str(self, encoding=None):
        # The XML prolog
        output = [
            '<?xml version="1.0" encoding="%s"?>\n' % encoding,
            '<!DOCTYPE tmx SYSTEM "http://www.lisa.org/tmx/tmx14.dtd">\n']

        # TMX header
        output.append('<tmx version="%s">\n' % self.version)
        attributes = [
            ' %s="%s"' % (key, XMLAttribute.encode(value))
            for key, value in self.header.items() ]
        output.append('<header%s>\n' % ''.join(attributes))
        # TMX header / notes
        for note in self.header_notes:
            output.append(note.to_str())
        output.append('</header>\n')

        # TMX body
        output.append('<body>\n')
        messages = self.messages
        msgids = messages.keys()
        msgids.sort()
        for msgid in msgids:
            output.append(messages[msgid].to_str())
        output.append('</body>\n')

        # Ok
        output.append('</tmx>\n')
        return ''.join(output)


    #######################################################################
    # API
    #######################################################################
    def get_languages(self):
        languages = []
        for m in self.messages.values():
            for l in m.msgstr.keys():
                if l not in languages:
                    languages.append(l)
        return languages


    def get_srclang(self):
        return u'%s' % self.header['srclang']


    def add_unit(self, filename, source, line):
        # FIXME Use 'filename' and 'line'
        unit = TMXUnit({})
        src_lang = self.header['srclang']
        sentence = Sentence({'lang': src_lang})
        sentence.text = source
        unit.msgstr[src_lang] = sentence
        self.messages[source] = unit
        return unit



register_handler_class(TMXFile)

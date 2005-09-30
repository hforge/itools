# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Nicolas Oyez <noyez@itaapy.com>
#               2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from itools
from itools.handlers.Text import Text
from itools.xml import parser



def protect_content(s):
    return s.replace('<','&lt;').replace('>','&gt;')



class Note(object):

    def __init__(self, text=None, attributes={}):
        self.text = text
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



class Sentence(object):

    def __init__(self, attributes):
        self.attributes = attributes
        self.text = ''
        self.notes = []


    def to_unicode(self):
        s = []
        attributes = ['xml:lang="%s"' % self.attributes['lang']]
        for attr_name in self.attributes:
            if attr_name != 'lang':
                attributes.append(u'%s="%s"' % (attr_name,
                                                self.attributes[attr_name]))
        s.append(u'<tuv %s>\n' % ' '.join(attributes))

        for note in self.notes:
            s.append(note.to_unicode())

        s.append(u'<seg>%s</seg>\n' % protect_content(self.text))
        s.append(u'</tuv>\n')
        return u''.join(s)



class Message(object):

    def __init__(self, attributes):
        self.attributes = attributes
        self.msgstr = {}
        self.notes = []


    def to_unicode(self):
        s = []
        if self.attributes != {}:
            att = [u' %s="%s"' %(k, self.attributes[k]) 
                  for k in self.attributes.keys()]
            s.append(u'<tu%s>\n' % u''.join(att))
        else:
            s.append(u'<tu>\n')
        
        if self.notes:
            for l in self.notes:
                s.append(l.to_unicode())
       
        languages = self.msgstr.keys()
        languages.sort()
        for language in languages:
            s.append(self.msgstr[language].to_unicode())
            
        s.append(u'</tu>\n')
        return u''.join(s)



class TMX(Text):

    def get_skeleton(self):
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<!DOCTYPE tmx SYSTEM "http://www.lisa.org/tmx/tmx14.dtd">\n'
                '<tmx version="1.4">\n'
                '  <header o-encoding="utf-8" srclang="fr">\n'
                '  </header>\n'
                '    <body>\n'
                '      <tu>\n'
                '        <tuv xml:lang="fr" >\n'
                '          <seg>nothing</seg>\n'
                '        </tuv>\n'
                '      </tu>\n'
                '    </body>\n'
                '</tmx>')


    #######################################################################
    # Load
    #######################################################################
    def _load_state(self, resource):
        state = self.state
        state.header = {}
        messages = {}
        state.header_notes = {}
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

                if local_name == 'tmx':
                    state.version = attributes['version']
                elif local_name == 'header':
                    state.header = attributes
                    default_srclang = attributes['srclang']
                    notes = []
                elif local_name == 'note':
                    note = Note(attributes=attributes)
                elif local_name == 'tu':
                    tu = Message(attributes)
                    notes = []
                elif local_name == 'tuv':
                    tuv = Sentence(attributes)
                    notes = []
                    segment = None
            elif event == parser.END_ELEMENT:
                namespace, local_name = value
                if local_name == 'header':
                    state.header_notes = notes
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
            elif event == parser.COMMENT:
                pass
            elif event == parser.TEXT:
                text = unicode(value, 'UTF-8')

        state.messages = messages


    #######################################################################
    # Save
    #######################################################################
    def xml_header_to_unicode(self, encoding='UTF-8'):
        state = self.state
        s = []
        # The XML declaration
        s.append(u'<?xml version="1.0" encoding="%s"?>\n' % encoding)
        # The document type
        if state.document_type is not None:
            s.append(u'<!DOCTYPE %s SYSTEM "%s">\n' % state.document_type[:2])

        return u''.join(s)


    def header_to_unicode(self, encoding='UTF-8'):
        state = self.state
        s = []
        if state.version:
            s.append(u'<tmx version="%s">\n' % state.version)
        else:
            s.append(u'<tmx>\n')
        
        if state.header != {}:
            attributes = [ u'\n%s="%s"' % (k, state.header[k])
                           for k in state.header.keys() ]
            s.append(u'<header %s>\n' % u''.join(attributes))
        else:
            s.append(u'<header>\n')

        if state.header_notes != []:
            for n in state.header_notes:
                s.append(n.to_unicode())

        s.append(u'</header>\n')
        return u''.join(s)


    def to_unicode(self, encoding=None):
        s = [self.xml_header_to_unicode(),
             self.header_to_unicode(),
             u'<body>']
        messages = self.state.messages
        msgids = messages.keys()
        msgids.sort()
        for msgid in msgids:
            s.append(messages[msgid].to_unicode())
        s.append(u'</body>')
        s.append(u'</tmx>')
        return u'\n'.join(s)


    #######################################################################
    # API
    #######################################################################
    def get_languages(self):
        state = self.state
        languages = []
        for m in state.messages.values():
            for l in m.msgstr.keys():
                if l not in languages:
                    languages.append(l)
        return languages


    def get_srclang(self):
        state = self.state
        return u'%s' % state.header['srclang']


    def build(self, xml_header, version, tmx_header, msgs):
        state = self.state
        state.document_type = xml_header['document_type']
        state.source_encoding = tmx_header['o-encoding']
        state.header = tmx_header
        state.messages = msgs
        state.version = version


Text.register_handler_class(TMX)

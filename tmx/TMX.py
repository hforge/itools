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

    def __init__(self, text, attributes={}, notes=[]):
        self.attributes = attributes
        self.text = text
        self.notes = notes

    def to_unicode(self):
        s = []
        att_lang = self.attributes['lang']
        if self.attributes != {}:
            att = [u'%s="%s"' % (k, self.attributes[k]) 
                  for k in self.attributes.keys() if k != 'lang']
            s.append(u'<tuv xml:lang="%s" %s>\n' % (att_lang,' '.join(att)))
        else:
            s.append(u'<tuv xml:lang="%s">\n' % att_lang)
        
        if self.notes:
            for l in self.notes:
                s.append(l.to_unicode())
        
        s.append(u'<seg>%s</seg>\n' % protect_content(self.text))
        
        s.append(u'</tuv>\n')
        return u''.join(s)



class Message(object):

    def __init__(self, msgstr, attributes={}, notes=[]):
        self.attributes = attributes
        self.msgstr = msgstr
        self.notes = notes

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
        
        for l in self.msgstr.keys():
            s.append(self.msgstr[l].to_unicode())
            
        s.append(u'</tu>\n')
        return u''.join(s)



class TMX(Text):

    #######################################################################
    # Load
    #######################################################################
    def _load_state(self, resource):
        state = self.state
        state.header, state.messages, state.header_notes = {}, {}, {}
        stack = [] 
        message = {}
        tu_attribute, tuv_attribute, note_att = {}, {}, {}
        srclang, text = None, ''
        notes = {'tu':[], 'tuv':[], 'header':[]}
        for event, value, line_number in parser.parse(resource.read()):
            if event == parser.XML_DECLARATION:
                state.xml_version, state.source_encoding = value[:2]
                state.standalone = value[2]
            elif event == parser.DOCUMENT_TYPE:
                state.document_type = value
            elif event == parser.START_ELEMENT:
                stack.append(value[2])
            elif event == parser.END_ELEMENT:
                local_name = value[2]
                if stack[-1] == local_name:
                    if local_name == 'tuv':
                        if text:
                            s = Sentence(text, tuv_attribute, notes['tuv'])
                            message[tuv_attribute['lang']] = s
                        notes['tuv'], tuv_attribute, text = [], {}, ''
                    elif local_name == 'header':
                        state.header_notes = notes['header']
                        notes['header'] = []
                    elif local_name == 'tu':
                        id_lang = srclang or state.header['srclang']
                        if id_lang == '*all*':
                            raise NotImplementedError, 'no support yet for '\
                                                 '"*all*" in srclang attribute.'
                        id = message['%s' % id_lang]
                        m = Message(message, tu_attribute, notes['tu'])
                        state.messages[id.text] = m
                        message, srclang, tu_attribute = {}, None, {}
                        notes['tu'] = []
                    stack.pop()
            elif event == parser.ATTRIBUTE:
                local_name, data = value[2], value[3]
                if stack[-1] == "tmx" and local_name == 'version':
                    state.version = data
                elif stack[-1] == "tu":
                    tu_attribute[local_name] = data 
                    if local_name == 'srclang':
                        srclang = data
                elif stack[-1] == "tuv":
                    tuv_attribute[local_name] = data 
                elif stack[-1] == "header":
                    state.header[local_name] = data
                elif stack[-1] == "note":
                    note_att[local_name] = data
            elif event == parser.COMMENT:
                pass
            elif event == parser.TEXT:
                if stack:
                    if stack[-1] == 'note':
                        n = Note(unicode(value,'utf8'), note_att)
                        notes[stack[-2]].append(n)
                        note_att = {}
                    elif stack[-1] == 'seg':
                        text = unicode(value,'utf8')



    def xml_header_to_unicode(self, encoding='UTF-8'):
        state = self.state
        s = []
        # The XML declaration
        if state.standalone == 1:
            pattern = u'<?xml version="%s" encoding="%s" standalone="yes"?>\n'
        elif state.standalone == 0:
            pattern = u'<?xml version="%s" encoding="%s" standalone="no"?>\n'
        else:       
            pattern = u'<?xml version="%s" encoding="%s"?>\n'
        s.append(pattern % (state.xml_version, encoding))
        # The document type
        if state.document_type is not None:
            pattern = u'<!DOCTYPE %s ' \
                      u'SYSTEM "%s">\n'
            s.append(pattern % state.document_type[:2])
                
        return u''.join(s)



    def header_to_unicode(self, encoding='UTF-8'):
        state = self.state
        s = []
        if state.version:
            s.append(u'<tmx version="%s">\n' % state.version)
        else:
            s.append(u'<tmx>\n')
        
        if state.header != {}:
            attributes = [u'\n%s="%s"' % (k, state.header[k]) 
                         for k in state.header.keys()]
            s.append(u'<header %s>\n' % u''.join(attributes))
        else:
            s.append(u'<header>\n')

        if state.header_notes != []:
            for n in state.header_notes:
                s.append(n.to_unicode())

        s.append(u'</header>\n')
            
        return u''.join(s)



    def to_unicode(self, encoding=None):
        state = self.state
        msgs = u'\n'.join([ x.to_unicode() for x in state.messages.values() ])
        s = []
        s.append(self.xml_header_to_unicode())
        s.append(self.header_to_unicode())
        s.append(u'<body>\n')
        s.append(msgs)
        s.append(u'</body>\n')
        s.append(u'</tmx>\n')
        return u''.join(s)

Text.register_handler_class(TMX)

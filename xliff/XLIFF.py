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




class Translation(object):

    def __init__(self, source=None, target=None, attributes={}, notes=[]):
        
        self.source = source
        self.target = target
        self.attributes = attributes
        self.notes = notes

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
            s.append(u'<source>%s</source>\n' % protect_content(self.source))

        if self.target:
            s.append(u'<target>%s</target>\n' % protect_content(self.target))

        if self.notes:
            for l in self.notes:
                s.append(l.to_unicode())
                
        s.append(u'</trans-unit>\n')

        return u''.join(s)



class File(object):

    def __init__(self, body={}, attributes={}, header=[]):
        self.body = body
        self.attributes = attributes
        self.header = header

    def to_unicode(self):
        s = []
        if self.attributes != {}:
            att = [u' %s="%s"' % (k, self.attributes[k]) 
                  for k in self.attributes.keys() if k != 'space']
            s.append(u'<file %s' % u'\n'.join(att))
            if 'space' in self.attributes.keys():
                s.append('xml:space="%s"' % self.attributes['space'])
            s.append(u'>\n')
        else:
            s.append(u'<file>\n')
        
        if self.header:
            s.append(u'<header>\n')
            for l in self.header:
                s.append(l.to_unicode())
            s.append(u'</header>\n')
            
        if self.body:
            msgs = u'\n'.join([ m.to_unicode() for m in self.body.values() ])
            
            s.append(u'<body>\n')
            s.append(msgs)
            s.append(u'</body>\n')
        
        s.append(u'</file>\n')

        return u''.join(s)
        


class XLIFF(Text):

    #######################################################################
    # Load
    #######################################################################
    def _load_state(self, resource):
        state = self.state
        state.files = []
        stack = []
        file_att, body = {}, {}
        trans_att, source, target, trans_id = {}, None, None, None
        note_att = {}
        notes = {'header':[], 'trans-unit':[]}
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
                    if local_name == 'file':
                        f = File(body, file_att, notes['header'])
                        state.files.append(f)
                        file_att, notes['header'] = {}, []
                    elif local_name == 'trans-unit':
                        t = Translation(source, target, trans_att, 
                                        notes['trans-unit'])
                        body[trans_id] = t
                        trans_att, notes['trans-unit'] = {}, []
                        source, target, trans_id = None, None, None
                    stack.pop()
            elif event == parser.ATTRIBUTE:
                local_name, data = value[2], value[3]
                if stack[-1] == "xliff" and local_name=='version':
                    state.version = data
                elif stack[-1] == "xliff" and local_name=='lang':
                    state.lang = data
                elif stack[-1] == "file":
                    file_att[local_name] = data
                elif stack[-1] == "trans-unit":
                    if local_name == 'id':
                        trans_id = data
                    trans_att[local_name] = data
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
                    elif stack[-1] == 'source':
                        source = unicode(value,'utf8')
                    elif stack[-1] == 'target':
                        target = unicode(value,'utf8')



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
        s.append(u'<xliff')
        if state.version:
            s.append(u'version="%s"' % state.version)
        if state.lang:
            s.append(u'xml:lang="%s"' % state.lang)
        s.append(u'>\n') 

        return u' '.join(s)



    def to_unicode(self, encoding=None):
        state = self.state
        
        files = u'\n'.join([ f.to_unicode() for f in state.files])

        s = []
        s.append(self.xml_header_to_unicode())
        s.append(self.header_to_unicode())
        s.append(files)
        s.append(u'</xliff>')

        return u''.join(s)


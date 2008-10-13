# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Nicolas Oyez <nicoyez@gmail.com>
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
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

# Import from itools
from itools.datatypes import XMLContent, XMLAttribute
from itools.gettext.po import encode_source
from itools.handlers import TextFile, register_handler_class
from itools.xml import XMLParser, START_ELEMENT, END_ELEMENT, COMMENT, TEXT
from itools.srx import TEXT as srx_TEXT, START_FORMAT, END_FORMAT


doctype = (
    '<!DOCTYPE xliff PUBLIC "-//XLIFF//DTD XLIFF//EN"\n'
    '  "http://www.oasis-open.org/committees/xliff/documents/xliff.dtd">\n')


# FIXME TMXNote and XLFNote are the same
class XLFNote(object):

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



class XLFUnit(object):

    def __init__(self, attributes):
        self.source = None
        self.target = None
        self.context = None
        self.line = None
        self.attributes = attributes
        self.notes = []


    def to_str(self):
        s = []
        if self.attributes != {}:
            att = ['%s="%s"' % (k, self.attributes[k])
                  for k in self.attributes.keys() if k != 'space']
            s.append('  <trans-unit %s ' % '\n'.join(att))
            if 'space' in self.attributes.keys():
                s.append('xml:space="%s"' % self.attributes['space'])
            s.append('>\n')
        else:
            s.append('  <trans-unit>\n')

        if self.source:
            s.append('    <source>')
            s.append(encode_source(self.source))
            s.append('</source>\n')

        if self.target:
            s.append('    <target>')
            s.append(encode_source(self.target))
            s.append('</target>\n')

        if self.line is not None or self.context is not None:
            s.append('    <context-group name="context info">\n')
            if self.line is not None:
                s.append('        <context context-type="linenumber">%d' %
                         self.line)
                s.append('</context>\n')
            if self.context is not None:
                s.append('        <context context-type="x-context">%s' %
                         self.context)
                s.append('</context>\n')
            s.append('    </context-group>\n')

        for note in self.notes:
            s.append(note.to_str())

        s.append('  </trans-unit>\n')
        return ''.join(s)



class File(object):

    def __init__(self, original, attributes):
        self.original = original
        self.attributes = attributes
        self.body = {}
        self.header = []


    def to_str(self):
        output = []

        # Opent tag
        open_tag = '<file original="%s"%s>\n'
        attributes = [
            ' %s="%s"' % (key, XMLAttribute.encode(value))
            for key, value in self.attributes.items() if key != 'space']
        if 'space' in self.attributes:
            attributes.append(' xml:space="%s"' % self.attributes['space'])
        attributes = ''.join(attributes)
        open_tag = open_tag % (self.original, attributes)
        output.append(open_tag)
        # The header
        if self.header:
            output.append('<header>\n')
            for line in self.header:
                output.append(line.to_str())
            output.append('</header>\n')
        # The body
        output.append('<body>\n')
        if self.body:
            output.extend([ unit.to_str() for unit in self.body.values() ])
        output.append('</body>\n')
        # Close tag
        output.append('</file>\n')

        return ''.join(output)



class XLFFile(TextFile):

    class_mimetypes = ['application/x-xliff']
    class_extension = 'xlf'

    def new(self, version='1.0'):
        self.version = version
        self.lang = None
        self.files = {}


    #######################################################################
    # Load
    def _load_state_from_file(self, file):
        # XXX Warning: we can just load our xliff file
        self.files = {}
        phrase = None
        id_stack = []
        for event, value, line_number in XMLParser(file.read()):
            if event == START_ELEMENT:
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
                    original = attributes.pop('original')
                    file = File(original, attributes)
                elif local_name == 'header':
                    notes = []
                elif local_name == 'trans-unit':
                    unit = XLFUnit(attributes)
                    notes = []
                elif local_name == 'note':
                    note = XLFNote(attributes=attributes)
                elif local_name == 'context':
                    context_type = attributes['context-type']
                elif local_name in ['source', 'target']:
                    phrase = []
                elif local_name in ('g', 'x'):
                    id = int(attributes['id'])
                    id_stack.append(id)
                    phrase.append((START_FORMAT, id))
            elif event == END_ELEMENT:
                namespace, local_name = value

                if local_name == 'file':
                    self.files[original] = file
                elif local_name == 'header':
                    file.header = notes
                elif local_name == 'trans-unit':
                    unit.notes = notes
                    file.body[unit.context, unit.source] = unit
                elif local_name == 'source':
                    unit.source = tuple(phrase)
                    phrase = None
                elif local_name == 'target':
                    unit.target = tuple(phrase)
                    phrase = None
                elif local_name in ('g', 'x'):
                    phrase.append((END_FORMAT, id_stack.pop()))
                elif local_name == 'note':
                    note.text = text
                    notes.append(note)
                elif local_name == 'context':
                    if context_type == 'linenumber':
                        unit.line = int(text)
                    elif context_type == 'x-context':
                        unit.context = text
            elif event == COMMENT:
                pass
            elif event == TEXT:
                text = unicode(value, 'UTF-8')
                if phrase is not None:
                    phrase.append((srx_TEXT, text))


    #######################################################################
    # Save
    #######################################################################
    def to_str(self, encoding='UTF-8'):
        output = []
        # The XML declaration
        output.append('<?xml version="1.0" encoding="%s"?>\n' % encoding)
        # The Doctype
        output.append(doctype)
        # <xliff>
        if self.lang:
            template = '<xliff version="%s">\n'
            output.append(template % self.version)
        else:
            template = '<xliff version="%s" xml:lang="%s">\n'
            output.append(template % (self.version, self.lang))
        # The files
        for file in self.files.values():
            output.append(file.to_str())
        # </xliff>
        output.append('</xliff>\n')
        # Ok
        return ''.join(output).encode(encoding)


    #######################################################################
    # API
    #######################################################################
    def build(self, version, files):
        self.version = version
        self.files = files


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


    def add_unit(self, filename, source, context, line):
        file = self.files.setdefault(filename, File(filename, {}))
        unit = XLFUnit({})
        unit.source = source
        unit.context = context
        unit.line = line
        file.body[context, source] = unit
        return unit


    def gettext(self, source, context=None):
        """Returns the translation of the given message id.

        If the context /msgid is not present in the message catalog, then the
        message id is returned.
        """

        key = (context, source)

        for file in self.files.values():
            if key in file.body:
                unit = file.body[key]
                if unit.target:
                    return unit.target
        return source


register_handler_class(XLFFile)

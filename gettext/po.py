# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2008 Sylvain Taverne <sylvain@itaapy.com>
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
from re import compile
from time import gmtime, strftime, time

# Import from itools
from itools.handlers import File, TextFile, register_handler_class
from itools.srx import TEXT, START_FORMAT, END_FORMAT
from itools.xml import XMLParser, TEXT as xml_TEXT, START_ELEMENT, END_ELEMENT

###########################################################################
# Exceptions
# To improve exceptions see:
# - http://python.org/doc/2.3.3/lib/module-exceptions.html,
# - http://python.org/doc/2.3.3/tut/node10.html
###########################################################################
class POError(Exception):
    pass


class POSyntaxError(Exception):

    def __init__(self, line_number, line_type=None):
        self.line_number = line_number
        self.line_type = line_type


    def __str__(self):
        if self.line_type is None:
            return 'syntax error at line %d' % self.line_number
        return 'unexpected %s at line %d' % (self.line_type, self.line_number)



###########################################################################
# Parser
###########################################################################
# Line types
BLANK = 'blank'
FUZZY = 'fuzzy'
COMMENT = 'comment'
MSGCTXT = 'msgctxt'
MSGID = 'msgid'
MSGSTR = 'msgstr'
STRING = 'string'
EOF = None

# The regular expressions for the line types
re_comment = compile('^#.*')
re_msgctxt = compile(r'^msgctxt *"(.*[^\\]*)"$')
re_msgid = compile(r'^msgid *"(.*[^\\]*)"$')
re_msgstr = compile(r'^msgstr *"(.*[^\\]*)"$')
re_str = compile(r'^"(.*[^\\])"$')


def get_lines(data):
    lines = data.split('\n') + ['']
    line_number = 0
    while line_number <= len(lines):
        # Check for end of file
        if line_number == len(lines):
            yield EOF, None, line_number
            break

        # Load line
        line = lines[line_number].strip()
        line_number += 1

        # Empty
        if not line:
            yield BLANK, None, line_number
        # Fuzzy flag
        elif line == '#, fuzzy':
            yield FUZZY, None, line_number
        # Comment
        elif line.startswith('#'):
            yield COMMENT, line[1:], line_number
        # msgctxt
        elif line.startswith('msgctxt'):
            match = re_msgctxt.match(line)
            if match is not None:
                value = match.group(1)
                yield MSGCTXT, unescape(value), line_number
        # msgid
        elif line.startswith('msgid'):
            match = re_msgid.match(line)
            if match is not None:
                value = match.group(1)
                yield MSGID, unescape(value), line_number
        # msgstr
        elif line.startswith('msgstr'):
            match = re_msgstr.match(line)
            if match is not None:
                value = match.group(1)
                yield MSGSTR, unescape(value), line_number
        # string
        elif line.startswith('"'):
            match = re_str.match(line)
            if match is not None:
                value = match.group(1)
                yield STRING, unescape(value), line_number

        # Unknown
        else:
            raise POSyntaxError(line_number)


def encode_source(source):
    result = []
    for i, (type, value) in enumerate(source):
        if type == TEXT:
            result.append(value)
        elif type == START_FORMAT:
            # A lonely tag ?
            if source[i+1][0] == END_FORMAT:
                result.append(u"<x id='%d'/>" % value)
            else:
                result.append(u"<g id='%d'>" % value)
        elif type == END_FORMAT:
            # A lonely tag ?
            if source[i-1][0] != START_FORMAT:
                result.append(u'</g>')
    return u''.join(result)


def decode_target(target):
    result = []
    id_stack = []
    for type, value, line in XMLParser(target.encode('UTF-8')):
        if type == xml_TEXT:
            result.append((TEXT, unicode(value, 'UTF-8')))
        elif type == START_ELEMENT:
            id = int(value[2][None, 'id'])
            id_stack.append(id)
            result.append((START_FORMAT, id))
        else:
            result.append((END_FORMAT, id_stack.pop()))
    return tuple(result)



###########################################################################
# Handler
###########################################################################

# Escape and unescape strings
def escape(s):
    return s.replace('\n', '\\n').replace('"', '\\"')


expr = compile(r'(\\.)')
def unescape(s):
    return expr.sub(lambda x: eval("'%s'" % x.group(0)), s)



class POUnit(object):
    """An entry in a PO file has the syntax:

    #  translator-comments
    #. automatic-comments
    #: reference...
    #, flag...
    msgctxt context
    msgid untranslated-string
    msgstr translated-string

    First the comments (optional), then the context, the message id, and
    finally the message string.

    A 'POUnit' object keeps this information as:

     => references = {<filename>: [<line number>, ...]}
     => context = [<msgctxt line>, ...] or None
     => source = [<msgid line>, ...]
     => target = [<msgstr line>, ...]
     => comments = [<comment line>, ...]

    XXX
    1. Right now the 'comments' list keeps translator comments, automatic
    comments and flags, we should distinguish them.
    2. Maybe the msgid and msgstr should be kept as a strings instead of
    lists.
    XXX
    """

    def __init__(self, comments, context, source, target, references={},
                 fuzzy=False):
        self.comments = comments
        self.references = references
        self.context = context
        self.source = source
        self.target = target
        self.fuzzy = fuzzy


    def to_str(self, encoding='UTF-8'):
        s = []
        # The comments
        for comment in self.comments:
            s.append('#%s\n' % comment.encode(encoding))
        # The reference comments
        for filename, lines in self.references.items():
            for line in lines:
                s.append('#: %s:%s\n' % (filename, line))
        # The Fuzzy flag
        if self.fuzzy:
            s.append('#, fuzzy\n')
        # The msgctxt
        if self.context is not None:
            s.append('msgctxt "%s"\n' % escape(self.context[0].encode(
                                               encoding)))
            for string in self.context[1:]:
                s.append('"%s"\n' % escape(string.encode(encoding)))
        # The msgid
        s.append('msgid "%s"\n' % escape(self.source[0].encode(encoding)))
        for string in self.source[1:]:
            s.append('"%s"\n' % escape(string.encode(encoding)))
        # The msgstr
        s.append('msgstr "%s"\n' % escape(self.target[0].encode(encoding)))
        for string in self.target[1:]:
            s.append('"%s"\n' % escape(string.encode(encoding)))

        return ''.join(s)


    def __repr__(self):
        msg = "<POUnit object context=%s source=%s target=%s (%s)>"
        return msg % (self.context, self.source, self.target, self.references)


    def __eq__(self, other):
        return ((other.context == self.context) and
                (other.source == self.source) and
                (other.target == self.target))



skeleton = """# SOME DESCRIPTIVE TITLE.
# Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER
# This file is distributed under the same license as the PACKAGE package.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\\n"
"POT-Creation-Date: %(pot_creation_date)s\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"""



class POFile(TextFile):

    class_mimetypes = [
        'text/x-gettext-translation',
        'text/x-gettext-translation-template',
        'text/x-po']
    class_extension = 'po'


    def new(self):
        # XXX Old style (like in the "get_skeleton" times)
        now = strftime('%Y-%m-%d %H:%m+%Z', gmtime(time()))
        self.load_state_from_string(skeleton % {'pot_creation_date': now})


    #######################################################################
    # Parsing
    #######################################################################
    def next_entry(self, data):
        # Initialize entry information
        id, comments, context = None, [], None
        source, target, fuzzy = [], [], False

        # Parse entry
        state = 0
        for line_type, value, line_number in get_lines(data):
            # Syntactic and semantic analysis
            if state == 0:
                # Wait for an entry
                if line_type == EOF:
                    return
                elif line_type == BLANK:
                    pass
                elif line_type == COMMENT:
                    comments.append(value)
                    state = 1
                elif line_type == FUZZY and not fuzzy:
                    fuzzy = True
                    state = 1
                elif line_type == MSGCTXT:
                    context = [value]
                    state = 2
                elif line_type == MSGID:
                    source.append(value)
                    state = 3
                else:
                    raise POSyntaxError(line_number, line_type)

            elif state == 1:
                # Read comments and wait for the context or message id
                if line_type == COMMENT:
                    comments.append(value)
                elif line_type == FUZZY and not fuzzy:
                    fuzzy = True
                elif line_type == BLANK:
                    # Discard isolated comments
                    fuzzy = False
                    comments = []
                    state = 0
                elif line_type == MSGCTXT:
                    context = [value]
                    state = 2
                elif line_type == MSGID:
                    source.append(value)
                    state = 3
                else:
                    raise POSyntaxError(line_number, line_type)

            elif state == 2:
                # Read the context and wait for the message id
                if line_type == STRING:
                    context.append(value)
                elif line_type == MSGID:
                    source.append(value)
                    state = 3
                else:
                    raise POSyntaxError(line_number, line_type)

            elif state == 3:
                # Read the message id and wait for the message string
                if line_type == STRING:
                    source.append(value)
                elif line_type == MSGSTR:
                    target.append(value)
                    id = ''.join(source)
                    state = 4
                else:
                    raise POSyntaxError(line_number, line_type)

            elif state == 4:
                # Read the message string
                if line_type == STRING:
                    target.append(value)
                    if (context, id) == (None, ''):
                        # Parse the header
                        # XXX Right now we only get the encoding, we should
                        # get everything.
                        key, value = value.split(':', 1)
                        if key == 'Content-Type':
                            mimetype, charset = value.split(';')
                            charset = charset.strip()
                            self.encoding = charset[len('charset='):]
                elif line_type == BLANK:
                    # End of the entry
                    yield (comments, context, source, target, fuzzy,
                           line_number)
                    # Reset
                    id, comments, context = None, [], None
                    source, target, fuzzy = [], [], False
                    state = 0
                elif line_type == COMMENT:
                    # Add entry
                    yield (comments, context, source, target, fuzzy,
                           line_number)
                    # Reset
                    id, comments, context = None, [], None
                    source, target, fuzzy = [], [], False
                    state = 5
                else:
                    raise POSyntaxError(line_number, line_type)

            elif state == 5:
                # Discard trailing comments
                if line_type == COMMENT:
                    pass
                elif line_type == BLANK:
                    # End of the entry
                    yield (comments, context, source, target, fuzzy,
                           line_number)
                    # Reset
                    id, comments, context = None, [], None
                    source, target, fuzzy = [], [], False
                    state = 0
                else:
                    raise POSyntaxError(line_number, line_type)


    def _load_state_from_file(self, file):
        """A PO file is made of entries, where entries are separated by one
        or more blank lines. Each entry consists of a msgid and a msgstr,
        optionally preceded by comments; if there are comments at the end
        of the entry they are ignored. So, an entry looks like:

        #  translator-comments
        #. automatic-comments
        #: reference...
        #, flag...
        msgid untranslated-string
        msgstr translated-string

        There could be an empty msgid, it contains information about the PO
        file, like the Project-Id-Version or the PO-Revision-Date.
        """
        # Initialize messages
        self.messages = {}

        # Defaults, XXX guess it instead?
        self.encoding = 'utf8'

        # Split the data by lines and intialize the line index
        data = file.read()

        # Add entries
        for entry in self.next_entry(data):
            comments, context, source, target, fuzzy, line_number = entry

            # Check for duplicated messages
            if context is not None:
                first_part = ''.join(context)
            else:
                first_part = None
            second_part = ''.join(source)
            key = (first_part, second_part)
            if key in self.messages:
                raise POError, 'msgid at line %d is duplicated' % line_number

            # Get the comments and the msgstr in unicode
            comments = [ unicode(x, self.encoding) for x in comments ]

            if context is not None:
                context = [ unicode(x, self.encoding) for x in context ]
            source = [ unicode(x, self.encoding) for x in source ]
            target = [ unicode(x, self.encoding) for x in target ]

            # Add the message
            self._set_message(context, source, target, comments, {}, fuzzy)


    def to_str(self, encoding='UTF-8'):
        messages = self.messages
        message_ids = messages.keys()
        message_ids.sort()
        messages = [ messages[x].to_str(encoding) for x in message_ids ]
        return '\n'.join(messages)


    #######################################################################
    # API / Private
    #######################################################################
    def _set_message(self, context, source, target=[u''], comments=[],
                     references={}, fuzzy=False):

        if context is not None and isinstance(context, (str, unicode)):
            context = [context]
        if isinstance(source, (str, unicode)):
            source = [source]
        if isinstance(target, (str, unicode)):
            target = [target]

        # Make the key
        if context is not None:
            first_part = ''.join(context)
        else:
            first_part = None
        second_part = ''.join(source)
        key = (first_part, second_part)

        unit = POUnit(comments, context, source, target, references, fuzzy)
        self.messages[key] = unit
        return unit




    #######################################################################
    # API / Public
    #######################################################################
    def get_msgids(self):
        """Returns all the (context, msgid).
        """
        return self.messages.keys()


    def get_units(self, srx_handler=None):
        """Returns all the message (objects of the class <POUnit>).
        """
        return self.messages.values()


    def get_msgstr(self, source, context=None):
        """Returns the 'msgstr' for the given (context, msgid).
        """
        message = self.messages.get((context, source))
        if message:
            return ''.join(message.target)
        return None


    def gettext(self, source, context=None):
        """Returns the translation of the given message id.

        If the context /msgid is not present in the message catalog, or if it
        is marked as "fuzzy", then the message id is returned.
        """

        message = self.messages.get((context, encode_source(source)))
        if message and not message.fuzzy:
            target = ''.join(message.target)
            if target:
                return decode_target(target)
        return source


    def add_unit(self, filename, source, context, line):
        if not source:
            return None

        # Change
        self.set_changed()

        source = encode_source(source)

        return self._set_message(context, [source], [u''], [],
                                 {filename: [line]})



register_handler_class(POFile)

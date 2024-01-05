# Copyright (C) 2003-2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2007, 2010 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2008 Sylvain Taverne <taverne.sylvain@gmail.com>
# Copyright (C) 2008 Wynand Winterbach <wynand.winterbach@gmail.com>
# Copyright (C) 2008, 2010 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2009 Aurélien Ansel <camumus@gmail.com>
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

import itertools
from re import compile
from time import gmtime, strftime, time

# Import from itools
from itools.core import freeze
from itools.handlers import TextFile, register_handler_class
from itools.srx import TEXT, START_FORMAT, END_FORMAT


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
REFERENCE = 'reference'
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
    if isinstance(data, bytes):
        data = data.decode("utf-8")

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
        # Reference
        elif line.startswith('#:'):
            yield REFERENCE, line[2:].strip(), line_number
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
                result.append("<x id='%d'/>" % value)
            else:
                result.append("<g id='%d'>" % value)
        elif type == END_FORMAT:
            # A lonely tag ?
            if source[i-1][0] != START_FORMAT:
                result.append('</g>')
    return ''.join(result)


def decode_target(target):
    # Prepare the regexp
    re_tags = compile('<(.*?)>')
    re_g_start = compile("^g id='(.*?)'$")
    re_g_end = compile("^/g$")
    re_x = compile("^x id='(.*?)'/$")

    # Parse !
    result = []
    id_stack = []
    tag = True
    text = ''
    for block in re_tags.split(target):
        tag = not tag
        if tag:
            # "<g id='...'>"
            sre = re_g_start.match(block)
            if sre:
                id = int(sre.groups()[0])
                id_stack.append(id)
                if text:
                    result.append((TEXT, text))
                    text = ''
                result.append((START_FORMAT, id))
                continue
            # "</g>"
            sre = re_g_end.match(block)
            if sre:
                if text:
                    result.append((TEXT, text))
                    text = ''
                result.append((END_FORMAT, id_stack.pop()))
                continue
            # "<x id='...'>"
            sre = re_x.match(block)
            if sre:
                id = int(sre.groups()[0])
                if text:
                    result.append((TEXT, text))
                    text = ''
                result.append((START_FORMAT, id))
                result.append((END_FORMAT, id))
                continue
            # Something else
            text += '<%s>' % block
            continue
        text += block
    # Push the last text
    if text:
        result.append((TEXT, text))
    return result


###########################################################################
# Handler
###########################################################################

# Escape and unescape strings
def escape(s):
    return s.replace('\r', '\\r').replace('\n', '\\n').replace('"', '\\"')


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

    __hash__ = None

    def __init__(self, comments, context, source, target,
                 references=freeze({}), fuzzy=False):
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
            s.append('#%s\n' % comment)
        # The reference comments
        i = 1
        references = self.references.items()
        nb_references = len(list(itertools.chain(*[y for x, y in references])))
        for filename, lines in references:
            for line in lines:
                comma = '' if i == nb_references else ','
                line = '#: %s:%s%s\n' % (filename, line, comma)
                s.append(line)
                i += 1
        # The Fuzzy flag
        if self.fuzzy:
            s.append('#, fuzzy\n')
        # The msgctxt
        if self.context is not None:
            s.append('msgctxt "%s"\n' % escape(self.context[0]))
            for string in self.context[1:]:
                s.append('"%s"\n' % escape(string))
        # The msgid
        s.append('msgid "%s"\n' % escape(self.source[0]))
        for string in self.source[1:]:
            s.append('"%s"\n' % escape(string))
        # The msgstr
        s.append('msgstr "%s"\n' % escape(self.target[0]))
        for string in self.target[1:]:
            s.append('"%s"\n' % escape(string))
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
        references = []

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
                elif line_type == REFERENCE:
                    for reference in value.split(' '):
                        value, line_no = reference.split(':')
                        references.append((value, line_no))
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
                elif line_type == REFERENCE:
                    for reference in value.split(' '):
                        value, line_no = reference.split(':')
                        references.append((value, line_no))
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
                    yield (comments, references, context, source, target, fuzzy,
                           line_number)
                    # Reset
                    id, comments, context = None, [], None
                    source, target, fuzzy = [], [], False
                    references = []
                    state = 0
                elif line_type == COMMENT:
                    # Add entry
                    yield (comments, references, context, source, target, fuzzy,
                           line_number)
                    # Reset
                    id, comments, context = None, [], None
                    source, target, fuzzy = [], [], False
                    references = []
                    state = 5
                else:
                    raise POSyntaxError(line_number, line_type)

            elif state == 5:
                # Discard trailing comments
                if line_type == COMMENT:
                    pass
                elif line_type == REFERENCE:
                    pass
                elif line_type == BLANK:
                    # End of the entry
                    yield (comments, references, context, source, target, fuzzy,
                           line_number)
                    # Reset
                    id, comments, context = None, [], None
                    source, target, fuzzy = [], [], False
                    references = []
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
            comments, references, context, source, target, fuzzy, line_number = entry

            # Check for duplicated messages
            if context is not None:
                first_part = ''.join(context)
            else:
                first_part = None
            second_part = ''.join(source)
            key = (first_part, second_part)
            if key in self.messages:
                raise POError('msgid at line %d is duplicated' % line_number)

            # Add the message
            self._set_message(context, source, target, comments, references, fuzzy)

    def to_str(self, encoding='UTF-8'):
        messages = self.messages
        message_ids = sorted(list(messages.keys()), key=lambda x: x[1])
        messages = [messages[x].to_str(encoding) for x in message_ids]
        return '\n'.join(messages)


    #######################################################################
    # API / Private
    #######################################################################
    def _set_message(self, context, source, target=freeze(['']),
                     comments=freeze([]), references=None, fuzzy=False):

        if context is not None and isinstance(context, (str, str)):
            context = [context]
        if isinstance(source, (str, str)):
            source = [source]
        if isinstance(target, (str, str)):
            target = [target]

        # Make the key
        if context is not None:
            first_part = ''.join(context)
        else:
            first_part = None
        second_part = ''.join(source)
        key = (first_part, second_part)

        # Already this entry ?
        messages = self.messages
        if key in messages:
            unit = messages[key]
            unit.target = target
        else:
            unit = POUnit(comments, context, source, target, {}, fuzzy)
            messages[key] = unit

        # Add the reference and return
        if not references:
            return unit
        for reference in references:
            unit.references.setdefault(reference[0], []).append(reference[1])
        return unit

    #######################################################################
    # API / Public
    #######################################################################
    def get_msgids(self):
        """Returns all the (context, msgid).
        """
        return list(self.messages.keys())

    def get_units(self):
        """Returns all the message (objects of the class <POUnit>).
        """
        return list(self.messages.values())

    def get_msgstr(self, source, context=None):
        """Returns the 'msgstr' for the given (context, msgid).
        """
        message = self.messages.get((context, source))
        if message:
            return ''.join(message.target)
        return None

    def set_msgstr(self, source, target, context=None):
        self._set_message(context, [source], [target])

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

        return self._set_message(context, [source], [''], [],
                                 [(filename, line)])


register_handler_class(POFile)

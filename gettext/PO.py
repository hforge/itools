# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the Standard Library
import re
import time

# Import from itools
from itools.handlers.File import File
from itools.handlers.Text import Text


# Line types
BLANK = 'blank'
FUZZY = 'fuzzy'
COMMENT = 'comment'
MSGID = 'msgid'
MSGSTR = 'msgstr'
STRING = 'string'
EOF = None

# The regular expressions for the line types
re_comment = re.compile('^#.*')
re_msgid = re.compile(r'^msgid *"(.*[^\\]*)"$')
re_msgstr = re.compile(r'^msgstr *"(.*[^\\]*)"$')
re_str = re.compile(r'^"(.*[^\\])"$')

# Module exceptions
# To improve exceptions see:
# - http://python.org/doc/2.3.3/lib/module-exceptions.html,
# - http://python.org/doc/2.3.3/tut/node10.html
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


# Escape and unescape strings
def escape(s):
    return s.replace('\n', '\\n').replace('"', '\\"')


expr = re.compile(r'(\\.)')
def unescape(s):
    return expr.sub(lambda x: eval("'%s'" % x.group(0)), s)



class Message(object):
    """
    An entry in a PO file has the syntax:

    #  translator-comments
    #. automatic-comments
    #: reference...
    #, flag...
    msgid untranslated-string
    msgstr translated-string

    First the comments (optional), then the message id, and finally the
    message string.

    A 'Message' object keeps this information as:

     => references = {<filename>: [<line number>, ...]}
     => msgid = [<msgid line>, ...]
     => msgstr = [<msgstr line>, ...]
     => comments = [<comment line>, ...]

    XXX
    1. Right now the 'comments' list keeps translator comments, automatic
    comments and flags, we should distinguish them.
    2. Maybe the msgid and msgstr should be kept as a strings instead of lists.
    XXX
    """

    def __init__(self, comments, msgid, msgstr, references={}, fuzzy=False):
        self.comments = comments
        self.references = references
        self.msgid = msgid
        self.msgstr = msgstr
        self.fuzzy = fuzzy


    def to_unicode(self):
        s = []
        # The comments
        for comment in self.comments:
            s.append(u'#%s\n' % comment)
        # The reference comments
        for filename, lines in self.references.items():
            for line in lines:
                s.append(u'#: %s:%s\n' % (filename, line))
        # The Fuzzy flag
        if self.fuzzy:
            s.append(u'#, fuzzy\n')
        # The msgid
        s.append(u'msgid "%s"\n' % escape(self.msgid[0]))
        for string in self.msgid[1:]:
            s.append(u'"%s"\n' % escape(string))
        # The msgstr
        s.append(u'msgstr "%s"\n' % escape(self.msgstr[0]))
        for string in self.msgstr[1:]:
            s.append(u'"%s"\n' % escape(string))
        
        return u''.join(s)



class PO(Text):

    class_mimetypes = ['text/x-po']
    class_extension = 'po'


    #########################################################################
    # The skeleton
    #########################################################################
    def get_skeleton(self):
        now = time.strftime('%Y-%m-%d %H:%m+%Z', time.gmtime(time.time()))
        lines = ["# SOME DESCRIPTIVE TITLE.",
                 "# Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER",
                 "# This file is distributed under the same license as the PACKAGE package.",
                 "# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.",
                 "#",
                 "#, fuzzy",
                 'msgid ""',
                 'msgstr ""',
                 '"Project-Id-Version: PACKAGE VERSION\\n"',
                 '"POT-Creation-Date: %s\\n"' % now,
                 '"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"',
                 '"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"',
                 '"Language-Team: LANGUAGE <LL@li.org>\\n"',
                 '"MIME-Version: 1.0\\n"',
                 '"Content-Type: text/plain; charset=UTF-8\\n"',
                 '"Content-Transfer-Encoding: 8bit\\n"']
        return '\n'.join(lines)


    #######################################################################
    # Parsing
    #######################################################################
    def next_line(self):
        lines = self.state.lines
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


    def next_entry(self):
        # Initialize entry information
        id, comments, msgid, msgstr, fuzzy = None, [], [], [], False
        # Parse entry
        state = 0
        for m in self.next_line():
            line_type, value, line_number = m
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
                elif line_type == MSGID:
                    msgid.append(value)
                    state = 2
                else:
                    raise POSyntaxError(line_number, line_type)
            elif state == 1:
                # Read comments and wait for the message id
                if line_type == COMMENT:
                    comments.append(value)
                elif line_type == FUZZY and not fuzzy:
                    fuzzy = True
                elif line_type == BLANK:
                    # Discard isolated comments
                    fuzzy = False
                    comments = []
                    state = 0
                elif line_type == MSGID:
                    msgid.append(value)
                    state = 2
                else:
                    raise POSyntaxError(line_number, line_type)
            elif state == 2:
                # Read the message id and wait for the message string
                if line_type == STRING:
                    msgid.append(value)
                elif line_type == MSGSTR:
                    msgstr.append(value)
                    state = 3
                else:
                    raise POSyntaxError(line_number, line_type)
            elif state == 3:
                # Read the message string
                if line_type == STRING:
                    msgstr.append(value)
                    if id == '':
                        # Parse the header
                        # XXX Right now we only get the encoding, we should
                        # get everything.
                        key, value = value.split(':', 1)
                        if key == 'Content-Type':
                            mimetype, charset = value.split(';')
                            charset = charset.strip()
                            self._encoding = charset[len('charset='):]
                elif line_type == BLANK:
                    # End of the entry
                    id = ''.join(msgid)
                    yield id, comments, msgid, msgstr, fuzzy, line_number
                    state = 0
                    id, comments, msgid, msgstr, fuzzy = None, [], [], [], False
                elif line_type == COMMENT:
                    # Add entry
                    self._set_message(msgid, msgstr, comments, {}, fuzzy)
                    # Reset
                    id, comments, msgid, msgstr, fuzzy = None, [], [], [], False
                    state = 4
                else:
                    raise POSyntaxError(line_number, line_type)
            elif state == 4:
                # Discard trailing comments
                if line_type == COMMENT:
                    pass
                elif line_type == BLANK:
                    # End of the entry
                    id = ''.join(msgid)
                    yield id, comments, msgid, msgstr, fuzzy, line_number
                    state = 0
                    id, comments, msgid, msgstr, fuzzy = None, [], [], [], False
                else:
                    raise POSyntaxError(line_number, line_type)


    def _load_state(self, resource):
        """
        A PO file is made of entries, where entries are separated by one
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
        state = self.state
        state.messages = {}

        # Defaults, XXX guess it instead?
        state.encoding = 'utf8'

        # Split the data by lines and intialize the line index
        data = resource.read()
        state.lines = data.split('\n') + ['']

        # Add entries
        for entry in self.next_entry():
            entry_id, comments, msgid, msgstr, fuzzy, line_number = entry
            # Check for duplicated messages
            if entry_id in state.messages:
                raise POError, 'msgid at line %d is duplicated' % line_number

            # Get the comments and the msgstr in unicode
            comments = [ unicode(x, state.encoding) for x in comments ]
            msgid = [ unicode(x, state.encoding) for x in msgid ]
            msgstr = [ unicode(x, state.encoding) for x in msgstr ]

            # Add the message
            self._set_message(msgid, msgstr, comments, {}, fuzzy)


    #######################################################################
    # API
    #######################################################################
    def get_msgids(self):
        return self.state.messages.keys()

    msgids = property(get_msgids, None, None, "")


    def get_messages(self):
        return self.state.messages.values()

    messages = property(get_messages, None, None, "")


    def get_msgstr(self, msgid):
        message = self.state.messages.get(msgid)
        if message:
            return ''.join(message.msgstr)
        return None


    # Same as precedent but do not translate fuzzy messages
    def get_translation(self, msgid):
        message = self.state.messages.get(msgid)
        if message and not message.fuzzy:
            return ''.join(message.msgstr)
        return msgid


    def to_unicode(self, encoding=None):
        messages = self.state.messages
        message_ids = messages.keys()
        message_ids.sort()
        messages = [ messages[x].to_unicode() for x in message_ids ]
        return '\n'.join(messages)


    def set_message(self, msgid, msgstr=[u''], comments=[], references={},
                    fuzzy=False):
        if msgid:
            self.set_changed()
            self._set_message(msgid, msgstr, comments, references, fuzzy)


    def _set_message(self, msgid, msgstr=[u''], comments=[], references={},
                     fuzzy=False):
        if isinstance(msgid, (str, unicode)):
            msgid = [msgid]
        if isinstance(msgstr, (str, unicode)):
            msgstr = [msgstr]

        id = ''.join(msgid)
        self.state.messages[id] = Message(comments, msgid, msgstr, references,
                                          fuzzy)


Text.register_handler_class(PO)

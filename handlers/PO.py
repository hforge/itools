# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


# Import from Python
import re
import time

# Import from itools
from File import File
from Text import Text



# Line types
BLANK = 'blank'
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
    return s.replace('\n', '\\n')


def unescape(s):
    s2 = ''
    state = 0
    for x in s:
        if state == 0:
            if x == '\\':
                state = 1
            else:
                s2 = s2 + x
        else:
            s2 = s2 + eval("'\%s'" % x)
            state = 0

    return s2



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

    def __init__(self, comments, msgid, msgstr, references={}):
        self.comments = comments
        self.references = references
        self.msgid = msgid
        self.msgstr = msgstr


    def to_unicode(self):
        s = u''
        # The comments
        for comment in self.comments:
            s += '#%s\n' % comment
        # The reference comments
        for filename, lines in self.references.items():
            for line in lines:
                s += '#: %s:%s\n' % (filename, line)
        # The msgid
        s += 'msgid "%s"\n' % escape(self.msgid[0])
        for string in self.msgid[1:]:
            s += '"%s"\n' % escape(string)
        # The msgstr
        s += 'msgstr "%s"\n' % escape(self.msgstr[0])
        for string in self.msgstr[1:]:
            s += '"%s"\n' % escape(string)
        
        return s



class PO(Text):

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
        # Check for end of file
        if self.line_number >= len(self.lines):
            return EOF, None

        # Load line
        line = self.lines[self.line_number].strip()
        self.line_number += 1

        # Empty
        if not line:
            return BLANK, None
        # Comment
        elif line.startswith('#'):
            return COMMENT, line[1:]
        # msgid
        elif line.startswith('msgid'):
            match = re_msgid.match(line)
            if match is not None:
                value = match.group(1)
                return MSGID, unescape(value)
        # msgstr
        elif line.startswith('msgstr'):
            match = re_msgstr.match(line)
            if match is not None:
                value = match.group(1)
                return MSGSTR, unescape(value)
        # string
        elif line.startswith('"'):
            match = re_str.match(line)
            if match is not None:
                value = match.group(1)
                return STRING, unescape(value)

        # Unknown
        raise POSyntaxError(self.line_number)


    def next_entry(self):
        # Load the next line
        line_type, value = self.next_line()

        # Initialize entry information
        id, comments, msgid, msgstr = None, [], [], []

        # Parse entry
        state = 0
        while 1:
            # Syntactic and semantic analysis
            if state == 0:
                # Wait for an entry
                if line_type == EOF:
                    return None, [], [], []
                elif line_type == BLANK:
                    pass
                elif line_type == COMMENT:
                    comments.append(value)
                    state = 1
                elif line_type == MSGID:
                    msgid.append(value)
                    state = 2
                else:
                    raise POSyntaxError(self.line_number, line_type)
            elif state == 1:
                # Read comments and wait for the message id
                if line_type == COMMENT:
                    comments.append(value)
                elif line_type == BLANK:
                    # Discard isolated comments
                    comments = []
                    state = 0
                elif line_type == MSGID:
                    msgid.append(value)
                    state = 2
                else:
                    raise POSyntaxError(self.line_number, line_type)
            elif state == 2:
                # Read the message id and wait for the message string
                if line_type == STRING:
                    msgid.append(value)
                elif line_type == MSGSTR:
                    msgstr.append(value)
                    state = 3
                else:
                    raise POSyntaxError(self.line_number, line_type)
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
                    break
                elif line_type == COMMENT:
                    # Add entry
                    self._set_message(msgid, msgstr, comments)
                    # Reset
                    id, comments, msgid, msgstr = None, [], [], []
                    state = 4
                else:
                    raise POSyntaxError(self.line_number, line_type)
            elif state == 4:
                # Discard trailing comments
                if line_type == COMMENT:
                    pass
                elif line_type == BLANK:
                    # End of the entry
                    break
                else:
                    raise POSyntaxError(self.line_number, line_type)

            # Next line
            line_type, value = self.next_line()

        id = ''.join(msgid)
        return id, comments, msgid, msgstr


    def _load(self, resource):
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
        File._load(self, resource)
        # Initialize messages
        self._messages = {}

        # Split the data by lines and intialize the line index
        self.lines = self._data.split('\n') + ['']
        self.line_number = 0
        del self._data

        # Parse header
        entry_id, comments, msgid, msgstr = self.next_entry()
        if entry_id == '':
            # Parse header
            for line in msgstr:
                if line:
                    key, value = line.split(':', 1)
                    # XXX Get everything, not just the content type
                    if key == 'Content-Type':
                        mimetype, charset = value.split(';')
                        charset = charset.strip()
                        self._encoding = charset[len('charset='):]
        else:
            # Defaults, XXX guess it instead??
            self._encoding = 'utf8'

        # Add entries
        while entry_id is not None:
            # Check for duplicated messages
            if entry_id in self._messages:
                raise POError, \
                      'msgid at line %d is duplicated' % self.line_number

            # Get the comments and the msgstr in unicode
            comments = [ unicode(x, self._encoding) for x in comments ]
            msgid = [ unicode(x, self._encoding) for x in msgid ]
            msgstr = [ unicode(x, self._encoding) for x in msgstr ]

            # Add the message
            self._set_message(msgid, msgstr, comments)

            entry_id, comments, msgid, msgstr = self.next_entry()

        # Remove auxiliar attributes
        del self.lines
        del self.line_number



    #######################################################################
    # API
    #######################################################################
    def get_msgids(self):
        return self._messages.keys()

    msgids = property(get_msgids, None, None, "")


    def get_messages(self):
        return self._messages.values()

    messages = property(get_messages, None, None, "")


    def get_msgstr(self, msgid):
        message = self._messages.get(msgid)
        if message:
            return ''.join(message.msgstr)
        return None


    def to_unicode(self):
        return '\n'.join([ x.to_unicode() for x in self._messages.values() ])


    def set_message(self, msgid, msgstr=[u''], comments=[], references={}):
        self._set_message(msgid, msgstr, comments, references)
        self.save()


    def _set_message(self, msgid, msgstr=[u''], comments=[], references={}):
        if isinstance(msgid, (str, unicode)):
            msgid = [msgid]
        if isinstance(msgstr, (str, unicode)):
            msgstr = [msgstr]

        id = ''.join(msgid)
        self._messages[id] = Message(comments, msgid, msgstr, references)

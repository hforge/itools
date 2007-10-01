# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


# Statuses
# Common
DEFAULT = 'DEFAULT'
# Block
LITERAL = 'LITERAL'
# Inline
EMPHASIS_OR_STRONG = 'EMPHASIS_OR_STRONG'
EMPHASIS = 'EMPHASIS'
EMPHASIS_STRONG = 'EMPHASIS_STRONG'
INTERPRETED_OR_LITERAL = 'INTERPRETED_OR_LITERAL'
INTERPRETED = 'INTERPRETED'
INTERPRETED_OR_REFERENCE = 'INTERPRETED_OR_REFERENCE'
FOOTNOTE = 'FOOTNOTE'
FOOTNOTE_OR_TEXT = 'FOOTNOTE_OR_TEXT'
SUBSTITUTION = 'SUBSTITUTION'
TARGET_INLINE = 'TARGET_INLINE'
REFERENCE_OR_TEXT = 'REFERENCE_OR_TEXT'

ADORNMENTS = r'''!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~'''


def strip_block(block):
    """Remove empty lines at the end of a block.

    Multiple spaces and tabulations are not significant.
    """
    while block:
        if not block[-1].strip(' \t'):
            block = block[:-1]
        else:
            break

    return block



def normalize_whitespace(text):
    """Replace all adjacent whitespace (including carriage returns) by a single
    space.

    Only use where whitespace is not significant, e.g. not in literal blocks.
    """
    return u" ".join(text.split())



class Document(object):

    __slots__ = ['events']

    def __init__(self, text):
        if not isinstance(text, unicode):
            raise TypeError, "Text must be decoded to unicode"
        events = [('text', text)]
        events = self.parse_blocks(events)
        events = self.parse_lists(events)
        events = self.parse_literal_blocks(events)
        events = self.parse_titles(events)
        self.events = events


    def __iter__(self):
        for event, value in self.events:
            yield event, value


    @staticmethod
    def parse_blocks(stream):
        events = []
        for event, value in stream:
            if event != 'text':
                raise ValueError, "can only split initial text"
            buffer = []
            for line in value.splitlines():
                buffer.append(line)
                if not line.strip(u' \t'):
                    events.append(('block', buffer))
                    buffer = []

        # Buffer left:
        if buffer:
            events.append(('block', buffer))

        return events


    @staticmethod
    def parse_lists(stream):
        events = []
        indents = [(None, 0)]

        for event, value in stream:
            if event != 'block':
                events.append((event, value))
                continue
            last_type, last_indent = indents[-1]
            # Check exit of list indent
            first_line = value[0]
            indent = len(first_line) - len(first_line.lstrip(u' \t'))
            if indent < last_indent:
                while indent < last_indent:
                    last_type, last_indent = indents.pop()
                    events.append(('list_item_end', last_indent))
                    # Prepare end of list just in case
                    events.append(('list_end', last_type))
                    last_type, last_indent = indents[-1]
            # Now check open list indent
            words = first_line.split()
            if words:
                first_word = words[0]
            else:
                first_word = first_line
            if first_word == u'*':
                list_indent = len(first_line[:first_line.index(u'*') + 2])
            elif first_word == u'-':
                list_indent = len(first_line[:first_line.index(u'-') + 2])
            elif first_word[:-1].isdigit() and first_word[-1] == u'.':
                list_indent = len(first_line[:first_line.index(u'.') + 2])
                # Unify marker for ordered lists
                first_word = u'#'
            else:
                list_indent = None
            if list_indent is not None:
                if not events or (events[-1] != ('list_end', first_word)):
                    # The list was not begun
                    events.append(('list_begin', first_word))
                else:
                    # Remove 'list_end', another item follows
                    events.pop()
                events.append(('list_item_begin', list_indent))
                block = [value[0][list_indent:]] + value[1:]
                events.append(('block', block))
                indents.append((first_word, list_indent))
            else:
                events.append(('block', value))

        # Indents left (except default indent)
        if len(indents) > 1:
            del indents[0]
            while indents:
                last_type, last_indent = indents.pop()
                events.append(('list_item_end', last_indent))
            events.append(('list_end', last_type))

        return events


    @staticmethod
    def parse_literal_blocks(stream):
        events = []
        status = DEFAULT
        indent_level = None
        buffer = []

        for event, value in stream:
            if status == DEFAULT:
                if event != 'block':
                    events.append((event, value))
                    continue
                block = strip_block(value)
                if block:
                    last_line = block[-1]
                    if last_line.endswith(u'::'):
                        block = block[:-1] + [last_line[:-1]]
                        status = LITERAL
                        first_line = block[0]
                        indent_level = len(first_line) - len(first_line.lstrip(u' \t'))
                        buffer = []
                if block and block != [u':']:
                    events.append(('block', block))
            elif status == LITERAL:
                if event != 'block':
                    block = strip_block(buffer)
                    events.append(('literal_block', u'\n'.join(block)))
                    events.append((event, value))
                    status = DEFAULT
                elif strip_block(value):
                    first_line = value[0]
                    indent = len(first_line) - len(first_line.lstrip(u' \t'))
                    if indent > indent_level:
                        buffer.extend(value)
                    else:
                        block = strip_block(buffer)
                        events.append(('literal_block', u'\n'.join(block)))
                        events.append((event, value))
                        status = DEFAULT
                else:
                    buffer.extend(value)


        return events


    @staticmethod
    def parse_titles(stream):
        events = []

        for event, value in stream:
            if event != 'block':
                events.append((event, value))
                continue
            first_line = value[0]
            first_char = first_line[0]
            # Look for an overlined title
            if (first_char in ADORNMENTS
                    and first_line.count(first_char) == len(first_line)):
                # Look for underline
                for i, line in enumerate(value[1:]):
                    if line == first_line:
                        break
                else:
                    # Failed to recognize a title
                    block = strip_block(value)
                    if block:
                        text = u' '.join(block)
                        text = normalize_whitespace(text)
                        events.append(('paragraph', text))
                    continue
                # Split title and possible paragraph
                title = value[:i + 2]
                # Return title and adornments separately
                overline = title[0][0]
                underline = title[-1][0]
                title = u'\n'.join(title[1:-1])
                events.append(('title', (overline, title, underline)))
                # A paragraph may be glued
                buffer = value[i + 2:]
                block = strip_block(buffer)
                if block:
                    text = u' '.join(block)
                    text = normalize_whitespace(text)
                    events.append(('paragraph', text))
            else:
                # Look for an underlined title
                for i, line in enumerate(value):
                    if (line and line[0] in ADORNMENTS
                            and line.count(line[0]) == len(line)):
                        break
                else:
                    # No title found
                    block = strip_block(value)
                    if block:
                        text = u' '.join(block)
                        text = normalize_whitespace(text)
                        events.append(('paragraph', text))
                    continue
                # Split title and possible paragraph
                title = value[:i + 1]
                # Special case: '..' on its own means directive
                # TODO remove when directives are implemented?
                if title[-1] == u'..':
                    text = u' '.join(value)
                    text = normalize_whitespace(text)
                    events.append(('paragraph', text))
                    continue
                # Return title and adornments separately
                overline = u''
                underline = title[-1][0]
                title = u'\n'.join(title[:-1])
                events.append(('title', (overline, title, underline)))
                # A paragraph may be glued
                buffer = value[i + 1:]
                block = strip_block(buffer)
                if block:
                    text = u' '.join(block)
                    text = normalize_whitespace(text)
                    events.append(('paragraph', text))

        return events



def parse_inline(text):
    status = DEFAULT
    buffer = []

    if not isinstance(text, unicode):
        raise TypeError, "Text must be decoded to unicode"

    for c in text:
        if status == DEFAULT:
            if c == u'*':
                if buffer:
                    yield 'text', u''.join(buffer)
                    buffer = []
                status = EMPHASIS_OR_STRONG
            elif c == u'`':
                if buffer:
                    yield 'text', u''.join(buffer)
                    buffer = []
                status = INTERPRETED_OR_LITERAL
            elif c == u'[':
                if buffer:
                    yield 'text', u''.join(buffer)
                # Keep opening bracket in case it was a false positive
                buffer = [u'[']
                status = FOOTNOTE
            elif c == u'|':
                if buffer:
                    yield 'text', u''.join(buffer)
                    buffer = []
                status = SUBSTITUTION
            elif c == u'_':
                # Before or after a word?
                if buffer and buffer[-1].isspace():
                    yield 'text', u''.join(buffer)
                    buffer = []
                    status = TARGET_INLINE
                else:
                    buffer.append(c)
                    status = REFERENCE_OR_TEXT
            else:
                buffer.append(c)
        elif status == EMPHASIS_OR_STRONG:
            if c == u'*':
                status = EMPHASIS_STRONG
            else:
                buffer.append(c)
                status = EMPHASIS
        elif status == EMPHASIS:
            if c == u'*':
                yield 'emphasis', u''.join(buffer)
                buffer = []
                status = DEFAULT
            else:
                buffer.append(c)
        elif status == EMPHASIS_STRONG:
            if c == u'*' and buffer and buffer[-1] == u'*':
                yield 'strong', u''.join(buffer[:-1])
                buffer = []
                status = DEFAULT
            else:
                buffer.append(c)
        elif status == INTERPRETED_OR_LITERAL:
            if c == u'`':
                status = LITERAL
            else:
                buffer = [c]
                status = INTERPRETED
        elif status == LITERAL:
            if c == u'`' and buffer and buffer[-1] == u'`':
                yield 'literal', u''.join(buffer[:-1])
                buffer = []
                status = DEFAULT
            else:
                buffer.append(c)
        elif status == INTERPRETED:
            if c == u'`':
                status = INTERPRETED_OR_REFERENCE
            else:
                buffer.append(c)
        elif status == INTERPRETED_OR_REFERENCE:
            if c == u'_':
                reference = u''.join(buffer)
                # Whitespace should not be significant in a reference
                reference = normalize_whitespace(reference)
                yield 'reference', reference
                buffer = []
                status = DEFAULT
            else:
                yield 'interpreted', u''.join(buffer)
                buffer = [c]
                status = DEFAULT
        elif status == FOOTNOTE:
            if c == u']':
                # Keeping closing bracket in case it was a false positive
                buffer.append(c)
                status = FOOTNOTE_OR_TEXT
            else:
                buffer.append(c)
        elif status == FOOTNOTE_OR_TEXT:
            if c == u'_':
                # Reference as expected
                footnote = ''.join(buffer[1:-1])
                if footnote.isdigit() or footnote == u'#':
                    yield 'footnote', footnote
                else:
                    yield 'citation', footnote
                buffer = []
                status = DEFAULT
            else:
                # False positive
                buffer.append(c)
                yield 'text', u''.join(buffer)
            buffer = []
            status = DEFAULT
        elif status == SUBSTITUTION:
            if c == u'|':
                yield 'substitution', u''.join(buffer)
                buffer = []
                status = DEFAULT
            else:
                buffer.append(c)
        elif status == TARGET_INLINE:
            if c == u'`':
                if buffer:
                    yield 'target', u''.join(buffer)
                    buffer = []
                    status = DEFAULT
            else:
                buffer.append(c)
        elif status == REFERENCE_OR_TEXT:
            if c == u' ':
                # Really was a reference name
                reference = u''.join(buffer)
                if u' ' in reference:
                    separator_index = reference.rindex(u' ') + 1
                    remain, reference = (reference[:separator_index],
                                         reference[separator_index:-1])
                    yield 'text', remain
                # Whitespace should not be significant in a reference
                reference = normalize_whitespace(reference)
                yield 'reference', reference
                buffer = [c]
            else:
                # Was a regular '_' in a word
                buffer.append(c)
            status = DEFAULT

    # Buffer left
    if buffer:
        yield 'text', u''.join(buffer)



if __name__ == '__main__':
    from itools.handlers import Text
    from pprint import pprint

    f = open('../../pep-0333.txt')
    data = f.read()
    encoding = Text.guess_encoding(data)
    text = unicode(data, encoding)
    doc = Document(text)
    print "events"
    pprint(doc.events)

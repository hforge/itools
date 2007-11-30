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

# Import from itools
from itools.xml import TEXT, START_ELEMENT, END_ELEMENT


# Statuses for use in automatons
(DEFAULT, LITERAL, EMPHASIS_OR_STRONG, EMPHASIS, EMPHASIS_STRONG,
 INTERPRETED_OR_LITERAL, INTERPRETED, INTERPRETED_OR_REFERENCE, FOOTNOTE,
 FOOTNOTE_OR_TEXT, SUBSTITUTION, TARGET_INLINE, REFERENCE_OR_TEXT) = range(13)

# Events of the internal data structure
(XBLOCK, XCITATION, XEMPHASIS, XFOOTNOTE, XINTERPRETED, XLIST_BEGIN,
 XLIST_END, XLIST_ITEM_BEGIN, XLIST_ITEM_END, XLITERAL, XLITERAL_BLOCK,
 XPARAGRAPH, XREFERENCE, XSTRONG, XSUBSTITUTION, XTARGET, XTEXT,
 XTITLE) = range(18)




src = ur"""ÄÅÁÀÂÃäåáàâãÇçÉÈÊËéèêëæÍÌÎÏíìîïÑñÖÓÒÔÕØöóòôõøßÜÚÙÛüúùûÝŸýÿ"""
dst = ur"""AAAAAAaaaaaaCcEEEEeeeeeIIIIiiiiNnOOOOOOooooooSUUUUuuuuYŸyy"""

transmap = {}
for i in range(len(src)):
    a, b = src[i], dst[i]
    transmap[ord(a)] = ord(b)


def checkid(id):
    """Turn a bytestring or unicode into an identifier only composed of
    alphanumerical characters and a limited list of signs.

    It only supports Latin-based alphabets.
    """
    if isinstance(id, str):
        id = unicode(id, 'utf8')

    # Strip diacritics
    id = id.strip().translate(transmap)

    # Check for unallowed characters
    allowed_characters = set([u'.', u'-', u'_', u'@'])
    id = [ (c.isalnum() or c in allowed_characters) and c or u'-' for c in id ]

    # Merge hyphens
    id = u''.join(id)
    id = id.split(u'-')
    id = u'-'.join([x for x in id if x])

    # Check wether the id is empty
    if len(id) == 0:
        return None

    # Return a safe ASCII bytestring
    return str(id)



def parse_blocks(text):
    """Splits the given text in blocks separated by blank lines.
    """
    buffer = []
    for line in text.splitlines():
        buffer.append(line)
        if not line.strip():
            yield XBLOCK, buffer
            buffer = []

    # Buffer left
    if buffer:
        yield XBLOCK, buffer



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
    """Replace all adjacent whitespace (including carriage returns) by a
    single space.

    Only use where whitespace is not significant, e.g. not in literal blocks.
    """
    return u" ".join(text.split())



def parse_lists(stream):
    events = []
    indents = [(None, 0)]

    for event, value in stream:
        if event != XBLOCK:
            events.append((event, value))
            continue
        last_type, last_indent = indents[-1]
        # Check exit of list indent
        first_line = value[0]
        indent = len(first_line) - len(first_line.lstrip(u' \t'))
        while indent < last_indent:
            last_type, last_indent = indents.pop()
            events.append((XLIST_ITEM_END, last_indent))
            # Prepare end of list just in case
            events.append((XLIST_END, last_type))
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
            if not events or (events[-1] != (XLIST_END, first_word)):
                # The list was not begun
                events.append((XLIST_BEGIN, first_word))
            else:
                # Remove XLIST_END, another item follows
                events.pop()
            events.append((XLIST_ITEM_BEGIN, list_indent))
            block = [value[0][list_indent:]] + value[1:]
            events.append((XBLOCK, block))
            indents.append((first_word, list_indent))
        else:
            events.append((XBLOCK, value))

    # Indents left (except default indent)
    if len(indents) > 1:
        del indents[0]
        while indents:
            last_type, last_indent = indents.pop()
            events.append((XLIST_ITEM_END, last_indent))
        events.append((XLIST_END, last_type))

    return events


def parse_literal_blocks(stream):
    status = DEFAULT
    indent_level = None
    buffer = []

    for event, value in stream:
        if status == DEFAULT:
            if event != XBLOCK:
                yield event, value
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
                yield XBLOCK, block
        elif status == LITERAL:
            if event != XBLOCK:
                block = strip_block(buffer)
                yield XLITERAL_BLOCK, u'\n'.join(block)
                yield event, value
                status = DEFAULT
            elif strip_block(value):
                first_line = value[0]
                indent = len(first_line) - len(first_line.lstrip(u' \t'))
                if indent > indent_level:
                    buffer.extend(value)
                else:
                    block = strip_block(buffer)
                    yield XLITERAL_BLOCK, u'\n'.join(block)
                    yield event, value
                    status = DEFAULT
            else:
                buffer.extend(value)



def parse_titles(stream):
    adornments = r'''!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~'''

    for event, value in stream:
        if event != XBLOCK:
            yield event, value
            continue
        first_line = value[0]
        first_char = first_line[0]
        # Look for an overlined title
        if (first_char in adornments
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
                    yield XPARAGRAPH, text
                continue
            # Split title and possible paragraph
            title = value[:i + 2]
            # Return title and adornments separately
            overline = title[0][0]
            underline = title[-1][0]
            title = u'\n'.join(title[1:-1])
            yield XTITLE, (overline, title, underline)
            # A paragraph may be glued
            buffer = value[i + 2:]
            block = strip_block(buffer)
            if block:
                text = u' '.join(block)
                text = normalize_whitespace(text)
                yield XPARAGRAPH, text
        else:
            # Look for an underlined title
            for i, line in enumerate(value):
                if (line and line[0] in adornments
                        and line.count(line[0]) == len(line)):
                    break
            else:
                # No title found
                block = strip_block(value)
                if block:
                    text = u' '.join(block)
                    text = normalize_whitespace(text)
                    yield XPARAGRAPH, text
                continue
            # Split title and possible paragraph
            title = value[:i + 1]
            # Special case: '..' on its own means directive
            # TODO remove when directives are implemented?
            if title[-1] == u'..':
                text = u' '.join(value)
                text = normalize_whitespace(text)
                yield XPARAGRAPH, text
                continue
            # Return title and adornments separately
            overline = u''
            underline = title[-1][0]
            title = u'\n'.join(title[:-1])
            yield XTITLE, (overline, title, underline)
            # A paragraph may be glued
            buffer = value[i + 1:]
            block = strip_block(buffer)
            if block:
                text = u' '.join(block)
                text = normalize_whitespace(text)
                yield XPARAGRAPH, text



def parse_everything(text):
    # The variable "text" must be a unicode string
    events = parse_blocks(text)
    events = parse_lists(events)
    events = parse_literal_blocks(events)
    events = parse_titles(events)
    return events



###########################################################################
# Parse inline elements
###########################################################################

def parse_inline(text):
    status = DEFAULT
    buffer = []

    if not isinstance(text, unicode):
        raise TypeError, "Text must be decoded to unicode"

    for c in text:
        if status == DEFAULT:
            if c == u'*':
                if buffer:
                    yield XTEXT, u''.join(buffer)
                    buffer = []
                status = EMPHASIS_OR_STRONG
            elif c == u'`':
                if buffer:
                    yield XTEXT, u''.join(buffer)
                    buffer = []
                status = INTERPRETED_OR_LITERAL
            elif c == u'[':
                if buffer:
                    yield XTEXT, u''.join(buffer)
                # Keep opening bracket in case it was a false positive
                buffer = [u'[']
                status = FOOTNOTE
            elif c == u'|':
                if buffer:
                    yield XTEXT, u''.join(buffer)
                    buffer = []
                status = SUBSTITUTION
            elif c == u'_':
                # Before or after a word?
                if buffer and buffer[-1].isspace():
                    yield XTEXT, u''.join(buffer)
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
                yield XEMPHASIS, u''.join(buffer)
                buffer = []
                status = DEFAULT
            else:
                buffer.append(c)
        elif status == EMPHASIS_STRONG:
            if c == u'*' and buffer and buffer[-1] == u'*':
                yield XSTRONG, u''.join(buffer[:-1])
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
                yield XLITERAL, u''.join(buffer[:-1])
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
                yield XREFERENCE, reference
                buffer = []
                status = DEFAULT
            else:
                yield XINTERPRETED, u''.join(buffer)
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
                    yield XFOOTNOTE, footnote
                else:
                    yield XCITATION, footnote
                buffer = []
                status = DEFAULT
            else:
                # False positive
                buffer.append(c)
                yield XTEXT, u''.join(buffer)
            buffer = []
            status = DEFAULT
        elif status == SUBSTITUTION:
            if c == u'|':
                yield XSUBSTITUTION, u''.join(buffer)
                buffer = []
                status = DEFAULT
            else:
                buffer.append(c)
        elif status == TARGET_INLINE:
            if c == u'`':
                if buffer:
                    yield XTARGET, u''.join(buffer)
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
                    yield XTEXT, remain
                # Whitespace should not be significant in a reference
                reference = normalize_whitespace(reference)
                yield XREFERENCE, reference
                buffer = [c]
            else:
                # Was a regular '_' in a word
                buffer.append(c)
            status = DEFAULT

    # Buffer left
    if buffer:
        yield XTEXT, u''.join(buffer)



def inline_stream(text):
    """Turn a text into a list of events similar to XML: START_ELEMENT,
    END_ELEMENT, TEXT.

    Inline elements (emphasis, strong, reference sources...) are concerned.
    """
    events = []

    for event, value in parse_inline(text):
        if event == XTEXT:
            events.append((TEXT, value.encode('utf-8'), None))
        elif event == XFOOTNOTE:
            target = checkid(value).lower()
            attributes = {XTARGET: target}
            events.append((START_ELEMENT, (rest_uri, event, attributes), None))
            events.append((TEXT, value.encode('utf-8'), None))
            events.append((END_ELEMENT, (rest_uri, event), None))
        elif event == XREFERENCE:
            target = checkid(value).lower()
            attributes = {XTARGET: target}
            events.append((START_ELEMENT, (rest_uri, event, attributes), None))
            events.append((TEXT, value.encode('utf-8'), None))
            events.append((END_ELEMENT, (rest_uri, event), None))
        else:
            events.append((START_ELEMENT, (rest_uri, event, {}), None))
            events.append((TEXT, value.encode('utf-8'), None))
            events.append((END_ELEMENT, (rest_uri, event), None))

    return events



###########################################################################
# Public API
###########################################################################
# XXX dummy
rest_uri = 'http://docutils.sourceforge.net/docs/ref/docutils.dtd'



def block_stream(text):
    """Turn a text into a list of events similar to XML: START_ELEMENT,
    END_ELEMENT, TEXT.

    Block elements (lists, literal blocks, paragraphs, titles...) are
    concerned. Inline elements are loaded as well where applicable.
    """
    if isinstance(text, str):
        text = unicode(text, 'utf-8')

    events = []
    for event, value in parse_everything(text):
        if event == XTITLE:
            overline, title, underline = value
            target = checkid(title).lower()
            attributes = {(rest_uri, 'overline'): overline,
                          (rest_uri, 'underline'): underline,
                          (rest_uri, XTARGET): target}
            events.append((START_ELEMENT, (rest_uri, event, attributes), None))
            events.extend(inline_stream(title))
            events.append((END_ELEMENT, (rest_uri, event), None))
        elif event == XPARAGRAPH:
            events.append((START_ELEMENT, (rest_uri, event, {}), None))
            events.extend(inline_stream(value))
            events.append((END_ELEMENT, (rest_uri, event), None))
        elif event == XLITERAL_BLOCK:
            events.append((START_ELEMENT, (rest_uri, event, {}), None))
            events.append((TEXT, value.encode('utf-8'), None))
            events.append((END_ELEMENT, (rest_uri, event), None))
        elif event == XLIST_BEGIN:
            events.append((START_ELEMENT, (rest_uri, 'list',
                {(rest_uri, 'item'): value}), None))
        elif event == XLIST_END:
            events.append((END_ELEMENT, (rest_uri, 'list'), None))
        elif event == XLIST_ITEM_BEGIN:
            events.append((START_ELEMENT, (rest_uri, 'list_item', {}), None))
        elif event == XLIST_ITEM_END:
            events.append((END_ELEMENT, (rest_uri, 'list_item'), None))
        else:
            raise NotImplementedError, event

    return events


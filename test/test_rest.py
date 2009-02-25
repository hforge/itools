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

# Import from the Standard Library
from unittest import TestCase, main

# Import from itools.rest
from itools.rest.parser import strip_block, normalize_whitespace, parse_inline
from itools.rest.parser import parse_blocks, parse_lists, parse_literal_blocks
from itools.rest.parser import parse_titles
from itools.rest.parser import XBLOCK, XCITATION, XEMPHASIS, XFOOTNOTE
from itools.rest.parser import XINTERPRETED, XLIST_BEGIN, XLIST_END
from itools.rest.parser import XLIST_ITEM_BEGIN, XLIST_ITEM_END, XLITERAL
from itools.rest.parser import XLITERAL_BLOCK, XPARAGRAPH, XREFERENCE, XSTRONG
from itools.rest.parser import XSUBSTITUTION, XTARGET, XTEXT, XTITLE



class TestParserUtils(TestCase):

    def test_strip_block_empty(self):
        block = []
        stripped = strip_block(block)
        self.assertEqual(stripped, [])


    def test_strip_block_regular(self):
        block = [u"A test", u""]
        stripped = strip_block(block)
        self.assertEqual(stripped, [u"A test"])


    def test_strip_block_whitespace(self):
        block = [u"A test", u"  "]
        stripped = strip_block(block)
        self.assertEqual(stripped, [u"A test"])


    def test_strip_block_tab(self):
        block = [u"A test", u"\t"]
        stripped = strip_block(block)
        self.assertEqual(stripped, [u"A test"])


    def test_normalize_whitespace(self):
        text = u"""  I am   full
of\tinsignificant  \t whitespace. """
        text = normalize_whitespace(text)
        self.assertEqual(text, u"I am full of insignificant whitespace.")



class TestInlineParser(TestCase):

    def test_bytestring(self):
        """I am a bytestring, not text."""
        data = """I am a bytestring, not text."""
        self.assertRaises(TypeError, parse_inline(data))

    def test_text(self):
        """I am a regular text."""
        data = u"""I am a regular text."""
        events = parse_inline(data).next()
        self.assertEqual(events, (XTEXT, u'I am a regular text.'))


    def test_emphasis(self):
        """This text *contains* emphasis."""
        data = u"""This text *contains* emphasis."""
        events = list(parse_inline(data))
        self.assertEqual(events[0], (XTEXT, u'This text '))
        self.assertEqual(events[1], (XEMPHASIS, u'contains'))
        self.assertEqual(events[2], (XTEXT, u' emphasis.'))


    def test_emphasis_strong(self):
        """This text *contains* **strong** emphasis."""
        data = u"""This text *contains* **strong** emphasis."""
        events = list(parse_inline(data))
        self.assertEqual(events[0], (XTEXT, u'This text '))
        self.assertEqual(events[1], (XEMPHASIS, u'contains'))
        self.assertEqual(events[2], (XTEXT, u' '))
        self.assertEqual(events[3], (XSTRONG, u'strong'))
        self.assertEqual(events[4], (XTEXT, u' emphasis.'))


    def test_interpreted(self):
        """This `word` is interpreted."""
        data = u"""This `word` is interpreted."""
        events = list(parse_inline(data))
        self.assertEqual(events[0], (XTEXT, u'This '))
        self.assertEqual(events[1], (XINTERPRETED, u'word'))
        self.assertEqual(events[2], (XTEXT, u' is interpreted.'))


    def test_inline_literal(self):
        """This ``word`` is inline literal."""
        data = u"""This ``word`` is inline literal."""
        events = list(parse_inline(data))
        self.assertEqual(events[0], (XTEXT, u'This '))
        self.assertEqual(events[1], (XLITERAL, u'word'))
        self.assertEqual(events[2], (XTEXT, u' is inline literal.'))


    def test_reference_simple(self):
        """This word_ is a reference to a target."""
        data = u"""This word_ is a reference to a target."""
        events = list(parse_inline(data))
        self.assertEqual(events[0], (XTEXT, u'This '))
        self.assertEqual(events[1], (XREFERENCE, u'word'))
        self.assertEqual(events[2], (XTEXT, u' is a reference to a target.'))


    def test_reference_quoted(self):
        """This `couple of words`_ is a reference too."""
        data = u"""This `couple of words`_ is a reference too."""
        events = list(parse_inline(data))
        self.assertEqual(events[0], (XTEXT, u'This '))
        self.assertEqual(events[1], (XREFERENCE, u'couple of words'))
        self.assertEqual(events[2], (XTEXT, u' is a reference too.'))


    def test_not_reference(self):
        """This is a_trap for the ``__parser__``."""
        data = u"""This is a_trap for the ``__parser__``."""
        events = list(parse_inline(data))
        self.assertEqual(events[0], (XTEXT, u'This is a_trap for the '))
        self.assertEqual(events[1], (XLITERAL, u'__parser__'))
        self.assertEqual(events[2], (XTEXT, u'.'))


    def test_fake_footnote(self):
        """I look like a footnote[1]."""
        data = u"""I look like a footnote[1]."""
        events = list(parse_inline(data))
        self.assertEqual(events[0], (XTEXT, u'I look like a footnote'))
        self.assertEqual(events[1], (XTEXT, u'[1].'))


    def test_reference_footnote(self):
        """See the footnote[1]_."""
        data = u"""See the footnote[1]_."""
        events = list(parse_inline(data))
        self.assertEqual(events[0], (XTEXT, u'See the footnote'))
        self.assertEqual(events[1], (XFOOTNOTE, u'1'))
        self.assertEqual(events[2], (XTEXT, u'.'))


    def test_reference_citation(self):
        """See the citation [CIT2002]_."""
        data = u"""See the citation [CIT2002]_."""
        events = list(parse_inline(data))
        self.assertEqual(events[0], (XTEXT, u'See the citation '))
        self.assertEqual(events[1], (XCITATION, u'CIT2002'))
        self.assertEqual(events[2], (XTEXT, u'.'))


    def test_reference_substitution(self):
        """Introducing the |substitution|!"""
        data = u"""Introducing the |substitution|!"""
        events = list(parse_inline(data))
        self.assertEqual(events[0], (XTEXT, u'Introducing the '))
        self.assertEqual(events[1], (XSUBSTITUTION, u'substitution'))
        self.assertEqual(events[2], (XTEXT, u'!'))


    def test_target_inline(self):
        """I am a _`inline target`."""
        data = u"""I am a _`inline target`."""
        events = list(parse_inline(data))
        self.assertEqual(events[0], (XTEXT, u'I am a '))
        self.assertEqual(events[1], (XTARGET, u'inline target'))
        self.assertEqual(events[2], (XTEXT, u'.'))



class TestDocumentParser(TestCase):

    def test_blocks(self):
        text = u"""\
I am a block.

I am another
block."""
        events = parse_blocks(text)
        events = list(events)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0], (XBLOCK, [u'I am a block.', u'']))
        self.assertEqual(events[1], (XBLOCK, [u'I am another', u'block.']))


    def test_single_lists(self):
        text = u"""\
* I am an unordered list item
  on several lines.

1. I am an ordered list item
   on several lines."""
        events = parse_blocks(text)
        events = parse_lists(events)
        self.assertEqual(len(events), 10)
        self.assertEqual(events[0], (XLIST_BEGIN, u'*'))
        self.assertEqual(events[1], (XLIST_ITEM_BEGIN, 2))
        self.assertEqual(events[2], (XBLOCK, [u'I am an unordered list item',
                                              u'  on several lines.', u'']))
        self.assertEqual(events[3], (XLIST_ITEM_END, 2))
        self.assertEqual(events[4], (XLIST_END, u'*'))
        self.assertEqual(events[5], (XLIST_BEGIN, u'#'))
        self.assertEqual(events[6], (XLIST_ITEM_BEGIN, 3))
        self.assertEqual(events[7], (XBLOCK, [u'I am an ordered list item',
                                              u'   on several lines.']))
        self.assertEqual(events[8], (XLIST_ITEM_END, 3))
        self.assertEqual(events[9], (XLIST_END, u'#'))


    def test_double_lists(self):
        text = u"""\
* I am an unordered list item;

* on several lines.

1. I am an ordered list item;

2. on several lines."""
        events = parse_blocks(text)
        events = parse_lists(events)
        self.assertEqual(len(events), 16)
        self.assertEqual(events[0], (XLIST_BEGIN, u'*'))
        self.assertEqual(events[1], (XLIST_ITEM_BEGIN, 2))
        self.assertEqual(events[2], (XBLOCK, [u'I am an unordered list item;',
                                              u'']))
        self.assertEqual(events[3], (XLIST_ITEM_END, 2))
        self.assertEqual(events[4], (XLIST_ITEM_BEGIN, 2))
        self.assertEqual(events[5], (XBLOCK, [u'on several lines.', u'']))
        self.assertEqual(events[6], (XLIST_ITEM_END, 2))
        self.assertEqual(events[7], (XLIST_END, u'*'))
        self.assertEqual(events[8], (XLIST_BEGIN, u'#'))
        self.assertEqual(events[9], (XLIST_ITEM_BEGIN, 3))
        self.assertEqual(events[10], (XBLOCK, [u'I am an ordered list item;',
                                               u'']))
        self.assertEqual(events[11], (XLIST_ITEM_END, 3))
        self.assertEqual(events[12], (XLIST_ITEM_BEGIN, 3))
        self.assertEqual(events[13], (XBLOCK, [u'on several lines.']))
        self.assertEqual(events[14], (XLIST_ITEM_END, 3))
        self.assertEqual(events[15], (XLIST_END, u'#'))


    def test_nested_lists(self):
        text = u"""\
* First list.

  1. Second list.

     Second list, second paragraph.

  First list, second paragraph."""
        events = parse_blocks(text)
        events = parse_lists(events)
        self.assertEqual(len(events), 12)
        self.assertEqual(events[0], (XLIST_BEGIN, u'*'))
        self.assertEqual(events[1], (XLIST_ITEM_BEGIN, 2))
        self.assertEqual(events[2], (XBLOCK, [u'First list.', u'']))
        self.assertEqual(events[3], (XLIST_BEGIN, u'#'))
        self.assertEqual(events[4], (XLIST_ITEM_BEGIN, 5))
        self.assertEqual(events[5], (XBLOCK, [u'Second list.', u'']))
        self.assertEqual(events[6], (XBLOCK,
            [u'     Second list, second paragraph.', u'']))
        self.assertEqual(events[7], (XLIST_ITEM_END, 5))
        self.assertEqual(events[8], (XLIST_END, u'#'))
        self.assertEqual(events[9], (XBLOCK,
            [u'  First list, second paragraph.']))
        self.assertEqual(events[10], (XLIST_ITEM_END, 2))
        self.assertEqual(events[11], (XLIST_END, u'*'))


    def test_literal_blocks(self):
        text = u"""\
The code reads as follow::

    >>> from itools.rest import parser

But failed with a NotImplementedError."""
        events = parse_blocks(text)
        events = parse_literal_blocks(events)
        events = list(events)
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0], (XBLOCK, [u'The code reads as follow:']))
        self.assertEqual(events[1], (XLITERAL_BLOCK,
            u'    >>> from itools.rest import parser'))
        self.assertEqual(events[2], (XBLOCK,
            [u'But failed with a NotImplementedError.']))


    def test_list_literal(self):
        text = u"""\
1. I am a list
   containing a literal::

     >>> from itools.rest import parser

2. and several
   items."""
        events = parse_blocks(text)
        events = parse_lists(events)
        events = parse_literal_blocks(events)
        events = list(events)
        self.assertEqual(len(events), 9)
        self.assertEqual(events[0], (XLIST_BEGIN, u'#'))
        self.assertEqual(events[1], (XLIST_ITEM_BEGIN, 3))
        self.assertEqual(events[2], (XBLOCK, [u'I am a list',
            u'   containing a literal:']))
        self.assertEqual(events[3], (XLITERAL_BLOCK,
            u'     >>> from itools.rest import parser'))
        self.assertEqual(events[4], (XLIST_ITEM_END, 3))
        self.assertEqual(events[5], (XLIST_ITEM_BEGIN, 3))
        self.assertEqual(events[6], (XBLOCK, [u'and several',  u'   items.']))
        self.assertEqual(events[7], (XLIST_ITEM_END, 3))
        self.assertEqual(events[8], (XLIST_END, u'#'))


    def test_paragraph(self):
        text = u"""\
I am a paragraph.

I am another one."""
        events = parse_blocks(text)
        events = parse_titles(events)
        events = list(events)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0], (XPARAGRAPH, u'I am a paragraph.'))
        self.assertEqual(events[1], (XPARAGRAPH, u'I am another one.'))


    def test_title_overline(self):
        text = u"""\
#############################
I am the king of the titles
#############################"""
        events = parse_blocks(text)
        events = parse_titles(events)
        events = list(events)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], (XTITLE,
            (u'#', u'I am the king of the titles', u'#')))


    def test_title_underline(self):
        text = u"""\
I am the prince of the titles
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"""
        events = parse_blocks(text)
        events = parse_titles(events)
        events = list(events)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], (XTITLE,
            (u'', u'I am the prince of the titles', u'%')))


    def test_title_paragraph(self):
        text = u"""\
Please allow to introduce myself
````````````````````````````````
I'm a man of wealth and taste"""
        events = parse_blocks(text)
        events = parse_titles(events)
        events = list(events)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0], (XTITLE,
            (u'', u'Please allow to introduce myself', u'`')))
        self.assertEqual(events[1], (XPARAGRAPH,
            u"I'm a man of wealth and taste"))


    def test_paragraph_literal(self):
        text = u"""\
The code reads as follow::

    >>> from itools.rest import parser

But failed with a NotImplementedError."""
        events = parse_blocks(text)
        events = parse_literal_blocks(events)
        events = parse_titles(events)
        events = list(events)
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0], (XPARAGRAPH, u'The code reads as follow:'))
        self.assertEqual(events[1], (XLITERAL_BLOCK,
            u'    >>> from itools.rest import parser'))
        self.assertEqual(events[2], (XPARAGRAPH,
            u'But failed with a NotImplementedError.'))


    def test_paragraph_list(self):
        text = u"""\
* I am a block.

  I am the same block.

I am a paragraph."""
        events = parse_blocks(text)
        events = parse_lists(events)
        events = parse_titles(events)
        events = list(events)
        self.assertEqual(len(events), 7)
        self.assertEqual(events[0], (XLIST_BEGIN, u'*'))
        self.assertEqual(events[1], (XLIST_ITEM_BEGIN, 2))
        self.assertEqual(events[2], (XPARAGRAPH, u'I am a block.'))
        self.assertEqual(events[3], (XPARAGRAPH, u'I am the same block.'))
        self.assertEqual(events[4], (XLIST_ITEM_END, 2))
        self.assertEqual(events[5], (XLIST_END, u'*'))
        self.assertEqual(events[6], (XPARAGRAPH, u'I am a paragraph.'))





if __name__ == '__main__':
    main()

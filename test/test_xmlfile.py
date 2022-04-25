# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2009 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2008 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2008 Sylvain Taverne <taverne.sylvain@gmail.com>
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
from unittest import TestCase, main

# Import from itools
import itools.html
from itools.srx import TEXT as srx_TEXT
from itools.xml import XMLParser
from itools.xmlfile import XMLFile



class XMLTestCase(TestCase):

    # Identity
    def test_identity(self):
        """
        Tests wether the input and the output match.
        """
        data = ('<html>\n'
                '<head></head>\n'
                '<body>\n'
                ' this is a <span style="color: red">test</span>\n'
                '</body>\n'
                '</html>')
        h1 = XMLFile(string=data)
        h2 = XMLFile(string=data)

        self.assertEqual(h1, h2)


    # Entities: http://www.w3.org/TR/REC-xml/#sec-entexpand
    def test_1(self):
        data = ('<?xml version="1.0"?>\n'
                '<!DOCTYPE test\n'
                '[\n'
                '<!ENTITY example "<p>An ampersand (&#38;#38;) may be '
                'escaped numerically (&#38;#38;#38;) or with a general '
                ' entity (&amp;amp;).</p>" >\n'
                ']>\n'
                '<test>&example;</test>\n')

        parser = XMLParser(data)
        self.assertEqual(list(parser)[6:9], [
                  (2, (None, 'p', {}), 6),
                  (4, 'An ampersand (&) may be escaped numerically (&#38;) '
                      'or with a general  entity (&amp;).', 6),
                  (3, (None, 'p'), 6)])

    def test_2(self):
        data = ('<?xml version="1.0"?>\n'
                '<!DOCTYPE test [\n'
                '<!ELEMENT test (#PCDATA) >\n'
                "<!ENTITY % xx '&#37;zz;'>\n"
                """<!ENTITY % zz '&#60;!ENTITY tricky "error-prone" >' >\n"""
                '%xx;\n'
                ']>\n'
                '<test>This sample shows a &tricky; method.</test>')

        parser = XMLParser(data)
        self.assertEqual(list(parser)[5], (4,
                         'This sample shows a error-prone method.', 8))

    def test_3(self):
        data = ('<?xml version="1.0"?>\n'
                '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n'
                '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
                '<html>&laquo; &fnof; &Xi; &psi; &permil; &real; &infin; '
                '&there4; &clubs;</html>\n')
        expected = '« ƒ Ξ ψ ‰ ℜ ∞ ∴ ♣'

        parser = XMLParser(data)
        self.assertEqual(list(parser)[5][1], expected)



class TranslatableTestCase(TestCase):

    def test_surrounding(self):
        text = '<em>Hello World</em>'
        parser = XMLFile(string=text)

        messages = [unit[0] for unit in parser.get_units()]
        self.assertEqual(messages, [((srx_TEXT, u'Hello World'),)])



if __name__ == '__main__':
    main()

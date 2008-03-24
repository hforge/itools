# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import unittest
from unittest import TestCase

# Import from itools
from itools.abnf import build_grammar, Parser, BaseContext


###########################################################################
# Syntax
###########################################################################
lr1_grammar = build_grammar(
    'S = A\r\n'
    'S = "xb"\r\n'
    'A = "a" A "b"\r\n'
    'A = B\r\n'
    'B = "x"\r\n')


expression_grammar = build_grammar(
    'E = I\r\n'
    'E = E "+" E\r\n'
    'E = E "*" E\r\n'
    'I = 1*DIGIT\r\n')


ip_grammar = build_grammar(
    # IPv4
    'IPv4address = dec-octet "." dec-octet "." dec-octet "." dec-octet\r\n'
    'dec-octet = DIGIT\r\n'
    '          / %x31-39 DIGIT\r\n'
    '          / "1" DIGIT DIGIT\r\n'
    '          / "2" %x30-34 DIGIT\r\n'
    '          / "25" %x30-35\r\n'
    # IPv6
    'IPv6address =                            6( h16 ":" ) ls32\r\n'
    '            /                       "::" 5( h16 ":" ) ls32\r\n'
    '            / [               h16 ] "::" 4( h16 ":" ) ls32\r\n'
    '            / [ *1( h16 ":" ) h16 ] "::" 3( h16 ":" ) ls32\r\n'
    '            / [ *2( h16 ":" ) h16 ] "::" 2( h16 ":" ) ls32\r\n'
    '            / [ *3( h16 ":" ) h16 ] "::"    h16 ":"   ls32\r\n'
    '            / [ *4( h16 ":" ) h16 ] "::"              ls32\r\n'
    '            / [ *5( h16 ":" ) h16 ] "::"              h16\r\n'
    '            / [ *6( h16 ":" ) h16 ] "::"\r\n'
    'h16         = 1*4HEXDIG\r\n'
    'ls32        = ( h16 ":" h16 ) / IPv4address\r\n'
    )



class SyntaxTestCase(TestCase):

    def test_lr1(self):
        is_valid = lr1_grammar.is_valid
        self.assertEqual(is_valid('S', 'xb'), True)
        self.assertEqual(is_valid('S', 'aaaxbbb'), True)
        self.assertEqual(is_valid('S', 'aaabbb'), False)
        self.assertEqual(is_valid('S', 'aaaaxbbb'), False)


    def test_expression(self):
        is_valid = expression_grammar.is_valid
        self.assertEqual(is_valid('E', '32'), True)
        self.assertEqual(is_valid('E', '14342523543365634'), True)
        self.assertEqual(is_valid('E', '1434252x5435634'), False)
        self.assertEqual(is_valid('E', ''), False)
        self.assertEqual(is_valid('E', '32+7'), True)
        self.assertEqual(is_valid('E', '32 + 7'), False)
        self.assertEqual(is_valid('E', '32+'), False)


    def test_ipv4address(self):
        is_valid = ip_grammar.is_valid
        self.assertEqual(is_valid('IPv4address', '192.168.0.1'), True)
        self.assertEqual(is_valid('IPv4address', '192.168.00.1'), False)
        self.assertEqual(is_valid('IPv4address', '192.168.1'), False)
        self.assertEqual(is_valid('IPv4address', '192.168.256.1'), False)


    def test_ipv6address(self):
        is_valid = ip_grammar.is_valid
        self.assertEqual(is_valid('IPv6address', '2001:db8::7'), True)
        self.assertEqual(is_valid('IPv6address', '2001:dg8::7'), False)



###########################################################################
# Semantic
###########################################################################
class ExpressionContext(BaseContext):

    def I(self, start, end, *args):
        return int(self.data[start:end])


    def E_1(self, start, end, value):
        return value


    def E_2(self, start, end, left, right):
        return left + right


    def E_3(self, start, end, left, right):
        return left * right



class IPv4Context(BaseContext):

    def dec_octet(self, start, end, *args):
        return int(self.data[start:end])


    def IPv4address(self, start, end, *args):
        return args



parse_expression = Parser(expression_grammar, ExpressionContext, 'E')
parse_ipv4address = Parser(ip_grammar, IPv4Context, 'IPv4address')



class SemanticTestCase(TestCase):

    def test_expression(self):
        self.assertEqual(parse_expression('32'), 32)
        self.assertEqual(parse_expression('14342523543354'), 14342523543354)
        self.assertRaises(ValueError, parse_expression, '1434252x5435634')
        self.assertRaises(ValueError, parse_expression, '')
        self.assertEqual(parse_expression('32+7'), 39)
        self.assertEqual(parse_expression('32+7+2'), 41)
        self.assertEqual(parse_expression('3+2*5'), 13)
        self.assertEqual(parse_expression('3*2+5'), 11)


    def test_ipv4address(self):
        run = ip_grammar.run
        self.assertEqual(parse_ipv4address('192.168.0.1'), (192, 168, 0, 1))
        self.assertRaises(ValueError, parse_ipv4address, '192.168.00.1')



if __name__ == '__main__':
    unittest.main()

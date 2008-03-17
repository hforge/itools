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
from string import ascii_letters, digits, hexdigits

# Import from itools
from grammar import Grammar, BaseContext


# Constants (core rules)
ALPHA = frozenset(ascii_letters)
BIT = frozenset('01')
CHAR = frozenset([ chr(x) for x in range(1, 128) ])
CR = frozenset('\r')
CTL = frozenset([ chr(x) for x in range(32) ] + [chr(127)])
DIGIT = frozenset(digits)
DQUOTE = frozenset('"')
HEXDIG = frozenset(hexdigits)
HTAB = frozenset('\t')
LF = frozenset('\n')
OCTET = frozenset([ chr(x) for x in range(256) ])
SP = frozenset(' ')
VCHAR = frozenset([ chr(x) for x in range(33, 127) ])
WSP = frozenset(' \t')
# Constants (other)
DASH = frozenset('-')
DOT = frozenset('.')
EQUAL = frozenset('=')
SLASH = frozenset('/')


# Grammar
abnf_grammar = Grammar()
add_rule = abnf_grammar.add_rule
# rulelist
add_rule("rulelist", "rulelist'", (None, "rulelist'"))
add_rule("rulelist'", "rule")
add_rule("rulelist'", "*c-wsp", "c-nl")
# rule
add_rule("rule", "rulename", "defined-as", "elements", "c-nl")
# rulename
add_rule("rulename", ALPHA, (None, "rulename'"))
add_rule("rulename'", ALPHA)
add_rule("rulename'", DIGIT)
add_rule("rulename'", DASH)
# defined-as
add_rule("defined-as", "*c-wsp", "defined-as'", "*c-wsp")
add_rule("defined-as'", EQUAL)
#add_rule("defined-as'", EQUAL, SLASH)
# elements
add_rule("elements", "alternation", "*c-wsp")
# c-wsp
add_rule("c-wsp", WSP)
add_rule("c-wsp", "c-nl", WSP)
add_rule("*c-wsp", (None, "c-wsp"))
add_rule("+c-wsp", "c-wsp", "*c-wsp")
# c-nl
add_rule("c-nl", "comment")
add_rule("c-nl", "crlf")
# comment
add_rule("comment", frozenset(';'), (None, "comment'"), "crlf")
add_rule("comment'", WSP)
add_rule("comment'", VCHAR)
# alternation
add_rule("alternation", "concatenation", "alternation'")
add_rule("alternation'",
    "*c-wsp", SLASH, "*c-wsp", "concatenation", "alternation'")
add_rule("alternation'")
#add_rule("alternation",
#    "concatenation", (None, "*c-wsp", SLASH, "*c-wsp", "concatenation"))
# concatenation
add_rule("concatenation", "repetition", "concatenation'")
add_rule("concatenation'", "+c-wsp", "repetition", "concatenation'")
add_rule("concatenation'")
#add_rule("concatenation", "repetition", (None, "+c-wsp", "repetition"))
# repetition
add_rule("repetition", (1, "repeat"), "element")
# repeat
add_rule("repeat", "+digit")
add_rule("repeat", "*digit", frozenset('*'), "*digit")
add_rule("*digit", (None, DIGIT))
# element
add_rule("element", "rulename")
add_rule("element", "group")
add_rule("element", "option")
add_rule("element", "char-val")
add_rule("element", "num-val")
add_rule("element", "prose-val")
# group
add_rule("group",
    frozenset('('), "*c-wsp", "alternation", "*c-wsp", frozenset(')'))
# option
add_rule("option",
    frozenset('['), "*c-wsp", "alternation", "*c-wsp", frozenset(']'))
# char-val
aux = frozenset([ chr(x) for x in [32, 33] + range(35, 127) ])
add_rule("char-val", DQUOTE, (None, aux), DQUOTE)
# num-val
add_rule("num-val", frozenset('%'), "num-val'")
#add_rule("num-val'", "bin-val")
add_rule("num-val'", "dec-val")
add_rule("num-val'", "hex-val")
# bin-val
#add_rule("bin-val", frozenset('b'), "+bit", (1, "bin-val'"))
#add_rule("bin-val'", DOT, "+bit", (None, DOT, "+bit"))
#add_rule("bin-val'", DASH, "+bit")
#add_rule("+bit", BIT, (None, BIT))
# dec-val
add_rule("dec-val", frozenset('d'), "+digit", (1, "dec-val'"))
add_rule("dec-val'", DOT, "+digit", (None, DOT, "+digit"))
add_rule("dec-val'", DASH, "+digit")
add_rule("+digit", DIGIT, (None, DIGIT))
# hex-val
add_rule("hex-val", frozenset('x'), "+hexdig", (1, "hex-val'"))
add_rule("hex-val'", DOT, "+hexdig", (None, DOT, "+hexdig"))
add_rule("hex-val'", DASH, "+hexdig")
add_rule("+hexdig", HEXDIG, (None, HEXDIG))
# prose-val
aux = frozenset([ chr(x) for x in range(32, 62) + range(63, 127) ])
add_rule("prose-val", frozenset('<'), (None, aux), frozenset('>'))
# crlf
add_rule("crlf", CR, LF)


#abnf_grammar.pprint_grammar()
core_rules = {
    'ALPHA': [ALPHA],
    'BIT': [BIT],
    'CHAR': [CHAR],
    'CR': [CR],
    'CRLF': [CR, LF],
    'CTL': [CTL],
    'DIGIT': [DIGIT],
    'DQUOTE': [DQUOTE],
    'HEXDIG': [HEXDIG],
    'HTAB': [HTAB],
    'LF': [LF],
#    'LWSP': ,
    'OCTET': [OCTET],
    'SP': [SP],
    'VCHAR': [VCHAR],
    'WSP': [WSP],
    }



class Context(BaseContext):

    def __init__(self, data):
        BaseContext.__init__(self, data)
        self.grammar = Grammar()


    def rulename(self, start, end, *args):
        # FIXME The RFC says rulenames are case-insensitive
        return self.data[start:end]


    def char_val(self, start, end, *args):
        value = self.data[start+1:end-1]
        return [ frozenset([x.lower(), x.upper()]) for x in value ]


    def num_val(self, start, end, value):
        return value


    def hex_val(self, start, end, *args):
        value = self.data[start+1:end]
        if '-' in value:
            # Range: %x30-39
            a, b = [ eval('0x%s' % x) for x in value.split('-') ]
            return frozenset([ chr(x) for x in range(a, b+1) ])
        elif '.' in value:
            # Concatenation: %x0D.0A
            value = [ eval('0x%s' % x) for x in value.split('.') ]
            return [ frozenset(chr(x)) for x in value ]
        else:
            # Simple: %x20
            value = eval('0x%s' % value)
            return frozenset(chr(value))


    def dec_val(self, start, end, *args):
        value = self.data[start+1:end]
        if '-' in value:
            # Range: %x30-39
            raise NotImplementedError
        elif '.' in value:
            # Concatenation: %x0D.0A
            raise NotImplementedError
        else:
            # Simple: %x20
            value = int(value)
            return frozenset(chr(value))


    def prose_val(self, start, end, *args):
        return []


    def element(self, start, end, value):
        # rulename
        if isinstance(value, str):
            return core_rules.get(value, [value])
        elif isinstance(value, frozenset):
            return [value]
        return value


    def repeat(self, start, end, *args):
        value = self.data[start:end]
        if '*' in value:
            # repeat = *digit "*" *digit
            min, max = value.split('*')
            min = min and int(min) or 0
            max = max and int(max) or None
            return min, max
        else:
            # repeat = 1*digit
            return int(value)


    def repetition(self, start, end, *args):
        if len(args) == 1:
            return args[0]
        repeat, element = args
        if isinstance(repeat, int):
            # <n>element
            return repeat * element
        else:
            # <a>*<b>element
            min, max = repeat
            return (min * element) + [tuple([max] + element)]


    def concatenation(self, start, end, first, rest):
        if rest is None:
            return first
        return first + rest


    def concatenation_(self, start, end, *args):
        if len(args) == 0:
            return None
        space, first, rest = args
        if isinstance(first, tuple):
            first = [first]
        if rest is None:
            return first
        return first + rest


    def alternation(self, start, end, first, rest):
        if rest is None:
            return [first]
        return [first] + rest


    def alternation_(self, start, end, *args):
        if len(args) == 0:
            return None
        space, space, first, rest = args
        if rest is None:
            return [first]
        return [first] + rest


    def group(self, start, end, space1, alternation, space2):
        if len(alternation) == 1:
            return alternation[0]

        grammar = self.grammar
        rulename = grammar.get_internal_rulename()
        for elements in alternation:
            grammar.add_rule(rulename, *elements)
        return [rulename]


    def option(self, start, end, space1, alternation, space2):
        if len(alternation) == 1:
            return [tuple([1] + alternation[0])]
        raise NotImplementedError


    def elements(self, start, end, alternation, space):
        return alternation


    def rule(self, start, end, rulename, defined_as, elements, tail):
        if rulename in core_rules:
            raise ValueError, 'the "%s" rule is reserved' % value
        for elements in elements:
            self.grammar.add_rule(rulename, *elements)


    def rulelist(self, start, end, *args):
        return self.grammar



class Parser(object):

    def __init__(self, grammar, context_class, start_symbol):
        self.grammar = grammar
        self.context_class = context_class
        self.start_symbol = start_symbol
        grammar.get_table(start_symbol, context_class)


    def __call__(self, data):
        context = self.context_class(data)
        return self.grammar.run(self.start_symbol, data, context)


build_grammar = Parser(abnf_grammar, Context, 'rulelist')

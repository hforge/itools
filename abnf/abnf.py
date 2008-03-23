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
add_rule("rulelist", "rulelist-item", (None, "rulelist-item"))
add_rule("rulelist-item", "rule")
add_rule("rulelist-item", "c-wsp*", "c-nl")
# rule
add_rule("rule", "rulename", "defined-as", "alternation", "c-wsp*", "c-nl")
# rulename
add_rule("rulename", ALPHA, (None, ALPHA | DIGIT | DASH))
# defined-as
add_rule("defined-as", "c-wsp*", EQUAL, "c-wsp*")
#add_rule("defined-as", "c-wsp*", EQUAL, SLASH, "c-wsp*")
# c-wsp
add_rule("c-wsp", WSP)
add_rule("c-wsp", "c-nl", WSP)
add_rule("c-wsp+", "c-wsp", "c-wsp*")
add_rule("c-wsp*", (None, "c-wsp"))
# c-nl
add_rule("c-nl", "comment")
add_rule("c-nl", "crlf")
# comment
add_rule("comment", frozenset(';'), (None, WSP | VCHAR), "crlf")
# alternation
add_rule("alternation", "concatenation", "alternation-tail")
add_rule("alternation-tail", "c-wsp*", SLASH, "c-wsp*", "concatenation",
    "alternation-tail")
add_rule("alternation-tail")
# concatenation
add_rule("concatenation", "repetition", "concatenation-tail")
add_rule("concatenation-tail", "c-wsp+", "repetition", "concatenation-tail")
add_rule("concatenation-tail")
# repetition
add_rule("repetition", (1, "repeat"), "element")
# repeat
add_rule("repeat", "digit+")
add_rule("repeat", "digit*", frozenset('*'), "digit*")
add_rule("digit*", (None, DIGIT))
# element
add_rule("element", "rulename")
add_rule("element", "group")
add_rule("element", "option")
add_rule("element", "char-val")
add_rule("element", "num-val")
add_rule("element", "prose-val")
# group
add_rule("group",
    frozenset('('), "c-wsp*", "alternation", "c-wsp*", frozenset(')'))
# option
add_rule("option",
    frozenset('['), "c-wsp*", "alternation", "c-wsp*", frozenset(']'))
# char-val
aux = frozenset([ chr(x) for x in [32, 33] + range(35, 127) ])
add_rule("char-val", DQUOTE, (None, aux), DQUOTE)
# num-val
#add_rule("num-val", frozenset('%'), "bin-val")
add_rule("num-val", frozenset('%'), "dec-val")
add_rule("num-val", frozenset('%'), "hex-val")
# bin-val
#add_rule("bin-val", frozenset('b'), "bit+", (None, DOT, "bit+"))
#add_rule("bin-val", frozenset('b'), "bit+", DASH, "bit+")
#add_rule("bit+", BIT, (None, BIT))
# dec-val
add_rule("dec-val", frozenset('d'), "digit+", (None, DOT, "digit+"))
add_rule("dec-val", frozenset('d'), "digit+", DASH, "digit+")
add_rule("digit+", DIGIT, (None, DIGIT))
# hex-val
add_rule("hex-val", frozenset('x'), "hexdig+", (None, DOT, "hexdig+"))
add_rule("hex-val", frozenset('x'), "hexdig+", DASH, "hexdig+")
add_rule("hexdig+", HEXDIG, (None, HEXDIG))
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


    def hex_val_1(self, start, end, *args):
        value = self.data[start+1:end]
        if '.' in value:
            # Concatenation: %x0D.0A
            value = [ eval('0x%s' % x) for x in value.split('.') ]
            return [ frozenset(chr(x)) for x in value ]
        else:
            # Simple: %x20
            value = eval('0x%s' % value)
            return frozenset(chr(value))


    def hex_val_2(self, start, end, left, right):
        value = self.data[start+1:end]
        # Range: %x30-39
        a, b = [ eval('0x%s' % x) for x in value.split('-') ]
        return frozenset([ chr(x) for x in range(a, b+1) ])


    def dec_val_1(self, start, end, *args):
        value = self.data[start+1:end]
        if '.' in value:
            # Concatenation: %x0D.0A
            raise NotImplementedError
        else:
            # Simple: %x20
            value = int(value)
            return frozenset(chr(value))


    def dec_val_2(self, start, end, left, right):
        value = self.data[start+1:end]
        # Range: %x30-39
        raise NotImplementedError


    def prose_val(self, start, end, *args):
        return []


    def element_1(self, start, end, rulename):
        # element = rulename
        return core_rules.get(rulename, [rulename])


    def element(self, start, end, value):
        if isinstance(value, frozenset):
            return [value]
        return value


    def repeat_1(self, start, end, value):
        value = self.data[start:end]
        # repeat = 1*digit
        return int(value)


    def repeat_2(self, start, end, left, right):
        value = self.data[start:end]
        # repeat = *digit "*" *digit
        min, max = value.split('*')
        min = min and int(min) or 0
        max = max and int(max) or None
        return min, max


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
            if max is not None:
                max = max - min
            return (min * element) + [tuple([max] + element)]


    def concatenation(self, start, end, first, rest):
        if rest is None:
            return first
        return first + rest


    def concatenation_tail(self, start, end, *args):
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
        # Optimize, compact structures of the form: "a" / "b"
        if len(first) == 1 and isinstance(first[0], frozenset):
            for i, conc in enumerate(rest):
                if len(conc) == 1 and isinstance(conc[0], frozenset):
                    rest[i] = [first[0] | conc[0]]
                    return rest

        return [first] + rest


    def alternation_tail(self, start, end, *args):
        if len(args) == 0:
            return None
        space, space, first, rest = args
        if rest is None:
            return [first]
        # Optimize, compact structures of the form: "a" / "b"
        # FIXME Duplicated code (see above)
        if len(first) == 1 and isinstance(first[0], frozenset):
            for i, conc in enumerate(rest):
                if len(conc) == 1 and isinstance(conc[0], frozenset):
                    rest[i] = [first[0] | conc[0]]
                    return rest

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


    def rule(self, start, end, rulename, defined_as, alternation, *args):
        if rulename in core_rules:
            raise ValueError, 'the "%s" rule is reserved' % value
        for elements in alternation:
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

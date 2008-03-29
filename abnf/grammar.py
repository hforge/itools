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

# Import from itools
from tokenizer import Tokenizer, EOI



def pformat_element(element):
    element_type = type(element)
    # Grammar symbol
    if element_type is str:
        return element
    # Repetition
    if element_type is tuple:
        max = element[0]
        rest = ' '.join([ pformat_element(x) for x in element[1:] ])
        if max is None:
            return '*(%s)' % rest
        return '*%s(%s)' % (max, rest)
    # Terminal
    if element_type is frozenset:
        tokens = []
        for token in element:
            if token == EOI:
                tokens.append('$')
            else:
                tokens.append(repr(token))
        return "{%s}" % ','.join(tokens)
    # ?
    raise ValueError, 'XXX'


def pformat_rule(name, rule):
    line = [name, '=']
    if len(rule) == 0:
        line.append("ε")
    else:
        for element in rule:
            line.append(pformat_element(element))
    return ' '.join(line)


def replace_charsets_by_tokens(elements, lexical_table):
    """This helper function receives a sequence of elements with terminals
    expressed as sets of characters (charsets).  Returns the same sequence
    with these charsets replaced by sets-of-tokens, as defined by the given
    "lexical_table".

    Used by the "Grammar.get_tokenizer" method.
    """
    # Charset to token set function
    cs2ts = lambda cs: frozenset([ lexical_table[ord(c)] for c in cs ])

    new_elements = []
    for element in elements:
        element_type = type(element)
        if element_type is frozenset:
            # Charset
            element = cs2ts(element)
        elif element_type is tuple:
            # Repetition
            max, rest = element[0], element[1:]
            element = (max,) + replace_charsets_by_tokens(rest, lexical_table)
        new_elements.append(element)

    if type(elements) is tuple:
        return tuple(new_elements)

    return new_elements



class BaseContext(object):

    def __init__(self, data):
        self.data = data



###########################################################################
# The grammar description
###########################################################################
class Grammar(object):
    """This class keeps the description of the grammar, defined by a set of
    rules of the form:

      grammar-symbol = elements

    Where a grammar symbol is defined by a byte string, and elements is a
    sequence of:

      - grammar symbols (a byte string)

      - character sets (a frozenset of characters)

      - repetitions (tuples of 2 or more elements, where the first element
        is an integer expressing the maximum number of repetitions allowed,
        or None for infinitum)

    For example (TODO make a better example):

      ABNF         elements
      ===========  ==============================
      4 hexdig     hexdig, hexdig, hexdig, hexdig
      1*4 hexdig   hexdig, (3, hexdig)
    """

    def __init__(self):
        self.symbols = set()
        self.rules = {}
        # The lexical layer
        self.charsets = []
        self.tokenizer = None
        self.tokens = None
        # The semantic layer
        self.context_class = None
        self.semantic_map = {}


    #######################################################################
    # Stage 0: Add rules one by one
    #######################################################################
    def add_rule(self, name, *elements):
        """Add the given rule to the set of rules (and update the list of
        character sets).
        """
        # Check the grammar has already been tokenized
        if self.charsets is None:
            msg = 'cannot add any more rules, grammar already tokenized'
            raise ValueError, msg

        # Add the new rule
        self.symbols.add(name)
        rules = self.rules.setdefault(name, [])
        elements = list(elements)
        rules.append(elements)

        # Update the character sets
        elements = set(elements)
        charsets = self.charsets
        while elements:
            element = elements.pop()
            element_type = type(element)
            # Grammar symbol
            if element_type is str:
                continue
            # Repetition
            if element_type is tuple:
                for x in element[1:]:
                    elements.add(x)
                continue
            # Character set
            i = 0
            while i < len(charsets):
                charset = charsets[i]
                # Already included: stop
                if element == charset:
                    break
                # Nothing in common: continue
                intersection = charset & element
                if not intersection:
                    i += 1
                    continue
                # Update charsets
                charsets.remove(charset)
                charsets.append(intersection)
                difference = charset - element
                if difference:
                    charsets.append(difference)
                # Done?
                element = element - charset
                if not element:
                    break
            else:
                # Loop exhausted
                charsets.append(element)


    #######################################################################
    # Pretty Print
    #######################################################################
    def pprint_grammar(self):
        symbols = list(self.symbols)
        symbols.sort()
        for name in symbols:
            for rule in self.rules[name]:
                print pformat_rule(name, rule)


    #######################################################################
    # Stage 1: infer the lexical analyser (tokenizer) from the grammar
    # description, and update the grammar.
    #######################################################################
    def get_tokenizer(self):
        """Infere a lexical layer from the grammar.
        """
        # Initialize the lexical table, a table from character to token id, or
        # None if the character is not allowed in the grammar.
        lexical_table = 256 * [None]

        # Build the lexical table, and the tokenizer.
        # Start at 1, the 0 is for End-Of-Input.
        token = 1
        for charset in self.charsets:
            for char in charset:
                lexical_table[ord(char)] = token
            token += 1
        self.tokens = range(token)
        self.tokenizer = Tokenizer(lexical_table)

        # Update the grammar, replace the sets-of-characters by sets-of-tokens
        self.charsets = None
        rules = self.rules
        for rulename in rules:
            for i, rule in enumerate(rules[rulename]):
                rule = replace_charsets_by_tokens(rule, lexical_table)
                rules[rulename][i] = rule

        return self.tokenizer


    #######################################################################
    # Stage 2: Compile and Optimize the grammar taking into account the
    # semantic layer.
    #######################################################################
    def get_internal_rulename(self, name=None):
        symbols = self.symbols
        if name is None:
            # Used to expand terminal rules (produced while infering the
            # lexical analyser).
            suffixes = [ x[1:] for x in symbols if x[0] == '_']
            suffixes = [ int(x) for x in suffixes if x.isdigit() ]
            suffixes.sort()
            if suffixes:
                name = "_%s" % (suffixes[-1] + 1)
            else:
                name = "_0"
        else:
            # Used to expand repetition and optionality rules.
            n = len(name)
            suffixes = [ x[n:] for x in symbols if x.startswith(name) ]
            suffixes = [ x for x in suffixes if x == len(x) * "'" ]
            if suffixes:
                suffixes.sort()
                name = name + suffixes[-1] + "'"
            else:
                name = name + "'"

        symbols.add(name)
        return name


    def compile_grammar(self, context_class=None):
        self.context_class = context_class

        rules = self.rules
        symbols = self.symbols

        # The semantic side of things
        map = self.semantic_map
        if context_class is not None:
            for name in symbols:
                map[name] = False
                method_name = name.replace('-', '_').replace("'", '_')
                default = getattr(context_class, method_name, None)
                for i in range(len(rules[name])):
                    aux = '%s_%s' % (method_name, i + 1)
                    method = getattr(context_class, aux, default)
                    map[(name, i)] = method
                    if method is not None:
                        map[name] = True

        # Expand
        changed = True
        while changed:
            changed = False
            symbols = list(self.symbols)
            for name in symbols:
                action = map.get(name)
                # Expand rules of the form "A = *(...)"
                if not action and len(rules[name]) == 1:
                    rule = rules[name][0]
                    if len(rule) == 1:
                        element = rule[0]
                        if type(element) is tuple and element[0] is None:
                            changed = True
                            rest = element[1:]
                            rules[name] = [[], list(rest + (name,))]
                            continue
                # Other expansions
                for rule_index, rule in enumerate(rules[name]):
                    for element_index, element in enumerate(rule):
                        if not isinstance(element, tuple):
                            continue
                        changed = True
                        # New productions
                        max, rest = element[0], element[1:]
                        if max is None:
                            # Expand
                            aux = self.get_internal_rulename(name)
                            rule[element_index] = aux
                            # Case 1: max = infinitum
                            rules[aux] = [[], list(rest + (aux,))]
                        else:
                            # Case 2: max = n
                            if action:
                                # Expand
                                aux = self.get_internal_rulename(name)
                                rule[element_index] = aux
                                rules[aux] = []
                                for i in range(max+1):
                                    rules[aux].append(list(i * rest))
                            else:
                                left = tuple(rule[:element_index])
                                right = tuple(rule[element_index+1:])
                                for i in range(max+1):
                                    rules[name].append(
                                        list(left + (i * rest) + right))
                                rules[name][rule_index] = None
                rules[name] = [ x for x in rules[name] if x is not None ]

        # Optimize the grammar, reduce rules that are just a frozenset (and
        # not used by the semantic layer).
        changed = True
        while changed:
            changed = False
            # Merge rules of the kind: A = {tokens}
            for symbol in symbols:
                terminal_rules = []
                for i, rule in enumerate(rules[symbol]):
                    if len(rule) == 1 and isinstance(rule[0], frozenset):
                        terminal_rules.append(i)
                if len(terminal_rules) > 1:
                    terminal_rules.reverse()
                    aux = frozenset()
                    for i in terminal_rules:
                        aux |= rules[symbol][i][0]
                        del rules[symbol][i]
                    rules[symbol].append([aux])

            # Inline symbols that only have one rule of the form: A = {tokens}
            # and that are not used by the semantic layer.
            reducible = {}
            for symbol in symbols:
                if map.get(symbol):
                    continue
                if len(rules[symbol]) == 1:
                    rule = rules[symbol][0]
                    if len(rule) == 1 and isinstance(rule[0], frozenset):
                        reducible[symbol] = rule[0]
                        del rules[symbol]
                        changed = True
            self.symbols = set(rules.keys())
            symbols = self.symbols
            # Reduce
            for symbol in symbols:
                for rule in rules[symbol]:
                    for i, element in enumerate(rule):
                        if isinstance(element, str) and element in reducible:
                            rule[i] = reducible[element]


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


# Constants
# End Of Input
EOI = 0



def pformat_element(element):
    if isinstance(element, str):
        return element
    tokens = []
    for token in element:
        if token is EOI:
            tokens.append('$')
        else:
            tokens.append(str(token))
    return "{%s}" % ','.join(tokens)



class BaseContext(object):

    def __init__(self, data):
        self.data = data



class Grammar(object):

    def __init__(self):
        self.rules = {}
        self.symbols = set()
        self.is_compiled = False
        # The lexical analyser
        self.tokens = [EOI]
        self.lexical_table = None
        # The semantic layer
        self.semantic_map = {}


    #######################################################################
    # API Private
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


    def build_lexical_table(self):
        """Infere a lexical layer from the grammar.
        """
        rules = self.rules

        # Find out the set of terminals as defined in the grammar
        input_terminals = set()
        for symbol in rules:
            for rule in rules[symbol]:
                for element in rule:
                    if isinstance(element, frozenset):
                        input_terminals.add(element)
        input_terminals = list(input_terminals)

        # Compute the set of tokens, where a token is defined by a set of
        # characters that do not appear in any other token.
        tokens = []
        while input_terminals:
            t1 = input_terminals.pop()
            for i in range(len(input_terminals)):
                t2 = input_terminals[i]
                if t1 & t2:
                    del input_terminals[i]
                    input_terminals.append(t1 & t2)
                    if t1 - t2:
                        input_terminals.append(t1 - t2)
                    if t2 - t1:
                        input_terminals.append(t2 - t1)
                    break
            else:
                tokens.append(t1)

        # Build the lexical analyser, a table from character to token id, or
        # None if the character is not allowed in the grammar.
        lexical_table = 256 * [None]
        # Start at 1, the 0 is for End-Of-Input.
        token = 1
        for characters in tokens:
            self.tokens.append(token)
            for char in characters:
                lexical_table[ord(char)] = token
            token += 1
        self.lexical_table = lexical_table

        # Update the grammar, replace the sets-of-characters by sets-of-tokens
        symbols = rules.keys()
        for symbol in symbols:
            for rule in rules[symbol]:
                for j, element in enumerate(rule):
                    if isinstance(element, frozenset):
                        rule[j] = frozenset([
                            lexical_table[ord(char)] for char in element ])


    def pformat_rule(self, name, rule):
        line = [name, '=']
        if len(rule) == 0:
            line.append("ε")
        else:
            for element in rule:
                line.append(pformat_element(element))
        return ' '.join(line)


    #######################################################################
    # API Public
    #######################################################################
    def pprint_grammar(self):
        symbols = list(self.symbols)
        symbols.sort()
        for name in symbols:
            for rule in self.rules[name]:
                print self.pformat_rule(name, rule)


    def add_rule(self, name, *elements):
        """Add a new rule to the grammar, where a rule is defined by its
        name and a sequence of elements:

          rule-name -> element-1 element-2 ...

        Where 'element' may be:

        - a grammar symbol (non terminal)
        - a terminal, expressed as a set of allowed characters
        - a three-elements tuple, to express repetition and optionality,
          like "(min, max, element)"

        For example:

          ABNF         elements
          ===========  ==============
          4 hexdig     (4, hexdig)
          1*4 hexdig   (1, 4, hexdig)

        """
        self.symbols.add(name)
        rules = self.rules.setdefault(name, [])
        elements = list(elements)
        rules.append(elements)


    def compile_grammar(self, context_class=None):
        if self.is_compiled:
            return
        self.is_compiled = True

        rules = self.rules
        symbols = rules.keys()

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
            symbols = rules.keys()
            for name in symbols:
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
                            self.symbols.add(aux)
                            rule[element_index] = aux
                            # Case 1: max = infinitum
                            rules[aux] = [[], list(rest + (aux,))]
                        else:
                            # Case 2: max = n
                            if map.get(name):
                                # Expand
                                aux = self.get_internal_rulename(name)
                                self.symbols.add(aux)
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

        # Build the lexical table
        if self.lexical_table is None:
            self.build_lexical_table()

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


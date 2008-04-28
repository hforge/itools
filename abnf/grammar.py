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

"""This module defines the Grammar class, used to keep the description
of a context-free grammar.  And the function 'compile_grammar', which
splits a grammar description at the character level in two: a regular
and a context-free grammar.
"""


###########################################################################
# Base
###########################################################################
class Grammar(object):
    """A grammar is defined by a set of rules of the form:

      A = X1, ... Xn-1

    Where "A" is a non-terminal symbol, and "Xi" is either a terminal or a
    non-terminal.

    Internally a non-terminal is idenfied by a number, but we keep its name
    for debugging purposes.
    """

    def __init__(self):
        self.rules = {}


    def add_rule(self, name, *elements):
        elements = list(elements)
        self.rules.setdefault(name, []).append(elements)


    def get_rules(self):
        for name in self.rules:
            for rule in self.rules[name]:
                yield name, rule


#######################################################################
# Expand repetition rules (only used by the regular and context-free
# grammars).
def get_internal_rulename(rules, name):
    """Given a set of rulenames and a rulename within that set, return
    a new rulename this way:

      - If the name is P, return P' on the first call, P'' on the second
        call, and so on.
    """
    # Used to expand repetition and optionality rules.
    n = len(name)
    suffixes = [ x[n:] for x in rules if x[:n] == name ]
    suffixes = [ x for x in suffixes if x and x == len(x) * "'" ]
    if suffixes:
        suffixes.sort()
        return name + suffixes[-1] + "'"

    return name + "'"



def expand_re_grammar(grammar):
    """Expand repetition rules using these patterns:

      (1) P = (n, body) tail    =>  P = tail               (0)
                                    P = body tail          (1)
                                    ...
                                    P = body .. body tail  (n)

      (2) P = (*, body) tail    =>  P = tail               (0)
                                    P = body P             (*)

      (3) P = head (body) tail  =>  P = head P'
                                    P' = (..) tail
    """
    new_grammar = Grammar()
    names = set(grammar.rules.keys())
    rules = grammar.get_rules()
    rules = list(rules)

    while rules:
        name, rule = rules.pop()
        # Stop condition: no repetitions
        for i, element in enumerate(rule):
            if type(element) is tuple:
                break
        else:
            new_grammar.add_rule(name, *rule)
            continue

        # P = (x, body) tail
        if i == 0:
            first, tail = rule[0], rule[1:]
            max, body = first[0], first[1:]
            body = list(body)
            if max is None:
                # P = (*, body) tail
                rules.append((name, tail))
                rules.append((name, body + [name]))
            else:
                # P = (n, body) tail
                for i in range(0, max+1):
                    rules.append((name, body*i + tail))
            continue

        # P = head (..) tail
        head, body, tail = rule[:i], rule[i], rule[i+1:]
        aux = get_internal_rulename(names, name)
        names.add(aux)
        rules.append((name, head + [aux]))
        rules.append((aux, [body] + tail))

    return new_grammar



def expand_cf_grammar(grammar):
    """Replace repetition patterns by non-terminals.
    """
    changed = True
    while changed:
        changed = False
        rules = grammar.get_rules()
        rules = list(rules)
        for name, rule in rules:
            for element_index, element in enumerate(rule):
                if type(element) is not tuple:
                    continue
                changed = True
                # Insert new symbol
                max, rest = element[0], element[1:]
                aux = get_internal_rulename(grammar.rules, name)
                rule[element_index] = aux
                # Add the new rules
                if max is None:
                    # Case 1: max = infinitum
                    grammar.add_rule(aux, *(rest + (aux,)))
                    grammar.add_rule(aux)
                else:
                    # Case 2: max = n
                    for i in range(max+1):
                        grammar.add_rule(aux, *(i * rest))



###########################################################################
# Logic to derive a context-free and a regular grammar from the input
# (character) grammar.
###########################################################################
def repetition_is_regular(repetition):
    n = len(repetition)
    i = 1
    while i < n:
        element = repetition[i]
        element_type = type(element)
        if element_type is str:
            return False
        if element_type is tuple:
            if repetition_is_regular(element) is False:
                return False
        i += 1

    return True


def process_elements(elements, tokens):
    reg_expr = []
    new_elements = []

    for element in elements:
        # Check whether the next element is regular.
        element_type = type(element)
        if element_type is str:
            is_regular = False
        elif element_type is frozenset:
            is_regular = True
        elif element_type is tuple:
            is_regular = repetition_is_regular(element)
            if is_regular is False:
                element = (element[0],) + process_elements(element[1:], tokens)

        if is_regular:
            # Regular
            reg_expr.append(element)
        else:
            # Not-Regular
            if reg_expr:
                reg_expr = tuple(reg_expr)
                if reg_expr in tokens:
                    token = tokens[reg_expr]
                else:
                    token = '%s' % len(tokens)
                    tokens[reg_expr] = token
                new_elements.append(token)
                # Reset
                reg_expr = []
            new_elements.append(element)

    # Tail
    if reg_expr:
        reg_expr = tuple(reg_expr)
        if reg_expr in tokens:
            token = tokens[reg_expr]
        else:
            token = '%s' % len(tokens)
            tokens[reg_expr] = token
        # Build the new-elements
        new_elements.append(token)

    return tuple(new_elements)



def compile_grammar(ch_grammar):
    """Produce a regular and a context-free grammar.
    """
    tokens = {}

    # Build the context-free grammar
    cf_grammar = Grammar()
    for name, rule in ch_grammar.get_rules():
        cf_rule = process_elements(rule, tokens)
        cf_grammar.add_rule(name, *cf_rule)

    # Build the regular grammar
    re_grammar = Grammar()
    for reg_expr in tokens:
        token = tokens[reg_expr]
        re_grammar.add_rule(token, *reg_expr)

    # Expand both grammars
    re_grammar = expand_re_grammar(re_grammar)
    expand_cf_grammar(cf_grammar)

    # Return
    return re_grammar, cf_grammar


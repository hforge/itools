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

"""This module provides logic to visualize and debug the parsing tables
of both lexical and syntactical analysers.
"""

# Import from itools
from tokenizer import EOI
from ptable import SHIFT


###########################################################################
# Shared code
###########################################################################
def _format_chars(chars):
    chars = list(chars)
    chars.sort()
    if EOI in chars:
        chars.remove(EOI)
        chars.append('#')
    chars = ''.join(chars)
    chars = chars.replace('\n', '\\n')
    chars = chars.replace('\r', '\\r')
    chars = chars.replace('\t', '\\t')
    return chars


def _format_element(element):
    element_type = type(element)
    # Symbol (terminal or non-terminal)
    if element_type is str:
        return element

    # Repetition
    if element_type is tuple:
        max = element[0]
        rest = ' '.join([ _format_element(x) for x in element[1:] ])
        if max is None:
            return '*(%s)' % rest
        elif max == 1:
            return '[%s]' % rest
        return '*%s(%s)' % (max, rest)

    # Chars
    chars = _format_chars(element)
    return "{%s}" % chars


def _format_lex_item(grammar, item):
    token, name, i, j, look_ahead = item
    rule = grammar.rules[name][i]

    line = ['(%s) %s =' % (token, name)]
    for element in rule[:j]:
        line.append(_format_element(element))
    line.append('•')
    for element in rule[j:]:
        line.append(_format_element(element))

    # Look-ahead
    chars = _format_chars(look_ahead)
    line.append('[%s]' % chars)
    return ' '.join(line)



def _format_syn_item(grammar, item):
    name, i, j, look_ahead = item
    rule = grammar.rules[name][i]

    line = [name, '=']
    for element in rule[:j]:
        line.append(_format_element(element))
    line.append('•')
    for element in rule[j:]:
        line.append(_format_element(element))

    # Look-ahead
    if look_ahead[0] == EOI:
        line.append('[#]')
    else:
        chars = _format_chars(look_ahead[1])
        line.append('[%s {%s}]' % (look_ahead[0], chars))

    return ' '.join(line)



def _format_rule(name, rule):
    if len(rule) == 0:
        return '%s = ε' % name

    line = ['%s =' % name]
    for element in rule:
        line.append(_format_element(element))
    return ' '.join(line)



def _print_table(filename, grammar, parsing_table, state2is, format_item):
    lines = []
    lines.append('digraph G {\n')
    # The item sets
    for state in state2is:
        itemset = []
        for item in state2is[state]:
            item = format_item(grammar, item)
            item = item.replace('\\r', '\\\\r')
            item = item.replace('\\n', '\\\\n')
            item = item.replace('\\t', '\\\\t')
            item = item.replace('"', '\\"')
            itemset.append(item)
        itemset.sort()
        itemset = '\\l'.join(itemset)
        lines.append('    %s [label="S%s\\n%s\l",shape="box"];\n'
                     % (state, state, itemset))
    # Build the transitions
    transitions = {}
    for key in parsing_table:
        src, symbol = key
        action, dst = parsing_table[key]
        if action == SHIFT:
            transitions.setdefault((src, dst), set()).add(symbol)
    # Add the transitions to the dot file
    for key in transitions:
        src, dst = key
        label = [ x == -1 and '$' or str(x) for x in transitions[key] ]
        label = ','.join(label)
        lines.append('    %s -> %s [label="%s"];\n' % (src, dst, label))

    lines.append('}\n')

    # Write the file
    file = open('/tmp/%s.dot' % filename, 'w')
    file.write(''.join(lines))
    file.close()



###########################################################################
# Public API
###########################################################################
def print_grammar(grammar):
    names = grammar.rules.keys()
    names.sort()
    for name in names:
        for rule in grammar.rules[name]:
            print _format_rule(name, rule)


def print_lex_itemset(grammar, itemset):
    lines = [ _format_lex_item(grammar, x) for x in itemset ]
    lines.sort()
    for line in lines:
        print line


def print_syn_itemset(grammar, itemset):
    lines = [ _format_syn_item(grammar, x) for x in itemset ]
    lines.sort()
    for line in lines:
        print line


def print_lex_table(grammar, shift_table, state2is):
    _print_table('gr_lex', grammar, shift_table, state2is, _format_lex_item)


def print_syn_table(grammar, shift_table, state2is):
    _print_table('gr_syn', grammar, shift_table, state2is, _format_syn_item)



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
from grammar import pformat_element
from tokenizer import EOI


def expand_itemset(grammar, itemset):
    """Expand the given item-set.
    """
    rules = grammar.rules

    new_itemset = set()
    while itemset:
        item = itemset.pop()
        new_itemset.add(item)

        name, i, j, look_ahead = item
        rule = rules[name][i]

        n = len(rule)
        m = len(look_ahead)

        if j < n:
            # Within the rule
            element = rule[j]
            if type(element) is str:
                # Non Terminal.  Find out the look-ahead.
                look_ahead = tuple(rule[j+1:]) + look_ahead
                # Expand
                for i in range(len(rules[element])):
                    itemset.add((element, i, 0, look_ahead))
        elif j < n + m:
            # Within the look-ahead
            k = j - n
            element = look_ahead[k]
            if type(element) is str:
                left = look_ahead[:k]
                right = look_ahead[k+1:]
                # Expand
                for rule in rules[element]:
                    if element == 'c-wsp*' and len(rule) == 0:
                        print name, i, j, left + tuple(rule) + right
                        continue
                    itemset.add((name, i, j, left + tuple(rule) + right))

    return frozenset(new_itemset)



def move_token(grammar, itemset, token):
    """Return the item-set obtained by shifting the given terminal over the
    given item-set.
    """
    next_itemset = set()
    for item in itemset:
        name, i, j, look_ahead = item
        rule = grammar.rules[name][i]

        n = len(rule)
        m = len(look_ahead)

        if j < n:
            # Within the rule
            element = rule[j]
            if type(element) is frozenset and token in element:
                next_itemset.add((name, i, j+1, look_ahead))
        elif j < n + m:
            # Within the look-ahead
            element = look_ahead[j - n]
            if type(element) is frozenset and token in element:
                next_itemset.add((name, i, j+1, look_ahead))

#   if token == 1:
#       return frozenset(next_itemset)

    return expand_itemset(grammar, next_itemset)



def move_symbol(grammar, itemset, symbol):
    """Return the item-set obtained by shifting the given non-terminal over
    the given item-set.
    """
    next_itemset = set()
    for item in itemset:
        name, i, j, look_ahead = item
        rule = grammar.rules[name][i]

        n = len(rule)
        m = len(look_ahead)

        # Within the rule
        n = len(rule)
        if j < n:
            element = rule[j]
            if type(element) is str and symbol == element:
                next_itemset.add((name, i, j+1, look_ahead))
        elif j < n + m:
            # Within the look-ahead
            element = look_ahead[j - n]
            if type(element) is str and symbol == element:
                next_itemset.add((name, i, j+1, look_ahead))

    return expand_itemset(grammar, next_itemset)



def itemset_is_leaf(grammar, itemset):
    """Return True if the item-set is made up only of reduces, each with a
    distinct look-ahead.
    """
    # Check the itemset is made up of reduces only
    for name, i, j, look_ahead in itemset:
        rule = grammar.rules[name][i]
        if j < len(rule):
            return False
    # Check there is only one reduce
    if len(itemset) == 1:
        return True
    # Check if there are terminal reduces
    aux = set()
    for name, i, j, look_ahead in itemset:
        rule = grammar.rules[name][i]
        k = j - len(rule)
        if k < len(look_ahead):
            if look_ahead[k] in aux:
                return False
            aux.add(look_ahead[k])
        else:
            print 'WARNING: reduce/reduce conflict'

    return True


def get_nlr_table(grammar, start_symbol):
    """Buils and returns the NSLR(1) parsing table for the given grammar
    starting with the given start symbol.

    The NSLR(1) adds 1 symbol look-aheads to the LR(0) table; these symbols
    maybe terminals or non-teminals.
    """
    lr_table = {}
    states = {}
    rules = grammar.rules
    tokens = grammar.tokens
    symbols = rules.keys()

    # Build the initial item-set
    eoi_look_ahead = (EOI,)
    init_itemset = set()
    for i, rule in enumerate(rules[start_symbol]):
        init_itemset.add((start_symbol, i, 0, eoi_look_ahead))
    init_itemset = expand_itemset(grammar, init_itemset)
    states[init_itemset] = 1

    # Build the shift-tables
    stack = set([init_itemset])
    done = set()
    next_state = 2
    while stack:
        src_itemset = stack.pop()
        done.add(src_itemset)
        src_state = states[src_itemset]

        # Check the itemset really needs to be shifted
        if itemset_is_leaf(grammar, src_itemset):
            continue

        # Tokens
        for token in tokens:
            dst_itemset = move_token(grammar, src_itemset, token)
            if not dst_itemset:
                continue
            # Find out the destination state
            if dst_itemset in states:
                dst_state = states[dst_itemset]
            else:
                states[dst_itemset] = next_state
                dst_state = next_state
                next_state += 1
            if dst_itemset not in done:
                stack.add(dst_itemset)
            # Add transition
            lr_table[(src_state, token)] = dst_state
        # Symbols
        for symbol in symbols:
            dst_itemset = move_symbol(grammar, src_itemset, symbol)
            if not dst_itemset:
                continue
            # Find out the destination state
            if dst_itemset in states:
                dst_state = states[dst_itemset]
            else:
                states[dst_itemset] = next_state
                dst_state = next_state
                next_state += 1
            if dst_itemset not in done:
                stack.add(dst_itemset)
            # Add transition
            lr_table[(src_state, symbol)] = dst_state

    # Debug
    if start_symbol == 'rulelist':
        build_graph(grammar, lr_table, states)
    return lr_table, states



###########################################################################
# Debugging
###########################################################################
def pformat_item(grammar, item):
    name, i, j, look_ahead = item
    rule = grammar.rules[name][i]

    line = [name, '=']
    # The rule
    n = len(rule)
    for element in rule[:j]:
        line.append(pformat_element(element))
    if j <= n:
        line.append('•')
        for element in rule[j:]:
            line.append(pformat_element(element))
    # The look-ahead
    line.append(' : ')
    if j <= n:
        for element in look_ahead:
            line.append(pformat_element(element))
    else:
        k = j - n
        for element in look_ahead[:k]:
            line.append(pformat_element(element))
        line.append('•')
        for element in look_ahead[k:]:
            line.append(pformat_element(element))


    return ' '.join(line)



def pformat_item_set(grammar, item_set):
    lines = [ pformat_item(grammar, x) for x in item_set ]
    lines.sort()
    return lines



def build_graph(grammar, shift_table, states):
    lines = []
    lines.append('digraph G {\n')
    # The item sets
    for itemset in states:
        state = states[itemset]
        # Find out conflicts
#       reduce_reduce = False
#       reduce_look_aheads = set()
#       shift_look_aheads = set()
#       n_reduces = 0
#       for item in itemset:
#           name, i, j, look_ahead = item
#           rule = grammar.rules[name][i]
#           if j == len(rule):
#               n_reduces += 1
#               if reduce_look_aheads & look_ahead:
#                   reduce_reduce = True
#               reduce_look_aheads |= look_ahead
#           elif type(rule[j]) is str:
#               shift_look_aheads.add(rule[j])
#           else:
#               shift_look_aheads |= rule[j]
        color = None
#       if reduce_reduce:
#           # Reduce/Reduce
#           color = 'red'
#       elif n_reduces >= 1 and (reduce_look_aheads & shift_look_aheads):
#           # Shift/Reduce
#           color = 'red'

        itemset = pformat_item_set(grammar, itemset)
        itemset = '\\l'.join(itemset)
        if color is None:
            lines.append('    %s [label="S%s\\n%s\l",shape="box"];\n'
                         % (state, state, itemset))
        else:
            lines.append(
                '    %s [label="S%s\\n%s\l",shape="box",color="%s"];\n'
                % (state, state, itemset, color))
    # Build the transitions
    transitions = {}
    for key in shift_table:
        src, symbol = key
        dst = shift_table[key]
        transitions.setdefault((src, dst), set()).add(symbol)
    # Add the transitions to the dot file
    for key in transitions:
        src, dst = key
        label = [ x == 0 and '#' or str(x) for x in transitions[key] ]
        label = ','.join(label)
        lines.append('    %s -> %s [label="%s"];\n' % (src, dst, label))

    lines.append('}\n')

    # Write the file
    file = open('/tmp/graph.dot', 'w')
    file.write(''.join(lines))
    file.close()


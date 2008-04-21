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


# Epsilon (the empty alternative)
EPSILON = None
EPSILON_SET = frozenset([EPSILON])


def get_first_table(grammar):
    symbols = grammar.symbols
    rules = grammar.rules
    lexical_table = grammar.tokenizer.lexical_table

    first = {}
    # Initialize
    for symbol in symbols:
        first[symbol] = frozenset([symbol])
        for rule in rules[symbol]:
            for i in range(len(rule)):
                alternative = tuple(rule[i:])
                element = rule[i]
                if isinstance(element, frozenset):
                    first[element] = element
                    first[alternative] = element
                else:
                    first[alternative] = frozenset()
    first[()] = EPSILON_SET
    # Closure
    changed = True
    while changed:
        changed = False
        for symbol in symbols:
            for rule in rules[symbol]:
                # Inference rule 1: for each rule "N -> x", "first[N]" must
                # contain "first[x]"
                alternative = tuple(rule)
                if not first[alternative].issubset(first[symbol]):
                    first[symbol] |= first[alternative]
                    changed = True
                # Inference rules 2 and 3
                for i in range(len(rule)):
                    # Inference rule 2: for each alternative "Ax", "first[Ax]"
                    # must contain "first[A]" (excluding epsilon).
                    alternative = tuple(rule[i:])
                    aux = first[alternative[0]] - EPSILON_SET
                    if not aux.issubset(first[alternative]):
                        first[alternative] |= aux
                        changed = True
                    # Inference rule 3: for each alternative "Ax" where
                    # "first[A]" contains epsilon, "first[Ax]" must contain
                    # "first[x]"
                    if EPSILON in first[alternative[0]]:
                        aux = first[alternative[1:]]
                        if not aux.issubset(first[alternative]):
                            first[alternative] |= aux
                            changed = True

    return first



def expand_itemset(grammar, itemset, first):
    """Expand the given item-set.
    """
    rules = grammar.rules

    new_itemset = set()
    while itemset:
        item = itemset.pop()
        new_itemset.add(item)

        name, i, j, look_ahead = item
        rule = rules[name][i]

        # Nothing to expand (reduce rule or terminal)
        if j == len(rule) or type(rule[j]) is not str:
            continue

        # Non Terminal.  Find out the look-ahead.
        tail = tuple(rule[j+1:])
        tail_first = first[tail]
        if EPSILON in tail_first:
            look_ahead = (tail_first - EPSILON_SET) | look_ahead
        else:
            look_ahead = tail_first
        # Expand
        name = rule[j]
        for i in range(len(rules[name])):
            itemset.add((name, i, 0, look_ahead))

    return frozenset(new_itemset)



def move_token(grammar, itemset, token, first):
    """Return the item-set obtained by shifting the given terminal over the
    given item-set.
    """
    next_itemset = set()
    for item in itemset:
        name, i, j, look_ahead = item
        rule = grammar.rules[name][i]
        # End of rule
        if j == len(rule):
            continue
        # Shift
        element = rule[j]
        if type(element) is frozenset and token in element:
            next_itemset.add((name, i, j+1, look_ahead))

    return expand_itemset(grammar, next_itemset, first)



def move_symbol(grammar, itemset, symbol, first):
    """Return the item-set obtained by shifting the given non-terminal over
    the given item-set.
    """
    next_itemset = set()
    for item in itemset:
        name, i, j, look_ahead = item
        rule = grammar.rules[name][i]
        # End of rule
        if j == len(rule):
            continue
        # Shift
        element = rule[j]
        if type(element) is str and symbol == element:
            next_itemset.add((name, i, j+1, look_ahead))

    return expand_itemset(grammar, next_itemset, first)



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

    # The "first" set
    first = get_first_table(grammar)

    # Build the initial item-set
    eoi_look_ahead = frozenset([EOI])
    init_itemset = set()
    for i, rule in enumerate(rules[start_symbol]):
        init_itemset.add((start_symbol, i, 0, eoi_look_ahead))
    init_itemset = expand_itemset(grammar, init_itemset, first)
    states[init_itemset] = 1

    # Build the shift-tables
    stack = set([init_itemset])
    done = set()
    next_state = 2
    while stack:
        src_itemset = stack.pop()
        done.add(src_itemset)
        src_state = states[src_itemset]
        # Tokens
        for token in tokens:
            dst_itemset = move_token(grammar, src_itemset, token, first)
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
            dst_itemset = move_symbol(grammar, src_itemset, symbol, first)
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
    for element in rule[:j]:
        line.append(pformat_element(element))
    line.append('•')
    for element in rule[j:]:
        line.append(pformat_element(element))

    if look_ahead is not None:
        look_ahead = list(look_ahead)
        look_ahead.sort()
        look_ahead = [ (x == 0 and '#') or str(x) for x in look_ahead ]
        line.append('[%s]' % ','.join(look_ahead))
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
        reduce_reduce = False
        reduce_look_aheads = set()
        shift_look_aheads = set()
        n_reduces = 0
        for item in itemset:
            name, i, j, look_ahead = item
            rule = grammar.rules[name][i]
            if j == len(rule):
                n_reduces += 1
                if reduce_look_aheads & look_ahead:
                    reduce_reduce = True
                reduce_look_aheads |= look_ahead
            elif type(rule[j]) is str:
                shift_look_aheads.add(rule[j])
            else:
                shift_look_aheads |= rule[j]
        color = None
        if reduce_reduce:
            # Reduce/Reduce
            color = 'red'
        elif n_reduces >= 1 and (reduce_look_aheads & shift_look_aheads):
            # Shift/Reduce
            color = 'red'

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


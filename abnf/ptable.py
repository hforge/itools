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
from tokenizer import (Tokenizer, EOI, get_token_first_chars, EPSILON,
    EPSILON_SET)


###########################################################################
# Build the Parse Table
###########################################################################

class BaseContext(object):

    def __init__(self, data):
        self.data = data



# Actions
SHIFT = 0
REDUCE = 1



def get_itemset_core(itemset):
    """Returns the core of a LR(1) item set (i.e. the LR(0) item set).
    """
    core = [ (name, i, j) for name, i, j, look_ahead in itemset ]
    return frozenset(core)



def get_first_chars(cf_grammar, re_grammar, tail):
    """For a given sequence of symbols (including end-of-input), return
    the set of characters first expected.
    """
    chars = set()
    stack = set([tail])
    while stack:
        tail = stack.pop()
        if tail[0] == EOI:
            chars.add(EOI)
        elif type(tail[0]) is frozenset:
            chars.update(tail[0])
        elif tail[0].isdigit():
            first = get_token_first_chars(re_grammar, tail[0])
            chars |= (first - EPSILON_SET)
            if EPSILON in first:
                if len(tail) == 1:
                    error = ('the algorithm is not powerful enough to derive'
                             ' the lexical analyser')
                    raise NotImplementedError, error
                stack.add(tail[1:])
        else:
            for rule in cf_grammar.rules[tail[0]]:
                stack.add(tuple(rule) + tail[1:])

    return frozenset(chars)



def expand_itemset(cf_grammar, re_grammar, itemset):
    new_itemset = set()
    while itemset:
        item = itemset.pop()
        new_itemset.add(item)

        name, i, j, look_ahead = item
        rule = cf_grammar.rules[name][i]
        # Reduce item
        if j == len(rule):
            continue
        # Terminal
        name = rule[j]
        if name.isdigit():
            continue
        # Non Terminal
        # Find out the look-ahead set
        start = tuple(rule[j+1:]) + look_ahead
        look_aheads = set()
        stack = set([start])
        while stack:
            aux = stack.pop()
            if aux[0] == EOI:
                look_aheads.add((EOI, None))
            elif aux[0].isdigit():
                first_chars = get_first_chars(cf_grammar, re_grammar, aux[1:])
                look_aheads.add((aux[0], first_chars))
            else:
                for rule in cf_grammar.rules[aux[0]]:
                    stack.add(tuple(rule) + aux[1:])

        # Expand
        for i in range(len(cf_grammar.rules[name])):
            for look_ahead in look_aheads:
                new_item = (name, i, 0, look_ahead)
                if new_item not in new_itemset:
                    itemset.add(new_item)

    return frozenset(new_itemset)


def move_symbol(cf_grammar, re_grammar, itemset, symbol):
    """In the context of this method, by a symbol we understand both
    non-terminals and terminals (including the End-Of-Input).
    """
    next_itemset = set()
    for item in itemset:
        name, i, j, look_ahead = item
        rule = cf_grammar.rules[name][i]
        # Move
        if j == len(rule):
            continue
        element = rule[j]
        # Non terminal
        if type(symbol) is str:
            if symbol == element:
                next_itemset.add((name, i, j+1, look_ahead))
            continue
        # Terminal
        if type(element) is str:
            continue
        if symbol in element:
            next_itemset.add((name, i, j+1, look_ahead))

    return expand_itemset(cf_grammar, re_grammar, next_itemset)



def get_ptables(cf_grammar, re_grammar, start_symbol, context_class=None):
    """Build the parsing tables.
    """
    # Initialize
    parsing_table = {}

    # Build the initial set (s0)
    look_ahead = (EOI, None)
    s0 = set()
    for i in range(len(cf_grammar.rules[start_symbol])):
        s0.add((start_symbol, i, 0, look_ahead))
    s0 = expand_itemset(cf_grammar, re_grammar, s0)

    # Build the shift-table
    state2is = {0: frozenset(), 1: s0}
    s0_core = get_itemset_core(s0)
    is2state = {s0_core: 1}
    stack = set([s0])
    done = set()
    next_state = 2
    while stack:
        src_itemset = stack.pop()
        done.add(src_itemset)
        core = get_itemset_core(src_itemset)
        src_state = is2state[core]
        # Reduce table
        state2is[src_state] |= src_itemset
        # Find out the symbols to shift
        symbols = set()
        for name, i, j, look_ahead in src_itemset:
            rule = cf_grammar.rules[name][i]
            if j < len(rule):
                symbols.add(rule[j])
        # Shift
        for symbol in symbols:
            dst_itemset = move_symbol(cf_grammar, re_grammar, src_itemset,
                                      symbol)
            # Find out the destination state
            core = get_itemset_core(dst_itemset)
            if core in is2state:
                dst_state = is2state[core]
            else:
                dst_state = next_state
                is2state[core] = dst_state
                state2is[dst_state] = dst_itemset
                next_state += 1
            if dst_itemset not in done:
                stack.add(dst_itemset)
            # Add transition
            parsing_table[(src_state, symbol)] = (SHIFT, dst_state)

    # Find out the semantic actions
    map = {}
    if context_class is not None:
        for name in cf_grammar.rules:
            method_name = name.replace('-', '_').replace("'", '_')
            default = getattr(context_class, method_name, None)
            for i in range(len(cf_grammar.rules[name])):
                aux = '%s_%s' % (method_name, i + 1)
                method = getattr(context_class, aux, default)
                map[(name, i)] = method

    # XXX Debug
    from debug import print_syn_table
    print_syn_table(cf_grammar, parsing_table, state2is)

    # Build the action table
    tokenizer = Tokenizer(re_grammar)
    for state in state2is:
        if state == 0:
            continue
        itemset = state2is[state]
        # Find handles, where a handle is a 4 elements tuple:
        #
        #  rulename, stack-elements-to-pop, look-ahead, semantic-method
        #
        tokens = {}
        for name, i, j, look_ahead in itemset:
            rule = cf_grammar.rules[name][i]
            n = len(rule)
            if j == n:
                key = (state, look_ahead[0])
                method = map.get((name, i))
                action = REDUCE, (name, n, method)
                if key in parsing_table:
                    if parsing_table[key] != action:
                        raise ValueError, 'conflict on state %s' % state
                else:
                    parsing_table[key] = action
                # For the tokenizer
                aux = tokens.setdefault(look_ahead[0], set())
                if look_ahead[0] != EOI:
                    aux.update(look_ahead[1])
            elif rule[j].isdigit():
                token = rule[j]
                # For the tokenizer
                tail = tuple(rule[j+1:]) + look_ahead
                first_chars = get_first_chars(cf_grammar, re_grammar, tail)
                tokens.setdefault(token, set()).update(first_chars)
        # The tokenizer
        for token in tokens:
            tokens[token] = frozenset(tokens[token])
        tokenizer.set_state(state, tokens)

    # Update grammar
    return parsing_table, tokenizer, state2is


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


# End of Input
EOI = -1

# Epsilon (the empty alternative)
EPSILON = None
EPSILON_SET = frozenset([EPSILON])

# Actions
ACCEPT = 0
SHIFT = 1



class Tokenizer(object):

    def __init__(self, grammar):
        self.grammar = grammar
        self.tables = {}


    def set_state(self, state, tokens):
        shift_table, action_table, state2is = get_ltables(self.grammar, tokens)
        self.tables[state] = shift_table, action_table


    def get_token(self, data):
        tables = self.tables
        data_len = len(data)
        data_idx = 0
        token_start = 0
        # Init State is always 1
        parser_state = 1

        while data_idx < data_len:
            shift_table, action_table = tables[parser_state]
            # Find out and return the next token
            state = 0
            while True:
                if data_idx == data_len:
                    char = EOI
                else:
                    char = data[data_idx]
                key = (state, char)
                if key not in action_table:
                    msg = 'lexical error, unexpected character %s at byte %s'
                    raise ValueError, msg % (repr(char), data_idx)
                action, value = action_table[(state, char)]
                # Accept
                if action == ACCEPT:
                    parser_state = (yield value, token_start)
                    token_start = data_idx
                    break
                # Shift
                state = shift_table[key]
                data_idx += 1

        # End Of Input
        yield EOI, data_idx



def get_token_first_chars(grammar, token):
    """For the given token, return the first set of first chars, including
    Epsilon if the token may be of zero length.
    """
    # Initialize the stack
    stack = set()
    for rule in grammar.rules[token]:
        stack.add(tuple(rule))

    # Calculate first
    first = set()
    while stack:
        rule = stack.pop()
        if len(rule) == 0:
            first.add(EPSILON)
        elif type(rule[0]) is frozenset:
            first.update(rule[0])
        else:
            for aux in grammar.rules[rule[0]]:
                if aux and aux[0] == rule[0]:
                    raise NotImplementedError, 'cannot handle left recursion'
                stack.add(tuple(aux) + rule[1:])

    return first



def expand_itemset(grammar, itemset):
    new_itemset = set()

    while itemset:
        item = itemset.pop()
        token, name, i, j, look_ahead = item
        rule = grammar.rules[name][i]

        if j == len(rule):
            # Reduce item
            new_itemset.add(item)
        elif type(rule[j]) is frozenset:
            # Char
            new_itemset.add(item)
        else:
            # Expand
            name = rule[j]
            for i in range(len(grammar.rules[name])):
                new_itemset.add((token, name, i, 0, look_ahead))

    return frozenset(new_itemset)


def update_action_table(grammar, action_table, state, itemset):
    for token, name, i, j, look_ahead in itemset:
        if token == EOI:
            continue
        rule = grammar.rules[name][i]
        # Reduce or shit
        if j == len(rule):
            value = (ACCEPT, token)
            chars = look_ahead
        else:
            value = (SHIFT, None)
            chars = rule[j]
        # Update table
        for chr in chars:
            key = (state, chr)
            if key in action_table:
                if action_table[key] != value:
                    raise ValueError, 'table conflict'
            else:
                action_table[key] = value



def move_char(grammar, itemset, char):
    next_itemset = set()
    for token, name, i, j, look_ahead in itemset:
        rule = grammar.rules[name][i]
        if j < len(rule) and char in rule[j]:
            next_itemset.add((token, name, i, j+1, look_ahead))

    return expand_itemset(grammar, next_itemset)



def get_ltables(grammar, start_symbols):
    shift_table = {}
    action_table = {}

    # Do not need to consider the End-Of-Input token, it is done automatically
    # by the run-time.
    if EOI in start_symbols:
        del start_symbols[EOI]

    # Build the initial set (s0)
    s0 = set()
    for symbol in start_symbols:
        look_ahead = start_symbols[symbol]
        for i in range(len(grammar.rules[symbol])):
            s0.add((symbol, symbol, i, 0, look_ahead))
    s0 = expand_itemset(grammar, s0)
    update_action_table(grammar, action_table, 0, s0)

    # Build the shift-table
    state2is = {0: s0}
    is2state = {s0: 0}
    stack = set([s0])
    done = set()
    next_state = 1
    while stack:
        src_itemset = stack.pop()
        done.add(src_itemset)
        src_state = is2state[src_itemset]
        # Find out the chars to shift
        chars = set()
        for token, name, i, j, look_ahead in src_itemset:
            rule = grammar.rules[name][i]
            if j < len(rule) and type(rule[j]) is frozenset:
                chars.update(rule[j])
        # Shift
        for char in chars:
            dst_itemset = move_char(grammar, src_itemset, char)
            # Find out the destination state
            if dst_itemset in is2state:
                dst_state = is2state[dst_itemset]
            else:
                dst_state = next_state
                is2state[dst_itemset] = dst_state
                state2is[dst_state] = dst_itemset
                update_action_table(grammar, action_table, dst_state,
                                    dst_itemset)
                next_state += 1
            if dst_itemset not in done:
                stack.add(dst_itemset)
            # Add transition
            shift_table[(src_state, char)] = dst_state

    return shift_table, action_table, state2is


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
from collections import deque
import sys

# Import from itools
from nlr import get_nlr_table
from tokenizer import EOI


# Don't debug by default
debug = True



class Parser(object):

    def __init__(self, grammar, start_symbol, shift_table, reduce_table):
        self.grammar = grammar
        self.start_symbol = start_symbol
        self.shift_table = shift_table
        self.reduce_table = reduce_table


    def run(self, data, context=None):
        tokenizer = self.grammar.tokenizer
        start_symbol = self.start_symbol
        shift_table = self.shift_table
        reduce_table = self.reduce_table

        # Initialize the stack, where the stack is a list of tuples:
        #
        #   [...
        #    ([last_nodes], symbol, state, start, value),
        #    ...]
        #
        # The "start" field is a reference to the input stream.
        stack = deque()
        stack.append(([], None, 1, 0, None))
        active_nodes = deque()
        active_nodes.append(0)

        # Debug
#        debug = (start_symbol == 'rulelist')
#        debug = (start_symbol == 'IPv4address')
        if debug:
#            trace = open('/tmp/trace.txt', 'w')
            trace = sys.stdout

        get_token = tokenizer.get_token(data).next
        token, data_idx = get_token()

        while token != EOI:
            # Debug
            if debug:
                trace.write('=== shift %s: %s (%s) ===\n'
                            % (token, data_idx, repr(data[data_idx])))

            # Shift on all the parsing paths
            map = {}
            new_active_nodes = deque()
            for node_idx in active_nodes:
                state = stack[node_idx][2]
                next_state = shift_table.get((state, token), 0)
                if next_state == 0:
                    continue
                if next_state in map:
                    n = map[next_state]
                    stack[n][0].append(node_idx)
                else:
                    n = len(stack)
                    map[next_state] = n
                    new_active_nodes.append(n)
                    stack.append(
                        ([node_idx], token, next_state, data_idx+1, None))
            active_nodes = new_active_nodes

            # Debug
            if debug:
                pprint_stack(stack, active_nodes, data, trace)
                trace.write('=== reduce ===\n')

            # Next token
            token, data_idx = get_token()

            # Reduce
            new_active_nodes = deque()
            while active_nodes:
                node_idx = active_nodes.pop()
                kk, kk, state, kk, kk = stack[node_idx]
                shift, handles = reduce_table[state]
                # Shift
                if shift:
                    new_active_nodes.append(node_idx)
                # Reduce
                for name, n, look_ahead, method in handles:
                    # Look-Ahead
                    if token not in look_ahead:
                        continue
                    # Fork the stack
                    pointers = [[node_idx, []]]
                    while n > 0:
                        n -= 1
                        new_pointers = []
                        while pointers:
                            node_idx, values = pointers.pop()
                            last_nodes, symbol, kk, kk, value = stack[node_idx]
                            if type(symbol) is str:
                                values.insert(0, value)
                            for last_node in last_nodes:
                                new_pointers.append([last_node, values[:]])
                        pointers = new_pointers

                    for last_node, values in pointers:
                        kk, symbol, state, start, value = stack[last_node]
                        # Semantic action
                        if context is None:
                            value = None
                        elif method is None:
                            aux = [ x for x in values if x is not None ]
                            if len(aux) == 0:
                                value = None
                            else:
                                value = values
                        else:
                            value = method(context, start, data_idx, *values)
                        # Next state
                        next_state = shift_table.get((state, name), 0)
                        # Stop Condition
                        if last_node==0 and name == start_symbol and token==0:
                            return value
                        active_nodes.append(len(stack))
                        stack.append(
                            ([last_node], name, next_state, data_idx, value))
            active_nodes = new_active_nodes
            # Debug
            if debug:
                pprint_stack(stack, active_nodes, data, trace)
                trace.write('\n')

        raise ValueError, 'grammar error'


    def is_valid(self, data):
        try:
            self.run(data)
        except ValueError:
            return False

        return True



###########################################################################
# Build the Parse Table
###########################################################################

def find_handles(grammar, item_set):
    rules = grammar.rules

    handles = set()
    shift = False
    new_item_set = set()
    for name, i, j, look_ahead in item_set:
        if j == len(rules[name][i]):
            handles.add((name, i, look_ahead))
        else:
            shift = True

    return shift, tuple(handles)



def get_parser(grammar, start_symbol):
    """Build the parsing tables.
    """
#    debug = (start_symbol == 'rulelist')

    rules = grammar.rules
    map = grammar.semantic_map

    # Get the shift table
    lr_table, states = get_nlr_table(grammar, start_symbol)

    # Build the action table
    reduce_table = [None] * (len(states) + 1)
    reduce_table[0] = frozenset()
    for itemset in states:
        state = states[itemset]
        shift, handles = find_handles(grammar, itemset)
        # A handle is a 4 elements tuple:
        #
        #  rulename, stack-elements-to-pop, look-ahead, semantic-method
        #
        handles = [
            (name, len(rules[name][i]), look_ahead, map.get((name, i)))
            for name, i, look_ahead in handles ]
        reduce_table[state] = (shift, handles)
    reduce_table = tuple(reduce_table)

    # Update grammar
    return Parser(grammar, start_symbol, lr_table, reduce_table)


###########################################################################
# Debug Code
###########################################################################
def pprint_stack(stack, active_nodes, data, file=None):
    if file is None:
        file = sys.stdout

    in_paths = []
    for node_idx in active_nodes:
        in_paths.append([node_idx])

    paths = []
    while in_paths:
        path = in_paths.pop()
        node_idx = path[0]
        last_nodes = stack[node_idx][0]
        if len(last_nodes) == 0:
            paths.append(path)
            continue
        for last_node in last_nodes:
            in_paths.append([last_node] + path)

    lines = []
    for path in paths:
        line = []
        for node_idx in path:
            kk, symbol, state, start, value = stack[node_idx]
            if state == 1:
                line.append('S1')
            elif symbol == 0:
                line.append('# S%s' % state)
            elif value is None:
                line.append('%s S%s' % (symbol, state))
            else:
                line.append('%s(%s) S%s' % (symbol, value, state))
        line = ' '.join(line)
        file.write('%s\n' % line)


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
from ptable import REDUCE
from tokenizer import EOI


# Don't debug by default
debug = False



class Parser(object):

    def __init__(self, start_symbol, parsing_table, tokenizer):
        self.start_symbol = start_symbol
        self.parsing_table = parsing_table
        self.tokenizer = tokenizer


    def run(self, data, context=None):
        start_symbol = self.start_symbol
        parsing_table = self.parsing_table
        tokenizer = self.tokenizer

        # Initialize the stack, where the stack is a list of tuples:
        #
        #   [...
        #    (symbol, state, start, value),
        #    ...]
        #
        # The "start" field is a reference to the input stream.
        stack = deque()
        stack.append((None, 1, 0, None))

        # Debug
#        debug = (start_symbol == 'rulelist')
#        debug = (start_symbol == 'IPv4address')
        if debug:
#            trace = open('/tmp/trace.txt', 'w')
            trace = sys.stdout

        get_token = tokenizer.get_token(data)
        token, data_idx = get_token.next()
        get_token = get_token.send

        while token != EOI:
            # Shift
            state = stack[-1][1]
            action, next_state = parsing_table[(state, token)]
            stack.append((token, next_state, data_idx, None))

            # Next token
            token, data_idx = get_token(next_state)

            # Reduce
            action, value = parsing_table[(next_state, token)]
            while action is REDUCE:
                name, n, method = value
                # Pop
                values = []
                while n > 0:
                    symbol, kk, kk, value = stack.pop()
                    if not symbol.isdigit():
                        values.insert(0, value)
                    n -= 1
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
                    start = stack[-1][2]
                    value = method(context, start, data_idx, *values)
                # Check for the accept condition
                state = stack[-1][1]
                if state == 1 and name == start_symbol and token == EOI:
                    return value
                # Push
                action, next_state = parsing_table[(state, name)]
                stack.append((name, next_state, data_idx, value))
                # Next
                action, value = parsing_table[(next_state, token)]

            # Check for error
            if action is None:
                raise ValueError, 'grammar error'

        raise ValueError, 'grammar error'


    def is_valid(self, data):
        try:
            self.run(data)
        except ValueError:
            return False

        return True


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
            elif symbol == -1:
                line.append('$ S%s' % state)
            elif value is None:
                line.append('%s S%s' % (symbol, state))
            else:
                line.append('%s(%s) S%s' % (symbol, value, state))
        line = ' '.join(line)
        file.write('%s\n' % line)


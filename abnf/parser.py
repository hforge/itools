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
from grammar import pformat_element, EOI


# Don't debug by default
debug = False



class Parser(object):

    def __init__(self, grammar, start_symbol, token_table, symbol_table,
                 reduce_table):
        self.grammar = grammar
        self.start_symbol = start_symbol
        self.token_table = token_table
        self.symbol_table = symbol_table 
        self.reduce_table = reduce_table


    def run(self, data, context=None):
        tokenizer = self.grammar.tokenizer
        start_symbol = self.start_symbol
        token_table = self.token_table
        symbol_table = self.symbol_table
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
                next_state = token_table.get((state, token), 0)
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
                        next_state = symbol_table.get((state, name), 0)
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

# Epsilon (the empty alternative)
EPSILON = None
EPSILON_SET = frozenset([EPSILON])



def get_item_set_core(item_set):
    """Returns the core of a LR(1) item set (i.e. the LR(0) item set).
    """
    core = [ (name, i, j) for name, i, j, look_ahead in item_set ]
    return frozenset(core)



def merge_item_sets(a, b):
    """Given two LR(1) item sets merge their look-aheads to return an LALR(1)
    item set.
    """
    c = set()
    for name, i, j, a_look_ahead in a:
        for b_name, b_i, b_j, b_look_ahead in b:
            if b_name == name and b_i == i and b_j == j:
                look_ahead = frozenset(a_look_ahead | b_look_ahead)
                c.add((name, i, j, look_ahead))
                break
    return frozenset(c)



def is_item_in_item_set(item_set, item):
    name, i, j, look_ahead = item
    for b_item in item_set:
        b_name, b_i, b_j, b_look_ahead = b_item
        if b_name == name and b_i == i and b_j == j:
            if look_ahead.issubset(b_look_ahead):
                return True
    return False



def add_item_to_item_set(item_set, item):
    """Insert the given item into the given item-set, where an item is
    identified by the tuple (name, i, j), the look-ahead is merged.
    """
    name, i, j, look_ahead = item
    for b_item in item_set:
        b_name, b_i, b_j, b_look_ahead = b_item
        if b_name == name and b_i == i and b_j == j:
            item_set.remove(b_item)
            item_set.add((name, i, j, look_ahead | b_look_ahead))
            return
    item_set.add(item)



def get_first_table(grammar):
    symbols = grammar.symbols
    rules = grammar.rules
    lexical_table = grammar.tokenizer.lexical_table

    first = {}
    # Initialize
    for symbol in symbols:
        first[symbol] = frozenset()
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



def expand_itemset(grammar, item_set, first_table):
    rules = grammar.rules

    new_item_set = set()
    while item_set:
        item = item_set.pop()
        add_item_to_item_set(new_item_set, item)

        name, i, j, look_ahead = item
        rule = rules[name][i]
        # Reduce item
        if j == len(rule):
            continue
        # Terminal
        name = rule[j]
        if not isinstance(name, str):
            continue
        # Non Terminal
        # Find out the look-ahead set
        tail = tuple(rule[j+1:])
        if len(tail) > 0:
            first = first_table[tail]
            if EPSILON in first:
                look_ahead = look_ahead | (first - EPSILON_SET)
            else:
                look_ahead = first
        # Expand
        for i in range(len(rules[name])):
            new_item = (name, i, 0, look_ahead)
            if not is_item_in_item_set(new_item_set, new_item):
                add_item_to_item_set(item_set, new_item)

    return frozenset(new_item_set)


def move_symbol(grammar, item_set, symbol, first_table):
    """In the context of this method, by a symbol we understand both
    non-terminals and terminals (including the End-Of-Input).
    """
    rules = grammar.rules

    next_item_set = set()
    for item in item_set:
        name, i, j, look_ahead = item
        rule = rules[name][i]
        # Move
        if j == len(rule):
            continue
        element = rule[j]
        # Non terminal
        if isinstance(symbol, str):
            if symbol == element:
                next_item_set.add((name, i, j+1, look_ahead))
            continue
        # Terminal
        if isinstance(element, str):
            continue
        if symbol in element:
            next_item_set.add((name, i, j+1, look_ahead))

    return expand_itemset(grammar, next_item_set, first_table)



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

    tokens = grammar.tokens
    rules = grammar.rules
    map = grammar.semantic_map
    symbols = rules.keys()

    # First table
    first = get_first_table(grammar)

    # Build the initial set (s0)
    s0 = set()
    for i in range(len(rules[start_symbol])):
        s0.add((start_symbol, i, 0, frozenset([EOI])))
    s0 = expand_itemset(grammar, s0, first)
    # Initialize
    token_table = {}
    symbol_table = {}
    # Build the shift-tables
    reduce_table = {1: s0}
    s0_core = get_item_set_core(s0)
    states = {s0_core: 1}
    stack = set([s0])
    done = set()
    next_state = 2
    while stack:
        src_item_set = stack.pop()
        done.add(src_item_set)
        core = get_item_set_core(src_item_set)
        src_state = states[core]
        # Reduce table
        a = reduce_table[src_state]
        reduce_table[src_state] = merge_item_sets(a, src_item_set)
        # Chars
        for token in tokens:
            dst_item_set = move_symbol(grammar, src_item_set, token, first)
            if not dst_item_set:
                continue
            # Find out the destination state
            core = get_item_set_core(dst_item_set)
            if core in states:
                dst_state = states[core]
            else:
                states[core] = next_state
                dst_state = next_state
                next_state += 1
                reduce_table[dst_state] = dst_item_set
            if dst_item_set not in done:
                stack.add(dst_item_set)
            # Add transition
            token_table[(src_state, token)] = dst_state
        # Symbols
        for symbol in symbols:
            dst_item_set = move_symbol(grammar, src_item_set, symbol, first)
            if not dst_item_set:
                continue
            # Find out the destination state
            core = get_item_set_core(dst_item_set)
            if core in states:
                dst_state = states[core]
            else:
                states[core] = next_state
                dst_state = next_state
                next_state += 1
                reduce_table[dst_state] = dst_item_set
            if dst_item_set not in done:
                stack.add(dst_item_set)
            # Add transition
            symbol_table[(src_state, symbol)] = dst_state

    # Debug
    if debug:
        build_graph(grammar, reduce_table, token_table, symbol_table)

    # Finish the reduce-table
    reduce_table[0] = frozenset()
    # Find handles, calculate rule length and change to a tuple
    aux = []
    for state in reduce_table:
        item_set = reduce_table[state]
        shift, handles = find_handles(grammar, item_set)
        # A handle is a 4 elements tuple:
        #
        #  rulename, stack-elements-to-pop, look-ahead, semantic-method
        #
        handles = [ (x, len(rules[x][y]), z, map.get((x, y)))
                    for x, y, z in handles ]
        aux.append((state, (shift, handles)))
    aux.sort()
    aux = [ y for x, y in aux ]
    reduce_table = tuple(aux)

    # Update grammar
    return Parser(grammar, start_symbol, token_table, symbol_table,
                  reduce_table)


###########################################################################
# Debug Code
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

    look_ahead = list(look_ahead)
    look_ahead.sort()
    look_ahead = [ (x == 0 and '$') or str(x) for x in look_ahead ]
    line.append('{%s}' % ','.join(look_ahead))
    return ' '.join(line)


def pformat_item_set(grammar, item_set):
    lines = [ pformat_item(grammar, x) for x in item_set ]
    lines.sort()
    return lines


def build_graph(grammar, map, token_table, symbol_table):
    lines = []
    lines.append('digraph G {\n')
    # The item sets
    for state in map:
        item_set = map[state]
        item_set = pformat_item_set(grammar, item_set)
        item_set = '\\l'.join(item_set)
        lines.append('    %s [label="S%s\\n%s\l",shape="box"];\n'
                     % (state, state, item_set))
    # Build the transitions
    transitions = {}
    for key in token_table:
        src, token = key
        dst = token_table[key]
        transitions.setdefault((src, dst), set()).add(token)
    for key in symbol_table:
        src, symbol = key
        dst = symbol_table[key]
        transitions.setdefault((src, dst), set()).add(symbol)
    # Add the transitions to the dot file
    for key in transitions:
        src, dst = key
        label = [ x == 0 and '$' or str(x) for x in transitions[key] ]
        label = ','.join(label)
        lines.append('    %s -> %s [label="%s"];\n' % (src, dst, label))

    lines.append('}\n')

    # Write the file
    file = open('/tmp/graph.dot', 'w')
    file.write(''.join(lines))
    file.close()



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
                line.append('$ S%s' % state)
            elif value is None:
                line.append('%s S%s' % (symbol, state))
            else:
                line.append('%s(%s) S%s' % (symbol, value, state))
        line = ' '.join(line)
        file.write('%s\n' % line)


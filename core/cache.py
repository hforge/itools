# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

"""
This module implements a LRU (Least Recently Used) Cache.
http://en.wikipedia.org/wiki/Cache_algorithms
"""


class DNode(object):
    """This class makes the nodes of a doubly linked list.
    """

    __slots__ = ['prev', 'next', 'key']


    def __init__(self, key):
        self.key = key



class LRUCache(dict):

    __slots__ = ['first', 'last', 'key2node']


    def __init__(self):
        dict.__init__(self)
        self.first = None
        self.last = None
        self.key2node = {}


    def _append(self, key):
        node = DNode(key)

        # (1) Insert into the key-to-node map
        self.key2node[key] = node

        # (2) Append to the doubly-linked list
        node.prev = self.last
        node.next = None

        if self.first is None:
            # size = 0
            self.first = node
        else:
            # size > 0
            self.last.next = node

        self.last = node


    def _remove(self, key):
        # (1) Pop the node from the key-to-node map
        node = self.key2node.pop(key)

        # (2) Remove from the doubly-linked list
        if node.prev is None:
            self.first = node.next
        else:
            node.prev.next = node.next

        if node.next is None:
            self.last = node.prev
        else:
            node.next.prev = node.prev


    ######################################################################
    # Override dict API
    def __iter__(self):
        node = self.first
        while node is not None:
            yield node.key
            node = node.next


    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self._append(key)


    def iteritems(self):
        node = self.first
        while node is not None:
            yield node.key, self[node.key]
            node = node.next


    def pop(self, key):
        self._remove(key)
        return dict.pop(self, key)


    ######################################################################
    # Specific public API
    def touch(self, key):
        # (1) Get the node from the key-to-node map
        node = self.key2node[key]

        # (2) Touch in the doubly-linked list
        # Already the last one
        if node.next is None:
            return

        # Unlink
        if node.prev is None:
            self.first = node.next
        else:
            node.prev.next = node.next
        node.next.prev = node.prev

        # Link
        node.prev = self.last
        node.next = None
        self.last.next = node
        self.last = node




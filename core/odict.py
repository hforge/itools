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
This module implements an ordered dictionary, to be removed by Python 2.7
"""

class DNode(object):
    """This class makes the nodes of a doubly-linked list.
    """

    __slots__ = ['prev', 'next', 'key']


    def __init__(self, key):
        self.key = key



class OrderedDict(dict):

    def __init__(self, items=None):
        # The doubly-linked list
        self.first = None
        self.last = None
        # Map from key-to-node
        self.key2node = {}

        if items is not None:
            for key, value in items:
                self[key] = value


    def _check_integrity(self):
        """This method is for testing purposes, it checks the internal
        data structures are consistent.
        """
        keys = self.keys()
        keys.sort()
        # Check the key-to-node mapping
        keys2 = self.key2node.keys()
        keys2.sort()
        assert keys == keys2
        # Check the key-to-node against the doubly-linked list
        for key, node in self.key2node.iteritems():
            assert type(key) is type(node.key)
            assert key == node.key
        # Check the doubly-linked list against the cache
        keys = set(keys)
        node = self.first
        while node is not None:
            assert node.key in keys
            keys.discard(node.key)
            node = node.next
        assert len(keys) == 0


    def _append(self, key):
        node = DNode(key)

        # (1) Insert into the key-to-node map
        self.key2node[key] = node

        # (2) Append to the doubly-linked list
        node.prev = self.last
        node.next = None
        if self.first is None:
            self.first = node
        else:
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


    def __delitem__(self, key):
        self._remove(key)
        dict.__delitem__(self, key)


    def clear(self):
        dict.clear(self)
        self.key2node.clear()
        self.first = self.last = None


    def copy(self):
        message = "use 'copy.deepcopy' to copy an ordered dict"
        raise NotImplementedError, message


    def fromkeys(self, seq, value=None):
        raise NotImplementedError, "the 'fromkeys' method is not supported"


    def items(self):
        return list(self.iteritems())


    def iteritems(self):
        node = self.first
        while node is not None:
            yield node.key, self[node.key]
            node = node.next


    def iterkeys(self):
        node = self.first
        while node is not None:
            yield node.key
            node = node.next


    def itervalues(self):
        node = self.first
        while node is not None:
            yield self[node.key]
            node = node.next


    def keys(self):
        return list(self.iterkeys())


    def pop(self, key):
        self._remove(key)
        return dict.pop(self, key)


    def popitem(self):
        if self.first is None:
            raise KeyError, 'popitem(): ordered dict is empty'
        key = self.first.key
        value = self[key]
        del self[key]
        return (key, value)


    def setdefault(self, key, default=None):
        raise NotImplementedError, "the 'setdefault' method is not supported"


    def update(self, value=None, **kw):
        raise NotImplementedError, "the 'update' method is not supported"


    def values(self):
        return list(self.itervalues())


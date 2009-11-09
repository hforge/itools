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

# Import from itools
from odict import OrderedDict


class LRUCache(OrderedDict):
    """LRU stands for Least-Recently-Used.

    The LRUCache is a mapping from key to value, it is implemented as a dict
    with some differences:

    - The elemens within the cache are ordered by the access time, starting
      from the least-recently used value.  All iteration methods ('items',
      'iteritems', 'keys', etc.) return the objects sorted by this criteria,
      and so does 'popitem' too.

    - The constructor is different from that of a dict, it expects first a
      'size_min' argument, and optionally a 'size_max' argument, they are
      used to control the dict size.

      Optionally it can take an 'automatic' boolean argument, which defaults
      to 'True'.

    - When the size of the cache surpasses the defined maximum size, then
      the least-recently used values from the cache will be removed, until its
      size reaches the defined minimum.

      This happens unless the 'automatic' parameter is set to 'False'.  Then
      it will be the responsability of external code to explicitly remove the
      least-recently used values.

    Some of the dict methods have been de-activated on purpose: 'copy',
    'fromkeys', 'setdefault' and 'update'.

    There are other new methods too:

    - touch(key): defines the value identified by the given key as to be
      accessed, hence it will be at the end of the list.
    """

    def __init__(self, size_min, size_max=None, automatic=True):
        # Check arguments type
        if type(size_min) is not int:
            error = "the 'size_min' argument must be an int, not '%s'"
            raise TypeError, error % type(size_min)
        if type(automatic) is not bool:
            error = "the 'automatic' argument must be an int, not '%s'"
            raise TypeError, error % type(automatic)

        if size_max is None:
            size_max = size_min
        elif type(size_max) is not int:
            error = "the 'size_max' argument must be an int, not '%s'"
            raise TypeError, error % type(size_max)
        elif size_max < size_min:
            raise ValueError, "the 'size_max' is smaller than 'size_min'"

        # Initialize the dict
        super(LRUCache, self).__init__()
        # The cache size
        self.size_min = size_min
        self.size_max = size_max
        # Whether to free memory automatically or not (boolean)
        self.automatic = automatic


    def _append(self, key):
        super(LRUCache, self)._append(key)

        # Free memory if needed
        if self.automatic is True and len(self) > self.size_max:
            while len(self) > self.size_min:
                self.popitem()


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


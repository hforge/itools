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



class frozenlist(list):

    __slots__ = []


    #######################################################################
    # Mutable operations must raise 'TypeError'
    def __delitem__(self, index):
        raise TypeError, 'frozenlists are not mutable'


    def __delslice__(self, left, right):
        raise TypeError, 'frozenlists are not mutable'


    def __iadd__(self, alist):
        raise TypeError, 'frozenlists are not mutable'


    def __imul__(self, alist):
        raise TypeError, 'frozenlists are not mutable'


    def __setitem__(self, index, value):
        raise TypeError, 'frozenlists are not mutable'


    def __setslice__(self, left, right, value):
        raise TypeError, 'frozenlists are not mutable'


    def append(self, item):
        raise TypeError, 'frozenlists are not mutable'


    def extend(self, alist):
        raise TypeError, 'frozenlists are not mutable'


    def insert(self, index, value):
        raise TypeError, 'frozenlists are not mutable'


    def pop(self, index=-1):
        raise TypeError, 'frozenlists are not mutable'


    def remove(self, value):
        raise TypeError, 'frozenlists are not mutable'


    def reverse(self):
        raise TypeError, 'frozenlists are not mutable'


    def sort(self, cmp=None, key=None, reverse=False):
        raise TypeError, 'frozenlists are not mutable'


    #######################################################################
    # Non-mutable operations
    def __add__(self, alist):
        alist = list(self) + alist
        return frozenlist(alist)


    def __hash__(self):
        # TODO Implement frozenlists hash-ability
        raise NotImplementedError, 'frozenlists not yet hashable'


    def __mul__(self, factor):
        alist = list(self) * factor
        return frozenlist(alist)


    def __rmul__(self, factor):
        alist = list(self) * factor
        return frozenlist(alist)


    def __repr__(self):
        return 'frozenlist([%s])' % ', '.join([ repr(x) for x in self ])



class frozendict(dict):

    __slots__ = []


    #######################################################################
    # Mutable operations must raise 'TypeError'
    def __delitem__(self, index):
        raise TypeError, 'frozendicts are not mutable'


    def __setitem__(self, key, value):
        raise TypeError, 'frozendicts are not mutable'


    def clear(self):
        raise TypeError, 'frozendicts are not mutable'


    def pop(self, key, default=None):
        raise TypeError, 'frozendicts are not mutable'


    def popitem(self):
        raise TypeError, 'frozendicts are not mutable'


    def setdefault(self, key, default=None):
        raise TypeError, 'frozendicts are not mutable'


    def update(self, a_dict=None, **kw):
        raise TypeError, 'frozendicts are not mutable'


    #######################################################################
    # Non-mutable operations
    def __hash__(self):
        # TODO Implement frozendicts hash-ability
        raise NotImplementedError, 'frozendicts not yet hashable'


    def __repr__(self):
        aux = [ "%s: %s" % (repr(k), repr(v)) for k, v in self.items() ]
        return 'frozendict({%s})' % ', '.join(aux)



def freeze(value):
    # Freeze
    value_type = type(value)
    if value_type is list:
        return frozenlist(value)
    if value_type is dict:
        return frozendict(value)
    if value_type is set:
        return frozenset(value)
    # Already frozen
    if isinstance(value, (frozenlist, frozendict, frozenset)):
        return value
    # Error
    raise TypeError, 'unable to freeze "%s"' % value_type



# Copyright (C) 2008-2009 J. David Ibáñez <jdavid.ibp@gmail.com>
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

from string import ascii_lowercase
from unittest import TestCase, main

# Import from itools
from itools.core import freeze, frozenlist, frozendict
from itools.core import LRUCache


###########################################################################
# Freeze
###########################################################################
class FreezeTestCase(TestCase):

    def test_freeze_list(self):
        a_list = [1, 2, 3]
        a_frozen_list = freeze(a_list)
        self.assertEqual(a_frozen_list, a_list)
        self.assertTrue(isinstance(a_frozen_list, frozenlist))


    def test_freeze_dict(self):
        a_dict = {'a': 5, 'b': 3}
        a_frozen_dict = freeze(a_dict)
        self.assertEqual(a_frozen_dict, a_dict)
        self.assertTrue(isinstance(a_frozen_dict, frozendict))


    def test_freeze_set(self):
        a_set = set('abc')
        a_frozen_set = freeze(a_set)
        self.assertEqual(a_frozen_set, a_set)
        self.assertTrue(isinstance(a_frozen_set, frozenset))



###########################################################################
# Frozen lists
###########################################################################
a_frozen_list = freeze([1, 2, 3])


class FrozenlistTestCase(TestCase):

    def test_inheritance(self):
        self.assertTrue(isinstance(a_frozen_list, list))


    def test_identity(self):
        self.assertTrue(freeze(a_frozen_list) is a_frozen_list)


    #######################################################################
    # Mutable operations must raise 'TypeError'
    def test_setattr(self):
        self.assertRaises(AttributeError, setattr, a_frozen_list,  'x', 69)


    def test_append(self):
        self.assertRaises(TypeError, a_frozen_list.append, 5)


    def test_extend(self):
        self.assertRaises(TypeError, a_frozen_list.extend, [1, 2, 3])


    def test_delitem(self):
        try:
            del a_frozen_list[0]
        except TypeError:
            pass
        else:
            self.assertTrue(False)


    def test_del_slice(self):
        try:
            del a_frozen_list[0:2]
        except TypeError:
            pass
        else:
            self.assertTrue(False)


    def test_incremental_add(self):
        a_frozen_list = freeze([1, 2, 3])
        try:
            a_frozen_list += [4, 5]
        except TypeError:
            pass
        else:
            self.assertTrue(False)


    def test_incremental_mul(self):
        a_frozen_list = freeze([1, 2, 3])
        try:
            a_frozen_list *= 2
        except TypeError:
            pass
        else:
            self.assertTrue(False)


    def test_setitem(self):
        try:
            a_frozen_list[1] = 5
        except TypeError:
            pass
        else:
            self.assertTrue(False)


    def test_setslice(self):
        try:
            a_frozen_list[0:2] = [5]
        except TypeError:
            pass
        else:
            self.assertTrue(False)


    def test_insert(self):
        self.assertRaises(TypeError, a_frozen_list.insert, 0, 1)


    def test_pop(self):
        self.assertRaises(TypeError, a_frozen_list.pop)


    def test_remove(self):
        self.assertRaises(TypeError, a_frozen_list.remove, 1)


    def test_reverse(self):
        self.assertRaises(TypeError, a_frozen_list.reverse)


    def test_sort(self):
        self.assertRaises(TypeError, a_frozen_list.sort)


    #######################################################################
    # Test semantics of non-mutable operations
    def test_concatenation(self):
        """Like set objects, the concatenation of a frozenlist and a list
        must preserve the type of the left argument.
        """
        # frozenlist + frozenlist
        alist = freeze([]) + freeze([])
        self.assertTrue(isinstance(alist, frozenlist))
        # frozenlist + list
        alist = freeze([]) + []
        self.assertTrue(isinstance(alist, frozenlist))
        # list + frozenlist
        alist = [] + freeze([])
        self.assertTrue(not isinstance(alist, frozenlist))


    def test_equality(self):
        self.assertEqual(freeze([1, 2, 3]), [1, 2, 3])


    def test_multiplication(self):
        # frozenlist * n
        alist = freeze([1, 2]) * 2
        self.assertTrue(isinstance(alist, frozenlist))
        self.assertEqual(alist, [1, 2, 1, 2])
        # n * frozenlist
        alist = 2 * freeze([1, 2])
        self.assertTrue(isinstance(alist, frozenlist))
        self.assertEqual(alist, [1, 2, 1, 2])


    def test_representation(self):
        self.assertEqual(repr(a_frozen_list), 'frozenlist([1, 2, 3])')



# ###########################################################################
# # Frozen dicts
# ###########################################################################
a_frozen_dict = freeze({'a': 5, 'b': 3})


class FrozendictTestCase(TestCase):

    def test_inheritance(self):
        self.assertTrue(isinstance(a_frozen_dict, dict))


    def test_identity(self):
        self.assertTrue(freeze(a_frozen_dict) is a_frozen_dict)


    #######################################################################
    # Mutable operations must raise 'TypeError'
    def test_setattr(self):
        self.assertRaises(AttributeError, setattr, a_frozen_dict,  'x', 69)


    def test_delitem(self):
        try:
            del a_frozen_dict['a']
        except TypeError:
            pass
        else:
            self.assertTrue(False)


    def test_setitem(self):
        try:
            a_frozen_dict['c'] = 69
        except TypeError:
            pass
        else:
            self.assertTrue(False)


    def test_clear(self):
        self.assertRaises(TypeError, a_frozen_dict.clear)


    def test_pop(self):
        self.assertRaises(TypeError, a_frozen_dict.pop, 'a')


    def test_popitem(self):
        self.assertRaises(TypeError, a_frozen_dict.popitem)


    def test_setdefault(self):
        self.assertRaises(TypeError, a_frozen_dict.setdefault, 'x', 69)


    def test_update(self):
        self.assertRaises(TypeError, a_frozen_dict.update, {'a': 5})


    #######################################################################
    # Test semantics of non-mutable operations
    def test_equality(self):
        self.assertEqual(freeze({'a': 69, 'b': 88}), {'a': 69, 'b': 88})


    def test_representation(self):
        self.assertEqual(repr(a_frozen_dict), "frozendict({'a': 5, 'b': 3})")


# ###########################################################################
# # Cache
# ###########################################################################

class CacheTestCase(TestCase):

    def setUp(self):
        self.cache = LRUCache(3)
        for c in ascii_lowercase:
            self.cache[c] = c.upper()


    def tearDown(self):
        self.cache._check_integrity()


    #######################################################################
    # Dict API
    def test_init(self):
        self.assertRaises(TypeError, LRUCache)
        self.assertRaises(TypeError, LRUCache, 'aa')
        self.assertRaises(TypeError, LRUCache, 5, 'aa')
        self.assertRaises(ValueError, LRUCache, 5, 3)
        self.assertRaises(TypeError, LRUCache, 5, 5, 'aa')
        self.assertRaises(TypeError, LRUCache, 5, True, 4)


    def test_len(self):
        cache = self.cache
        self.assertEqual(len(cache), cache.size_min)


    def test_setitem(self):
        cache = self.cache
        key, value = 'c', 'C'
        cache[key] = value
        self.assertEqual(cache[key], value)


    def test_delitem(self):
        cache = self.cache
        self.assertEqual(len(cache), cache.size_min)
        key = 'y'
        del cache[key]
        self.assertEqual(len(cache), cache.size_min - 1)
        self.assertRaises(KeyError, cache.__getitem__, key)


    def test_in(self):
        cache = self.cache
        self.assertTrue('x' in cache)
        self.assertTrue('n' not in cache)


    def test_clear(self):
        cache = self.cache
        self.assertEqual(len(cache), cache.size_min)
        cache.clear()
        self.assertEqual(len(cache), 0)


    def test_copy(self):
        cache = self.cache
        self.assertRaises(NotImplementedError, cache.copy)


    def test_fromkeys(self):
        cache = self.cache
        self.assertRaises(NotImplementedError, cache.fromkeys, 'abc')


    def test_get(self):
        cache = self.cache
        self.assertEqual(cache.get('y'), 'Y')
        self.assertEqual(cache.get('c'), None)
        self.assertEqual(cache.get('c', 69), 69)


    def test_items(self):
        cache = self.cache
        items = cache.items()
        items = list(items)
        self.assertEqual(items, [('x', 'X'), ('y', 'Y'), ('z', 'Z')])


    def test_iterkeys(self):
        cache = self.cache
        keys = cache.keys()
        keys = list(keys)
        self.assertEqual(keys, list('xyz'))


    def test_itervalues(self):
        cache = self.cache
        values = cache.values()
        values = list(values)
        self.assertEqual(values, list('XYZ'))


    def test_keys(self):
        cache = self.cache
        keys = cache.keys()
        self.assertEqual(keys, list('xyz'))


    def test_pop(self):
        cache = self.cache
        self.assertEqual(len(cache), cache.size_min)
        key = 'y'
        value = cache.pop(key)
        self.assertEqual(value, key.upper())
        self.assertEqual(len(cache), cache.size_min - 1)
        self.assertRaises(KeyError, cache.__getitem__, key)


    def test_popitem(self):
        cache = self.cache
        self.assertEqual(len(cache), cache.size_min)
        item = cache.popitem()
        self.assertEqual(len(cache), cache.size_min - 1)
        self.assertEqual(item, ('x', 'X'))


    def test_setdefault(self):
        cache = self.cache
        self.assertRaises(NotImplementedError, cache.setdefault, 7)


    def test_update(self):
        cache = self.cache
        self.assertRaises(NotImplementedError, cache.update)


    def test_values(self):
        cache = self.cache
        values = cache.values()
        self.assertEqual(values, list('XYZ'))


    #######################################################################
    # Specific API
    def test_touch(self):
        cache = self.cache
        self.assertRaises(KeyError, cache.touch, 'r')
        cache.touch('x')
        keys = cache.keys()
        self.assertEqual(keys, list('yzx'))



if __name__ == '__main__':
    main()


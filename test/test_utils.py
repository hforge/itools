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
import unittest
from unittest import TestCase

# Import from itools
from itools.utils import frozenlist


class FrozenlistTestCase(TestCase):

    def test_init(self):
        """Test the different ways to create a frozenlist.
        """
        self.assertEqual(frozenlist(1, 2, 3), [1, 2, 3])


    #######################################################################
    # Mutable operations must raise 'TypeError'
    #######################################################################
    def test_append(self):
        alist = frozenlist()
        self.assertRaises(TypeError, alist.append, 5)


    def test_extend(self):
        alist = frozenlist()
        self.assertRaises(TypeError, alist.extend, [1,2,3])


    def test_del_item(self):
        alist = frozenlist(1, 2, 3)
        try:
            del alist[0]
        except TypeError:
            pass
        else:
            self.assert_(False)


    def test_del_slice(self):
        alist = frozenlist(1, 2, 3)
        try:
            del alist[0:2]
        except TypeError:
            pass
        else:
            self.assert_(False)


    def test_incremental_add(self):
        alist = frozenlist(1, 2, 3)
        try:
            alist += [4, 5]
        except TypeError:
            pass
        else:
            self.assert_(False)


    def test_incremental_mul(self):
        alist = frozenlist(1, 2, 3)
        try:
            alist *= 2
        except TypeError:
            pass
        else:
            self.assert_(False)


    def test_setitem(self):
        alist = frozenlist(1, 2, 3)
        try:
            alist[1] = 5
        except TypeError:
            pass
        else:
            self.assert_(False)


    def test_setslice(self):
        alist = frozenlist(1, 2, 3)
        try:
            alist[0:2] = [5]
        except TypeError:
            pass
        else:
            self.assert_(False)


    def test_insert(self):
        alist = frozenlist()
        self.assertRaises(TypeError, alist.insert, 0, 1)


    def test_pop(self):
        alist = frozenlist(1, 2, 3)
        self.assertRaises(TypeError, alist.pop)


    def test_remove(self):
        alist = frozenlist(1, 2, 3)
        self.assertRaises(TypeError, alist.remove, 1)


    def test_reverse(self):
        alist = frozenlist(1, 2, 3)
        self.assertRaises(TypeError, alist.reverse)


    def test_sort(self):
        alist = frozenlist(1, 2, 3)
        self.assertRaises(TypeError, alist.sort)


    #######################################################################
    # Test semantics of non-mutable operations
    #######################################################################
    def test_concatenation(self):
        """Like set objects, the concatenation of a frozenlist and a list
        must preserve the type of the left argument.
        """
        # frozenlist + frozenlist
        alist = frozenlist() + frozenlist()
        self.assert_(isinstance(alist, frozenlist))
        # frozenlist + list
        alist = frozenlist() + []
        self.assert_(isinstance(alist, frozenlist))
        # list + frozenlist
        alist = [] + frozenlist()
        self.assert_(not isinstance(alist, frozenlist))


    def test_equality(self):
        self.assertEqual(frozenlist(1, 2, 3), [1, 2, 3])


    def test_multiplication(self):
        # frozenlist * n
        alist = frozenlist(1, 2) * 2
        self.assert_(isinstance(alist, frozenlist))
        self.assertEqual(alist, [1, 2, 1, 2])
        # n * frozenlist
        alist = 2 * frozenlist(1, 2)
        self.assert_(isinstance(alist, frozenlist))
        self.assertEqual(alist, [1, 2, 1, 2])


    def test_representation(self):
        alist = frozenlist(1, 2)
        self.assertEqual(repr(alist), 'frozenlist(1, 2)')



if __name__ == '__main__':
    unittest.main()

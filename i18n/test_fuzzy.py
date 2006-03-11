# -*- coding: ISO-8859-1 -*-
#               2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
import unittest

# Import from itools
import fuzzy



class IsSimilarTestCase(unittest.TestCase):

    def test_different(self):
        a = "Good morning"
        b = "How do you do?"
        self.assertEqual(fuzzy.is_similar(a, b), False)


    def test_not_so_far(self):
        a = "Good morning"
        b = "Good afternoon"
        self.assertEqual(fuzzy.is_similar(a, b), False)


    def test_close(self):
        a = "You are wonderful"
        b = "You're wonderful"
        self.assertEqual(fuzzy.is_similar(a, b), True)


    def test_bingo(self):
        a = "In the middle of nowhere"
        b = "In the middle of nowhere"
        self.assertEqual(fuzzy.is_similar(a, b), True)


class MostSimilarTestCase(unittest.TestCase):

    database = ['Good morning', 'Good afternoon', 'Good night',
                'This is strange', 'Why not?', 'Freedom as in speak',
                'Where is my cat?', 'It is all about confidence']

    def test_good_evening(self):
        a = 'Good evening'
        most_similar = fuzzy.get_most_similar(a, *self.database)
        self.assertEqual(most_similar, 'Good morning')


    def test_where_is_my_dog(self):
        a = 'Where is my dog?'
        most_similar = fuzzy.get_most_similar(a, *self.database)
        self.assertEqual(most_similar, 'Where is my cat?')


    def test_free_beer(self):
        a = 'Free beer'
        most_similar = fuzzy.get_most_similar(a, *self.database)
        self.assertEqual(most_similar, 'Freedom as in speak')



if __name__ == '__main__':
    unittest.main()

# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004 Thierry Fromon <from.t@free.fr>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA


# Import from Python
import unittest

# Import from itools
import fuzzy



class Fuzzy_test(unittest.TestCase):

    def test_fuzzy_abrevation(self):
        first_text = """
        Mr toto is here
        """
        second_text = """
        toto is here Monsieur
        """
        p = fuzzy.Distance(first_text, second_text)
        print 'test_fuzzy_abrevation', p.distance()


    def test_fuzzy_no_abrevation(self):
        first_text = """
        Monsieur toto is here
        """
        second_text = """
        toto is here Monsieur
        """
        p = fuzzy.Distance(first_text, second_text)
        print  'test_fuzzy_no_abrevation', p.distance()


    def test_fuzzy_abrevation_differente(self):
        first_text = """
        Why toto is here
        """
        second_text = """
        toto is here Monsieur
        """
        p = fuzzy.Distance(first_text, second_text)
        print 'test_fuzzy_abrevation_differente', p.distance()


    def test_fuzzy_translation(self):
        first_text = """
        toto is here now
        """
        second_text = """
        now toto is here
        """
        p = fuzzy.Distance(first_text, second_text)
        print 'test_fuzzy_translation', p.distance()


    def test_fuzzy_not_all_translation(self):
        first_text = """
        Juan is here now
        """
        second_text = """
        now toto is here
        """
        p = fuzzy.Distance(first_text, second_text)
        print 'test_fuzzy_no_all_translation', p.distance()


    def test_same(self):
        first_text = """
        I am here.
        """
        second_text = """
        I am here.
        """
        p = fuzzy.Distance(first_text, second_text)
        print 'test_same', p.distance()




if __name__ == '__main__':
    unittest.main()



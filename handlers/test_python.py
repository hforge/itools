# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Luis A. Belmar Letelier <luis@itaapy.com>
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


# Import from Python
import unittest
from unittest import TestCase
from pprint import pprint 

# Import from itools
from itools.resources import memory
from itools.handlers import get_handler

# Import from itools.handlers
from itools.handlers.python import Python

data = """
import A
import A.B as AB
from B.E import F
from A.B import C as CC

class E(AA, C):
  pass
"""



code_0 = """
import A
import A.B as AB
from A.B import C as CC

class D(A.B.C):
    pass
class E(AB.C):
    pass
class F(CC):
    pass 
"""

dot_0 = """
digraph G {
rankdir=BT;
  "D" -> "A.B.C"
  "E" -> "A.B.C"
  "F" -> "A.B.C"
}"""

class PythonTestCase(TestCase):


    def test_get_imports(self):
        data = ("import A, B as BB, C\n"
                "import H\n")

        handler = Python(memory.File(data))
        res = handler.get_imports()
        expect = [([('A', None), ('B', 'BB'), ('C', None)],), ([('H', None)],)]
        self.assertEqual(expect, res)


    def test2_get_imports(self):
        data = ("import A\n"
                "import AA as A_as_A\n"
                "import A.B.Fbig as Fbig_as_F\n")

        handler = Python(memory.File(data))
        res = handler.get_imports()
        expect = [([('A', None)],), ([('AA', 'A_as_A')],), 
                  ([('A.B.Fbig', 'Fbig_as_F')],)]
        self.assertEqual(expect, res)


    def test_get_from_imports(self):
        data = ("import A\n"
                "from C import D\n"
                "from G.E import EE as EEasE\n"
                "from F import F1, F2 as FF2")
                
        handler = Python(memory.File(data))
        res = handler.get_from_imports()
        expect = [['C', [('D', None)]], ['G.E', [('EE', 'EEasE')]], 
                  ['F', [('F1', None), ('F2', 'FF2')]]]
        self.assertEqual(expect, res)


    def test_get_from_imports_dic(self):
        data = ("import A\n"
                "from C import D\n"
                "from G.E import EE as EEasE\n"
                "from F import F1, F2 as FF2")
                
        handler = Python(memory.File(data))
        res = handler.get_from_imports_dic()
        expect = {'D': 'C.D', 
                  'EEasE': 'G.E.EE', 
                  'F1': 'F.F1', 
                  'FF2': 'F.F2', 
                   }
        self.assertEqual(expect, res)

    def test_get_imports_dic(self):
        data = ("import A, B as BB, C\n"
                "import H\n")

        handler = Python(memory.File(data))
        res = handler.get_imports_dic()
        expect = {'BB': 'B'}
        self.assertEqual(expect, res)


    def test_get_classes(self):
        data = ("import A\n"
                "from C import D\n\n"
                "from G.E import EE as EEasE\n\n"
                "class F(D.E.T, EEasE):\n"
                "    'F class docstring'\n"
                "    pass")
        handler = Python(memory.File(data))
        res = handler.get_classes()
        expect = [('F', [['T', 'E', 'D'], ['EEasE']])]
        self.assertEqual(expect, res)


    def test2_get_classes(self):
        data = ("class F(A.B, G.H.K):\n"
                "    pass")
        handler = Python(memory.File(data))
        res = handler.get_classes()
        expect = [('F', [['B', 'A'], ['K', 'H', 'G']])]
        self.assertEqual(expect, res)


    def test3_get_classes(self):
        data = ("class F(A.B, E):\n"
                "    pass\n"
                "class G(C):\n"
                "    pass")
        handler = Python(memory.File(data))
        res = handler.get_classes()
        expect = [('F', [['B', 'A'], ['E']]), ('G', [['C']])]
        self.assertEqual(expect, res)



if __name__ == '__main__':
    unittest.main()


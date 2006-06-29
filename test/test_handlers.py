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

# Import from the Standard Library
import unittest
from unittest import TestCase

# Import from itools
from itools.handlers import get_handler
from itools.handlers.python import Python
from itools.handlers.dot import class_diagram_from_python



class TextTestCase(TestCase):
    
    def test_load(self):
        handler = get_handler('tests/hello.txt')
        self.assertEqual(handler.data, u'hello world\n')




#class BasicTestCase(TestCase):

#    def test_get(self):
#        handler = get_handler('hello.txt')
#        self.assertEqual(handler.to_str(), 'hello world\n')


#    def test_copy_file(self):
#        handler = get_handler('hello.txt')
#        copy = handler.copy_handler()
#        self.assertEqual(copy.to_str(), handler.to_str())


#    def test_copy_folder(self):
#        here = get_handler('.')
#        copy = here.copy_handler()
#        self.assertEqual(copy.get_handler('hello.txt').to_str(),
#                         here.get_handler('hello.txt').to_str())



#class PythonTestCase(TestCase):

#    def test_get_imports(self):
#        data = ("import A, B as BB, C\n"
#                "import H\n")

#        handler = Python(memory.File(data))
#        res = handler.get_imports()
#        expect = [([('A', None), ('B', 'BB'), ('C', None)],), ([('H', None)],)]
#        self.assertEqual(expect, res)


#    def test2_get_imports(self):
#        data = ("import A\n"
#                "import AA as A_as_A\n"
#                "import A.B.Fbig as Fbig_as_F\n")

#        handler = Python(memory.File(data))
#        res = handler.get_imports()
#        expect = [([('A', None)],), ([('AA', 'A_as_A')],), 
#                  ([('A.B.Fbig', 'Fbig_as_F')],)]
#        self.assertEqual(expect, res)


#    def test_get_from_imports(self):
#        data = ("import A\n"
#                "from C import D\n"
#                "from G.E import EE as EEasE\n"
#                "from F import F1, F2 as FF2")
#                
#        handler = Python(memory.File(data))
#        res = handler.get_from_imports()
#        expect = [['C', [('D', None)]], ['G.E', [('EE', 'EEasE')]], 
#                  ['F', [('F1', None), ('F2', 'FF2')]]]
#        self.assertEqual(expect, res)


#    def test_get_from_imports_dic(self):
#        data = ("import A\n"
#                "from C import D\n"
#                "from G.E import EE as EEasE\n"
#                "from F import F1, F2 as FF2")
#                
#        handler = Python(memory.File(data))
#        res = handler.get_from_imports_dic()
#        expect = {'D': 'C.D', 
#                  'EEasE': 'G.E.EE', 
#                  'F1': 'F.F1', 
#                  'FF2': 'F.F2', 
#                   }
#        self.assertEqual(expect, res)

#    def test_get_imports_dic(self):
#        data = ("import A, B as BB, C\n"
#                "import H\n")

#        handler = Python(memory.File(data))
#        res = handler.get_imports_dic()
#        expect = {'BB': 'B'}
#        self.assertEqual(expect, res)


#    def test_get_classes(self):
#        data = ("import A\n"
#                "from C import D\n\n"
#                "from G.E import EE as EEasE\n\n"
#                "class F(D.E.T, EEasE):\n"
#                "    'F class docstring'\n"
#                "    pass")
#        handler = Python(memory.File(data))
#        res = handler.get_classes()
#        expect = [('F', [['T', 'E', 'D'], ['EEasE']])]
#        self.assertEqual(expect, res)


#    def test2_get_classes(self):
#        data = ("class F(A.B, G.H.K):\n"
#                "    pass")
#        handler = Python(memory.File(data))
#        res = handler.get_classes()
#        expect = [('F', [['B', 'A'], ['K', 'H', 'G']])]
#        self.assertEqual(expect, res)


#    def test3_get_classes(self):
#        data = ("class F(A.B, E):\n"
#                "    pass\n"
#                "class G(C):\n"
#                "    pass")
#        handler = Python(memory.File(data))
#        res = handler.get_classes()
#        expect = [('F', [['B', 'A'], ['E']]), ('G', [['C']])]
#        self.assertEqual(expect, res)



#class DotTestCase(TestCase):

#    def test0_class_diagram_from_python(self):
#        data = ('from A import B\n'
#                'class N(B):\n'
#                '  pass\n'
#                )
#        handler = Python(memory.File(data))
#        res = class_diagram_from_python([handler])
#        expect = ('digraph G {\n'
#                  'rankdir=BT;\n'
#                  '  "N" -> "A.B"\n}')
#        self.assertEqual(expect, res)


#    def test1_class_diagram_from_python(self):
#        data = ('from A.B import C\n'
#                'from D import E\n'  
#                'class M(C.D):\n'
#                '  pass\n'
#                'class N(M, E.F.H):\n'
#                '  pass\n'
#                )
#        handler = Python(memory.File(data))
#        res = class_diagram_from_python([handler])
#        expect = ('digraph G {\n'
#                  'rankdir=BT;\n'
#                  '  "M" -> "A.B.C.D"\n'
#                  '  "N" -> "M"\n'
#                  '  "N" -> "D.E.F.H"\n'
#                  '}'
#                  )
#        self.assertEqual(expect, res)


#    def test2_class_diagram_from_python(self):
#        data = ('from A import B\n'
#                'class M(B):\n'
#                '  pass\n'
#                'class N(B):\n'
#                '  pass\n'
#                )
#        handler = Python(memory.File(data))
#        res = class_diagram_from_python([handler])
#        expect = ('digraph G {\n'
#                  'rankdir=BT;\n'
#                  '  "M" -> "A.B"\n'
#                  '  "N" -> "A.B"\n}')
#        self.assertEqual(expect, res)


#    def test3_class_diagram_from_python(self):
#        data = ('from A import B\n'
#                  'class M(B.C):\n'
#                  '  pass\n'
#                  'class N(B.C):\n'
#                  '  pass\n'
#                  )
#        handler = Python(memory.File(data))
#        res = class_diagram_from_python([handler])
#        expect = ('digraph G {\n'
#                  'rankdir=BT;\n'
#                  '  "M" -> "A.B.C"\n'
#                  '  "N" -> "A.B.C"\n}')
#        self.assertEqual(expect, res)

#        
#    def test4_class_diagram_from_python(self):
#        data = ('from A.B import C\n'
#                'from D import E\n'  
#                'class M(C.D):\n'
#                '  pass\n'
#                )
#        handler = Python(memory.File(data))
#        res = class_diagram_from_python([handler])
#        expect = ('digraph G {\n'
#                  'rankdir=BT;\n'
#                  '  "M" -> "A.B.C.D"\n}'
#                  )
#        self.assertEqual(expect, res)


#    def test5_class_diagram_from_python(self):
#        data = (  'from A.B import C\n'
#                  'from D import E\n'  
#                  'class M(C.D):\n'
#                  '  pass\n'
#                  'class N(M, E.F.H):\n'
#                  '  pass\n'
#                  )
#        handler = Python(memory.File(data))
#        res = class_diagram_from_python([handler])
#        expect = ('digraph G {\n'
#                  'rankdir=BT;\n'
#                  '  "M" -> "A.B.C.D"\n'
#                  '  "N" -> "M"\n'
#                  '  "N" -> "D.E.F.H"\n'
#                  '}'
#                  )
#        self.assertEqual(expect, res)


#    def test6_class_diagram_from_python(self):
#        data = ('import A.B.C as ABC\n'
#                'class M(ABC.D):\n'
#                '  pass\n'
#                )
#        handler = Python(memory.File(data))
#        res = class_diagram_from_python([handler])
#        expect = ('digraph G {\n'
#                  'rankdir=BT;\n'
#                  '  "M" -> "A.B.C.D"\n'
#                  '}'
#                  )
#        self.assertEqual(expect, res)


#    def test7_class_diagram_from_python(self):
#        """ start test of multiples python file input"""
#        data = ('import A.B.C as ABC\n'
#                'class M(ABC.D):\n'
#                '  pass\n'
#                )
#        handler = Python(memory.File(data))
#        handler.name = 'test'
#        res = class_diagram_from_python([handler])
#        expect = ('digraph G {\n'
#                  'rankdir=BT;\n'
#                  '  "test.M" -> "A.B.C.D"\n'
#                  '}'
#                  )
#        self.assertEqual(expect, res)


#    def test8_crossed_imports(self):
#        data = ("from A.B import C as CC\n"
#                "from D.E import F as FF\n"
#                "class G(CC):\n"
#                "    pass\n"
#                "\n"
#                "class H(G, FF):\n"
#                "    pass\n")
#        handler = Python(memory.File(data))
#        handler.name = 'test'
#        res = class_diagram_from_python([handler])
#        expect = ('digraph G {\n'
#                  'rankdir=BT;\n'
#                  '  "test.G" -> "A.B.C"\n'
#                  '  "test.H" -> "A.B.C.G"\n'
#                  '  "test.H" -> "D.E.F"\n'
#                  '}'
#                  )
#        self.assertEqual(expect, res)



if __name__ == '__main__':
    unittest.main()

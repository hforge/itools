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

# Import from itools
from itools.resources import memory
from python import Python
from dot import Dot


class DotTestCase(TestCase):

    def test_skeleton(self):
        handler = Dot()
        expect = ('digraph G {\n'
                  'rankdir=BT;\n'
                  '  \n}')
        self.assertEqual(expect, handler.to_str())


    def test0_class_diagram_from_python(self):
        data = ('from A import B\n'
                  'class N(B):\n'
                  '  pass\n'
                  )
        handler = Python(memory.File(data))
        dot = Dot()
        dot.class_diagram_from_python([handler])
        res = dot.to_str()
        expect = ('digraph G {\n'
                  'rankdir=BT;\n'
                  '  "N" -> "A.B"\n}')
        self.assertEqual(expect, res)


    def test1_class_diagram_from_python(self):
        data = (  'from A.B import C\n'
                  'from D import E\n'  
                  'class M(C.D):\n'
                  '  pass\n'
                  'class N(M, E.F.H):\n'
                  '  pass\n'
                  )
        dot = Dot()
        handler = Python(memory.File(data))
        dot.class_diagram_from_python([handler])
        expect = ('digraph G {\n'
                  'rankdir=BT;\n'
                  '  "M" -> "A.B.C.D"\n'
                  '  "N" -> "M"\n'
                  '  "N" -> "D.E.F.H"\n'
                  '}'
                  )
        res = dot.to_str()
        self.assertEqual(expect, res)


    def test2_class_diagram_from_python(self):
        data = ('from A import B\n'
                  'class M(B):\n'
                  '  pass\n'
                  'class N(B):\n'
                  '  pass\n'
                  )
        handler = Python(memory.File(data))
        dot = Dot()
        dot.class_diagram_from_python([handler])
        res = dot.to_str()
        expect = ('digraph G {\n'
                  'rankdir=BT;\n'
                  '  "M" -> "A.B"\n'
                  '  "N" -> "A.B"\n}')
        self.assertEqual(expect, res)


    def test3_class_diagram_from_python(self):
        data = ('from A import B\n'
                  'class M(B.C):\n'
                  '  pass\n'
                  'class N(B.C):\n'
                  '  pass\n'
                  )
        handler = Python(memory.File(data))
        dot = Dot()
        dot.class_diagram_from_python([handler])
        res = dot.to_str()
        expect = ('digraph G {\n'
                  'rankdir=BT;\n'
                  '  "M" -> "A.B.C"\n'
                  '  "N" -> "A.B.C"\n}')
        self.assertEqual(expect, res)

        
    def test4_class_diagram_from_python(self):
        data = (  'from A.B import C\n'
                  'from D import E\n'  
                  'class M(C.D):\n'
                  '  pass\n'
                  )
        handler = Python(memory.File(data))
        dot = Dot()
        dot.class_diagram_from_python([handler])
        res = dot.to_str()
        expect = ('digraph G {\n'
                  'rankdir=BT;\n'
                  '  "M" -> "A.B.C.D"\n}'
                  )
        self.assertEqual(expect, res)

        
    def test5_class_diagram_from_python(self):
        data = (  'from A.B import C\n'
                  'from D import E\n'  
                  'class M(C.D):\n'
                  '  pass\n'
                  'class N(M, E.F.H):\n'
                  '  pass\n'
                  )
        handler = Python(memory.File(data))
        dot = Dot()
        dot.class_diagram_from_python([handler])
        res = dot.to_str()
        expect = ('digraph G {\n'
                  'rankdir=BT;\n'
                  '  "M" -> "A.B.C.D"\n'
                  '  "N" -> "M"\n'
                  '  "N" -> "D.E.F.H"\n'
                  '}'
                  )
        self.assertEqual(expect, res)


    def test6_class_diagram_from_python(self):
        data = ('import A.B.C as ABC\n'
                'class M(ABC.D):\n'
                '  pass\n'
                )
        handler = Python(memory.File(data))
        dot = Dot()
        dot.class_diagram_from_python([handler])
        res = dot.to_str()
        expect = ('digraph G {\n'
                  'rankdir=BT;\n'
                  '  "M" -> "A.B.C.D"\n'
                  '}'
                  )
        self.assertEqual(expect, res)


    def test7_class_diagram_from_python(self):
        """ start test of multiples python file input"""
        data = ('import A.B.C as ABC\n'
                'class M(ABC.D):\n'
                '  pass\n'
                )
        handler = Python(memory.File(data))
        handler.name = 'test'
        dot = Dot()
        dot.class_diagram_from_python([handler])
        res = dot.to_str()
        expect = ('digraph G {\n'
                  'rankdir=BT;\n'
                  '  "test.M" -> "A.B.C.D"\n'
                  '}'
                  )
        self.assertEqual(expect, res)




if __name__ == '__main__':
    unittest.main()


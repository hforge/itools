# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Luis A. Belmar Letelier <luis@itaapy.com>
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
import unittest, tempfile, os
from unittest import TestCase
from pprint import pprint 

# Import from itools
from itools.resources import memory
import itools.handlers.python 
from itools.handlers import get_handler

# Import from itools.handlers
from itools.handlers.python import Python
from itools.handlers.Folder import Folder 
from itools.handlers.dot import Dot 


class itaapyTools_classDiagramTestCase(TestCase):


    def setUp(self):
        self.here = os.getcwd()


    def tearDown(self):
        os.chdir(self.here)


    def test_itaapyTools_classDiagram(self):
        data = ('from a import A\n'
                  'class B(A):\n'
                  '  pass\n')
        # make a tmp directory with test.py in it
        handler = Python(memory.File(data))
        temp = tempfile.mkdtemp('.test_itools')
        tmp = get_handler(temp)

        pkg = Folder(memory.Folder())
        pkg.set_handler('b.py', handler) 
        tmp.set_handler('python_pkg', pkg)
        tmp.save_state()
        ##os.system('tree %s' % temp)
        
        # Execute the command on the a.py
        os.chdir('%s/python_pkg' % temp)
        cmd = '/usr/bin/itaapyTools_classDiagram.py b.py' 
        os.system(cmd)

        # Check the result 
        tmp.load_state()
        expect = ('digraph G {\n'
                  'rankdir=BT;\n'
                  '  "b.B" -> "a.A"\n}')
        res = tmp.get_handler('python_pkg/out.dot').to_str()

        self.assertEqual(expect, res)
        os.system('rm -fr %s' % temp)


    def test_package_name_in_dot(self):

        a = ('class A(object):\n'
             '   pass\n')

        b = ('from a import A\n'
             'from StringIO import StringIO\n'
             'class B(A, StringIO):\n'
             '    pass\n')
 
        # make a tmp directory with test.py in it
        temp = tempfile.mkdtemp('.test_itools')
        tmp = get_handler(temp)

        pkg = Folder(memory.Folder())
        pkg.set_handler('__init__.py', Python(memory.File(" "))) 
        pkg.set_handler('a.py', Python(memory.File(a)))
        pkg.set_handler('b.py', Python(memory.File(b)))

        tmp.set_handler('python_pkg', pkg)
        tmp.save_state()
        #os.system('tree %s' % temp)
        
        # Execute the command on the test.py
        os.chdir('%s/python_pkg' % temp)
        cmd = '/usr/bin/itaapyTools_classDiagram.py b.py a.py' 
        os.system(cmd)

        # Check the result 
        tmp.load_state()
        expect = ('digraph G {\n'
                  'rankdir=BT;\n'
                  '  "python_pkg.b.B" -> "python_pkg.a.A"\n'
                  '  "python_pkg.b.B" -> "StringIO.StringIO"\n'
                  '  "python_pkg.a.A" -> "object"\n}')
        res = tmp.get_handler('python_pkg/out.dot').to_str()
        self.assertEqual(expect, res)
        os.system('rm -fr %s' % temp)


    def test2_package_name_in_dot(self):
        """ Here we remove the __init__.py file"""

        a = ('class A(object):\n'
             '   pass\n')

        b = ('from a import A\n'
             'from StringIO import StringIO\n'
             'class B(A, StringIO):\n'
             '    pass\n')
 
        # make a tmp directory with test.py in it
        temp = tempfile.mkdtemp('.test_itools')
        tmp = get_handler(temp)

        pkg = Folder(memory.Folder())
        #pkg.set_handler('__init__.py', Python(memory.File(" "))) 
        pkg.set_handler('a.py', Python(memory.File(a)))
        pkg.set_handler('b.py', Python(memory.File(b)))

        tmp.set_handler('python_pkg', pkg)
        tmp.save_state()
        #os.system('tree %s' % temp)
        
        # Execute the command on the test.py
        os.chdir('%s/python_pkg' % temp)
        cmd = '/usr/bin/itaapyTools_classDiagram.py b.py' 
        os.system(cmd)

        # Check the result 
        tmp.load_state()
        expect = ('digraph G {\n'
                  'rankdir=BT;\n'
                  '  "b.B" -> "a.A"\n'
                  '  "b.B" -> "StringIO.StringIO"\n}')
        res = tmp.get_handler('python_pkg/out.dot').to_str()
        self.assertEqual(expect, res)
        os.system('rm -fr %s' % temp)



if __name__ == '__main__':
    unittest.main()


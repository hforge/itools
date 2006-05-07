# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 J. David Ibáñez <jdavid@itaapy.com>
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
import compiler
from compiler.ast import Name, Getattr, Node 
from pprint import pprint

# Import from itools
from Text import Text
from itools.handlers.registry import register_handler_class


class VisitorUnicode(object):

    def __init__(self):
        self.messages = []


    def visitConst(self, const):
        if isinstance(const.value, unicode):
            self.messages.append((const.value, const.lineno))



class Visitor(object):

    def __init__(self):
        self.imports = []
        self.from_imports = []
        self.classes = []


    def visitImport(self, node):
        res = []
        for i in node.getChildren():
            name, as_name = i[0]
            res.append((name, as_name))
        self.imports.append(node.getChildren())


    def visitFrom(self, node):
        res = []
        for i in node.getChildren(): 
            res.append(i)
        self.from_imports.append(res)


    def flatten(self, getattr):
        """ from Getattr(Getattr(Name('D'), 'E'), 'T') 
            we make ['T', 'E', 'D'] """
        res = []
        exp, name = getattr.getChildren()
        res.append(name)
        while isinstance(exp, Getattr):
            exp, name = exp.getChildren()
            res.append(name)
        res.append(exp.name)
        return res


    def visitClass(self, node):
        res = []
        class_name = list(node)[0]
        bases = node.bases

        for n in bases:
            is_getattr = isinstance(n, Getattr)
            is_name = isinstance(n, Name)
            if is_getattr:
                res.append(self.flatten(n))
            elif is_name:
                res.append([n.name])
        self.classes.append((class_name, res))



class Python(Text):

    class_mimetypes = ['text/x-python']
    class_extension = 'py'


    #########################################################################
    # Load
    #########################################################################
    def _load_state(self, resource):
        Text._load_state(self, resource)
        state = self.state
        state.visitor = None 


    def get_package_name(self):
        parent = self.parent
        # Check if we are in a python package
        package_name = False 
        if parent is not None:
            if '__init__.py' in parent.get_handler_names():
                package_name = parent.name 
        return package_name 


    def get_module_name(self):
        name = self.name 
        return name


    def get_visitor(self):
        visitor = self.state.visitor 
        if visitor is None:
            ast = compiler.parse(self.to_str())
            visitor = Visitor()
            compiler.walk(ast, visitor)
            self.state.visitor = visitor
        return visitor


    def get_classes(self):
        visitor = self.get_visitor()
        
        pkg_name = self.get_package_name()
        module_name = self.get_module_name()
        classes = visitor.classes

        new_classes = []
        for name, bases in classes:
            new_cls = name, bases
            if module_name:
                new_cls = '%s.%s' % (module_name, name), bases
            if pkg_name:
                name, bases = new_cls
                new_cls = '%s.%s' % (pkg_name, name), bases
            new_classes.append(new_cls)
        return new_classes    


    def get_from_imports(self):
        visitor = self.get_visitor()
        return visitor.from_imports


    def get_imports(self):
        visitor = self.get_visitor()
        return visitor.imports


    def get_from_imports_dic(self):
        """
        from [['C', [('D', None)]], ['G.E', [('EE', 'EEasE')]], 
              ['F', [('F1', None), ('F2', 'FF2')]]]
        return {'F1': 'F.F1', 'EEasE': 'G.E.EE', 'D': 'C.D', 'FF2': 'F.F2'}
        """
        dic = {}
        from_imports = self.get_from_imports()
        for mod, imports in from_imports:
            for impor in imports:
                name, alias = impor
                if alias:
                    dic[alias] = '%s.%s' % (mod, name)
                else:
                    dic[name] = '%s.%s' % (mod, name)
        return dic


    def get_imports_dic(self):
        """
        from [([('A', None), ('B', 'BB'), ('C', None)],), ([('H', 'HH')],)]
        return {'BB': 'B', 'HH': 'H'}
        """
        dic = {}
        lines = self.get_imports()
        for line in lines:
            line = line[0] 
            for name, alias in line:
                if alias:
                    dic[alias] = name
        return dic


    def get_messages(self):
        ast = compiler.parse(self.to_str())
        visitor = VisitorUnicode()
        compiler.walk(ast, visitor)
        return visitor.messages


register_handler_class(Python)

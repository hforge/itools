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

# Import from the Standard Library
from pprint import pprint

# Import from itools
from Text import Text
from python import Python
from itools.resources import memory 


class Dot(Text):

    class_mimetypes = ['text/x-dot']
    class_extension = 'dot'
    class_version = '20050905'

    ########################################################################
    # Skeleton
    ########################################################################
    def get_skeleton(self):
        template = ('digraph G {\n'
                    'rankdir=BT;\n'
                    '  \n}')
        return template 


    ########################################################################
    # API 
    ########################################################################
    def class_diagram_from_python(self, handlers):
        """
        input : from A import B
                class N(B.C)
                    pass 

        output : "N" -> "A.B.C" 
        """

        imports_dict, modules_dict, all_classes = {}, {}, []
        for h in handlers:
            imports_dict.update(h.get_from_imports_dic())
            modules_dict.update(h.get_imports_dic())
            all_classes.extend([{'cls': h.get_classes(), 'h':h}])

        full_class_names = []
        for dic in all_classes:
            for cls in dic['cls']:
                class_name, bases = cls
                full_class_names.append(class_name)


        dot = []
        for dic in all_classes:
            h = dic['h']
            for cls in dic['cls']:
                class_name, bases = cls
                
                inherit_res = '' 
                for base_list in bases:
                    res = []
                    # base_list ['B', 'C']
                    while base_list:
                        base = base_list.pop()
                        #1 base = 'B' #2 base = 'C'
                        inherit_res = imports_dict.get(base, base)
                        inherit_res = modules_dict.get(base, inherit_res)
                        res.append(inherit_res) 
                        pkg_name = h.get_package_name()
                    res = '.'.join(res)
                    pkg_res = '%s.%s' % (pkg_name, res)
                    if pkg_name: 
                        if pkg_res in full_class_names:
                            res = pkg_res
                    dot.append('"%s" -> "%s"' % (class_name, res))

        relations = '\n  '.join(dot)
        data     = ('digraph G {\n'
                    'rankdir=BT;\n'
                    '  %s\n}') % relations
        resource = memory.File(data)
        self.load_state(resource)

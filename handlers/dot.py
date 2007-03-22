# -*- coding: UTF-8 -*-
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
import os



def class_diagram_from_python(handlers, base_path=None):
    """
    input : from A import B
            class N(B.C)
                pass 

    output : "N" -> "A.B.C" 
    """
    # Package name
    package_name = None
    if base_path is not None:
        if os.exists(os.path.join(base_path, '__init__.py')):
            package_name = os.path.basename(cwd)

    imports_dict, modules_dict, all_classes = {}, {}, []
    for handler in handlers:
        imports_dict.update(handler.get_from_imports_dic())
        modules_dict.update(handler.get_imports_dic())
        all_classes.extend([{'cls': handler.get_classes(package_name),
                             'h': handler}])

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
                res = '.'.join(res)
                pkg_res = '%s.%s' % (package_name, res)
                if package_name: 
                    if pkg_res in full_class_names:
                        res = pkg_res
                dot.append('"%s" -> "%s"' % (class_name, res))

    relations = '\n  '.join(dot)
    return ('digraph G {\n'
            'rankdir=BT;\n'
            '  %s\n}') % relations

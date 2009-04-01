# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2009 Romain Gauthier <romain.gauthier@itaapy.com>
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
from gc import get_referents
from sys import getsizeof


def format(txt, **kw):
    return txt.format(**kw)



def get_sizeof(obj):
    """Return the size of an object and all objects refered by it.
    """
    size = 0
    done = set()
    todo = {id(obj): obj}
    while todo:
        obj_id, obj = todo.popitem()
        size += getsizeof(obj)
        done.add(obj_id)
        done.add(id(obj.__class__)) # Do not count the class
        for obj in get_referents(obj):
            obj_id = id(obj)
            if obj_id not in done:
                todo[obj_id] = obj

    return size




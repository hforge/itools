# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

"""
This module implements what we call so far a "thingy", till we find a better
name.

From a semantical point of view a thingy is an abstraction of classes and
instances.  From an implementation point of view thingies are Python classes
that when instantiated create new classes, instead of class instances.

There are two ways to create a thingy:

  (1) Statically
  class my_thingy(thingy):
      ...

  (2) Dynamically
  my_thingy = thingy(...)

"""


class thingy(object):

    def __new__(cls, *args, **kw):
        # Make the new class
        name = "%s(%s)" % (cls.__name__, kw)
        new_class = type(name, (cls,), kw)
        # Initialize
        new_class.__init__(*args, **kw)
        # Ok
        return new_class


    @classmethod
    def __init__(self, *args, **kw):
        pass


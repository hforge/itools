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

# Import from the Standard Library
from types import FunctionType

# Import from itools
from lazy import lazy


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



class thingy_metaclass(type):

    def __new__(mcs, name, bases, dict):
        """
        This method is called when a thingy is created "statically":

            class A(thingy):
               ...
        """
        # We don't have instance methods
        for key, value in dict.iteritems():
            if type(value) is not FunctionType or key == '__new__':
                continue
            dict[key] = classmethod(value)

        # Make and return the class
        cls = type.__new__(mcs, name, bases, dict)
        return cls



class thingy(object):

    __metaclass__ = thingy_metaclass


    def __new__(cls, *args, **kw):
        """
        This method is called when a thingy is created "dynamically":

            thingy(...)
        """
        # Make the new class
        name = "%s(%s)" % (cls.__name__, kw)
        new_class = type.__new__(thingy_metaclass, name, (cls,), kw)
        # Initialize
        new_class.__init__(*args, **kw)
        # Ok
        return new_class


    def __init__(self, *args, **kw):
        pass



class thingy_lazy_property(lazy):

    def __get__(self, instance, owner):
        name = self.__name__
        for cls in owner.__mro__:
            if name in cls.__dict__:
                name = self.meth.func_name
                value = self.meth(owner)
                setattr(owner, name, value)
                return value


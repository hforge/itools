# -*- coding: UTF-8 -*-
# Copyright (C) 2009-2011 J. David Ibáñez <jdavid.ibp@gmail.com>
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
import traceback
from logging import getLogger
from sys import _getframe
from types import FunctionType

# Import from here
from .lazy import lazy


log = getLogger("itools.core")

"""
This module provides prototype-based programming:

  http://en.wikipedia.org/wiki/Prototype-based_programming

From a semantical point of view a prototype is an abstraction of classes and
instances.  From an implementation point of view thingies are Python classes
that when instantiated create new classes, instead of class instances.

There are two ways to create a new prototype:

  (1) Statically
  class my_prototype(prototype):
      ...

  (2) Dynamically
  my_prototype = prototype(...)

And you can combine this ad-aeternam:

  proto1 = prototype(...)
  class proto2(proto1):
      ...
  proto3 = proto2(...)

"""


class prototype_type(type):

    def __new__(mcs, class_name, bases, dict):
        """
        This method is called when a prototype is created "statically":

            class A(prototype):
               ...
        """
        # We don't have instance methods
        for name, value in dict.items():
            # There are not instance methods
            if type(value) is FunctionType and name != '__new__':
                value = classmethod(value)
                dict[name] = value

            # Ideally Python should support something like this:
            #
            # class A(object):
            #     x = B(...)
            #     def x.f(self):
            #         ...
            #
            #     # Or better
            #     x.f = func (self):
            #         ...
            #
            # But unfortunately it does not; so thingies work-around this
            # limit using a naming convention (and metaclasses):
            #
            # class A(prototype):
            #     x = prototype()
            #     def x__f(self):
            #         ...
            #
            if '__' in name and name[0] != '_' and name[-1] != '_':
                source_name = name
                name, rest = name.split('__', 1)
                sub = dict.get(name)
                if issubclass(type(sub), prototype_type):
                    # Closure
                    name = rest
                    while '__' in name:
                        subname, rest = name.split('__', 1)
                        aux = getattr(sub, subname, None)
                        if not issubclass(type(aux), prototype_type):
                            break
                        sub, name = aux, rest

                    setattr(sub, name, value)
                    del dict[source_name]
                    # Fix the name
                    if type(value) is classmethod:
                        value.__get__(None, dict).__func__.__name__ = name
                    elif type(value) is proto_property:
                        value.__name__ = name
                    elif type(value) is proto_lazy_property:
                        value.__name__ = name

        # Make and return the class
        return type.__new__(mcs, class_name, bases, dict)


class prototype(object, metaclass=prototype_type):

    def __new__(cls, *args, **kw):
        """
        This method is called when a prototype is created "dynamically":

            prototype(...)
        """
        # Make the new class
        name = f'[anonymous] from {cls.__module__}.{cls.__name__}'
        new_class = type.__new__(prototype_type, name, (cls,), kw)
        # Fix the module so repr(...) gives something meaningful
        new_class.__module__ = _getframe(1).f_globals.get('__name__')
        # Initialize
        new_class.__init__(*args, **kw)
        # Ok
        return new_class

    def __init__(self, *args, **kw):
        pass


class proto_property(lazy):

    def __get__(self, instance, owner):
        try:
            value = self.meth(owner)
        except Exception as e:
            tb = traceback.format_exc()
            log.error(f"Error on proto property: {tb}", exc_info=True)
            raise
        return value


class proto_lazy_property(lazy):

    def __get__(self, instance, owner):
        name = self.__name__
        for cls in owner.__mro__:
            if name in cls.__dict__:
                name = self.meth.__name__
                try:
                    value = self.meth(owner)
                except Exception as e:
                    tb = traceback.format_exc()
                    log.error(f"Error on proto lazy property: {tb}", exc_info=True)
                    raise
                setattr(owner, name, value)
                return value


def is_prototype(value, cls):
    from itools.gettext import MSG
    from itools.web import INFO, ERROR
    for c in [MSG, INFO, ERROR]:
        if cls is c and isinstance(value, c):
            log.debug("Warning: is_prototype(xxx, MSG) is obsolete. MSG is not a prototype anymore")
            return True
    return issubclass(type(value), prototype_type) and issubclass(value, cls)

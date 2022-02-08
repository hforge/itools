# -*- coding: UTF-8 -*-
# Copyright (C) 2009-2010 J. David Ibáñez <jdavid.ibp@gmail.com>
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


# From http://blog.pythonisito.com/2008/08/lazy-descriptors.html
class lazy(object):

    def __init__(self, meth):
        self.meth = meth
        # For introspection
        self.__name__ = meth.__name__
        self.__doc__ = meth.__doc__

    def __get__(self, instance, owner):
        if instance is None:
            return self
        name = self.meth.__name__
        value = self.meth(instance)
        instance.__dict__[name] = value
        return value

    def __repr__(self):
        return '%s wrapps %s' % (object.__repr__(self), repr(self.meth))

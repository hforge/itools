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
from re import compile



expr = compile('(\{.*?\})')

def format(txt, **kw):
    """Mimics the method 'str.format' from Python 2.6
    """
    # TODO Implement escaping curly brackets by doubling them: "{{}}"
    # TODO Raise an error if there are unbalanced curly brackets: "{" or "}"
    def repl(match):
        name = match.group(1)
        name = name[1:-1]
        if not name:
            raise ValueError, 'zero length field name in format'
        if name not in kw:
            raise KeyError, "'%s'" % name
        value = kw[name]
        return str(value)

    return expr.sub(repl, txt)



def get_sizeof(obj):
    raise NotImplementedError, "'get_sizeof' not supported in Python 2.5"

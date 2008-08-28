# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from itools
from itools.xml import XMLNamespace, register_namespace
from itools.xml import ElementSchema



xliff_elements = [
    # Top Level and Header
    ElementSchema('xliff'),
    ElementSchema('file'),
    ElementSchema('header'),
    ElementSchema('skl'),
    ElementSchema('external-file'),
    ElementSchema('internal-file'),
    ElementSchema('glossary'),
    ElementSchema('reference'),
    ElementSchema('phase-group'),
    ElementSchema('phase'),
    ElementSchema('tool'),  # 1.2
    ElementSchema('note'),
    # Named Group
    ElementSchema('context-group'),
    ElementSchema('context'),
    ElementSchema('count-group'),
    ElementSchema('count'),
    ElementSchema('prop-group'),
    ElementSchema('prop'),
    # Structural
    ElementSchema('body'),
    ElementSchema('group'),
    ElementSchema('trans-unit'),
    ElementSchema('source'),
    ElementSchema('target'),
    ElementSchema('bin-unit'),
    ElementSchema('bin-source'),
    ElementSchema('bin-target'),
    ElementSchema('alt-trans'),
    # Inline
    ElementSchema('g'),
    ElementSchema('x'),
    ElementSchema('bx'),
    ElementSchema('ex'),
    ElementSchema('bpt'),
    ElementSchema('ept'),
    ElementSchema('sub'),
    ElementSchema('it'),
    ElementSchema('ph'),
    # Delimiter
    ElementSchema('mrk'),
]





#'urn:oasis:names:tc:xliff:document:1.1'
xliff_namespace = XMLNamespace(
    'urn:oasis:names:tc:xliff:document:1.2', None, xliff_elements)


###########################################################################
# Register
###########################################################################
register_namespace(xliff_namespace)

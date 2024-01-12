# Copyright (C) 2008 J. David Ibáñez <jdavid.ibp@gmail.com>
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
    ElementSchema(name='xliff'),
    ElementSchema(name='file'),
    ElementSchema(name='header'),
    ElementSchema(name='skl'),
    ElementSchema(name='external-file'),
    ElementSchema(name='internal-file'),
    ElementSchema(name='glossary'),
    ElementSchema(name='reference'),
    ElementSchema(name='phase-group'),
    ElementSchema(name='phase'),
    ElementSchema(name='tool'),  # 1.2
    ElementSchema(name='note'),
    # Named Group
    ElementSchema(name='context-group'),
    ElementSchema(name='context'),
    ElementSchema(name='count-group'),
    ElementSchema(name='count'),
    ElementSchema(name='prop-group'),
    ElementSchema(name='prop'),
    # Structural
    ElementSchema(name='body'),
    ElementSchema(name='group'),
    ElementSchema(name='trans-unit'),
    ElementSchema(name='source'),
    ElementSchema(name='target'),
    ElementSchema(name='bin-unit'),
    ElementSchema(name='bin-source'),
    ElementSchema(name='bin-target'),
    ElementSchema(name='alt-trans'),
    # Inline
    ElementSchema(name='g'),
    ElementSchema(name='x'),
    ElementSchema(name='bx'),
    ElementSchema(name='ex'),
    ElementSchema(name='bpt'),
    ElementSchema(name='ept'),
    ElementSchema(name='sub'),
    ElementSchema(name='it'),
    ElementSchema(name='ph'),
    # Delimiter
    ElementSchema(name='mrk'),
]





#'urn:oasis:names:tc:xliff:document:1.1'
xliff_namespace = XMLNamespace(
    uri='urn:oasis:names:tc:xliff:document:1.2',
    prefix=None,
    elements=xliff_elements)


###########################################################################
# Register
###########################################################################
register_namespace(xliff_namespace)

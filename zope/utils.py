# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2002-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from string import translate, maketrans


src = ur""" @¹,;:!¡?ª$£¤+&/\"*#()[]{}'ÄÅÁÀÂÃäåáàâãÇçÉÈÊËéèêëæÍÌÎÏíìîïÑñÖÓÒÔÕØöóòôõøßÜÚÙÛüúùûÝ~ýÿ~^°"""
dst = ur"""___________________________AAAAAAaaaaaaCcEEEEeeeeeIIIIiiiiNnOOOOOOooooooSUUUUuuuuY_yy__-"""

transmap = {}
for i in range(len(src)):
    a, b = src[i], dst[i]
    transmap[ord(a)] = ord(b)


def checkid(id):
    """
    Checks wether th id is or not a valid Zope id. If it is the id is
    returned, but stripped. If it is a bad id None is returned to signal
    the error.
    """
    if isinstance(id, str):
        id = unicode(id, 'utf8')
    id = id.strip().translate(transmap).strip('_')

    # Check wether the id is empty
    if len(id) == 0:
        return None

    # Check for unallowed characters
    for c in id:
        if not c.isalnum() and c not in ('.', '-', '_'):
            return None

    # The id is good
    return str(id)

# Copyright (C) 2002-2003 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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



# Import from Python
from thread import get_ident

# Import from Zope
from AccessControl import getSecurityManager



def get_context():
    """Returns the context."""
    from Products.iHotfix import contexts
    return contexts.get(get_ident())



# XXX Some non ikaaro application use it, maybe we should try to put the
# authenticated user in the context, always
def get_user():
    """
    Returns the user object or None if it is anonymous.
    """
    user = getSecurityManager().getUser()
    if user.getUserName() == 'Anonymous User':
        return None
    return user

# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2002-2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


# Import from Zope
from AccessControl import Role
from Globals import DTMLFile


class RoleManager(Role.RoleManager):
    """
    Changes the static local roles that are changed through the management
    screens to a dynamic version that can easily be customized from the
    file system through inheritance.

    ALERT! With Zope the object has an Owner local role by default,
    since static local roles dissapear, the default Owner local role
    disappears too. Implement it yourself if you need it.
    """


    # Disable static local roles
    manage_listLocalRoles = DTMLFile('localroles', globals())
    manage_editLocalRoles = DTMLFile('localroles', globals())


    def manage_addLocalRoles(self, userid, roles, REQUEST=None):
        """ """
        return 'static local roles deactivated'


    def manage_setLocalRoles(self, userid, roles, REQUEST=None):
        """ """
        return 'static local roles deactivated'


    def manage_delLocalRoles(self, userids, REQUEST=None):
        """ """
        return 'static local roles deactivated'


    def has_local_roles(self):
        dict = self.__ac_local_roles__()
        return len(dict)


    def get_local_roles(self):
        dict = self.__ac_local_roles__()
        keys=dict.keys()
        keys.sort()
        info=[]
        for key in keys:
            value=tuple(dict[key])
            info.append((key, value))
        return tuple(info)


    def get_local_roles_for_userid(self, userid, *args):
        dict = self.__ac_local_roles__()
        return tuple(dict.get(userid, []))


    def __ac_local_roles__(self):
        roles = {}
        for role in self.localroles():
            for username in self.localroles(role):
                x = roles.setdefault(username, [])
                x.append(role)

        return roles


    # Interface to implement by subclasses
    def localroles(self, role=None):
        """
        If role is None, a list with all the local roles must be returned.

        If role is not None, a list with all the usernames of the users
        that have the given local role must be returned.
        """
        if role is None:
            return []
        else:
            return []


# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


class AccessControl(object):
    """Base class to control access. Provides default implementation; maybe
    overriden.
    """

    def is_access_allowed(self, context, resource, view):
        """Returns True if the given user is allowed to access the given
        method of the given resource. False otherwise.
        """
        # Get the access control definition (default to False)
        if view is None:
            return False
        access = view.access

        # Private (False) or Public (True)
        if isinstance(access, bool):
            return access

        # Access Control through a method
        if isinstance(access, str):
            method = getattr(self, access, None)
            if method is None:
                raise ValueError, 'access control "%s" not defined' % access

            return method(context.user, resource)

        # Only booleans and strings are allowed
        raise TypeError, 'unexpected value "%s"' % access


    #########################################################################
    # Basic Controls
    def is_authenticated(self, user, resource=None):
        return user is not None

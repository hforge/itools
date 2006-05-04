# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from itools
from itools.web import get_context


class AccessControl(object):

    def get_method(self, name):
        """
        If there is not a method with the given name an exception will be
        raised.

        If there is but the user has not the right to access it, the value
        'None' will be returned.

        If the user has the right, the method itself will be returned.
        """
        method = getattr(self, name)

        # Load the access control definition
        access = getattr(self, '%s__access__' % name, None)
        if isinstance(access, str):
            access = getattr(self, access, None)

        # Private methods
        if access is None or access is False:
            return None

        # Public methods
        if access is True:
            return method

        # XXX Remove 'im_func'?
        if access.im_func(self) is True:
            return method

        return None


    def is_admin(self):
        return get_context().root.is_in_role('admins')


##    def is_reviewer(self):
##        return get_context().root.is_in_role('reviewers')


    def is_authenticated(self):
        return get_context().user is not None


    def get_workplace(self):
        from users import User
        from WebSite import WebSite

        user = get_context().user
        # Get the "workplace"
        node = self
        while node is not None:
            if isinstance(node, (WebSite, User)):
                return node
            node = node.parent

        # We never should reach here (XXX Raise an exception?)
        return None


    def is_allowed_to_view(self):
        # Objects with workflow
        from workflow import WorkflowAware
        if isinstance(self, WorkflowAware):
            state = self.workflow_state
            # Anybody can see public objects
            if state == 'public':
                return True

            # Only those who can edit are allowed to see non-public objects
            return self.is_allowed_to_edit()

        # Everybody can see objects without workflow
        return True


    def is_allowed_to_edit(self):
        from users import User

        # Anonymous can touch nothing
        user = get_context().user
        if user is None:
            return False

        # Admins are all powerfull
        if self.is_admin():
            return True

        # Get the "workplace"
        workplace = self.get_workplace()

        # In the user's home, only him (and the admin) is allowed to edit
        if isinstance(workplace, User):
            return workplace.name == user.name

        # Reviewers and Members are allowed to edit
        if workplace.is_in_role('reviewers'):
            return True
        if workplace.is_in_role('members'):
            return True

        return False


    is_allowed_to_add = is_allowed_to_edit
    is_allowed_to_remove = is_allowed_to_edit
    is_allowed_to_copy = is_allowed_to_edit
    is_allowed_to_move = is_allowed_to_edit

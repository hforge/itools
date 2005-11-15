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
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

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


    def is_ingroup(self, name):
        """
        Checks wether the authenticated user is in the given group (e.g.
        admins, reviewers) within the context of this resource.
        """
        context = get_context()

        user = context.user
        if user is None:
            return False

        root = context.root
        users = root.get_handler(name).get_usernames()
        if user.name in users:
            return True

        return False


    def is_admin(self):
        return self.is_ingroup('admins')


    def is_reviewer(self):
        return self.is_ingroup('reviewers')


    def is_authenticated(self):
        return get_context().user is not None


    def is_allowed_to_view(self):
        from workflow import WorkflowAware

        if isinstance(self, WorkflowAware):
            user = get_context().user
            if user is None:
                if self.workflow_state != 'public':
                    return False

        return True


    def is_allowed_to_edit(self):
        from User import User

        context = get_context()

        user = context.user
        if user is None:
            return False

        if self.is_admin():
            return True

        here = self
        while here is not None:
            if isinstance(here, User):
                return here.name == user.name
            here = here.parent

        return True


    is_allowed_to_add = is_allowed_to_edit
    is_allowed_to_remove = is_allowed_to_edit
    is_allowed_to_copy = is_allowed_to_edit
    is_allowed_to_move = is_allowed_to_edit
    is_allowed_to_translate = is_allowed_to_edit



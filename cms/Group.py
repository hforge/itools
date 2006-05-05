# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

##class Group(Folder):

##    class_id = 'group'
##    class_version = '20040625'
##    class_title = u'Group'


##    #######################################################################
##    # Skeleton
##    #######################################################################
##    def get_skeleton(self, users=[]):
##        # Build the users handler manually, as a test (the other option is
##        # to build a handler class just to manage '.users')
##        return {'.users': ListOfUsers(users=users)}


##    #######################################################################
##    # Catalog
##    #######################################################################
##    def get_catalog_indexes(self):
##        document = Folder.get_catalog_indexes(self)
##        document['is_group'] = True
##        document['usernames'] = self.get_usernames()
##        return document


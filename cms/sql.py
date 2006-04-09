# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools.handlers.config import Config
from itools.stl.stl import stl
from text import Text
from registry import register_object_class

# Import other modules
try:
    import MySQLdb as mysql
except ImportError:
    mysql = None



class MySQL(Text, Config):

    class_id = 'mysql'
    class_title = u'MySQL Database'
    class_description = u'...'


    def get_skeleton(self, database=None):
        return 'database = %s' % database


    #########################################################################
    # User Interface
    #########################################################################
    def view(self, context):
        if mysql is None:
            message = u'The Python package MySQLdb is not installed.'
            return self.gettext(message)

        namespace = {}

        database = self.get_value('database')
        database = mysql.connect(db=database)
        cursor = database.cursor()
        cursor.execute('show tables')
        namespace['objects'] = [ x[0] for x in cursor.fetchall() ]

        handler = self.get_object('/ui/Database_view.xml')
        return stl(handler, namespace)


register_object_class(MySQL)

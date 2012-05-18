# -*- coding: UTF-8 -*-
# Copyright (C) 2006, 2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2008 David Versmisse <versmisse@lil.univ-littoral.fr>
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
# along with this program; if not, write to the:
# Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA

# Import from the Standard Library
import calendar
import datetime

# Import from itools
from itools.handlers import RWDatabase
from itools.loop import Loop
from itools.uri import get_reference
from itools.web import WebServer, RootResource, Resource, BaseView


class CalendarView(BaseView):
    access = True
    def GET(self, resource, context):
        month = int(resource.name)
        year = int(resource.parent.name)
        cal = calendar.month(year, month)
        context.set_content_type('text/html')
        return "<html><body><h2><pre>%s</pre></h2></body></html>" % cal

class Month(Resource):
    view_calendar = CalendarView()


class Year(Resource):
    def _get_resource(self, name):
        # Check the name is a valid month number
        try:
            month = int(name)
        except ValueError:
            raise LookupError
        if month < 1 or month > 12:
            raise LookupError
        return Month()


class RootView(BaseView):
    access = True
    def GET(self, resource, context):
        today = datetime.date.today()
        path = today.strftime('%Y/%m/;view_calendar')
        return get_reference(path)

class MyRoot(RootResource):
    default_view_name = 'root_view'
    root_view = RootView()

    def _get_resource(self, name):
        # Check the name is a valid year number
        try:
            year = int(name)
        except ValueError:
            raise LookupError
        if year < 1 or year > 9999:
            raise LookupError
        return Year()


if __name__ == '__main__':
    root = MyRoot()
    server = WebServer(root)
    server.listen('localhost', 8080)
    server.database = RWDatabase()
    loop = Loop()
    loop.run()


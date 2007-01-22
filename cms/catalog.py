# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
from datetime import datetime

# Import from itools
from itools.uri import Path
from itools import vfs
from workflow import WorkflowAware



class CatalogAware(object):

    def get_catalog_indexes(self):
        from access import RoleAware
        from File import File

        name = self.name
        abspath = self.get_abspath()
        get_property = self.get_metadata().get_property
        title = get_property('dc:title')

        mtime = self.timestamp
        if mtime is None:
            mtime = datetime.now()

        document = {
            'name': name,
            'abspath': abspath,
            'format': get_property('format'),
            'title': title,
            'text': self.to_text(),
            'owner': get_property('owner'),
            'title_or_name': title or name,
            'mtime': mtime.strftime('%Y%m%d%H%M%S'),
            }

        # Parent path
        parent = self.parent
        if parent is not None:
            if parent.parent is None:
                document['parent_path'] = '/'
            else:
                document['parent_path'] = parent.get_abspath()

        # All paths
        abspath = Path(abspath)
        document['paths'] = [ abspath[:x] for x in range(len(abspath) + 1) ]

        # Size
        if isinstance(self, File):
            size = len(self.to_str())
            # This will stop working for files bigger than 10G bytes
            document['size'] = 'X%010d' % size
        else:
            names = [ x for x in self.get_handler_names()
                      if (x[0] != '.' and x[-9:] != '.metadata') ]
            size = len(names)
            # This will stop working for folders with more than 10G objects
            document['size'] = '%10d' % size

        # Workflow state
        if isinstance(self, WorkflowAware):
            document['workflow_state'] = self.get_workflow_state()

        # Role Aware
        if isinstance(self, RoleAware):
            document['is_role_aware'] = True
            document['members'] = self.get_members()

        return document

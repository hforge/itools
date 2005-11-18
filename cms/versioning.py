# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the Standard Library
from time import time, mktime
import warnings

# Import from itools
from itools.handlers.Folder import Folder
from itools.xml.stl import stl
from itools.web.exceptions import UserError

# Import from iKaaro
from Handler import Handler
from utils import comeback



class VersioningAware(object):

    def new_archive_id(self):
        from Root import Root

        parent = self.parent
        if isinstance(parent, Root):
            id = '%s/%s' % (self.name, time())
        else:
            id = '%s/%s/%s' % (parent.abspath[1:], self.name, time())
        return id


    def set_archive_id(self, id=None):
        if id is None:
            id = self.new_archive_id()
        self.metadata.set_property('id', id)


    def get_archive_id(self):
        return self.metadata.get_property('id')


    def add_to_archive(self):
        archive = self.get_root().get_handler('.archive')

        archive_id = self.get_archive_id()
        if archive_id is None:
            archive_id = self.new_archive_id()
            self.set_archive_id(archive_id)

        path = archive_id.split('/')
        for i in range(len(path)):
            x = '/'.join(path[:i+1])
            if not archive.has_handler(x):
                archive.set_handler(x, Folder())
        archive.get_handler(archive_id).set_handler(path[-1], self)


    def commit_revision(self):
        # Add folders to archived file (XXX)
        archive_id = self.get_archive_id()
        if archive_id is None:
            # XXX Better to be logged
            warnings.warn('Resource %s, Metadata lacks the property "id"'
                          % self.abspath)
            return

        archive = self.get_root().get_handler('.archive')
        path = archive_id.split('/')
        for i in range(len(path)):
            x = '/'.join(path[:i+1])
            if not archive.has_handler(x):
                archive.set_handler(x, Folder())
        # Store revision in the archive
        revisions = archive.get_handler(archive_id)
        seconds_since_the_epoch = mktime(self.mtime.timetuple())
        revision_name = str(seconds_since_the_epoch)
        while revisions.resource.has_resource(revision_name):
            seconds_since_the_epoch += 0.1
            revision_name = str(seconds_since_the_epoch)
        revisions.set_handler(revision_name, self)


    #########################################################################
    # User Interface
    #########################################################################
    def get_views(self):
        return ['history_form']


    #######################################################################
    # History
    history_form__access__ = Handler.is_allowed_to_edit
    history_form__label__ = u'History'
    def history_form(self):
        namespace = {}
        # Revisions
        root = self.get_root()
        archive_id = self.get_archive_id()
        archive = root.get_handler('.archive').get_handler(archive_id)
        revisions = archive.resource.get_resource_names()
        revisions = [ (name, archive.resource.get_resource(name))
                      for name in sorted(revisions, reverse=True) ]
        revisions = [{'name': name,
                      'date': revision.get_mtime().strftime('%Y/%m/%d %H:%M:%S'),
                      'username': '', # XXX revision.username,
                      'action': '-',
                      'size': revision.get_size()}
                     for name, revision in revisions ]
        namespace['revisions'] = revisions
        # Compare
        namespace['compare'] = hasattr(self, 'compare')

        handler = self.get_handler('/ui/File_history.xml')
        return stl(handler, namespace)


    copy_to_present__access__ = Handler.is_allowed_to_edit
    def copy_to_present(self, names=[], **kw):
        if len(names) != 1:
            message = u'You must select one and only one revision.'
            raise UserError, self.gettext(message)
                  

        archive = self.get_root().get_handler('.archive')
        revisions = archive.get_handler(self.get_archive_id())
        revision = revisions.get_handler(names[0])
        self.load_state(revision.resource)

        message = self.gettext(u'Revision copied to present.')
        comeback(message)

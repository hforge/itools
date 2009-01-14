# -*- coding: UTF-8 -*-
# Copyright (C) 2009 David Versmisse <david.versmisse@itaapy.com>
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

# Import from the Standard Library
from urllib import quote

# Local import
from folder import Folder

# Import from gio
from gio import File, MountOperation

# Import from glib
from glib import MainLoop



class Archive(Folder):

    def __init__(self, g_file):
        self._folder = None

        # Make the archive uri
        uri = g_file.get_uri()
        uri = 'archive://' + quote(uri, '')

        # Mount the archive
        g_file = File(uri)
        mount_operation = MountOperation()
        mount_operation.set_anonymous(True)
        g_file.mount_enclosing_volume(mount_operation, self._mount_end)

        # Wait
        self._loop = MainLoop()
        self._loop.run()


#    def __del__(self):
#        # Umount the archive
#        self.unmount()


    ############################
    # Private API
    ############################
    def _mount_end(self, g_file, result):
        if g_file.mount_enclosing_volume_finish(result):
            self._folder = g_file
        self._loop.quit()


    def _unmount_end(self, g_mount, result):
        g_mount.unmount_finish(result)
        self._folder = None
        self._loop.quit()


    ############################
    # Public API
    ############################
    def unmount(self):
        # Unmount the archive
        if self._folder is not None:
            g_mount = self._folder.find_enclosing_mount()
            g_mount.unmount(self._unmount_end)

        # Wait
        self._loop.run()


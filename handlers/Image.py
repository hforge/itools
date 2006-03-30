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

# Import from the Standard Library
from StringIO import StringIO

# Import from the Python Image Library
try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None

# Import from itools
from File import File


class Image(File):

    class_mimetypes = ['image/*']


    def _load_state(self, resource):
        state = self.state
        state.data = None
        state.width = None
        state.height = None


    #########################################################################
    # API
    #########################################################################
    def _load_size(self):
        state = self.state
        state.width = 0
        state.height = 0

        if PILImage is None:
            return

        data = self.to_str()
        f = StringIO(data)
        try:
            im = PILImage.open(f)
        except IOError:
            pass
        else:
            state.width, state.height = im.size


    def get_width(self):
        state = self.state
        if state.width is None:
            self._load_size()

        return state.width


    def get_height(self):
        state = self.state
        if state.height is None:
            self._load_size()

        return state.height


    def get_thumbnail(self, width, height):
        if PILImage is None:
            return None

        data = self.to_str()
        state_width = self.get_width()
        state_height = self.get_height()
        f = StringIO(data)
        im = PILImage.open(f)

        if state_width > width or state_height > height:
            # XXX Improve the quality of the thumbnails by cropping? The
            # only problem would be the loss of information.
            im.thumbnail((width, height), PILImage.ANTIALIAS)
            thumbnail = StringIO()
            im.save(thumbnail, im.format)
            data = thumbnail.getvalue()
            thumbnail.close()

        return data, im.format


File.register_handler_class(Image)

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
from itools.handlers.registry import register_handler_class


class Image(File):

    class_mimetypes = ['image']


    def _load_state(self, resource):
        state = self.state
        # Data
        data = resource.read()
        state.data = data
        # Size
        state.size = 0, 0
        if PILImage is not None:
            f = StringIO(data)
            try:
                im = PILImage.open(f)
            except IOError:
                pass
            else:
                state.size = im.size
        # Thumbnails
        state.thumbnails = {}


    #########################################################################
    # API
    #########################################################################
    def get_size(self):
        return self.state.size


    def get_thumbnail(self, width, height):
        if PILImage is None:
            return None, None

        # Check the cache
        thumbnails = self.state.thumbnails
        key = (width, height)
        if key in thumbnails:
            return thumbnails[key]

        # Build the PIL object
        data = self.to_str()
        f = StringIO(data)
        im = PILImage.open(f)

        # Create the thumbnail if needed
        state_width, state_height = self.get_size()
        if state_width > width or state_height > height:
            # XXX Improve the quality of the thumbnails by cropping? The
            # only problem would be the loss of information.
            im.thumbnail((width, height), PILImage.ANTIALIAS)
            thumbnail = StringIO()
            im.save(thumbnail, im.format)
            data = thumbnail.getvalue()
            thumbnail.close()
        else:
            data = self.to_str()

        # Store in the cache and return
        thumbnails[key] = data, im.format
        return data, im.format


register_handler_class(Image)

# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
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
from cStringIO import StringIO

# Import from the Python Image Library
try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None

# Import from itools
from file import File
from registry import register_handler_class


class Image(File):

    class_mimetypes = ['image']


    def _load_state_from_file(self, file):
        self.data = file.read()

        # The size, a tuple with the width and height, or None if PIL is not
        # installed.
        if PILImage is None:
            self.size = None
        else:
            f = StringIO(self.data)
            try:
                im = PILImage.open(f)
            except IOError:
                self.size = 0, 0
            else:
                self.size = im.size

        # A cache for thumbnails, where the key is the size and the
        # value is the thumbnail.
        self.thumbnails = {}


    #########################################################################
    # API
    #########################################################################
    def get_size(self):
        return self.size


    def get_thumbnail(self, width, height, format="jpeg"):
        if PILImage is None:
            return None, None

        # Check the cache
        thumbnails = self.thumbnails
        key = (width, height)
        if key in thumbnails:
            return thumbnails[key]

        # Build the PIL object
        data = self.to_str()
        f = StringIO(data)
        try:
            im = PILImage.open(f)
        except IOError:
            return None, None

        # Create the thumbnail if needed
        state_width, state_height = self.size
        if state_width > width or state_height > height:
            # TODO Improve the quality of the thumbnails by cropping?
            # The only problem would be the loss of information.
            try:
                im.thumbnail((width, height), PILImage.ANTIALIAS)
            except IOError:
                # PIL does not support interlaced PNG files, raises IOError
                return None, None
            else:
                thumbnail = StringIO()
                im.save(thumbnail, format.upper(), quality=80)
                data = thumbnail.getvalue()
                thumbnail.close()
        else:
            data = self.to_str()

        # Store in the cache and return
        thumbnails[key] = data, format.lower()
        return data, format.lower()


register_handler_class(Image)

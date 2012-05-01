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
            self.size = 0, 0
        else:
            f = StringIO(self.data)
            try:
                im = PILImage.open(f)
            except (IOError, OverflowError):
                self.size = 0, 0
            else:
                self.size = im.size

        # A cache for thumbnails, where the key is the size and the format,
        # and the value is the thumbnail.
        self.thumbnails = {}


    def _get_handle(self):
        if PILImage is False:
            return None

        # Open image
        f = StringIO(self.data)
        try:
            im = PILImage.open(f)
        except (IOError, OverflowError):
            return None

        # Ok
        return im
    #########################################################################
    # API
    #########################################################################
    def get_size(self):
        return self.size


    def get_thumbnail(self, xnewsize, ynewsize, format=None, fit=False):
        # Get the handle
        handle = self._get_handle()
        if handle is None:
            return None, None
        format = format or handle.format

        # Icon's thumbnail is the icon itself
        if format == 'ICO':
            return self.to_str(), format.lower()

        xsize, ysize = self.size
        xratio, yratio = float(xnewsize)/xsize, float(ynewsize)/ysize
        # Case 1: fit
        if fit:
            # Scale the image so no more than one side overflows
            ratio = max(xratio, yratio)
            im, xsize, ysize = self._scale_down(handle, ratio)

            # Crop the image so none side overflows
            xsize = min(xsize, xnewsize)
            ysize = min(ysize, ynewsize)
            im = im.crop((0, 0, xsize, ysize))

            # Paste the image into a background so it fits the target size
            if xsize < xnewsize or ysize < xnewsize:
                newsize = (xnewsize, ynewsize)
                background = PILImage.new('RGBA', newsize, (255, 255, 255, 0))
                x = (xnewsize - xsize) / 2
                y = (ynewsize - ysize) / 2
                background.paste(im, (x, y))
                im = background

        # Case 2: thumbnail
        else:
            # Scale the image so none side overflows
            ratio = min(xratio, yratio)
            im, xsize, ysize = self._scale_down(handle, ratio)

        # To string
        output = StringIO()
        im.save(output, format, quality=80)
        value = output.getvalue()
        output.close()

        # Ok
        return value, format.lower()


    def _scale_down(self, im, ratio):
        # Convert to RGBA
        im = im.convert("RGBA")

        # Scale
        xsize, ysize = self.size
        if ratio < 1.0:
            xsize, ysize = int(xsize * ratio), int(ysize * ratio)
            im = im.resize((xsize, ysize), PILImage.ANTIALIAS)

        return im, xsize, ysize


register_handler_class(Image)

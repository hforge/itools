# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2008, 2010-2012 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2007 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2008 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2011 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2011 Nicolas Deram <nderam@gmail.com>
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
from io import BytesIO

# Import from the Python Image Library
try:
    from PIL.Image import frombuffer, new as new_image, open as open_image
    from PIL.Image import ANTIALIAS
except ImportError:
    PIL = False
else:
    PIL = True

# Import from rsvg
try:
    from cairo import Context, ImageSurface, FORMAT_ARGB32
    from rsvg import Handle as rsvg_handle
except ImportError:
    rsvg_handle = None

# Import from itools
from .file import File
from .registry import register_handler_class


# This number controls the max surface ratio that we can lose when we crop.
MAX_CROP_RATIO = 2.0


class Image(File):

    class_mimetypes = ['image']

    def _load_state_from_file(self, file):
        self.data = file.read()

        # Size
        handle = self._get_handle()
        if handle:
            self.size = self._get_size(handle)
        else:
            self.size = (0, 0)

    def _get_handle(self):
        if PIL is False:
            return None

        # Open image
        f = BytesIO(self.data)
        try:
            im = open_image(f)
        except (IOError, OverflowError):
            return None

        # Ok
        return im

    def _get_size(self, handle):
        return handle.size

    def _get_format(self, handle):
        return handle.format

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
        format = format or self._get_format(handle)

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
                background = new_image('RGBA', newsize, (255, 255, 255, 0))
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
        output = BytesIO()
        # JPEG : Convert to RGB
        if format.lower() in ("jpeg", "mpo"):
            im = im.convert("RGB")
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
            im = im.resize((xsize, ysize), ANTIALIAS)

        return im, xsize, ysize


class SVGFile(Image):

    class_mimetypes = ['image/svg+xml']

    def _get_handle(self):
        if rsvg_handle is None:
            return None

        data = self.to_str()
        svg = rsvg_handle()
        svg.write(data)
        svg.close()
        return svg

    def _get_size(self, handle):
        return handle.get_property('width'), handle.get_property('height')

    def _get_format(self, handle):
        return 'PNG'

    def _scale_down(self, handle, ratio):
        xsize, ysize = self.size
        if ratio >= 1.0:
            # Convert
            surface = ImageSurface(FORMAT_ARGB32, xsize, ysize)
            ctx = Context(surface)
        else:
            # Scale
            xsize, ysize = int(xsize * ratio), int(ysize * ratio)
            surface = ImageSurface(FORMAT_ARGB32, xsize, ysize)
            ctx = Context(surface)
            ctx.scale(ratio, ratio)

        # Render
        handle.render_cairo(ctx)

        # Transform to a PIL image for further manipulation
        size = (xsize, ysize)
        im = frombuffer('RGBA', size, surface.get_data(), 'raw', 'BGRA', 0, 1)
        surface.finish()

        return im, xsize, ysize


register_handler_class(Image)
register_handler_class(SVGFile)

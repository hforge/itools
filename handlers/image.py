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

# Import from pygtk
try:
    from gtk.gdk import INTERP_BILINEAR, Pixbuf, pixbuf_new_from_stream
    from gio import memory_input_stream_new_from_data
except ImportError:
    gdk = False
else:
    gdk = True

# Import from rsvg
try:
    from cairo import Context, ImageSurface, FORMAT_ARGB32
    from rsvg import Handle as rsvg_handle
except ImportError:
    rsvg_handle = None

# Import from itools
from file import File
from registry import register_handler_class


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
            self.img_format = self._get_format(handle)
        else:
            self.size = (0, 0)
            self.img_format = self._get_format(handle)


    def _get_handle(self):
        if gdk is False:
            return None

        # Load image
        stream = memory_input_stream_new_from_data(self.data)
        return pixbuf_new_from_stream(stream)


    def _get_size(self, handle):
        return handle.get_width(), handle.get_height()


    def _get_format(self, handle):
        return self.get_mimetype().split('/', 1)[-1]


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

        xsize, ysize = self.size
        xratio, yratio = float(xnewsize)/xsize, float(ynewsize)/ysize
        # Case 1: fit
        if fit:
            # Scale the image so no more than one side overflows
            ratio = max(xratio, yratio)
            pixbuf, xsize, ysize = self._scale_down(handle, ratio)

            # Crop the image so none side overflows
            xsize = min(xsize, xnewsize)
            ysize = min(ysize, ynewsize)
            new_pixbuf = Pixbuf(
                pixbuf.get_colorspace(),
                pixbuf.get_has_alpha(),
                pixbuf.get_bits_per_sample(),
                xnewsize, ynewsize)
            new_pixbuf.fill(0xFFFFFFFF)

            x = (xnewsize - xsize) / 2
            y = (ynewsize - ysize) / 2
            pixbuf.composite(
                new_pixbuf,
                x, y,                  # destination coordinates
                xsize, ysize,
                0, 0,                  # offset: upper-left corner
                1, 1, INTERP_BILINEAR, # do not scale
                255)                   # alpha: 0-255
            pixbuf = new_pixbuf

        # Case 2: thumbnail
        else:
            # Scale the image so none side overflows
            ratio = min(xratio, yratio)
            pixbuf, xsize, ysize = self._scale_down(handle, ratio)

        # To string
        output = []
        def save_func(data): output.append(data)
        format = format or self.img_format
        kw = {}
        if format == 'jpeg':
            kw['quality'] = '80'
        pixbuf.save_to_callback(save_func, format, kw)

        # Ok
        return ''.join(output), format


    def _scale_down(self, pixbuf, ratio):
        xsize, ysize = self.size
        if ratio < 1.0:
            xsize, ysize = int(xsize * ratio), int(ysize * ratio)
            pixbuf = pixbuf.scale_simple(xsize, ysize, INTERP_BILINEAR)

        return pixbuf, xsize, ysize



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
        return 'png'


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

        # Transform to a pixbuf for further manipulation
#        size = (xsize, ysize)
#        im = frombuffer('RGBA', size, surface.get_data(), 'raw', 'BGRA', 0, 1)
        surface.finish()

        return pixbuf, xsize, ysize



register_handler_class(Image)
register_handler_class(SVGFile)

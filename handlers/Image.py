# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA

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

        data = resource.read()
        state.data = data

        state.width = state.height = 0
        if PILImage is not None:
            f = StringIO(data)
            try:
                im = PILImage.open(f)
            except IOError:
                pass
            else:
                state.width, state.height = im.size

    #########################################################################
    # API
    #########################################################################
    def get_width(self):
        return self.state.width


    def get_height(self):
        return self.state.height


    def get_thumbnail(self, width, height):
        if PILImage is None:
            return None

        data = self.to_str()
        file = StringIO(data)
        im = PILImage.open(file)
        if self.state.width > width or self.state.height > height:
            im.thumbnail((width, height))
            thumbnail = StringIO()
            im.save(thumbnail, im.format)
            data = thumbnail.getvalue()
            thumbnail.close()

        return data, im.format


File.register_handler_class(Image)

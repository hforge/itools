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

# Import from itools
from itools.handlers.Image import Image as iImage
from itools.stl import stl

# Import from ikaaro
from File import File
from registry import register_object_class


class Image(File, iImage):

    class_id = 'image'
    class_title = u'Image'
    class_version = '20040625'
    class_icon16 = 'images/Image16.png'


    # XXX Temporal, until icon's API is fixed
    def icons_path(self):
        return ';icon48?width=144&height=144'


    #######################################################################
    # User interface
    #######################################################################
    icon48__access__ = True
    def icon48(self, context):
        width = context.get_form_value('width')
        height = context.get_form_value('height')

        width, height = int(width), int(height)

        if not hasattr(self, '_icon'):
            self._icon = {}

        if (width, height) not in self._icon:
            thumbnail = self.get_thumbnail(width, height)
            if thumbnail is None:
                data = self.get_handler('/ui/images/Image48.png').to_str()
                self._icon[(width, height)] = data, 'png'
            else:
                self._icon[(width, height)] = thumbnail

        data, format = self._icon[(width, height)]
        response = context.response
        response.set_header('Content-Type', 'image/%s' % format)
        return data


    def get_views(self):
        return ['view', 'externaledit', 'edit_metadata_form']


    #######################################################################
    # View
    view__access__ = 'is_allowed_to_view'
    view__label__ = u'View'
    view__sublabel__ = u'View'
    def view(self, context):
        handler = self.get_handler('/ui/Image_view.xml')
        return handler.to_str()


register_object_class(Image)



class Video(File):

    class_id = 'video'
    class_title = u'Video'
    class_description = u'Video'
    class_icon48 = 'images/Flash48.png'
    class_icon16 = 'images/Flash16.png'


    view__access__ = 'is_allowed_to_view'
    view__label__ = u'View'
    view__sublabel__ = u'View'
    def view(self):
        namespace = {}
        namespace['format'] = self.get_mimetype()

        handler = self.get_handler('/ui/Video_view.xml')
        return stl(handler, namespace)


register_object_class(Video)

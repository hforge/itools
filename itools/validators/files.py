# -*- coding: UTF-8 -*-
# Copyright (C) 2016 Sylvain Taverne <sylvain@agicia.com>
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

# Import from standard library
from io import StringIO

# Import from PIL
from PIL import Image as PILImage

# Import from itools
from itools.gettext import MSG

# Import from here
from .base import BaseValidator
from .exceptions import ValidationError


class FileExtensionValidator(BaseValidator):

    validator_id = 'file-extension'
    allowed_extensions = []
    errors = {'invalid_extension': MSG(
            "File extension '{extension}' is not allowed. "
            "Allowed extensions are: '{allowed_extensions}'.")}

    def check(self, value):
        extension = self.get_extension(value)
        if extension not in self.allowed_extensions:
            kw = {'extension': extension,
                  'allowed_extensions': ','.join(self.allowed_extensions)}
            self.raise_default_error(kw)

    def get_extension(self, value):
        filename, mimetype, body = value
        return filename.split('.')[-1]


class ImageExtensionValidator(FileExtensionValidator):

    validator_id = 'image-extension'
    allowed_extensions = ['jpeg', 'png', 'gif']


class MimetypesValidator(BaseValidator):

    validator_id = 'file-mimetypes'
    allowed_mimetypes = []
    errors = {'bad_mimetype': MSG(
            "File mimetype '{mimetype}' is not allowed. "
            "Allowed mimetypes are: '{allowed_mimetypes}'.")}


    def check(self, value):
        filename, mimetype, body = value
        if mimetype not in self.allowed_mimetypes:
            kw = {'mimetype': mimetype,
                  'allowed_mimetypes': ','.join(self.allowed_mimetypes)}
            self.raise_default_error(kw)


class ImageMimetypesValidator(MimetypesValidator):

    validator_id = 'image-mimetypes'
    allowed_mimetypes = ['image/jpeg', 'image/png', 'image/gif']


class FileSizeValidator(BaseValidator):

    validator_id = 'file-size'
    max_size = 1024*1024*10
    errors = {'too_big': MSG(u'Your file is too big. ({size})')}

    def check(self, value):
        filename, mimetype, body = value
        size = len(body)
        if size > self.max_size:
            kw = {'size': self.pretty_bytes(size),
                  'max_size': self.pretty_bytes(self.max_size)}
            self.raise_default_error(kw)

    def pretty_bytes(self, b):
        # 1 Byte = 8 Bits
        # 1 Kilobyte = 1024 Bytes
        # 1 Megabyte = 1048576 Bytes
        # 1 Gigabyte = 1073741824 Bytes
        if b < 1024:
            return u'%.01f Bytes' % b
        elif b < 1048576:
            return u'%.01f KB' % (b / 1024)
        elif b < 1073741824:
            return u'%.01f MB' % (b / 1048576)
        return u'%.01f GB' % (b / 1073741824)


class ImagePixelsValidator(BaseValidator):

    validator_id = 'image-pixels'
    max_pixels = 2000*2000

    errors = {'too_much_pixels': MSG("Image is too big."),
              'image_has_errors': MSG("Image contains errors.")}

    def check(self, value):
        filename, mimetype, body = value
        data = StringIO(body)
        try:
            im = PILImage.open(data)
            im.verify()
        except Exception:
            code = 'image_has_errors'
            raise ValidationError(self.errors[code], code, {})
        if im.width * im.height > self.max_pixels:
            code = 'too_much_pixels'
            raise ValidationError(self.errors[code], code, {})

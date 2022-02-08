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

# Import from the Standard Library
from unittest import TestCase, main

# Import from itools
from itools.validators import validator


class ValidatorsTestCase(TestCase):

    def test_hexadecimal(self):
        v = validator('hexadecimal')
        self.assertEqual(True, v.is_valid('#000000'))

    def test_equals(self):
        v = validator('equals-to', base_value=2)
        self.assertEqual(True, v.is_valid(2))
        self.assertEqual(False, v.is_valid(3))

    def test_integer_positive(self):
        v = validator('integer-positive')
        self.assertEqual(True, v.is_valid(0))
        self.assertEqual(True, v.is_valid(2))
        self.assertEqual(False, v.is_valid(-1))

    def test_integer_positive_not_null(self):
        v = validator('integer-positive-not-null')
        self.assertEqual(True, v.is_valid(2))
        self.assertEqual(False, v.is_valid(-1))
        self.assertEqual(False, v.is_valid(0))

    def test_image_mimetypes(self):
        v = validator('image-mimetypes')
        image1 = 'image.png', 'image/png', None
        image2 = 'image.png', 'application/xml', None
        self.assertEqual(True, v.is_valid(image1))
        self.assertEqual(False, v.is_valid(image2))


if __name__ == '__main__':
    main()

# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from itools
from file import File
from registry import register_handler_class


def guess_encoding(data):
    """Tries to guess the encoding by brute force. It is likely to get
    the wrong encoding, for example many utf8 files will be identified
    as latin1.
    """
    for encoding in ('ascii', 'utf8', 'iso8859'):
        try:
            unicode(data, encoding)
        except UnicodeError:
            pass
        else:
            return encoding

    # Default to UTF-8
    return 'utf8'


class TextFile(File):

    class_mimetypes = ['text']
    class_extension = 'txt'


    def new(self, data=u''):
        self.data = data
        self.encoding = 'utf-8'


    def _load_state_from_file(self, file):
        data = file.read()
        self.encoding = guess_encoding(data)
        self.data = unicode(data, self.encoding)


    #########################################################################
    # API
    #########################################################################
    def get_encoding(self):
        return self.encoding


    def to_str(self, encoding='utf-8'):
        return self.data.encode(encoding)


    def to_text(self):
        return unicode(self.to_str(), 'utf-8')


    def is_empty(self):
        return self.to_text().strip() == u""



register_handler_class(TextFile)

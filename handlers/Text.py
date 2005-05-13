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

# Import from itools
from File import File


class Text(File):

    class_mimetypes = ['text/*']
    class_extension = 'txt'


    #########################################################################
    # Load
    #########################################################################
    def _load_state(self, resource):
        state = self.state
        data = resource.read()
        state.encoding = self.guess_encoding(data)
        state.data = unicode(data, state.encoding)


    def guess_encoding(cls, data):
        """
        Tries to guess the encoding by brute force. It is likely to get
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

    guess_encoding = classmethod(guess_encoding)


    def guess_language(self):
        """
        XXX Now it does nothing, sometime in the future it will try to guess
        the language of the data.
        """


    #########################################################################
    # API
    #########################################################################
    def get_encoding(self):
        return self.state.encoding


    def to_unicode(self, encoding='UTF-8'):
        return self.state.data


    def to_str(self, encoding='UTF-8'):
        # XXX Maybe the default behaviour should be to use the original
        # encoding, but for now I prefer utf8, because we live in a
        # multilingual world.

        # Warning!! Some files (XML, PO, etc.) store the encoding information
        # within the document. For them this method should change that
        # information to the given encoding.
        return self.to_unicode(encoding).encode(encoding)


File.register_handler_class(Text)

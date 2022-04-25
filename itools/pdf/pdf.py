# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2007 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2009 Hervé Cauwelier <herve@oursours.net>
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
from itools.handlers import register_handler_class, File
try:
    from pdftotext import pdf_to_text
except ImportError:
    pdf_to_text = None


class PDFFile(File):

    class_mimetypes = ['application/pdf']
    class_extension = 'pdf'

    def to_text(self):
        if pdf_to_text is None:
            return ""
        return pdf_to_text(self.to_str())


register_handler_class(PDFFile)

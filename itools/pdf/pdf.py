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

try:
    import poppler
except ImportError:
    poppler = None

# Import from itools
from itools.handlers import register_handler_class, File


def pdf_to_text(data):
    document = poppler.load_from_data(data)

    text = []
    for i in range(document.pages):
        page = document.create_page(i)
        text.append(page.text())

    return '\f'.join(text)

class PDFFile(File):

    class_mimetypes = ['application/pdf']
    class_extension = 'pdf'

    def to_text(self):
        if poppler is None:
            return ""

        data = self.to_str()
        return pdf_to_text(data)


register_handler_class(PDFFile)

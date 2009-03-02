# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
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

# Import other modules
try:
    from xlrd import open_workbook
except ImportError:
    open_workbook = None

# Import from itools
from itools.handlers import File, register_handler_class
from rtf import rtf_to_text
try:
    from doctotext import doc_to_text, DocRtfException
except ImportError:
    doc_to_text = None



class MSWord(File):
    class_mimetypes = ['application/msword']
    class_extension = 'doc'


    def to_text(self):
        if doc_to_text is None:
            return u""
        data = self.to_str()
        try:
            return doc_to_text(data)
        except DocRtfException:
            return rtf_to_text(data)



class MSExcel(File):
    class_mimetypes = ['application/vnd.ms-excel']
    class_extension = 'xls'


    def to_text(self):
        if open_workbook is None:
            return u""

        data = self.to_str()

        # Load the XLRD file
        # XXX This is slow (try 'print book.load_time_stage_2')
        book = open_workbook(file_contents=data)

        # Get the text
        text = []
        for sheet in book.sheets():
            for idx in range(sheet.nrows):
                for value in sheet.row_values(idx):
                    if type(value) is not unicode:
                        try:
                            value = unicode(value)
                        except UnicodeError:
                            continue
                    text.append(value)
        return u' '.join(text)




# Register
register_handler_class(MSWord)
register_handler_class(MSExcel)

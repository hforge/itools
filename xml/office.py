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

# Import from the Standard Library
from os.path import join as join_path
from subprocess import Popen, PIPE
from tempfile import mkdtemp

# Import other modules
from xlrd import open_workbook

# Import from itools
from itools import vfs
from itools.handlers import File, register_handler_class
from indexer import xml_to_text


class ConversionError(Exception):
    pass



def convert(handler, cmdline, use_outfile=False):
    # We may need a temporary folder (for the input and/or the output)
    uri = handler.uri
    if (uri.scheme != 'file') or (handler.dirty is not None) or (use_outfile):
        path = mkdtemp('itools')
    else:
        path = None

    # We may need to write the handler to a temporary file
    if uri.scheme == 'file' and handler.dirty is None:
        infile_path = str(uri.path)
    else:
        infile_path = join_path(path, 'infile')
        with open(infile_path, 'wb') as infile:
            infile.write(handler.to_str())

    # We may need to write the output to a file
    if use_outfile is True:
        outfile_path = join_path(path, 'outfile')
        cmdline = cmdline % (infile_path, outfile_path)
    else:
        cmdline = cmdline % infile_path

    # Call, and read stdout and stderr
    popen = Popen(cmdline.split(), stdout=PIPE, stderr=PIPE)
    stdout, stderr = popen.communicate()

    if use_outfile is True:
        try:
            outfile = open(outfile_path)
        except IOError, e:
            raise ConversionError, stderr or stdout or str(e)
        else:
            stdout = outfile.read()
            outfile.close()

    # Clean temporary folder if needed
    if path is not None:
        vfs.remove(path)

    # Ok
    if stderr:
        return ''
    return stdout



class ExternalIndexer(File):
    source_encoding = 'UTF-8'


    def to_text(self, use_outfile=False):
        stdout = convert(self, self.source_converter, use_outfile)
        return unicode(stdout, self.source_encoding, 'replace')



class MSWord(ExternalIndexer):
    class_mimetypes = ['application/msword']
    class_extension = 'doc'
    source_converter = 'wvText %s %s'


    def to_text(self):
        return ExternalIndexer.to_text(self, use_outfile=True)



class MSExcel(File):
    class_mimetypes = ['application/vnd.ms-excel']
    class_extension = 'xls'


    def to_text(self):
        data = self.to_str()

        # Load the XLRD file
        # XXX This is slow (try 'print book.load_time_stage_2')
        book = open_workbook(file_contents=data)

        # Get the text
        text = []
        for sheet in book.sheets():
            for idx in range(sheet.nrows):
                for value in sheet.row_values(idx):
                    if not isinstance(value, unicode):
                        try:
                            value = unicode(value)
                        except UnicodeError:
                            continue
                    text.append(value)
        return u' '.join(text)



class MSPowerPoint(ExternalIndexer):
    class_mimetypes = ['application/vnd.ms-powerpoint']
    class_extension = 'ppt'
    source_converter = 'ppthtml %s'


    def to_text(self):
        stdout = convert(self, self.source_converter)
        return xml_to_text(stdout)



class RTF(ExternalIndexer):
    class_mimetypes = ['text/rtf']
    class_extenstion = 'rtf'
    source_encoding = 'ISO-8859-1'
    source_converter = 'unrtf --text --nopict %s'


    def to_text(self):
        text = ExternalIndexer.to_text(self)
        words = text.split()
        # Filter noise by unrtf
        words = [word for word in words if len(word) < 100]
        return u' '.join(words)


handlers = [MSWord, MSExcel, MSPowerPoint, RTF]
for handler in handlers:
    register_handler_class(handler)

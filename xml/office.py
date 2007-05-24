# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
#               2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
from cStringIO import StringIO
import mimetypes
from os.path import join as path_join
from subprocess import call
import tempfile
from zipfile import ZipFile, BadZipfile

# Import from itools
from itools import vfs
from itools.handlers import File, register_handler_class
from indexer import xml_to_text



def convert(handler, cmdline, outfile=None):
    cmdline = cmdline % 'stdin'

    # Serialize the handler to a temporary file in the file system
    path = tempfile.mkdtemp('itools')
    file_path = path_join(path, 'stdin')
    open(file_path, 'w').write(handler.to_str())

    # stdout & stderr
    stdout_path = path_join(path, 'stdout')
    stdout = open(stdout_path, 'w')
    stderr_path =path_join(path, 'stderr')
    stderr = open(stderr_path, 'w')

    # Call convert method
    try:
        # XXX do not use pipes, not enough buffer to hold stdout
        call(cmdline.split(), stdout=stdout, stderr=stderr, cwd=path)
    except OSError:
        vfs.remove(path)
        raise

    # Read output
    if outfile is not None:
        stdout_path = path_join(path, outfile)
    try:
        stdout = open(stdout_path).read()
    except IOError:
        vfs.remove(path)
        raise
    stderr = open(stderr_path).read()

    # Remove the temporary files
    vfs.remove(path)

    return stdout, stderr



class OfficeDocument(File):

    source_encoding = 'UTF-8'


    def to_text(self, outfile=None):
        stdout, stderr = convert(self, self.source_converter, outfile)

        if stderr != "":
            return u''

        return unicode(stdout, self.source_encoding, 'replace')



class MSWord(OfficeDocument):

    class_mimetypes = ['application/msword']
    class_extension = 'doc'
    source_converter = 'wvText %s out.txt'


    def to_text(self):
        return OfficeDocument.to_text(self, 'out.txt')



class MSExcel(OfficeDocument):

    class_mimetypes = ['application/vnd.ms-excel']
    class_extension = 'xls'
    source_converter = 'xlhtml -a -fw -nc -nh -te %s'


    def to_text(self):
        stdout, stderr = convert(self, self.source_converter)

        if stderr != "":
            return u''

        return xml_to_text(stdout)



class MSPowerPoint(OfficeDocument):

    class_mimetypes = ['application/vnd.ms-powerpoint']
    class_extension = 'ppt'
    source_converter = 'ppthtml %s'


    def to_text(self):
        stdout, stderr = convert(self, self.source_converter)

        if stderr != "":
            return u''
        
        return xml_to_text(stdout)



class OOffice(OfficeDocument):

    def to_text(self):
        file = StringIO(self.to_str())
        zip = ZipFile(file)
        content = zip.read('content.xml')
        zip.close()

        return xml_to_text(content)



class OOWriter(OOffice):

    class_mimetypes = ['application/vnd.sun.xml.writer',
                       'application/vnd.oasis.opendocument.text']
    class_extension = 'sxw'



class OOCalc(OOffice):

    class_mimetypes = ['application/vnd.sun.xml.calc',
                       'application/vnd.oasis.opendocument.spreadsheet']
    class_extension = 'sxc'



class OOImpress(OOffice):

    class_mimetypes = ['application/vnd.sun.xml.impress',
                       'application/vnd.oasis.opendocument.presentation']
    class_extension = 'sxi'



class PDF(OfficeDocument):

    class_mimetypes = ['application/pdf']
    class_extension = 'pdf'
    source_converter = 'pdftotext -enc UTF-8 -nopgbrk %s -'



class RTF(OfficeDocument):

    class_mimetypes = ['text/rtf']
    class_extenstion = 'rtf'
    source_encoding = 'ISO-8859-1'
    source_converter = 'unrtf --text --nopict %s'


    def to_text(self):
        text = OfficeDocument.to_text(self)
        words = text.split()
        # Filter noise by unrtf
        words = [word for word in words if len(word) < 100]
        return u' '.join(words)


# Register
mimetypes.add_type('application/vnd.sun.xml.writer', '.sxw')
mimetypes.add_type('application/vnd.sun.xml.calc', '.sxc')
mimetypes.add_type('application/vnd.sun.xml.impress', '.sxi')


handlers = [MSWord, MSExcel, MSPowerPoint, OOWriter, OOCalc, OOImpress, PDF,
    RTF]
for handler in handlers:
    register_handler_class(handler)

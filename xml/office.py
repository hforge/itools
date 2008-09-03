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
from subprocess import call
from tempfile import mkdtemp

# Import from itools
from itools import vfs
from itools.handlers import File, register_handler_class
from indexer import xml_to_text


class ConversionError(Exception):
    pass



def convert(handler, cmdline, use_outfile=False):
    path = mkdtemp('itools')
    # Serialize the handler to a temporary file in the file system
    infile_path = join_path(path, 'infile')
    # TODO use "with" ASAP
    infile = open(infile_path, 'wb')
    infile.write(handler.to_str())
    infile.close()
    # stdout
    stdout_path = join_path(path, 'stdout')
    stdout = open(stdout_path, 'wb')
    # stderr
    stderr_path = join_path(path, 'stderr')
    stderr = open(stderr_path, 'wb')
    # output
    if use_outfile is True:
        cmdline = cmdline % ('infile', 'outfile')
    else:
        cmdline = cmdline % 'infile'

    # Call convert method
    # XXX do not use pipes, not enough buffer to hold stdout
    call(cmdline.split(), stdout=stdout, stderr=stderr, cwd=path)
    stdout.close()
    stdout = open(stdout_path)
    standard_output = stdout.read()
    stdout.close()
    stderr.close()
    stderr = open(stderr_path)
    error_output = stderr.read()
    stderr.close()

    if use_outfile is True:
        outfile_path = join_path(path, 'outfile')
        try:
            outfile = open(outfile_path)
            output = outfile.read()
            outfile.close()
        except IOError, e:
            message = error_output or standard_output or str(e)
            raise ConversionError, message

    vfs.remove(path)

    if use_outfile is True:
        return output, error_output
    return standard_output, error_output



class OfficeDocument(File):
    source_encoding = 'UTF-8'


    def to_text(self, use_outfile=False):
        stdout, stderr = convert(self, self.source_converter, use_outfile)
        if stderr != "":
            return u''
        return unicode(stdout, self.source_encoding, 'replace')



class MSWord(OfficeDocument):
    class_mimetypes = ['application/msword']
    class_extension = 'doc'
    source_converter = 'wvText %s %s'


    def to_text(self):
        return OfficeDocument.to_text(self, use_outfile=True)



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


handlers = [MSWord, MSExcel, MSPowerPoint, RTF]
for handler in handlers:
    register_handler_class(handler)

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
from htmlentitydefs import name2codepoint
from os.path import join as join_path
from subprocess import Popen, PIPE
from tempfile import mkdtemp

# Import from itools
from itools.handlers import File, register_handler_class, guess_encoding
from itools import vfs


# Append &apos;, the apostrophe (simple quote) for XML
name2codepoint['apos'] = 39



def xml_to_text(data):
    """A brute-force text extractor for XML and HTML syntax, even broken to
    some extent.

    We don't use itools.xml.parser (yet) because expat would raise an error
    for too many documents.

    The encoding is guessed for each text chunk because 'xlhtml' mixes UTF-8
    and Latin1 encodings, and the most broken converters don't declare the
    encoding at all.

    TODO use the C parser instead with itools 0.15.
    """

    output = []
    # 0 = Default
    # 1 = Start tag
    # 2 = Start text
    # 3 = Char or entity reference
    state = 0
    buffer = ''

    for c in data:
        if state == 0:
            if c == '<':
                state = 1
        elif state == 1:
            if c == '>':
                # Force word separator
                output.append(u' ')
                state = 2
        elif state == 2:
            if c == '<' or c == '&':
                encoding = guess_encoding(buffer)
                output.append(unicode(buffer, encoding, 'replace'))
                buffer = ''
                if c == '<':
                    state = 1
                elif c == '&':
                    state = 3
            else:
                buffer += c
        elif state == 3:
            if c == ';':
                if buffer[0] == '#':
                    output.append(unichr(int(buffer[1:])))
                elif buffer[0] == 'x':
                    output.append(unichr(int(buffer[1:], 16)))
                else:
                    # XXX Assume entity
                    output.append(unichr(name2codepoint.get(buffer, 63))) # '?'
                buffer = ''
                state = 2
            else:
                buffer += c

    return u''.join(output)



###########################################################################
# Handler
###########################################################################
class ExternalIndexer(File):

    def convert(self):
        uri = self.uri
        if uri.scheme == 'file' and self.dirty is None:
            # Case 1: Use directly the handler's path
            cmdline = self.source_converter + [str(uri.path)]
            popen = Popen(cmdline, stdout=PIPE, stderr=PIPE)
            stdout, stderr = popen.communicate()
        else:
            # Case 2: Use a temporary file
            data = self.to_str()
            tmp_folder = mkdtemp('itools')
            try:
                # Write the temporary file
                infile_path = join_path(tmp_folder, 'infile')
                with open(infile_path, 'wb') as infile:
                    infile.write(data)
                # Call, and read stdout and stderr
                cmdline = self.source_converter + [infile_path]
                popen = Popen(cmdline, stdout=PIPE, stderr=PIPE)
                stdout, stderr = popen.communicate()
            finally:
                vfs.remove(tmp_folder)

        # Ok
        if stderr:
            return ''
        return stdout


    def to_text(self):
        stdout = self.convert()
        return unicode(stdout, 'utf-8', 'replace')



class MSPowerPoint(ExternalIndexer):
    class_mimetypes = ['application/vnd.ms-powerpoint']
    class_extension = 'ppt'
    source_converter = ['ppthtml']


    def to_text(self):
        stdout = self.convert()
        return xml_to_text(stdout)



# Register
register_handler_class(MSPowerPoint)

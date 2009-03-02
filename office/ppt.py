# -*- coding: UTF-8 -*-
# Copyright (C) 2004 Alex Ott <alexott@gmail.com>
# Copyright (C) 2006-2009 Hervé Cauwelier <herve@itaapy.com>
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
from cStringIO import StringIO

# Import from itools
from itools.handlers import File, register_handler_class
from ole import SEEK_CUR, getshort, getulong, convert_char, Ole


DOCUMENT                      = 1000
DOCUMENT_END                  = 1002
SLIDE_BASE                    = 1004
SLIDE                         = 1006
NOTES                         = 1008
MAIN_MASTER                   = 1016
LIST                          = 2000
TEXT_CHARS_ATOM               = 4000
TEXT_BYTES_ATOM               = 4008
CSTRING                       = 4026
HEADERS_FOOTERS               = 4057
SLIDE_LIST_WITH_TEXT          = 4080


def process_item(entry, rectype, reclen):
    if rectype in (DOCUMENT, SLIDE, SLIDE_BASE, NOTES,
                     HEADERS_FOOTERS, MAIN_MASTER, LIST,
                     SLIDE_LIST_WITH_TEXT):
        pass
    elif rectype == TEXT_BYTES_ATOM:
        for i in range(reclen):
            buf = entry.read(1)
            if ord(buf) != 0x0d:
                yield convert_char(ord(buf))
            else:
                yield u"\n"
        yield u"\n"
    elif rectype == TEXT_CHARS_ATOM or rectype == CSTRING:
        text_len = reclen / 2
        for i in range(text_len):
            buf = entry.read(2)
            u = getshort(buf, 0)
            if u != 0x0d:
                yield convert_char(u)
            else:
                yield u"\n"
        yield u"\n"
    else:
        entry.seek(reclen, SEEK_CUR)



def do_ppt(entry):
    itemsread = 1

    while itemsread:
        recbuf = entry.read(8)
        itemsread = len(recbuf)
        if entry.is_eof():
            for char in process_item(entry, DOCUMENT_END, 0):
                yield char
            return
        if itemsread < 8:
            break
        rectype = getshort(recbuf, 2)
        reclen = getulong(recbuf, 4)
        if reclen < 0:
            return
        for char in process_item(entry, rectype, reclen):
            yield char



def ppt_to_text(data):
    buffer = []
    file = StringIO(data)
    ole = Ole(file)

    for entry in ole.readdir():
        if entry.open() >= 0:
            if entry.name == 'PowerPoint Document':
                for text in do_ppt(entry):
                    buffer.append(text)
    return u"".join(buffer)



###########################################################################
# Handler
###########################################################################
class MSPowerPoint(File):

    class_mimetypes = ['application/vnd.ms-powerpoint']
    class_extension = 'ppt'


    def to_text(self):
        return ppt_to_text(self.to_str())


# Register
register_handler_class(MSPowerPoint)

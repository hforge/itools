# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
from zipfile import ZipFile
from tarfile import TarFile
from cStringIO import StringIO

# Import from itools
from File import File
from registry import register_handler_class


#
# XXX Backported from tarfile 0.7.7
# 
class BZ2Proxy(object):
    """Small proxy class that enables external file object
       support for "r:bz2" and "w:bz2" modes. This is actually
       a workaround for a limitation in bz2 module's BZ2File
       class which (unlike gzip.GzipFile) has no support for
       a file object argument.
    """

    blocksize = 16 * 1024

    def __init__(self, fileobj, mode):
        self.fileobj = fileobj
        self.mode = mode
        self.init()


    def init(self):
        import bz2
        self.pos = 0
        if self.mode == "r":
            self.bz2obj = bz2.BZ2Decompressor()
            self.fileobj.seek(0)
            self.buf = ""
        else:
            self.bz2obj = bz2.BZ2Compressor()


    def read(self, size):
        b = [self.buf]
        x = len(self.buf)
        while x < size:
            try:
                raw = self.fileobj.read(self.blocksize)
                data = self.bz2obj.decompress(raw)
                b.append(data)
            except EOFError:
                break
            x += len(data)
        self.buf = "".join(b)

        buf = self.buf[:size]
        self.buf = self.buf[size:]
        self.pos += len(buf)
        return buf


    def seek(self, pos):
        if pos < self.pos:
            self.init()
        self.read(pos - self.pos)


    def tell(self):
        return self.pos


    def write(self, data):
        self.pos += len(data)
        raw = self.bz2obj.compress(data)
        self.fileobj.write(raw)


    def close(self):
        if self.mode == "w":
            raw = self.bz2obj.flush()
            self.fileobj.write(raw)
            self.fileobj.close()



class Archive(File):

    def get_contents(self):
        raise NotImplementedError


register_handler_class(Archive)



class ZipArchive(Archive):
    class_mimetypes = ['application/zip']

    def get_contents(self):
        archive = self.resource
        archive.open()
        zip = ZipFile(archive)
        contents = zip.namelist()
        zip.close()
        archive.close()

        return contents


register_handler_class(ZipArchive)



class TarArchive(Archive):
    class_mimetypes = ['application/x-tar']

    def get_contents(self):
        name = self.resource.name
        archive = StringIO(self.to_str())
        if name.endswith('gz'):
            # try gzip support
            import gzip
            mode = 'r|gz'
        elif name.endswith('.bz2'):
            # try bz2 support
            import bz2
            mode = 'r|'
            archive = BZ2Proxy(archive, 'r')
        else:
            mode = 'r|'
        tar = TarFile.open(name=name, mode=mode, fileobj=archive)
        contents = tar.getnames()
        tar.close()

        return contents


register_handler_class(TarArchive)

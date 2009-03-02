# -*- coding: UTF-8 -*-
# Copyright (C) 1996-2003 Victor B Wagner
# Copyright (C) 2003 Alex Ott <alexott@gmail.com>
# Copyright (C) 2009 Hervé Cauwelier <herve@itaapy.com>
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
from struct import unpack, error as UnpackError
from sys import stderr

SEEK_SET = 0
SEEK_CUR = 1
SEEK_END = 2

BBD_BLOCK_SIZE  = 512
SBD_BLOCK_SIZE  =  64
PROP_BLOCK_SIZE = 128
OLENAMELENGHT   =  32
MSAT_ORIG_SIZE  = 436

TYPE_OLE_DIR = 1
TYPE_OLE_STREAM = 2
TYPE_OLE_ROOTDIR = 5
TYPE_OLE_UNKNOWN = 3

ole_sign = '\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'


def getshort(buffer, offset):
    """Reads 2-byte LSB  int from buffer at given offset platfom-indepent
    way
    """
    return unpack('<H', buffer[offset:offset + 2])[0]


def getlong(buffer, offset):
    """Reads 4-byte LSB  int from buffer at given offset almost
    platfom-indepent way
    """
    return unpack('<l', buffer[offset:offset + 4])[0]


def getulong(buffer, offset):
    return unpack('<L', buffer[offset:offset + 4])[0]


def convert_char(uc):
    if uc == 0x001C:
        return u"\t"
    elif uc == 0x001E:
        return u"\n"
    elif uc == 0x00AD:
        return u""
    return unichr(uc)


def getOleType(oleBuf):
    return ord(oleBuf[0x42])


def rightOleType(oleBuf):
    return getOleType(oleBuf) in (TYPE_OLE_DIR, TYPE_OLE_STREAM,
                                  TYPE_OLE_ROOTDIR, TYPE_OLE_UNKNOWN)



class OleEntry(object):

    __slots__ = ['ole', 'file', 'name', 'startBlock', 'curBlock', 'length',
                 'ole_offset', 'file_offset', 'dirPos', 'type',
                 'numOfBlocks', 'blocks', 'isBigBlock']


    def __init__(self, ole):
        self.ole = ole


    def open(self):
        """Open stream, which correspond to directory entry last read by
        readdir
        """
        if self.type != TYPE_OLE_STREAM:
            return -2
        self.ole_offset = 0
        self.file_offset = self.file.tell()
        return 0


    def calcFileBlockOffset(self, blk):
        block = self.blocks[blk]
        ole = self.ole
        sectorSize = ole.sectorSize
        shortSectorSize = ole.shortSectorSize

        if self.isBigBlock:
            res = 512 + block * sectorSize
        else:
            sbdPerSector = sectorSize / shortSectorSize
            sbdSecNum = block / sbdPerSector
            sbdSecMod = block % sbdPerSector
            res = (512 + ole.rootEntry.blocks[sbdSecNum] * sectorSize
                    + sbdSecMod * shortSectorSize)
        return res


    def read(self, size):
        """Reads block from open ole stream interface-compatible with read

        @param size size of block

        @return block
        """
        ole = self.ole
        file = self.file
        buffer = 0
        rread = 0
        llen = size

        if self.ole_offset + llen > self.length:
            llen = self.length - self.ole_offset

        ssize = ole.sectorSize if self.isBigBlock else ole.shortSectorSize
        blockNumber = self.ole_offset / ssize
        if blockNumber >= self.numOfBlocks or llen <= 0:
            return ''

        modBlock = self.ole_offset % ssize
        bytesInBlock = ssize - modBlock
        if bytesInBlock < llen:
            toReadBlocks = (llen - bytesInBlock) / ssize
            toReadBytes = (llen - bytesInBlock) % ssize
        else:
            toReadBlocks = toReadBytes = 0
        newoffset = self.calcFileBlockOffset(blockNumber) + modBlock
        if self.file_offset != newoffset:
            file.seek(newoffset, SEEK_SET)
            self.file_offset = newoffset
        buffer = file.read(min(llen, bytesInBlock))
        rread = len(buffer)
        self.file_offset += rread
        for i in range(toReadBlocks):
            blockNumber += 1
            newoffset = self.calcFileBlockOffset(blockNumber)
            if newoffset != self.file_offset:
                file.seek(newoffset, SEEK_SET)
                self.file_offset = newoffset
                newbuf = file.read(min(llen - rread, ssize))
                readbytes = len(newbuf)
                buffer += newbuf
                rread += readbytes
                self.file_offset += readbytes
        if toReadBytes > 0:
            blockNumber += 1
            newoffset = self.calcFileBlockOffset(blockNumber)
            file.seek(newoffset, SEEK_SET)
            self.file_offset = newoffset
            newbuf = file.read(toReadBytes)
            readbytes = len(newbuf)
            buffer += newbuf
            rread += readbytes
            self.file_offset += readbytes
        self.ole_offset += rread
        return buffer


    def is_eof(self):
        return self.ole_offset >= self.length


    def seek(self, offset, whence):
        ole = self.ole
        new_ole_offset = 0
        if whence == SEEK_SET:
            new_ole_offset = offset
        elif whence == SEEK_CUR:
            new_ole_offset = self.ole_offset + offset
        elif whence == SEEK_END:
            new_ole_offset = self.length + offset
        else:
            raise ValueError, "Invalid whence!"
        if new_ole_offset < 0:
            new_ole_offset = 0
        if new_ole_offset > self.length:
            new_ole_offset = self.length

        ssize = ole.sectorSize if self.isBigBlock else ole.shortSectorSize
        blockNumber = new_ole_offset / ssize
        if blockNumber >= self.numOfBlocks:
            return -1

        modBlock = new_ole_offset % ssize
        new_file_offset = self.calcFileBlockOffset(blockNumber) + modBlock
        self.file.seek(new_file_offset, SEEK_SET)
        self.file_offset = new_file_offset
        self.ole_offset = new_ole_offset
        return 0


    def tell(self):
        """Tell position inside OLE stream

        @return current position inside OLE stream
        """
        return self.ole_offset



class Ole(object):

    __slots__ = ['file', 'sectorSize', 'shortSectorSize', 'bbdNumBlocks',
                 'BBD', 'sbdNumber', 'SBD', 'rootEntry', 'propCurNumber',
                 'propNumber', 'properties', 'fileLength']

    def __init__(self, file):
        """Initializes ole structure

        @param f (FILE *) compound document file, positioned at bufSize
                  byte. Might be pipe or socket
        """
        file.seek(0, SEEK_END)
        self.fileLength = fileLength = file.tell()
        file.seek(0, SEEK_SET)
        oleBuf = file.read(BBD_BLOCK_SIZE)
        if len(oleBuf) != BBD_BLOCK_SIZE:
            raise ValueError, "bad BBD_BLOCK_SIZE"
        if not oleBuf.startswith(ole_sign):
            raise ValueError, "not a PPT file"
        self.file = file
        self.sectorSize = sectorSize = 1 << getshort(oleBuf, 0x1e)
        self.shortSectorSize = shortSectorSize = 1 << getshort(oleBuf, 0x20)

        # Read BBD into memory
        BBD = []
        self.bbdNumBlocks = bbdNumBlocks = getulong(oleBuf, 0x2c)
        tmpBuf = oleBuf[0x4c:0x4c + MSAT_ORIG_SIZE]
        mblock = getlong(oleBuf, 0x44)
        msat_size = getlong(oleBuf, 0x48)

        i = 0
        while mblock >= 0 and i < msat_size:
            file.seek(512 + mblock * sectorSize, SEEK_SET)
            newbuf = file.read(sectorSize)
            if len(newbuf) != sectorSize:
                raise ValueError, "Error read MSAT"
            tmpBuf = tmpBuf[:MSAT_ORIG_SIZE + (sectorSize - 4) * i] + newbuf
            i += 1
            mblock = getlong(tmpBuf, MSAT_ORIG_SIZE + (sectorSize - 4) * i)

        for i in range(bbdNumBlocks):
            bbdSector = getlong(tmpBuf, 4 * i)
            if bbdSector >= (fileLength / sectorSize) or bbdSector < 0:
                raise ValueError, "Bad BBD entry!"
            file.seek(512 + bbdSector * sectorSize, SEEK_SET)
            newbuf = file.read(sectorSize)
            if len(newbuf) != sectorSize:
                raise ValueError, "Can't read BBD!"
            BBD.append(newbuf)
        self.BBD = ''.join(BBD)

        # Read SBD into memory
        SBD = []
        sbdLen = 0
        sbdCurrent = sbdStart = getlong(oleBuf, 0x3c)
        if sbdStart > 0:
            while 1:
                file.seek(512 + sbdCurrent * sectorSize, SEEK_SET)
                newbuf = file.read(sectorSize)
                if len(newbuf) != sectorSize:
                    raise ValueError, "Can't read SBD!"
                SBD.append(newbuf)
                sbdLen += 1
                sbdCurrent = getlong(self.BBD, sbdCurrent * 4)
                if sbdCurrent < 0 or sbdCurrent >= fileLength / sectorSize:
                    break
            self.sbdNumber = sbdNumber = ((sbdLen * sectorSize)
                                          / shortSectorSize)
            self.SBD = ''.join(SBD)
        else:
            self.SBD = None

        # Read property catalog into memory
        propLen = 0
        propCurrent = propStart = getlong(oleBuf, 0x30)
        if propStart >= 0:
            self.properties = ''
            while 1:
                file.seek(512 + propCurrent * sectorSize, SEEK_SET)
                newbuf = file.read(sectorSize)
                if len(newbuf) != sectorSize:
                    raise ValueError, "Bad property entry!"
                self.properties += newbuf
                propLen += 1
                propCurrent = getlong(self.BBD, propCurrent * 4)
                if propCurrent < 0 or propCurrent >= fileLength / sectorSize:
                    break
            self.propNumber = (propLen * sectorSize) / PROP_BLOCK_SIZE
            self.propCurNumber = 0
        else:
            raise ValueError, "Bad properties!"

        # Find Root Entry
        self.rootEntry = None
        for tEntry in self.readdir():
            if tEntry.type == TYPE_OLE_ROOTDIR:
                self.rootEntry = tEntry
                break
        self.propCurNumber = 0
        file.seek(0, SEEK_SET)
        if self.rootEntry is None:
            raise ValueError, ("Broken OLE structure. "
                               "Cannot find root entry in this file!")


    def readdir(self):
        file = self.file

        while 1:
            if self.propCurNumber >= self.propNumber or file is None:
                return
            oleBuf = self.properties[self.propCurNumber * PROP_BLOCK_SIZE:]
            if not rightOleType(oleBuf):
                return

            entry = OleEntry(self)
            entry.dirPos = oleBuf
            entry.type = getOleType(oleBuf)
            entry.file = file
            entry.startBlock = getlong(oleBuf, 0x74)
            entry.blocks = None

            nLen = getshort(oleBuf, 0x40)
            # minus 1 to remove trailing '\0'
            name = [oleBuf[i * 2] for i in range((nLen / 2) - 1)]
            entry.name = ''.join(name)
            self.propCurNumber += 1
            entry.length = getulong(oleBuf, 0x78)

            # Read sector chain for object
            entry.numOfBlocks = 0
            chainCurrent = entry.startBlock
            entry.isBigBlock = (entry.length >= 0x1000
                                or entry.name == 'Root Entry')
            sector_size = (self.sectorSize if entry.isBigBlock
                                           else self.shortSectorSize)
            if (entry.startBlock >= 0 and entry.length >= 0
                    and entry.startBlock <= (self.fileLength / sector_size)):
                entry.blocks = blocks = []
                while 1:
                    blocks.append(chainCurrent)
                    entry.numOfBlocks += 1
                    if entry.isBigBlock:
                        try:
                            chainCurrent = getlong(self.BBD,
                                                   chainCurrent * 4)
                        except UnpackError:
                            chainCurrent = -1
                    elif self.SBD is not None:
                        try:
                            chainCurrent = getlong(self.SBD,
                                                   chainCurrent * 4)
                        except UnpackError:
                            chainCurrent = -1
                    else:
                        chainCurrent = -1
                    if entry.isBigBlock:
                        chainNumber = (self.bbdNumBlocks * sector_size) / 4
                    else:
                        chainNumber = (self.sbdNumber * sector_size) / 4
                    if (chainCurrent <= 0
                            or chainCurrent >= chainNumber
                            or entry.numOfBlocks > (entry.length
                                                    / sector_size)):
                        break

            if entry.length > sector_size * entry.numOfBlocks:
                entry.length = sector_size * entry.numOfBlocks
            yield entry

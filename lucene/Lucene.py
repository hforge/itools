# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA


# Import from itools
import struct

# Import from itools
import itools.handlers



class File(itools.handlers.File.File):
    """
    Base class for Lucene handlers that implements the decoding (load) and
    encoding (save) of values (byte, int32, uint32, uint64, vint, string
    and terminfo).
    """

    def load_byte(self):
        byte = self.data[self.index]
        self.index += 1
        return ord(byte)


    def save_byte(cls, byte):
        return chr(byte)

    save_byte = classmethod(save_byte)


    def load_int32(self):
        uint32 = self.data[self.index:self.index+4]
        self.index = self.index + 4
        uint32 = struct.unpack('>i', uint32)[0]
        return int(uint32)


    def save_int32(cls, int32):
        return struct.pack('>i', int32)

    save_int32 = classmethod(save_int32)


    def load_uint32(self):
        uint32 = self.data[self.index:self.index+4]
        self.index = self.index + 4
        uint32 = struct.unpack('>I', uint32)[0]
        return int(uint32)


    def save_uint32(cls, uint32):
        return struct.pack('>I', uint32)

    save_uint32 = classmethod(save_uint32)


    def load_uint64(self):
        uint64 = self.data[self.index:self.index+8]
        self.index = self.index + 8
        uint64 = struct.unpack('>Q', uint64)[0]
        return int(uint64)


    def save_uint64(cls, uint64):
        return struct.pack('>Q', uint64)

    save_uint64 = classmethod(save_uint64)


    def load_vint(self):
        """
        The Java version also provides the VLong type. We don't because,
        thanks to Python, the value returned is automatically a long integer
        if it needs to be.
        """
        i = 0
        byte = self.load_byte()
        x = byte & 0x7F

        while byte & 0x80:
            i = i + 1
            byte = self.load_byte()
            x |= (byte & 0x7F) << (i * 7)
        return int(x)


    def save_vint(cls, vint):
        if vint == 0:
            return '\x00'
        bytes = []
        while vint:
            byte = vint & 127
            bytes.append(byte)
            vint = vint >> 7
        data = ''
        for byte in bytes[:-1]:
            data += chr(byte | 128)
        return data + chr(bytes[-1])

    save_vint = classmethod(save_vint)


    def load_string(self):
        length = self.load_vint()
        chars = self.data[self.index:self.index+length]
        self.index = self.index + length
        return unicode(chars, 'utf8')


    def save_string(cls, string):
        if isinstance(string, unicode):
            string = string.encode('utf8')

        data = cls.save_vint(len(string))
        return data + string

    save_string = classmethod(save_string)


    def load_terminfo(self):
        prefix_length = self.load_vint()
        suffix = self.load_string()
        field_num = self.load_vint()
        doc_freq = self.load_vint()
        freq_delta = self.load_vint()
        prox_delta = self.load_vint()
        skip_delta = self.load_vint()

        return prefix_length, suffix, field_num, doc_freq, freq_delta, \
               prox_delta, skip_delta


##    def save_terminfo(self, terminfo):
##        pass



############################################################################
# Fields
############################################################################
class FieldInfos(File):
    """
    Handler for '<segment>.fnm' files. It keeps the fields information
    (the name and wether it is indexed and stored):

      fields = [(<field name>, <is indexed>, <is stored>), ...]

    Where <field name> is an unicode string, <indexed> and <stored> are
    booleans. The position of a field in the list is the field number.
    """

    def _load(self):
        self.data = self.resource.get_data()
        self.index = 0
        # Parse
        count = self.load_vint()
        self.fields = []
        for i in range(count):
            name = self.load_string()
            bits = self.load_byte()
            indexed = bool(bits & 0x01)
            stored = bool(bits & 0x02)
            self.fields.append((name, indexed, stored))

        if self.index < len(self.data):
            raise ValueError, 'the file size is bigger than expected'
        # Remove temporal data
        del self.data
        del self.index


    def get_skeleton(self, fields=[]):
        data = self.save_vint(len(fields))
        for name, indexed, stored in fields:
            data += self.save_string(name)
            byte = int(stored) << 1 | int(indexed)
            data += self.save_byte(byte)
        return data


    def __str__(self):
        data = self.save_vint(len(self.fields))
        for name, indexed, stored in self.fields:
            data += self.save_string(name)
            byte = int(stored) << 1 | int(indexed)
            data += self.save_byte(byte)
        return data


    def set_field(self, name, indexed=True, stored=False):
        self.fields.append((name, indexed, stored))
        self.save()



############################################################################
# Stored fields
class FieldIndex(File):
    """
    Handler for '<segment>.fdx' files:

      documents = [<index to FieldData>, ...]
    """

    def _load(self, num_docs=0):
        self.data = self.resource.get_data()
        self.index = 0
        # Parse
        self.documents = []
        for i in range(num_docs):
            index = self.load_uint64()
            self.documents.append(index)

        # Remove temporal data
        del self.data
        del self.index



class FieldData(File):
    """
    Handler for '<segment>.fdt' files:

      documents = [<fields>, ...]
      fields = [(<field number>, <is tokenized>, <field value>), ...]
    """

    def _load(self):
        self.data = self.resource.get_data()
        self.index = 0
        # Parse
        self.documents = []
        while self.index < len(self.data):
            count = self.load_vint()
            fields = []
            for i in range(count):
                num = self.load_vint()
                bits = self.load_byte()
                tokenized = bool(bits & 0x01)
                value = self.load_string()
                fields.append((num, tokenized, value))
            self.documents.append(fields)

        # Remove temporal data
        del self.data
        del self.index


    def __str__(self):
        s = ''
        for fields in self.documents:
            s += self.save_vint(len(fields))
            for field_number, is_tokenized, value in fields:
                s += self.save_vint(field_number)
                s += self.save_byte(int(is_tokenized))
                s += self.save_string(value)
        return s


############################################################################
# Term Dictionary
############################################################################
class TermInfoFile(File):
    """
    Handler for '<segment>.tis' files. It loads the metadata:

      version = <int>
      num_terms = <int>
      index_interval = <int>
      skip_interval = <int>

    Instances of this class are iterators too, so it is possible to write:

      for terminfo in tis:
          prefix_length, suffix, field_number, ... = terminfo
    """

    def _load(self, field_names=[]):
        """
        The parameter 'field_names' must be the list of field names from the
        FieldInfos (fnm) file, we need it because the TermInfoFile (tis) is
        ordered first by the field name.
        """
        self.data = self.resource.get_data()
        self.index = 0
        # Load metadata
        self.version = self.load_int32()
        self.term_count = self.load_uint64()
        self.index_interval = self.load_uint32()
        self.skip_interval = self.load_uint32()
        # Set start
        self.terminfo_base = self.index


    def get_skeleton(self):
        # The defaults for IndexInterval (128) and SkipInterval (16) are
        # those foind in the Java implementation.
        return self.save_int32(-1) \
               + self.save_uint64(0) \
               + self.save_uint32(128) \
               + self.save_uint32(16)


    def __iter__(self):
        self.index = self.terminfo_base
        return self


    def next(self):
        if self.index >= len(self.data):
            raise StopIteration
        return self.load_terminfo()


        
class TermInfoIndex(File):
    """
    Handler for '<segment>.tii' files:

      indices = [(term_info, index_delta), ...]
    """

    def _load(self):
        self.data = self.resource.get_data()
        self.index = 0
        # Parse
        count = self.load_uint32()
        indices = []
        for i in range(count):
            terminfo = self.load_terminfo()
            # XXX Process term text??
            index_delta = self.load_vint()
            indices.append((term_info, index_delta))

        # Remove temporal data
        del self.data
        del self.index


    def get_skeleton(self):
        return self.save_uint32(0)



############################################################################
# Frequencies
class FreqFile(File):
    """
    Handler for '<segment>.frq' files.
    """

    def _load(self, num_terms=0):
        self.data = self.resource.get_data()
        self.index = 0


    def load_termfreqs(self, doc_freq):
        doc_number = 0
        term_freqs = []
        for i in range(doc_freq):
            doc_delta = self.load_vint()
            doc_number = doc_number + doc_delta/2
            if doc_delta % 2 == 1:
                freq = 1
            else:
                freq = self.load_vint()
            term_freqs.append((doc_number, freq))
        return term_freqs
            
##            # Load SkipData
##            skip_data = []
##            for j in range(doc_freq/skip_interval):
##                doc_skip = self.load_vint()
##                freq_skip = self.load_vint()
##                prox_skip = self.load_vint()
##                skip_data.append(doc_skip, freq_skip, prox_skip)
##            self.frequency.append((term_freqs, skip_data))


############################################################################
# Positions
class ProxFile(File):
    """
    Handler for '<segment>.prx' files.
    """

    def _load(self, num_terms=0):
        self.data = self.resource.get_data()
        self.index = 0


    def load_positions(self, freq):
        positions = []
        position = 0
        for i in range(freq):
            position_delta = self.load_vint()
            position += position_delta
            positions.append(position)
        return positions


############################################################################
# Normalization Factors
############################################################################
class Normalization(File):
    """
    Handler for '<segment>.f??' files (there is one per field):

      documents = <normalization factor>
    """

    def _load(self, num_docs=0):
        self.data = self.resource.get_data()
        self.index = 0
        # Parse
        self.documents = []
        for i in range(num_docs):
            byte = self.load_byte()
            if byte == 0:
                f = 0.0
            else:
                mantissa = byte & 0x07
                exponent = (byte & 0xF8) >> 3
                # 3
                exponent = exponent + 48
                # 4 and 5
                mantissa = mantissa << 21
                #
                f = mantissa * (10 ** exponent)
            self.documents.append(f)
        # Remove temporal data
        del self.data
        del self.index



############################################################################
# Term Vectors
############################################################################
class DocumentIndex(File):
    """
    Handler for '<segment>.tvx' files:

      indexes = [<document index>, ...]
    """

    def _load(self, num_docs=0):
        self.data = self.resource.get_data()
        self.index = 0
        # Parse
        self.version = self.load_int32()
        self.indexes = []
        for i in range(num_docs):
            doc_index = self.load_uint64()
            self.indexes.append(doc_index)
        # Remove temporal data
        del self.data
        del self.index


    def get_skeleton(self):
        return self.save_int32(-1)



class Document(File):
    """
    Handler for '<segment>.tvd' files:

      documents = [<document>, ...]

    Where:

      document = [<field>, ...]
      field = (<field num>, <field index>)
    """

    def _load(self, num_docs=0):
        self.data = self.resource.get_data()
        self.index = 0
        # Parse
        self.version = self.load_int32()
        self.documents = []
        for i in range(num_docs):
            num_fields = self.load_vint()
            fields = []
            for j in range(num_fields):
                field_num = self.load_vint()
                fields.append(field_num)
            for j in range(num_fields):
                field_index = self.load_vint()
                fields[0] = (fields[0], field_index)
            self.documents.append(fields)
        # Remove temporal data
        del self.data
        del self.index


    def get_skeleton(self):
        return self.save_int32(-1)


    def __str__(self):
        data = self.save_int32(-1)
        for document in self.documents:
            data += self.save_vint(len(document))
            for field_number, field_index in document:
                data += self.save_vint(field_number)
            for field_number, field_index in document:
                data += self.save_vint(field_index)
        return data


    ######################################################################
    # API
    ######################################################################
    def get_nfields(self):
        """
        Returns the number of fields, needed to load the Field (tvd) resource.
        """
        nfields = 0
        for document in self.documents:
            nfields += len(document)
        return nfields



class Field(File):
    """
    Handler for '<segment>.tvf' files:

      fields = [<field>, ...]

    Where:

      field = [<term>, ...]
      term = (<text>, <frequency>)
    """

    def _load(self, num_fields=0):
        self.data = self.resource.get_data()
        self.index = 0
        # Parse
        self.version = self.load_int32()
        self.fields = []
        for i in range(num_fields):
            num_terms = self.load_vint()
            num_distinct = self.load_vint() # Future use
            term_freqs = []
            for j in range(num_terms):
                term_text = self.load_string()
                term_freq = self.load_vint()
                term_freqs.append(term_text, term_freq)
            self.fields.append(term_freqs)
        # Remove temporal data
        del self.data
        del self.index


    def get_skeleton(self):
        return self.save_int32(-1)


    def __str__(self):
        data = self.save_int32(-1)
        for field in self.fields:
            data += self.save_vint(len(field))
            data += self.save_vint(0) # Future use
            for term_text, term_freq in field:
                data += self.save_string(term_text)
                data += self.save_vint(term_freq)


############################################################################
# Deleted Documents
############################################################################
class DeletedDocuments(File):
    """
    Handler for '<segment>.del' files:

    """

    def _load(self):
        self.data = self.resource.get_data()
        self.index = 0
        # Parse
        byte_count = self.load_uint32()
        bit_count = self.load_uint32()
        for i in range(byte_count):
            byte = self.load_byte()
        # Remove temporal data
        del self.data
        del self.index




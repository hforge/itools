#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from optparse import OptionParser

# Import from itools
import itools
from itools import vfs
from itools.catalog.io import (decode_byte, decode_character, decode_link,
                               decode_string, decode_uint32, decode_vint)



def format_int_as_hex(x, length=4):
    if x is None:
        return ' ' * (length + 1)
    x = hex(x)
    x = x[2:].upper()
    return '0' * (length - len(x)) + x



def inspect_index(target):
    file = target.open('tree')
    try:
        i = 0
        data = file.read(16)
        while data:
            if i == 0:
                c = ' '
                docs = None
                child = decode_link(data[8:12])
                sibling = None
            else:
                c = decode_character(data[:4])
                docs = decode_link(data[4:8])
                child = decode_link(data[8:12])
                sibling = decode_link(data[12:16])
            docs = format_int_as_hex(docs)
            child = format_int_as_hex(child)
            sibling = format_int_as_hex(sibling)
            print format_int_as_hex(i), c, docs, child, sibling
            # Next
            i += 1
            data = file.read(16)
    finally:
        file.close()


def inspect_documents(target):
    index = target.open('index').read()
    docs = target.open('documents').read()

    n = len(index) / 8
    for i in range(n):
        base = i * 8
        pointer = decode_link(index[base:base+4])
        if pointer is None:
            continue

        print 'DOC', i
        size = decode_uint32(index[base+4:base+8])
        doc = docs[pointer:pointer+size]

        while doc:
            first_byte = decode_byte(doc[0])
            doc = doc[1:]
            fn, is_stored = first_byte & 127, first_byte & 128
            if is_stored:
                value, doc = decode_string(doc)
                print '%s (STORED)' % fn, repr(value)
            else:
                n_terms, doc = decode_vint(doc)
                values = []
                for j in range(n_terms):
                    value, doc = decode_string(doc)
                    values.append(value)
                print '%s (NOT STORED)' % fn, values

        print




if __name__ == '__main__':
    # The command line parser
    usage = '%prog INDEX'
    version = 'itools %s' % itools.__version__
    description = 'Inspects the given INDEX.'
    parser = OptionParser(usage, version=version, description=description)

    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error('incorrect number of arguments')

    target = args[0]
    target = vfs.open(target)
    if target.exists('tree'):
        inspect_index(target)
    else:
        inspect_documents(target)



# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from itools
from itools.uri import uri
from registry import get_file_system


def get_layer_and_reference(reference):
    """
    Internal function, from the given reference (usually a byte string),
    builds the absolute URI reference. Then find outs which is the protocol
    handler for it (layer), and returns both.
    """
    reference = uri.get_absolute_reference(reference)
    fs = get_file_system(reference.scheme)
    return fs, reference


def exists(reference):
    layer, reference = get_layer_and_reference(reference)
    return layer.exists(reference)


def is_file(reference):
    layer, reference = get_layer_and_reference(reference)
    return layer.is_file(reference)


def is_folder(reference):
    layer, reference = get_layer_and_reference(reference)
    return layer.is_folder(reference)


def get_ctime(reference):
    layer, reference = get_layer_and_reference(reference)
    return layer.get_ctime(reference)


def get_mtime(reference):
    layer, reference = get_layer_and_reference(reference)
    return layer.get_mtime(reference)


def get_atime(reference):
    layer, reference = get_layer_and_reference(reference)
    return layer.get_atime(reference)


def get_mimetype(reference):
    layer, reference = get_layer_and_reference(reference)
    return layer.get_mimetype(reference)


def make_file(reference):
    layer, reference = get_layer_and_reference(reference)
    return layer.make_file(reference)


def make_folder(reference):
    layer, reference = get_layer_and_reference(reference)
    return layer.make_folder(reference)


def remove(reference):
    layer, reference = get_layer_and_reference(reference)
    return layer.remove(reference)


def open(reference):
    layer, reference = get_layer_and_reference(reference)
    return layer.open(reference)


def copy(source, target):
    if is_file(source):
        # File
        make_file(target)
        try:
            source = open(source)
            target = open(target)
            target.write(source.read())
        finally:
            source.close()
            target.close()
    else:
        # Folder (XXX)
        raise NotImplementedError


def move(source, target):
    source_layer, source_reference = get_layer_and_reference(source)
    target_layer, target_reference = get_layer_and_reference(target)

    if source_layer is target_layer:
        # Move within the same layer
        source_layer.move(source_reference, target_reference)
    else:
        # Move across different layers (copy and remove)
        copy(source_reference, target_reference)
        remove(source_reference)


##########################################################################
# Folders only
def get_names(reference):
    layer, reference = get_layer_and_reference(reference)
    return layer.get_names(reference)











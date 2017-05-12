# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007, 2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2009-2010 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2010 Hervé Cauwelier <herve@oursours.net>
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
from datetime import datetime
from cStringIO import StringIO
from os import listdir
from os.path import basename
from urllib import quote, unquote
from urlparse import urlsplit

# Import from gio
from gi.repository.GLib import MainLoop, GError
from gi.repository.Gio import File, MountOperation, Cancellable
from gi.repository.Gio import FILE_ATTRIBUTE_TIME_CHANGED, FILE_ATTRIBUTE_TIME_MODIFIED
from gi.repository.Gio import FILE_ATTRIBUTE_TIME_ACCESS
from gi.repository.Gio import FILE_ATTRIBUTE_STANDARD_SIZE, FILE_ATTRIBUTE_STANDARD_NAME
from gi.repository.Gio import FILE_ATTRIBUTE_STANDARD_TYPE
from gi.repository import Gio
from gi.repository.Gio import FileCreateFlags, FileCopyFlags
from gi.repository.Gio import FileType
from gi.repository.Gio import FILE_ATTRIBUTE_ACCESS_CAN_READ
from gi.repository.Gio import FILE_ATTRIBUTE_ACCESS_CAN_WRITE

# Import from itools
from itools.uri import resolve_uri, resolve_uri2, get_uri_name, get_uri_path
from common import READ, WRITE, READ_WRITE, APPEND, get_mimetype


######################################################################
# Private API
######################################################################
def _is_file(g_file):
    try:
        info = g_file.query_info(FILE_ATTRIBUTE_STANDARD_TYPE, Gio.FileQueryInfoFlags.NONE)
        the_type = info.get_attribute_uint32(FILE_ATTRIBUTE_STANDARD_TYPE)
    except GError:
        return False
    return (the_type == FileType.REGULAR or
            the_type == FileType.SYMBOLIC_LINK)


def _is_folder(g_file):
    try:
        info = g_file.query_info(FILE_ATTRIBUTE_STANDARD_TYPE, Gio.FileQueryInfoFlags.NONE)
        the_type = info.get_attribute_uint32(FILE_ATTRIBUTE_STANDARD_TYPE)
    except GError:
        return False
    return the_type == FileType.DIRECTORY


def _get_names(g_file):
    # FIXME This is a hack, see bug #675
    # Local ?
    if g_file.is_native():
        path = g_file.get_path()
        return listdir(path)

    children = g_file.enumerate_children(FILE_ATTRIBUTE_STANDARD_NAME)
    return [child.get_name() for child in children]


def _make_directory_with_parents(g_file):
    if g_file.query_exists():
        return
    g_file.make_directory_with_parents(Cancellable())


def _remove(g_file):
    # Is a directory ?
    if _is_folder(g_file):
        for child in _get_names(g_file):
            child = g_file.resolve_relative_path(child)
            _remove(child)
    g_file.delete()


def _copy(source, target):
    # "source to target/" or "source to target" ?
    if target.query_exists() and _is_folder(target):
        source_name = source.get_basename()
        target = target.resolve_relative_path(source_name)

    # Is a directory ?
    if _is_folder(source):
        # Copy the directory
        # XXX Must we handle the attributes ?
        target.make_directory()
        for child in _get_names(source):
            child_source = source.resolve_relative_path(child)
            child_target = target.resolve_relative_path(child)
            _copy(child_source, child_target)
    else:
        source.copy(target, FileCopyFlags.NONE)


def _traverse(g_file):
    yield g_file.get_uri()

    # Is a directory ?
    if _is_folder(g_file):
        for child in _get_names(g_file):
            child = g_file.resolve_relative_path(child)
            for grandchild in _traverse(child):
                yield grandchild


######################################################################
# Public API
######################################################################
class Folder(object):

    def __init__(self, obj=None):
        if obj is None:
            self._folder = File.new_for_path('.')
        elif type(obj) is str:
            self._folder = File.new_for_path(obj)
        elif isinstance(obj, File):
            self._folder = obj
        else:
            raise ValueError, 'unexpected obj "%s"' % obj


    ############################
    # Private API
    ############################
    def _get_g_file(self, uri):
        if type(uri) is not str:
            raise TypeError, 'unexpected "%s"' % repr(uri)

        # Your folder is None => new File
        if self._folder is None:
            return File.new_for_uri(uri)

        # Your folder is not None, we must resolve the uri
        scheme, authority, path, query, fragment = urlsplit(uri)

        # A scheme or an authority => new File
        # XXX This is not truly exact:
        #     we can have a scheme and a relative path.
        if scheme or authority:
            return File.new_for_uri(uri)

        # Else we resolve the path
        return self._folder.resolve_relative_path(uri)


    def _get_xtime(self, uri, attribut):
        g_file = self._get_g_file(uri)
        info = g_file.query_info(attribut, Gio.FileQueryInfoFlags.NONE)
        uint64 = info.get_attribute_uint64(attribut)
        return datetime.fromtimestamp(uint64)


    def _can_x(self, uri, attribut):
        g_file = self._get_g_file(uri)
        info = g_file.query_info(attribut, Gio.FileQueryInfoFlags.NONE)
        return info.get_attribute_boolean(attribut)


    #######################################################################
    # Public API
    #######################################################################
    def exists(self, uri):
        g_file = self._get_g_file(uri)
        return g_file.query_exists()


    def is_file(self, uri):
        g_file = self._get_g_file(uri)
        return _is_file(g_file)


    def is_folder(self, uri):
        g_file = self._get_g_file(uri)
        return _is_folder(g_file)


    def can_read(self, uri):
        return self._can_x(uri, FILE_ATTRIBUTE_ACCESS_CAN_READ)


    def can_write(self, uri):
        return self._can_x(uri, FILE_ATTRIBUTE_ACCESS_CAN_WRITE)


    def make_file(self, uri):
        g_file = self._get_g_file(uri)

        # Make the parent's directory
        _make_directory_with_parents(g_file.get_parent())

        return g_file.create(FileCreateFlags.PRIVATE)


    def make_folder(self, uri):
        g_file = self._get_g_file(uri)
        _make_directory_with_parents(g_file)


    def get_ctime(self, uri):
        return self._get_xtime(uri, FILE_ATTRIBUTE_TIME_CHANGED)


    def get_mtime(self, uri):
        return self._get_xtime(uri, FILE_ATTRIBUTE_TIME_MODIFIED)


    def get_atime(self, uri):
        return self._get_xtime(uri, FILE_ATTRIBUTE_TIME_ACCESS)


    def get_mimetype(self, uri):
        """Try to guess the mimetype for a resource, given the resource
        itself and its name.

        See `itools.fs.base.get_mimetype` for complete description.
        """
        g_file = self._get_g_file(uri)
        # TODO Use magic numbers too (like file -i).

        # Not a file ?
        if not _is_file(g_file):
            return 'application/x-not-regular-file'

        # Find out the filename extension
        scheme, authority, path, query, fragment = urlsplit(uri)
        path = unquote(path)
        name = basename(path)

        return get_mimetype(name)


    def get_size(self, uri):
        g_file = self._get_g_file(uri)
        info = g_file.query_info(FILE_ATTRIBUTE_STANDARD_SIZE, Gio.FileQueryInfoFlags.NONE)
        return info.get_attribute_uint64(FILE_ATTRIBUTE_STANDARD_SIZE)


    def open(self, uri, mode=READ):
        g_file = self._get_g_file(uri)

        # A directory => a new Folder ?
        if g_file.query_exists() and _is_folder(g_file):
            return Folder(g_file)

        # Get the Stream
        if mode is READ:
            # XXX can we find a better implementation ?
            # The problem is that a GFileInputStream object
            # doesn't implement all the usual functions of "file"
            # by example, there is no get_lines member.
            MAX_READ_FILE_SIZE = 4*1024*1024*1024
            data = g_file.read().read_bytes(MAX_READ_FILE_SIZE).get_data()
            return StringIO(data)
        elif mode is WRITE:
            return g_file.replace('', False, FileCopyFlags.NONE)
        elif mode is APPEND:
            return g_file.append_to(FileCreateFlags.PRIVATE)
        # XXX Finish me
        elif mode is READ_WRITE:
            raise NotImplementedError


    def remove(self, uri):
        g_file = self._get_g_file(uri)
        _remove(g_file)


    def copy(self, source, target):
        source = self._get_g_file(source)
        target = self._get_g_file(target)

        # Make the target's parent directory
        _make_directory_with_parents(target.get_parent())

        _copy(source, target)


    def move(self, source, target):
        source = self._get_g_file(source)
        target = self._get_g_file(target)

        # Make the target's parent directory
        _make_directory_with_parents(target.get_parent())

        source.move(target, FileCopyFlags.NONE)


    def get_names(self, uri='.'):
        g_file = self._get_g_file(uri)
        return _get_names(g_file)


    def traverse(self, uri):
        g_file = self._get_g_file(uri)
        return _traverse(g_file)


    def mount_archive(self, uri):
        g_file = self._get_g_file(uri)
        return Archive(g_file)


    def get_uri(self, reference='.'):
        g_file = self._get_g_file(reference)
        return g_file.get_uri()


    def get_relative_path(self, uri):
        g_file = self._get_g_file(uri)
        if self._folder is None:
            return g_file.get_path()
        return self._folder.get_relative_path(g_file)


    #######################################################################
    # Used by itools.handlers
    #######################################################################
    @staticmethod
    def get_basename(reference):
        return get_uri_name(reference)


    @staticmethod
    def get_path(reference):
        return get_uri_path(reference)


    @staticmethod
    def resolve(base, reference):
        return resolve_uri(base, reference)


    @staticmethod
    def resolve2(base, reference):
        return resolve_uri2(base, reference)


    # Resolution method for handler database keys
    normalize_key = get_uri



class Archive(Folder):

    def __init__(self, g_file):
        self._folder = None
        self._loop = MainLoop()

        # Make the archive uri
        uri = g_file.get_uri()
        uri = 'archive://' + quote(uri, '')

        # Mount the archive if needed
        g_file = File.new_for_path(uri)
        # Already mounted ?
        if g_file.query_exists():
            self._folder = g_file
        else:
            mount_operation = MountOperation()
            mount_operation.set_anonymous(True)
            g_file.mount_enclosing_volume(mount_operation, self._mount_end)

            # Wait
            self._loop.run()


#    def __del__(self):
#        # Umount the archive
#        self.unmount()


    ############################
    # Private API
    ############################
    def _mount_end(self, g_file, result):
        if g_file.mount_enclosing_volume_finish(result):
            self._folder = g_file
        self._loop.quit()


    def _unmount_end(self, g_mount, result):
        g_mount.unmount_finish(result)
        self._folder = None
        self._loop.quit()


    ############################
    # Public API
    ############################
    def unmount(self):
        # Unmount the archive
        if self._folder is not None:
            g_mount = self._folder.find_enclosing_mount()
            g_mount.unmount(self._unmount_end)

        # Wait
        self._loop.run()


# The entrypoint is the current working directory
vfs = Folder()

# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2009 David Versmisse <david.versmisse@itaapy.com>
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>

# Import from the Standard Library
from datetime import datetime
from cStringIO import StringIO
from os import listdir
from os.path import basename
from urllib import unquote
from urlparse import urlsplit

# Import from itools
from itools.core import guess_type
from filename import FileName

# Import from gio
from gio import File, Error
from gio import FILE_ATTRIBUTE_TIME_CHANGED, FILE_ATTRIBUTE_TIME_MODIFIED
from gio import FILE_ATTRIBUTE_TIME_ACCESS
from gio import FILE_ATTRIBUTE_STANDARD_SIZE, FILE_ATTRIBUTE_STANDARD_NAME
from gio import FILE_ATTRIBUTE_STANDARD_TYPE
from gio import FILE_TYPE_DIRECTORY, FILE_TYPE_REGULAR
from gio import FILE_TYPE_SYMBOLIC_LINK
from gio import FILE_ATTRIBUTE_ACCESS_CAN_READ
from gio import FILE_ATTRIBUTE_ACCESS_CAN_WRITE



######################################################################
# Constants
######################################################################
READ = 'r'
WRITE = 'w'
READ_WRITE = 'rw'
APPEND = 'a'



######################################################################
# Private API
######################################################################
def _is_file(g_file):
    try:
        info = g_file.query_info(FILE_ATTRIBUTE_STANDARD_TYPE)
        the_type = info.get_attribute_uint32(FILE_ATTRIBUTE_STANDARD_TYPE)
    except Error:
        return False
    return (the_type == FILE_TYPE_REGULAR or
            the_type == FILE_TYPE_SYMBOLIC_LINK)


def _is_folder(g_file):
    try:
        info = g_file.query_info(FILE_ATTRIBUTE_STANDARD_TYPE)
        the_type = info.get_attribute_uint32(FILE_ATTRIBUTE_STANDARD_TYPE)
    except Error:
        return False
    return the_type == FILE_TYPE_DIRECTORY


def _get_names(g_file):
    # FIXME This is a hack, see bug #675
    # Local ?
    uri = g_file.get_uri()
    if uri.startswith('file:'):
        path = g_file.get_path()
        return listdir(path)

    children = g_file.enumerate_children(FILE_ATTRIBUTE_STANDARD_NAME)
    return [child.get_name() for child in children]


def _make_directory_with_parents(g_file):
    # Make the todo list
    todo = []
    while not g_file.query_exists():
        todo.append(g_file.get_basename())
        g_file = g_file.get_parent()

    # Make the directories
    while todo:
        g_file = g_file.resolve_relative_path(todo.pop())
        g_file.make_directory()


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
        source.copy(target)


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
            self._folder = None
        elif type(obj) is str:
            self._folder = File(obj)
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
            return File(uri)

        # Your folder is not None, we must resolve the uri
        scheme, authority, path, query, fragment = urlsplit(uri)

        # A scheme or an authority => new File
        # XXX This is not truly exact:
        #     we can have a scheme and a relative path.
        if scheme or authority:
            return File(uri)

        # Else we resolve the path
        return self._folder.resolve_relative_path(uri)


    def _get_xtime(self, uri, attribut):
        g_file = self._get_g_file(uri)
        info = g_file.query_info(attribut)
        uint64 = info.get_attribute_uint64(attribut)
        return datetime.fromtimestamp(uint64)


    def _can_x(self, uri, attribut):
        g_file = self._get_g_file(uri)
        info = g_file.query_info(attribut)
        return info.get_attribute_boolean(attribut)


    ############################
    # Public API
    ############################
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

        return g_file.create()


    def make_folder(self, uri):
        g_file = self._get_g_file(uri)
        # XXX g_file_make_directory_with_parents is not yet implemented!!
        _make_directory_with_parents(g_file)


    def get_ctime(self, uri):
        return self._get_xtime(uri, FILE_ATTRIBUTE_TIME_CHANGED)


    def get_mtime(self, uri):
        return self._get_xtime(uri, FILE_ATTRIBUTE_TIME_MODIFIED)


    def get_atime(self, uri):
        return self._get_xtime(uri, FILE_ATTRIBUTE_TIME_ACCESS)


    def get_mimetype(self, uri):
        """Try to guess the mimetype for a resource, given the resource itself
        and its name. To guess from the name we need to extract the type
        extension, we use an heuristic for this task, but it needs to be
        improved because there are many patterns:

        <name>                                 README
        <name>.<type>                          index.html
        <name>.<type>.<language>               index.html.en
        <name>.<type>.<language>.<encoding>    index.html.en.UTF-8
        <name>.<type>.<compression>            itools.tar.gz
        etc...

        And even more complex, the name could contain dots, or the filename
        could start by a dot (a hidden file in Unix systems).
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

        name, extension, language = FileName.decode(name)
        # Figure out the mimetype from the filename extension
        if extension is not None:
            mimetype, encoding = guess_type('%s.%s' % (name, extension))
            # FIXME Compression schemes are not mimetypes, see /etc/mime.types
            if encoding == 'gzip':
                if mimetype == 'application/x-tar':
                    return 'application/x-tgz'
                return 'application/x-gzip'
            elif encoding == 'bzip2':
                if mimetype == 'application/x-tar':
                    return 'application/x-tbz2'
                return 'application/x-bzip2'
            elif mimetype is not None:
                return mimetype

        return 'application/octet-stream'


    def get_size(self, uri):
        g_file = self._get_g_file(uri)
        info = g_file.query_info(FILE_ATTRIBUTE_STANDARD_SIZE)
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
            return StringIO(g_file.read().read())
        elif mode is WRITE:
            return g_file.replace('', False)
        elif mode is APPEND:
            return g_file.append_to()
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

        source.move(target)


    def get_names(self, uri='.'):
        g_file = self._get_g_file(uri)
        return _get_names(g_file)


    def traverse(self, uri):
        g_file = self._get_g_file(uri)
        return _traverse(g_file)


    def mount_archive(self, uri):
        g_file = self._get_g_file(uri)
        from archive import Archive
        return Archive(g_file)


    def get_uri(self, reference='.'):
        g_file = self._get_g_file(reference)
        return g_file.get_uri()


    def get_relative_path(self, uri):
        g_file = self._get_g_file(uri)
        if self._folder is None:
            return g_file.get_path()
        return self._folder.get_relative_path(g_file)



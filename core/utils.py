# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from mimetypes import MimeTypes
from os import getcwd
from os.path import join, sep, splitdrive
from subprocess import Popen, PIPE
from sys import _getframe, modules, getsizeof
from gc import get_referents


def get_abspath(local_path, mname=None):
    """Returns the absolute path to the required file.
    """
    if mname is None:
        mname = _getframe(1).f_globals.get('__name__')

    if mname == '__main__' or mname == '__init__':
        mpath = getcwd()
    else:
        module = modules[mname]
        if hasattr(module, '__path__'):
            mpath = module.__path__[0]
        elif '.' in mname:
            mpath = modules[mname[:mname.rfind('.')]].__path__[0]
        else:
            mpath = mname

    drive, mpath = splitdrive(mpath)
    mpath = drive + join(mpath, local_path)

    # Make it working with Windows. Internally we use always the "/".
    if sep == '\\':
        mpath = mpath.replace(sep, '/')

    return mpath



def merge_dicts(d, *args, **kw):
    """Merge two or more dictionaries into a new dictionary object.
    """
    new_d = d.copy()
    for dic in args:
        new_d.update(dic)
    new_d.update(kw)
    return new_d



def get_sizeof(obj):
    """Return the size of an object and all objects refered by it.
    """
    size = 0
    done = set()
    todo = {id(obj): obj}
    while todo:
        obj_id, obj = todo.popitem()
        size += getsizeof(obj)
        done.add(obj_id)
        for obj in get_referents(obj):
            obj_id = id(obj)
            if obj_id not in done:
                todo[obj_id] = obj

    return size



###########################################################################
# Mimetypes
###########################################################################
mimetypes = MimeTypes()


def guess_type(filename):
    return mimetypes.guess_type(filename)


def add_type(mimetype, extension):
    mimetypes.add_type(mimetype, extension)


def guess_extension(mimetype):
    return mimetypes.guess_extension(mimetype)


def guess_all_extensions(mimetype):
    return mimetypes.guess_all_extensions(mimetype)


def has_extension(extension):
    filename = 'toto.%s' % extension
    mimetype, encoding = mimetypes.guess_type(filename)
    return mimetype is not None


def has_encoding(extension):
    extension = '.%s' % extension
    encodings_map = mimetypes.encodings_map
    return extension in encodings_map or extension.lower() in encodings_map


###########################################################################
# Wrapper around 'subprocess.Popen'
###########################################################################
def get_pipe(command, cwd=None):
    popen = Popen(command, stdout=PIPE, stderr=PIPE, cwd=cwd)
    errno = popen.wait()
    if errno:
        strerror = popen.stderr.read()
        raise EnvironmentError, (errno, strerror)
    return popen.stdout


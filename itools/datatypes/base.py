# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2011 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2008 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2008-2009 David Versmisse <versmisse@lil.univ-littoral.fr>
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

# Import from itools
from itools.core import prototype
import os
import base64
from Crypto.Cipher import AES
from Crypto import Random
from cryptography.fernet import Fernet


# Encryption/Decryption functions


def _pad(in_str):
    missing = int(os.getenv('_BS')) - len(in_str) % int(os.getenv('_BS'))
    return in_str + missing * chr(missing)


def _unpad(in_str):
    return in_str[:-ord(in_str[len(in_str) - 1:])]


def encrypt(raw):
    raw = _pad(raw)
    b_raw = raw.encode('utf8')
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(bytes(base64.urlsafe_b64decode(os.getenv('_KEY'))), AES.MODE_CBC, iv)
    return base64.b64encode(iv + cipher.encrypt(b_raw))


def decrypt(enc):
    not_enc = enc
    try:
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(bytes(base64.urlsafe_b64decode(os.getenv('_KEY'))), AES.MODE_CBC, iv)
        return _unpad(cipher.decrypt(enc[AES.block_size:]))
    except (UnicodeDecodeError, ValueError, TypeError):
        return not_enc

class DataType(prototype):

    # Default value
    default = None
    multiple = False
    encrypted = False


    def get_default(cls):
        default = cls.default
        if cls.multiple:
            if isinstance(default, list):
                return default
            # Change "default" explicitly to have an initialized list
            return []
        return default


    @staticmethod
    def decode(data):
        """Deserializes the given byte string to a value with a type.
        """
        raise NotImplementedError


    @staticmethod
    def encode(value):
        """Serializes the given value to a byte string.
        """
        raise NotImplementedError


    @staticmethod
    def is_valid(value):
        """Checks whether the given value is valid.

        For example, for a natural number the value will be an integer, and
        this method will check that it is not a negative number.
        """
        return True


    @staticmethod
    def is_empty(value):
        """Checks whether the given value is empty or not.

        For example, a text string made of white spaces may be considered
        as empty.  (NOTE This is used by the multilingual code.)
        """
        return value is None

    @classmethod
    def encrypt(cls, value):
        print("ENCRYPT !")
        print("raw value is")
        print(value)
        if not cls.encrypted:
            print("value is not encrypted")
            return value
        print("value will be encrypted")
        value = encrypt(value)
        print(value)
        return value


    @classmethod
    def decrypt(cls, value):
        print("DECRYPT !")
        print("raw value is")
        print(value)
        if not cls.encrypted:
            print("value is not encrypted")
            return value
        print("value will be decrypted")
        value = decrypt(value)
        print("decrypted")
        print(value)
        return value

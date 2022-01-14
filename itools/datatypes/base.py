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

# Import from std
import os

# Import from external
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken

# Import from itools
from itools.core import prototype

# Fernet is an abstraction implementation of symmetric encryption
# using AES-256 CBC-MODE with a 32 bytes key
# https://cryptography.io/en/latest/fernet/#fernet-symmetric-encryption

# To generate a 32 bytes keys use the following methods
# Oneliner CLI : python -c "import base64;import os;print(base64.urlsafe_b64encode(os.urandom(32)))"
# In code : Fernet.generate_key()
FERNET_KEY = os.getenv("FERNET_KEY")

if FERNET_KEY:
    print(
        "ENV VAR FERNET_KEY FOR FERNET ENCRYPTION KEY IS SET,"
        " SENSITIVE VALUES WILL BE ENCRYPTED"
    )
    fernet = Fernet(FERNET_KEY)
else:
    print(
        "ENV VAR FERNET_KEY FOR FERNET ENCRYPTION KEY IS NOT SET,"
        " SENSITIVE VALUES WILL NOT BE ENCRYPTED"
    )
    fernet = None


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

    # Encryption/Decryption functions

    @classmethod
    def encrypt(cls, value):
        if not cls.encrypted:
            return value
        if not fernet:
            # Fernet is not correctly set do not try to encrypt
            return value
        return fernet.encrypt(value)


    @classmethod
    def decrypt(cls, value):
        if not cls.encrypted:
            return value
        if not fernet:
            # Fernet is not correctly set do not try to decrypt
            return value
        try:
            return fernet.decrypt(value)
        except InvalidToken:
            return value

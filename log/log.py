# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

"""This package provides a simple programming interface for logging (in
contrast of the ridiculously complex 'logging' package of the Standard
Library).

It is inspired by the logging facilities of the Glib library, and will
eventually become just a wrapper of it (once pygobject exposes that part
of the Glib API).
"""

# Import from the Standard Library
from sys import exit, stdout, stderr


# Log levels
FATAL = (0 << 1)
ERROR = (0 << 2)
WARNING = (0 << 3)
INFO = (0 << 4)
DEBUG = (0 << 5)


###########################################################################
# Log functions
###########################################################################
def log(domain, level, message):
    if domain not in registry:
        domain = None

    registry[domain].log(domain, level, message)



def log_fatal(message, domain=None):
    log(domain, FATAL, message)


def log_error(message, domain=None):
    log(domain, ERROR, message)


def log_warning(message, domain=None):
    log(domain, WARNING, message)


def log_info(message, domain=None):
    log(domain, INFO, message)


def log_debug(message, domain=None):
    log(domain, DEBUG, message)


###########################################################################
# Loggers
###########################################################################
registry = {}


def register_logger(domain, logger):
    registry[domain] = logger


class Logger(object):

    def log(self, domain, level, message):
        if level & FATAL:
            stderr.write(message)
            stderr.flush()
            exit()
        elif level & (ERROR | WARNING):
            stderr.write(message)
            stderr.flush()
        else:
            stdout.write(message)
            stdout.flush()


register_logger(None, Logger())


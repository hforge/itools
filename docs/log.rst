:mod:`itools.log` (Logging)
***************************

.. module:: itools.log
   :synopsis: Logging

.. index::
   single: Logging

.. contents::

The :mod:`itools.log` package provides a simple programming interface for
logging events (errors, warning messages, etc.). It is inspired by the
logging facilities included in the `GLib
<http://library.gnome.org/devel/glib/>`_ library.

Levels
======

Every log event belongs to one of these five levels:

.. data:: FATAL

   Log level for fatal errors, see :func:`log_fatal`

.. data:: ERROR

   Log level for common errors, see :func:`log_error`

.. data:: WARNING

   Log level for warning messages, see :func:`log_warning`

.. data:: INFO

   Log level for informational messages, see :func:`log_info`

.. data:: DEBUG

   Log level for debug messages, see :func:`log_debug`


Logging functions
=================

For every level there is a function. Below we define the default behavior
of these functions, we will see later how to override this behavior.

.. function:: log_fatal(message, domain=None)

   Prints the given message into the standard error, and then aborts the
   application.

.. function:: log_error(message, domain=None)

   Prints the given message into the standard error.

.. function:: log_warning(message, domain=None)

   Prints the given message into the standard error.

.. function:: log_info(message, domain=None)

   Prints the given message into the standard output.

.. function:: log_debug(message, domain=None)

   By default this function does nothing, debug messages are ignored.

The ``domain`` argument allows to classify the log events by application
domains. This argument is optional, if not given then the event belongs to
the default domain.

.. note::

   Through :mod:`itools` we define one domain per package (``itools.http``,
   ``itools.web``, etc.)

Here there are some examples:

.. code-block:: python

   >>> from itools.log import log_fatal, log_error, log_warning, log_debug
   >>> log_error('Internal Server Error', domain='itools.http')
   2009-08-21 15:06:22 tucu itools.http[7268]: Internal Server Error
   >>> log_debug('I am here')
   >>> log_warning('Failed to connect to SMTP host', domain='itools.mail')
   2009-08-21 15:07:23 tucu itools.mail[7268]: Failed to connect to SMTP host
   >>> log_fatal('Panic')
   2009-08-21 15:07:39 tucu [7268]: Panic

It can be appreciated that the format of the log line looks a lot like the
syslog messages of Unix systems; except for the date, which is in a different
format.

More important is the fact that the itools logging system allows log events to
span multiple lines. For instance, by default, if we are handling an
exception while logging, the traceback will be printed:

.. code-block:: python

   >>> try:
   ...    5/0
   ... except Exception:
   ...   log_error('Division failed')
   ...
   2009-08-21 15:16:53 tucu [7362]: Division failed
     Traceback (most recent call last):
       File "<stdin>", line 2, in <module>
     ZeroDivisionError: integer division or modulo by zero

This allows to recover from errors while recording them.


Override the default behavior
=============================

To override the default behavior at least one new logger must be registered,
this is done with the :func:`register_logger` function:


.. function:: register_logger(logger, \*domains)

   Register the given logger object for the given domains.

For instance:

.. code-block:: python

   from itools.log import Logger, WARNING, register_logger

   logger = Logger('/tmp/log', WARNING)
   register_logger(logger, None)

With the code above errors and warning messages will be written to the
``/tmp/log`` file, while debug and informational messages will be ignored.
This will become the default behavior for all domains.

Here there is the description of the default logger class:

.. class:: Logger(log_file=None, min_level=INFO)

   By default messages are printed to the standard error or the standard
   output, depending on the level of the message. If the ``log_file``
   argument is given, it must be a file path, then messages will be written
   to the indicated file instead of printed.

   By default debug messages are ignored. The argument ``min_level`` allows
   to change this, for instance, to log all messages, pass the :data:`DEBUG`
   value.

   .. method:: format_header(domain, level, message)

      TODO

   .. method:: get_body()

      TODO

   .. method:: format_body()

      TODO

   .. method:: format(domain, level, message)

      TODO

   .. method:: log(domain, level, message)

      TODO

It is possible to subclass the :class:`Logger` class to personalize the
behavior of the logger as needed.

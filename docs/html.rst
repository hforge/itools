:mod:`itools.html` -- (X)HTML
*****************************

.. module:: itools.html
   :synopsis: (X)HTML

.. index:: (X)HTML

.. contents::


This chapter covers the package :mod:`itools.html`.


The HTML parser
===============

The package :mod:`itools.html` includes a parser for HTML documents. Its
programming interface is similar, but not exactly the same, to that of the XML
parser from the :mod:`itools.xml` package.

Example::

    >>> from itools.html import HTMLParser
    >>> from itools.xml import START_ELEMENT, END_ELEMENT, TEXT
    >>>
    >>> data = 'Hello <em>Baby</em>'
    >>> for type, value, line in HTMLParser(data):
    ...     if type == START_ELEMENT:
    ...         tag_uri, tag_name, attributes = value
    ...         print 'START TAG :', tag_name
    ...     elif type == END_ELEMENT:
    ...         tag_uri, tag_name = value
    ...         print 'END TAG   :', tag_name
    ...     elif type == TEXT:
    ...         print 'TEXT      :', value
    ...
    TEXT      : Hello
    START TAG : em
    TEXT      : Baby
    END TAG   : em

This example just prints a message to the standard output each time the start
of an element, the end of an element or a text node is found.

The parser returns a list of events, where every event is a tuple of three
values: the event type, the value (which depends on the event type) and the
line number. The events implemented are:

    =============== ================================================
    Event           Value
    =============== ================================================
    *DOCUMENT_TYPE* ``(name, <DocType object>)``
    --------------- ------------------------------------------------
    *START_ELEMENT* ``(tag uri, tag name, attributes)``
    --------------- ------------------------------------------------
    *END_ELEMENT*   ``(tag uri, tag name)``
    --------------- ------------------------------------------------
    *TEXT*          ``value``
    --------------- ------------------------------------------------
    *COMMENT*       ``value``
    =============== ================================================

All values (text nodes, comments, attribute values, etc.) are returned as byte
strings, in the source encoding.


Attributes
----------

The element attributes are returned as a dictionary where the key is the
qualified name of the attribute (a tuple namespace / name) and the value is
the value of the attribute.

For example, when processing the XML fragment:

.. code-block:: html

    <a href="http://www.gnu.org/"
       title="GNU's Not Unix">GNU</a>

The parser will return the attributes this way::

    {(None, 'href'): 'http://www.gnu.org/',
     (None, 'title'): "GNU's Not Unix"}


The file handlers
=================

The :mod:`itools.html` package provides a file handler for XHTML documents.
It is not much different from the handler for XML files (see
:mod:`itools.xml`).

First, if we create a new XHTML handler from scratch it will be correctly
initialized::

    >>> from itools.html import XHTMLFile
    >>> doc = XHTMLFile(title='Hello World')
    >>> print doc.to_str()
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
      "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">
      <head>
        <meta http-equiv="Content-Type" content="..."/>

        <title>Hello World</title>
      </head>
      <body></body>
    </html>

Second, we have a couple of handy methods to get the *head* and the *body* of
the document::

    >>> print doc.get_head().get_content()
    <meta http-equiv="Content-Type" content="..."/>
    <title>Hello World</title>
    >>>
    >>> print doc.get_body().get_content()


The HTML handlers
-----------------

The HTML handler is very much similar to the XHTML handler.


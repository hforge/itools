:mod:`itools.stl` -- Simple Template Language (STL)
***************************************************

.. module:: itools.stl
   :synopsis: A Simple Template Language

.. index:: STL

.. contents::


There are many template languages available. The *Simple Template Language*
distinct attributes are:

* it is so simple it can be described as minimalist;
* it enforces strict separation of presentation and logic, it is not possible
  to mix Python code into a template;
* very easy to learn, high productivity, very fast.

Here there is a snippet:

.. code-block:: html

    <h2>Task Tracker</h2>
    <div stl:repeat="task tasks"
         xmlns:stl="http://www.hforge.org/xml-namespaces/stl">
      <h4>${task/title} (<em>${task/state}</em>)</h4>
      <p>${task/description}</p>
    </div>

I like to define **STL** as a *descriptive* language. It is amazing how many
template languages are out there that allow to put Python code inside a
template, and call it a feature.


Usage
=====

.. figure:: figures/stl.*
    :scale: 50
    :align: center

    The Simple Template Language (**STL**)

This figure shows how **STL** works. Basically :func:`stl` is a function that
receives two parameters, an XML template and a Python namespace, and returns
an XML string as the output.


This is the way we use **STL**::

    # Import from itools
    from itools.handlers import ro_database
    from itools.stl import stl

    # Build the namespace
    namespace = {}
    namespace['title'] = 'Hello World'
    namespace['description'] = 'XXX'

    # Load the template
    template = ro_database.get_handler('template.xml')

    # Call STL
    output = stl(template, namespace)


One thing should be clear now is that all the logic required to build the
namespace is done in Python. **STL** enforces strict separation of concerns.
We use the best language for each purpose, Python for the logic, XML for the
presentation.


Variable substitution
=====================

The first and most basic feature of the language is variable substitution.
**STL** uses a syntax that resembles the one implemented by the
:class:`string.Template` [#string.template]_ from the *Python Standard
Library*:

  ``${expression}`` defines a substitution placeholder. The *expression* will
  be evaluated and the result value will be inserted.

This technique can be used in text nodes and attribute values. For example:

.. code-block:: html

    <a href="edit_task?id=${task/id}">${task/title}</a>


.. _stl-expressions:

Expressions
-----------

The expressions of **STL** are very simple, its syntax is:

    ``name[/name]*``

That is, a sequence of names separated by slashes. The expressions are
evaluated this way:

#. Look the first name in the namespace stack.
#. If there are more names left, the last value found must be a namespace,
   then look the next name in that namespace.

   Iterate until the last name is consumed.

#. Once the end of the sequence is reached, we will have a value. If the value
   is callable, then call it to get the final value.

If the value we get at the end is :obj:`None`, the placeholder will be
removed. If the placeholder is alone within an attribute, the attribute will
be removed altogether.

If the value is other than :obj:`None`, it will probably be a string, which
will be just inserted in the placeholder. If it is something else like an
integer, the value will be coerced to a string and inserted into the
placeholder.

There is an special case however, the boolean expressions.

.. _stl-boolean:

Boolean expressions
-------------------

Boolean expressions are meant to be used in boolean attributes, for example in
HTML we have the attributes ``checked``, ``disabled``, ``read-only`` and
``selected`` (among others).

Boolean expressions are slightly different than normal expressions:

    ``[not] name[/name]*``

They are evaluated the same way than normal expressions, but the value must be
a boolean (if it is not it will be coerced to a boolean). If the keyword
``not`` is present then we will apply the logical :keyword:`not` operator to
the value.

Here there is an example:

.. code-block:: html

    <input type="checkbox" name="high_priority" value="1"
      checked="${task/is_high_priority}" />

If at the end the value is :obj:`True` then **STL** will insert the name of
the attribute into placeholder, as it is the behaviour defined by (X)HTML
[#xhtml]_. If the value is :obj:`False` the attribute will be removed.


Conditional elements
====================

With **STL** it is possible to show or to hide a XML element based on a
condition. For this purpose we use the ``stl:if`` and the ``stl:omit-tag``
attributes.

The difference between ``stl:if`` and ``stl:omit-tag`` is that the first
one hides the entire element (and its children) and the second one only the
tag (not its children). For example, we will either have a link to a form to
edit the task, or we will just have the title of the task, depends on the
value of the variable :obj:`can_edit`. We can do that with:

.. code-block:: html

    <a href="edit_task" stl:if="can_edit">${title}</a>
    <stl:inline stl:if="not can_edit">${title}</stl:inline>

or

.. code-block:: html

    <a href="edit_task" stl:omit-tag="not can_edit">${title}</a>


This is the syntax of the ``stl:if`` and ``stl:omit-tag`` attributes:

    ``stl:if="[not] expression"``
    ``stl:if="[not] expression1 and [not] expression2"``
    ``stl:if="[not] expression1 or [not] expression2"``

    ``stl:omit-tag="[not] expression"``


The value of the attribute is a boolean expression, the same boolean
expressions we have seen in section :ref:`stl-boolean`.


STL is an XML namespace
=======================

Something important to note from the previous template snippet is that the
language **STL** uses XML namespaces, this means that the **STL**
namespace must be declared:

.. code-block:: html

    <?xml version="1.0" encoding="UTF-8"?>
    <html xmlns:stl="http://www.hforge.org/xml-namespaces/stl">
      ...


Loops
=====

It is also possible to repeat a block *n* times, for that purpose we have the
``stl:repeat`` attribute:

.. code-block:: html

    <div stl:repeat="task tasks">
      <h4>${task/title}</h4>
      <p>${task/description}</p>
    </div>

This is the syntax of the ``stl:repeat`` attribute:

    ``stl:repeat="name expression"``

The *expression* is a normal expression, as we have seen in Section
:ref:`stl-expressions`. The only difference is that the value we get at the
end must be a sequence.

For every item in the sequence, **STL** will process the XML element,
with the :obj:`name` variable associated to the value of the item. For
instance, with the namespace::

    namespace['tasks'] = [
        {'title': 'Finish the Documentation',
         'description': 'Documentation is very important'},
        {'title': 'Release 1.0',
         'description': 'And rejoice'},
        ]

We would get the output:

.. code-block:: html

    <div>
      <h4>Finish the Documentation</h4>
      <p>Documentation is very important</p>
    </div>
    <div>
      <h4>Release 1.0</h4>
      <p>And rejoice</p>
    </div>


Dummy blocks
============

Finally, **STL** defines two XML elements, ``stl:block`` and ``stl:inline``,
which will be committed when processing the template.

They are useful when we want to apply the ``stl:if`` or ``stl:repeat``
attributes to a block of XML that does not match an XML element. For example
we may rewrite the snippet from the previous section this way:


.. code-block:: html

    <stl:block stl:repeat="task tasks">
      <h4>${task/title}</h4>
      <p>${task/description}</p>
    </stl:block>

To get this output:

.. code-block:: html

    <h4>Finish the Documentation</h4>
    <p>Documentation is very important</p>

    <h4>Release 1.0</h4>
    <p>And rejoice</p>

The difference between the two elements is that ``stl:block`` is a block
element while ``stl:inline`` is an inline element (see the HTML documentation
to learn what this means exactly [#xhtml-inline]_. The reason we make this
difference is because it has an impact on the localization of the templates.


Example
=======

Now we are going to illustrate **STL** with a more complex example. Building
up on the Task Tracker from the section :ref:`handlers-example` in the
handlers chapter, we are going to write a method that produces an HTML page
showing all the tasks.


The Template
------------

.. code-block:: html

    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
      "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:stl="http://www.hforge.org/xml-namespaces/stl">
      <head></head>
      <body>
        <h2>Task Tracker</h2>
        <stl:block stl:repeat="task tasks">
          <h4>
            #${task/id}: ${task/title} (<em>${task/state}</em>)
          </h4>
          <p>${task/description}</p>
        </stl:block>
      </body>
    </html>


The Namespace
-------------
::

    def view(self):
        # Load the STL template
        handler = ro_database.get_handler('TaskTracker_view.xml')

        # Build the namespace
        namespace = {}
        namespace['tasks'] = []
        for i, task in enumerate(self.tasks):
            namespace['tasks'].append({'id': i,
                                       'title': task.title,
                                       'description': task.description,
                                       'state': task.state,
                                       'is_open': task.state == 'open'})

        # Process the template and return the output
        return stl(handler, namespace, mode='xhtml')


The Output
----------

The output may be something like (depends on the content of
:obj:`self.tasks`):

.. code-block:: html

    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
         "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">
      <head><meta http-equiv="Content-Type"
                  content="application/xhtml+xml; charset=utf-8"/>
      </head>
      <body>
        <h2>Task Tracker</h2>
          <h4>
            #0: Re-write the chapter about writing handler classes.
     (<em>closed </em>)
          </h4>
          <p>A new chapter...


This Figure shows how the HTML may look with a browser.

.. figure:: figures/task_tracker.*
    :align: center

    The task tracker view


Modes
-----

In the latter example, we have called **STL** with a *mode* parameter.  By
default **STL** returns a stream of events like "element is opening", "text",
element is closing". When using the *xhtm* mode, **STL** will return a valid
XHTML document as a Python string. There is also an *html* mode returning an
HTML document with forbidden end tags omitted, e.g. ``<br>`` instead of the
invalid ``<br/>``.

The reason we use the stream mode by default is that **STL** will not accept
to interpret (X)HTML content by default, thus protecting from unexpected code
injection. **STL** will however accept streams and merge them into the
ouput. To inject an (X)HTML string, you must first parse it using the
:class:`~itools.xml.XMLParser` or :class:`~itools.html.HTMLParser`.

In the real world, we compute and combine several templates, for instance a
generated form into a page into a website layout, and only the final
:func:`stl` call would be asked for an *html* output (valid XHTML support is
still little spreaded).


.. seealso::

    If you are interested in streams, see the section :ref:`xml-parser` in the
    :mod:`itools.xml` chapter.

.. rubric:: Footnotes

.. [#string.template] http://docs.python.org/dev/2.5/lib/node40.html
.. [#xhtml] http://www.w3.org/TR/html4/intro/sgmltut.html\#h-3.3.4.2
.. [#xhtml-inline] http://www.w3.org/TR/html4/struct/global.html\#h-7.5.3





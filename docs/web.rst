:mod:`itools.web` Web
*********************

.. module:: itools.web
   :synopsis: Web

.. index::
   single: Web

.. contents::


The package :mod:`itools.web` is a *Web Framework*: it provides a high level
programming interface to develop Web applications. An immediate example of
such a Web application is the :mod:`ikaaro` package (see
http://www.hforge.org/ikaaro/).


Example: Hello World
====================

Let's see a basic usage of the framework::

    # Import from itools
    from itools.handlers import RWDatabase
    from itools.loop import Loop
    from itools.web import WebServer, RootResource, BaseView


    class MyView(BaseView):
        access = True
        def GET(self, resource, context):
            context.set_content_type('text/plain')
            return 'Hello World'

    class MyRoot(RootResource):
        default_view_name = 'my_view'
        my_view = MyView()

    if __name__ == '__main__':
        root = MyRoot()
        server = WebServer(root)
        server.listen('localhost', 8080)
        server.database = RWDatabase()
        loop = Loop()
        loop.run()

To test the code above, type:

.. code-block:: sh

    $ python hello.py

Then open a browser and go to http://localhost:8080 to see the famous
sentence.

These few lines of code expose several aspects of :mod:`itools.web` that we
will see later with more details:


.. class:: WebServer

    This class implements a Web server. It expects the root of your
    application as the first parameter of its constructor.

.. class:: RootResource

    The root of the application must be an instance of this class. You
    subclass it to write your own application.

.. class:: BaseView

  .. method:: GET(self, resource, context)

        This method will be called for HTTP GET requests.

        The method expects the *context* as a parameter. The context object is
        the primary programming interface.

        The method returns the string that will be sent to the browser.

  .. attribute:: access

        We have to open access to the :meth:`GET` with ``access = True``,
        because by default everything is closed.


:mod:`itools.web` follows the Model-View-Controller architectural pattern.
Here the ``root`` is the controller and the view is ``my_view``.


Traversal
=========

In a Web application the main user interface is the URI, for instance:

    http://localhost:8080/2007/05/;view_calendar

With :mod:`itools.web` a URI path is divided into two parts: the path and the
method. The method is explicitly identified because it is preceded by the
semicolon character. In this example:

* The path is ``2007/05``.
* The method is ``view_calendar``.


The Path
--------

Information is logically organized in a tree. In our example the tree would
look like this:

.. code-block:: none

    /
    |-- 2007
    |   |-- 01
    |   |-- 02
    |   |-- 03
    |   |-- 04
    |   |-- 05   <== the node at 2007/05
    |   |-- 06
    |   |-- 07
    |   |-- 08
    |   |-- 09
    |   |-- 10
    |   |-- 11
    |   \-- 12
    |-- 2008
    |   |-- 01
    ...


With :mod:`itools.web` all nodes in the tree are Python objects, instances of
the class :class:`Resource` (note that this is a base class, this is to say,
it must be specialized).

The path (``2007/05`` in our example) identifies a resource in the tree.


The method
----------

Once we have the resource, the view (:meth:`view_calendar` in our example)
will identify a view of that resource.

If the view is not explicitly specified, like in the URI:

    http://localhost:8080/2006/05

Then a default view is called.

Once we have the view (a class), the good method (GET, POST, ...) will be
called. And the value it returns will be used to build the response that the
server will send to the client.


Traversal
---------

In a word, by traversal we basically understand the process of:

* Picking the resource in the tree identified by the given path.
* Picking a view of this resource, either explicitly if specified in the
  URI, or implicitly.
* Calling the good method.


Example: Calendar
-----------------

To illustrate what has been explained so far, see this code::

    # Import from the Standard Library
    import calendar
    import datetime

    # Import from itools
    from itools.handlers import RWDatabase
    from itools.loop import Loop
    from itools.uri import get_reference
    from itools.web import WebServer, RootResource, Resource, BaseView


    class CalendarView(BaseView):
        access = True
        def GET(self, resource, context):
            month = int(resource.name)
            year = int(resource.parent.name)
            cal = calendar.month(year, month)
            context.set_content_type('text/html')
            return "<html><body><h2><pre>%s</pre></h2></body></html>" % cal

    class Month(Resource):
        view_calendar = CalendarView()


    class Year(Resource):
        def _get_resource(self, name):
            # Check the name is a valid month number
            try:
                month = int(name)
            except ValueError:
                raise LookupError
            if month < 1 or month > 12:
                raise LookupError
            return Month()


    class RootView(BaseView):
        access = True
        def GET(self, resource, context):
            today = datetime.date.today()
            path = today.strftime('%Y/%m/;view_calendar')
            return get_reference(path)

    class MyRoot(RootResource):
        default_view_name = 'root_view'
        root_view = RootView()

        def _get_resource(self, name):
            # Check the name is a valid year number
            try:
                year = int(name)
            except ValueError:
                raise LookupError
            if year < 1 or year > 9999:
                raise LookupError
            return Year()


    if __name__ == '__main__':
        root = MyRoot()
        server = WebServer(root)
        server.listen('localhost', 8080)
        server.database = RWDatabase()
        loop = Loop()
        loop.run()

To try this example type:

.. code-block:: sh

    $ python cal.py

Then go to the URL http://localhost:8080, and enjoy.


Basic programming interface
---------------------------

As the calendar example shows, with :mod:`itools.web` all nodes in the graph
must be instances of the base class :class:`Resource`. And all of them will
have two attributes:


.. class:: Resource

  .. attribute:: parent

        The parent resource. For the root resource it will be :obj:`None`.

  .. attribute:: name

        The name of the resource, this is to say the name it was used to reach
        the resource from its parent. For the root resource it will be the
        empty string.

  Based on these two attributes, the :class:`~itools.web.Resource` class
  provides a rich API, here is an excerpt:


  .. method:: get_root()

        Returns the root resource.

  .. method:: get_abspath()

        Returns the absolute path of this resource, as a
        :class:`~itools.uri.Reference` instance.

  .. method:: get_pathto(resource)

        Returns the relative path from this resource to the given resource, as
        a :class:`~itools.uri.Reference` instance.


The namespace
^^^^^^^^^^^^^

Another important thing the example shows is the method :meth:`_get_resource`.
Our hierarchy of years and months is dynamically created, so we build objects
to support traversal and drop them after the response is returned.

.. method:: Resource._get_resource(name)

    Returns the resource for the given name.  If there is not any resource
    with that name it must raise the :exc:`LookupError` exception.


Return values
^^^^^^^^^^^^^

Something new in this example is the value returned by the
:meth:`RootView.GET` method is not a byte string, but a
:class:`~itools.uri.Reference` instance. The values a method can return are:

* a *byte string*

  If everything is alright, a *200 OK* response will be sent to the client,
  and the byte string will be its body.

* a :class:`~itools.uri.Reference` instance

  The client will be redirected to the given URI. That is to say, a response
  *302 Found* will be sent to the client with the response header *Location*
  set to the given URI.

* the value :obj:`None`

  A response *204 No Content* is sent to the client.

Most often these values will be enough for the programmer. If the response
needs to be further modified, for example to send a different status code, or
to add a response header, it is possible to directly manipulate the response
object.


The context
===========

.. class:: Context

  .. attribute:: server

        The Web server. Useful for example to access the error log.

  .. attribute:: root

        The root object, your application.

  .. attribute:: user

        The authenticated user (an object that provides the API for users, we
        will see them later). Or :obj:`None` if the user is not authenticated.

  .. attribute:: uri

        The URI as it was typed by the user in the browser bar. May be
        different than the URI of the request object when there is virtual
        hosting. It is a Reference instance.

  .. attribute:: path

        The path to traverse from the application's root to reach the object
        to be published. It is a Path object.

  .. attribute:: view_name

        The view used for a resource.

  .. attribute:: resource

        The object we get after traversing the path, or :obj:`None`.


This is what the :obj:`context` object is made of, but the programmer can set
attributes to it to pass values around.

The context also provides an API.


The form values
---------------

The client may send data to the server either with the URI's query, or
within the request body, for example when the user submits a form. To
access these values it is possible to use the request object, but it is
strongly recommended to use the higher level API provided by the context:

.. method:: Context.get_form_keys()

    Returns the keys of all the form values sent by the client.

.. method:: Context.get_form_value(self, name, type=String, default=None)

    Returns the form value for the given *name*. If the client sent more than
    one value for the same name it will return the first one.

    The value returned will be a byte string. Unless the *type* parameter is
    passed, then it will be used to deserialize the value (see
    :mod:`itools.datatypes` for details on :mod:`itools` datatypes).

    If the client did not sent any value, the value of the *default* parameter
    will be returned. Unless the *type* parameter is passed, then the default
    value for the given type will be returned.


Example: Hello *buddy*
^^^^^^^^^^^^^^^^^^^^^^

To practice the API above we are going to see an slightly more elaborate
example::

    class MyView(BaseView):
        access = True
        def GET(self, resource, context):
            context.set_content_type("text/plain")
            name = context.get_form_value('name', default='World')
            return 'Hello %s' % name

Now, the URI http://localhost:8080 will return the same response as before,
but http://localhost:8080/?name=buddy will give a customized message. You can
try with other values to better appreciate the power of this code.


Cookies
-------

Cookies can be used to implement client side sessions [#web-rq]_, this is, to
keep information across several requests. The context object provides a high
level API to work with them:

.. method:: Context.get_cookie(self, name, type=None)

    Returns the value of the cookie with the given name. If there is not a
    cookie with that name return :obj:`None`.

.. method:: Context.set_cookie(name, value, \*\*kw)

    Sets the cookie with the given name to the given value. The keyword
    parameters are to define any of the cookie attributes *expires*, *domain*,
    *path*, *max\_age*, *comment* and *secure*.

.. method:: Context.del_cookie(name)

    Removes the cookie with the given name.


Redirect
--------

The context object offers this API for redirections:

.. method:: Context.come_back(self, message, goto=None, keep=freeze([]), **kw)

    This is a high level function that builds and returns a Reference instance
    that can be sent back for a redirection. It is often useful to use in the
    action of a form.

    The base URI is defined by the *goto* parameter. If it is not passed the
    referrer will be used instead.

    To the base URI we add the form values defined by the *keep* parameter. By
    default we add nothing.

    Finally, we add the value defined by the *message* parameter. But first
    this *message* will be translated (see the internationalization document),
    and then interpolated (using the "``$``" syntax) with the given keyword
    parameters (*kw*).


API
===


The Tree: Resources
-------------------


Private API
^^^^^^^^^^^

.. method:: Resource._get_names()

    Returns a list of the sub-resources names.

.. method:: Resource._get_resource(name)

    Makes it possible to return dynamically created resources. The default
    implementation raises :exc:`LookupError` so the Web server will return
    "``404 Not Found``".


Public API
^^^^^^^^^^

.. method:: Resource.get_root()

     Returns the root resource.

.. method:: Resource.get_resource(path)

     Returns the resource at the given path.

.. method:: Resource.get_names(path='.')

    Returns the names of the resources at the given path.

.. method:: Resource.get_abspath()

    Returns the absolute path.

.. method:: Resource.get_pathto(resource)

    Returns the relative path to the given resource.

.. method:: Resource.get_view(name, query=None)

    Returns the view to call based on its name. In the calendar application
    above, the name was ``view_calendar``.

.. method:: Resource.get_access_control()

    Returns the object responsible for the security of the application.  The
    default implementation looks up for the closest instance of the
    :class:`AccessControl` class in the parent path.


The Views: BaseView
-------------------

.. method:: BaseView.GET(resource, context)

.. method:: BaseView.HEAD(resource, context)

.. method:: BaseView.POST(resource, context)

.. method:: BaseView.PUT(resource, context)

.. method:: BaseView.LOCK(resource, context)

.. method:: BaseView.UNLOCK(resource, context)

    Those methods are mapped to the HTTP methods. Note that :func:`LOCK` and
    :func:`UNLOCK` are part of the :func:`WebDAV` protocol.

    They must return a byte string for the response body, or a Reference for
    redirection, or None for not returning a body. Raising an exception will
    make the Web server returning an error page instead.



.. rubric:: Footnotes

.. [#web-rq]

    Note that :mod:`itools.web` does not provide and will never provide server
    side sessions, because they are bad, bad, bad.}








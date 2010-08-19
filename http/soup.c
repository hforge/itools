/*
 * Copyright (C) 2009 Juan David Ibáñez Palomar <jdavid@itaapy.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <Python.h>
#include <soup.h>
#include <string.h>

/* Variable names are prefixed by one letter:
 *   p_xxx - is a Python object
 *   g_xxx - is a glib object
 *   s_xxx - is a libsoup object
 *
 * Variables without a prefix are standard C types.
 */


/**************************************************************************
 * Access Log
 *************************************************************************/

static gchar *
get_request_line (SoupMessage * s_msg)
{
  SoupHTTPVersion s_http_version;
  gchar * format;
  SoupURI * s_uri;
  char * uri;
  gchar * request_line;

  /* The request URI */
  s_uri = soup_message_get_uri (s_msg);
  uri = soup_uri_to_string (s_uri, TRUE);

  /* The HTTP version */
  s_http_version = soup_message_get_http_version (s_msg);
  if (s_http_version == SOUP_HTTP_1_0)
    format = "%s %s HTTP/1.0";
  else
    format = "%s %s HTTP/1.1";

  request_line = g_strdup_printf (format, s_msg->method, uri);
  free (uri);
  return request_line;
}


static gboolean
log_access (GSignalInvocationHint *ihint, guint n_param_values,
            const GValue *param_values, gpointer data)
{
  PyObject * p_server;
  SoupMessage * s_msg;
  SoupClientContext * s_client;
  gchar * request_line;

  s_msg = (SoupMessage*) g_value_get_object (param_values + 1);
  s_client = (SoupClientContext*) g_value_get_boxed(param_values + 2);

  /* Must be freed */
  request_line = get_request_line (s_msg);

  /* Python callback */
  /* The callback function must have this signature:
   * log_access(self, host, request_line, status_code, body_length)
   * => str str int int*/
  p_server = (PyObject*) data;  request_line = get_request_line (s_msg);
  if (!PyObject_CallMethod (p_server, "log_access", "ssii",
                            soup_client_context_get_host (s_client),
                            request_line,
                            s_msg->status_code,
                            (int) s_msg->response_body->length))
    {
      free (request_line);
      /* The Python callback should never fail, it is its responsability to
       * catch and handle exceptions */
      printf("ERROR! Python's access log failed, this should never happen\n");
      abort ();
    }
  free (request_line);

  return TRUE;
}



/**************************************************************************
 * PyMessage
 *************************************************************************/

typedef struct
{
  PyObject_HEAD
  SoupMessage * s_msg;
} PyMessage;

static PyObject *
PyMessage_new (PyTypeObject * type, PyObject * args, PyObject * kwdict)
{
  PyMessage * self;

  self = (PyMessage *) type->tp_alloc (type, 0);
  if (self != NULL)
    self->s_msg = NULL;

  return (PyObject *) self;
}


static void
PyMessage_dealloc (PyMessage * self)
{
  if (self->s_msg)
  {
    g_type_free_instance ((GTypeInstance *) self->s_msg);
    self->s_msg = NULL;
  }

  self->ob_type->tp_free ((PyObject *) self);
}


static int
PyMessage_init (PyMessage * self, PyObject * args, PyObject * kwdict)
{
  if (self->s_msg)
    g_type_free_instance ((GTypeInstance *) self->s_msg);

  self->s_msg = soup_message_new ("GET", "http://localhost/");
  if (self->s_msg == NULL)
  {
    PyErr_Format (PyExc_RuntimeError, "call to 'soup_message_new' failed");
    return -1;
  }

  return 0;
}


static PyObject *
PyMessage_get_request_line (PyMessage * self, PyObject * args,
                            PyObject * kwdict)
{
  PyObject * result;
  gchar * c_result;

  c_result = get_request_line(self->s_msg);
  result = PyString_FromString (c_result);
  free(c_result);

  /* result can be NULL */
  return result;
}


static PyObject *
PyMessage_get_body (PyMessage * self, PyObject * args, PyObject * kwdict)
{
  goffset length;

  length = self->s_msg->request_body->length;
  if (length == 0)
    Py_RETURN_NONE;

  return PyString_FromStringAndSize (self->s_msg->request_body->data, length);
}


static PyObject *
PyMessage_get_headers (PyMessage * self, PyObject * args, PyObject * kwdict)
{
  SoupMessageHeadersIter iter;
  const char *name, *value;
  PyObject *pair, *result;

  /* Initialize the result */
  result = PyList_New(0);
  if (result == NULL)
    return NULL;

  /* Read each header */
  soup_message_headers_iter_init (&iter, self->s_msg->request_headers);
  while (soup_message_headers_iter_next (&iter, &name, &value) == TRUE)
  {
    pair = Py_BuildValue ("(ss)", name, value);
    if (pair == NULL)
    {
      Py_DECREF (result);
      return NULL;
    }
    if (PyList_Append (result, pair) == -1)
    {
      Py_DECREF (result);
      Py_DECREF (pair);
      return NULL;
    }
    /* Append increment the counter */
    Py_DECREF (pair);
  }

  return result;
}


static PyObject *
PyMessage_get_header (PyMessage * self, PyObject * args, PyObject *kwdict)
{
  char * name;
  const char * value;

  if (!PyArg_ParseTuple (args, "s", &name))
    return NULL;

  value = soup_message_headers_get_one (self->s_msg->request_headers, name);
  if (value == NULL)
    Py_RETURN_NONE;

  return PyString_FromString (value);
}


static PyObject *
PyMessage_get_host (PyMessage * self, PyObject * args, PyObject *kwdict)
{
  SoupURI * s_uri;

  s_uri = soup_message_get_uri (self->s_msg);
  return PyString_FromString(s_uri->host);
}


static PyObject *
PyMessage_get_method (PyMessage * self, PyObject * args, PyObject *kwdict)
{
  return PyString_FromString (self->s_msg->method);
}


static PyObject *
PyMessage_get_query (PyMessage * self, PyObject * args, PyObject *kwdict)
{
  SoupURI * s_uri;

  s_uri = soup_message_get_uri (self->s_msg);
  if (s_uri->query == NULL)
    Py_RETURN_NONE;

  return PyString_FromString(s_uri->query);
}


static PyObject *
PyMessage_append_header (PyMessage * self, PyObject * args, PyObject *kwdict)
{
  char *name, *value;

  if (!PyArg_ParseTuple (args, "ss", &name, &value))
    return NULL;

  soup_message_headers_append (self->s_msg->response_headers, name, value);

  Py_RETURN_NONE;
}


static PyObject *
PyMessage_set_header (PyMessage * self, PyObject * args, PyObject *kwdict)
{
  char *name, *value;

  if (!PyArg_ParseTuple (args, "ss", &name, &value))
    return NULL;

  soup_message_headers_replace (self->s_msg->response_headers, name, value);

  Py_RETURN_NONE;
}


static PyObject *
PyMessage_set_response (PyMessage * self, PyObject * args, PyObject *kwdict)
{
  char *content_type, *body;
  int content_length;

  if (!PyArg_ParseTuple (args, "ss#", &content_type, &body, &content_length))
    return NULL;

  soup_message_set_response (self->s_msg, content_type, SOUP_MEMORY_COPY, body,
                             (gsize)content_length);

  Py_RETURN_NONE;
}


static PyObject *
PyMessage_set_status (PyMessage * self, PyObject * args, PyObject * kwdict)
{
  guint status;

  if (!PyArg_ParseTuple (args, "I", &status))
    return NULL;

  soup_message_set_status (self->s_msg, status);

  Py_RETURN_NONE;
}


static PyMethodDef PyMessage_methods[] = {
  {"append_header", (PyCFunction) PyMessage_append_header, METH_VARARGS,
   "Append the given response header"},
  {"get_request_line", (PyCFunction) PyMessage_get_request_line, METH_NOARGS,
   "Returns the request line"},
  {"get_body", (PyCFunction) PyMessage_get_body, METH_NOARGS,
   "Returns the body of the request"},
  {"get_headers", (PyCFunction) PyMessage_get_headers, METH_NOARGS,
   "Returns all the headers of the request"},
  {"get_header", (PyCFunction) PyMessage_get_header, METH_VARARGS,
   "Returns the value of the given request header"},
  {"get_host", (PyCFunction) PyMessage_get_host, METH_NOARGS,
   "Get the host from the request uri"},
  {"get_method", (PyCFunction) PyMessage_get_method, METH_NOARGS,
   "Get the request method"},
  {"get_query", (PyCFunction) PyMessage_get_query, METH_NOARGS,
   "Get the query from the request uri"},
  {"set_header", (PyCFunction) PyMessage_set_header, METH_VARARGS,
   "Set the given response header"},
  {"set_response", (PyCFunction) PyMessage_set_response, METH_VARARGS,
   "Set the response body"},
  {"set_status", (PyCFunction) PyMessage_set_status, METH_VARARGS,
   "Set the response status code"},
  {NULL} /* Sentinel */
};


static PyTypeObject PyMessageType = {
  PyObject_HEAD_INIT(NULL)
  0,                                         /* ob_size */
  "itools.http.soup.SoupMessage",            /* tp_name */
  sizeof (PyMessage),                        /* tp_basicsize */
  0,                                         /* tp_itemsize */
  (destructor) PyMessage_dealloc,            /* tp_dealloc */
  0,                                         /* tp_print */
  0,                                         /* tp_getattr */
  0,                                         /* tp_setattr */
  0,                                         /* tp_compare */
  0,                                         /* tp_repr */
  0,                                         /* tp_as_number */
  0,                                         /* tp_as_sequence */
  0,                                         /* tp_as_mapping */
  0,                                         /* tp_hash */
  0,                                         /* tp_call */
  0,                                         /* tp_str */
  0,                                         /* tp_getattro */
  0,                                         /* tp_setattro */
  0,                                         /* tp_as_buffer */
  Py_TPFLAGS_DEFAULT,                        /* tp_flags */
  "Wrapper of SoupMessage",                  /* tp_doc */
  0,                                         /* tp_traverse */
  0,                                         /* tp_clear */
  0,                                         /* tp_richcompare */
  0,                                         /* tp_weaklistoffset */
  0,                                         /* tp_iter */
  0,                                         /* tp_iternext */
  PyMessage_methods,                         /* tp_methods */
  0,                                         /* tp_members */
  0,                                         /* tp_getset */
  0,                                         /* tp_base */
  0,                                         /* tp_dict */
  0,                                         /* tp_descr_get */
  0,                                         /* tp_descr_set */
  0,                                         /* tp_dictoffset */
  (initproc) PyMessage_init,                 /* tp_init */
  0,                                         /* tp_alloc */
  (newfunc) PyMessage_new,                   /* tp_new */
};


/**************************************************************************
 * PyServer
 *************************************************************************/

typedef struct
{
  PyObject_HEAD
  SoupServer * s_server;
} PyServer;


void
s_server_callback (SoupServer * s_server, SoupMessage * s_msg,
                   const char * path, GHashTable * g_query,
                   SoupClientContext * s_client, gpointer user_data)
{
  PyMessage * p_message;
  PyObject * p_callback;
  PyObject * p_args;
  PyObject * p_result;

  /* Create the Python Message object */
  p_message = PyObject_New (PyMessage, &PyMessageType);
  if (!p_message)
    return;

  p_message->s_msg = s_msg;

  /* Call the Python callback */
  p_args = Py_BuildValue("(Ns)", p_message, path);
  if (!p_args)
    return;

  p_callback = (PyObject*) user_data;
  p_result = PyObject_CallObject (p_callback, p_args);
  if (!p_result)
    {
      printf("ERROR! Python's callback failed, this should never happen\n");
      abort ();
    }

  return;
}


static int
PyServerType_init (PyServer * self, PyObject * args, PyObject * kwdict)
{
  /* Initialization of the Glib interface */
  /* http://bugzilla.gnome.org/show_bug.cgi?id=532778 */
  if (!g_thread_supported ())
    g_thread_init (NULL);
  g_type_init();

  /* Ok */
  return 0;
}


static PyObject *
PyServerType_listen (PyServer * self, PyObject * args, PyObject * kwdict)
{
  /* libsoup variables */
  guint signal_id;
  char *address = NULL;
  guint port = 8080;
  SoupServer *s_server;
  SoupAddress *s_address = NULL;

  /* Arguments */
  if (!PyArg_ParseTuple (args, "zI", &address, &port))
    return NULL;

  /* s_address */
  if ( (address != NULL) && (strcmp(address, "") != 0) )
    s_address = soup_address_new (address, port);
  else
    s_address = soup_address_new_any (SOUP_ADDRESS_FAMILY_IPV4, port);

  if (!s_address)
  {
    PyErr_Format (PyExc_RuntimeError, "Bad address/port arguments");
    return NULL;
  }
  soup_address_resolve_sync(s_address, NULL);

  /* s_server */
  s_server = soup_server_new (SOUP_SERVER_SERVER_HEADER, "itools.http",
                              SOUP_SERVER_INTERFACE, s_address, NULL);
  if (!s_server)
  {
    PyErr_Format (PyExc_RuntimeError, "could not make the SoupServer");
    return NULL;
  }
  self->s_server = s_server;

  /* Signals */
  signal_id = g_signal_lookup ("request-finished", SOUP_TYPE_SERVER);
  g_signal_add_emission_hook (signal_id, 0, log_access, self, NULL);

  signal_id = g_signal_lookup ("request-aborted", SOUP_TYPE_SERVER);
  g_signal_add_emission_hook (signal_id, 0, log_access, self, NULL);

  /* Go */
  soup_server_run_async (self->s_server);

  Py_RETURN_NONE;
}


static PyObject *
PyServerType_stop (PyServer * self, PyObject * args, PyObject * kwdict)
{
  soup_server_quit (self->s_server);

  Py_RETURN_NONE;
}


static PyObject *
PyServerType_add_handler (PyServer * self, PyObject * args, PyObject * kwdict)
{
  char * path;
  PyObject * p_user_data;

  if (!PyArg_ParseTuple (args, "sO", &path, &p_user_data))
    return NULL;

  Py_INCREF (p_user_data);
  soup_server_add_handler (self->s_server, path, s_server_callback,
                           (gpointer) p_user_data, NULL);

  Py_RETURN_NONE;
}


static PyMethodDef PyServer_methods[] = {
  {"listen", (PyCFunction) PyServerType_listen, METH_VARARGS,
   "Listen to the given interface and port"},
  {"stop", (PyCFunction) PyServerType_stop, METH_NOARGS, "Stop the server"},
  {"add_handler", (PyCFunction) PyServerType_add_handler, METH_VARARGS,
   "Adds a handler for requests under path"},
  {NULL} /* Sentinel */
};


static PyTypeObject PyServerType = {
  PyObject_HEAD_INIT(NULL)
  0,                                         /* ob_size */
  "itools.http.soup.SoupServer",             /* tp_name */
  sizeof (PyServer),                         /* tp_basicsize */
  0,                                         /* tp_itemsize */
  0,                                         /* tp_dealloc */
  0,                                         /* tp_print */
  0,                                         /* tp_getattr */
  0,                                         /* tp_setattr */
  0,                                         /* tp_compare */
  0,                                         /* tp_repr */
  0,                                         /* tp_as_number */
  0,                                         /* tp_as_sequence */
  0,                                         /* tp_as_mapping */
  0,                                         /* tp_hash */
  0,                                         /* tp_call */
  0,                                         /* tp_str */
  0,                                         /* tp_getattro */
  0,                                         /* tp_setattro */
  0,                                         /* tp_as_buffer */
  Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,  /* tp_flags */
  "HTTP Server",                             /* tp_doc */
  0,                                         /* tp_traverse */
  0,                                         /* tp_clear */
  0,                                         /* tp_richcompare */
  0,                                         /* tp_weaklistoffset */
  0,                                         /* tp_iter */
  0,                                         /* tp_iternext */
  PyServer_methods,                          /* tp_methods */
  0,                                         /* tp_members */
  0,                                         /* tp_getset */
  0,                                         /* tp_base */
  0,                                         /* tp_dict */
  0,                                         /* tp_descr_get */
  0,                                         /* tp_descr_set */
  0,                                         /* tp_dictoffset */
  (initproc) PyServerType_init,              /* tp_init */
  0,                                         /* tp_alloc */
  PyType_GenericNew,                         /* tp_new */
};



/**************************************************************************
 * Declaration of the module
 *************************************************************************/

static PyMethodDef module_methods[] = {
  {NULL}                        /* Sentinel */
};


/* declarations for DLL import/export */
#ifndef PyMODINIT_FUNC
#define PyMODINIT_FUNC void
#endif

/* Declaration */
PyMODINIT_FUNC
initsoup (void)
{
  PyObject *module;

  /* Intialilze module */
  module = Py_InitModule3 ("soup", module_methods, "Wrapper of libsoup");
  if (module == NULL)
    return;

  /* Server Type */
  if (PyType_Ready (&PyServerType) != 0)
    return;
  Py_INCREF (&PyServerType);
  PyModule_AddObject (module, "SoupServer", (PyObject *) & PyServerType);

  /* Message Type */
  if (PyType_Ready (&PyMessageType) != 0)
    return;
  Py_INCREF (&PyMessageType);
  PyModule_AddObject (module, "SoupMessage", (PyObject *) & PyMessageType);
}

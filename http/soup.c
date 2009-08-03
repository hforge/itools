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

/* Variable names are prefixed by one letter:
 *   p_xxx - is a Python object
 *   g_xxx - is a glib object
 *   s_xxx - is a libsoup object
 *
 * Variables without a prefix are standard C types.
 */



/*
 * HTTP Server
 */

typedef struct
{
  PyObject_HEAD
} Server;


void
s_server_callback (SoupServer * s_server, SoupMessage * s_msg,
                   const char * path, GHashTable * g_query,
                   SoupClientContext * s_client, gpointer server)
{
  PyObject * p_result;

  if (!PyObject_CallMethod (server, "callback", NULL))
    /* TODO How to trigger the Python error? */
    printf("Error\n");
}


static PyObject *
PyServer_start (PyObject * self, PyObject * args, PyObject * kwdict)
{
  /* Defines the parameters */
  static char *kwlist[] = { "address", "port", NULL };
  char *address = "";
  guint port = 8080;
  /* Glib and libsoup variables */
  GMainLoop *g_mainloop;
  SoupAddress *s_address;
  SoupServer *s_server;

  /* Arguments */
  if (!PyArg_ParseTupleAndKeywords (args, kwdict, "|sI", kwlist, &address,
                                    &port))
    return NULL;

  /* HTTP Server */
  printf("Listen %s:%d\n", address, port);
  g_thread_init (NULL); /* http://bugzilla.gnome.org/show_bug.cgi?id=532778 */

  /* TODO This does not work, soup_server_new fails with SOUP_SERVER_INTERFACE
   * Loosely related, http://bugzilla.gnome.org/show_bug.cgi?id=561547
   */
  s_address = soup_address_new (address, port);
  if (!s_address)
    /* TODO Set Python error condition */
    return NULL;

  s_server = soup_server_new (SOUP_SERVER_SERVER_HEADER, "itools.http",
                              /* SOUP_SERVER_INTERFACE, s_address, */
                              SOUP_SERVER_PORT, port, NULL);
  if (!s_server)
    /* TODO Set Python error condition */
    return NULL;

  /* Handler */
  soup_server_add_handler (s_server, "/", s_server_callback, self, NULL);

  /* Run */
  soup_server_run_async (s_server);
  g_mainloop = g_main_loop_new (NULL, FALSE);
  g_main_loop_run (g_mainloop);

  Py_RETURN_NONE;
}


static PyMethodDef PyServer_methods[] = {
  {"start", (PyCFunction) PyServer_start, METH_VARARGS | METH_KEYWORDS,
   "Start the server"},
  {NULL} /* Sentinel */
};


static PyTypeObject PyServer = {
  PyObject_HEAD_INIT(NULL)
  0,                                         /* ob_size */
  "itools.http.soup.SoupServer",             /* tp_name */
  sizeof (Server),                           /* tp_basicsize */
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
  0,                                         /* tp_init */
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

  /* Server Object */
  if (PyType_Ready (&PyServer) != 0)
    return;
  Py_INCREF (&PyServer);
  PyModule_AddObject (module, "SoupServer", (PyObject *) & PyServer);
}

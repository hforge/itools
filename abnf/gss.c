#include <Python.h>
#include "structmember.h"


typedef struct
{
  PyObject_HEAD int number;
} GSS;


static void
GSS_dealloc (GSS * self)
{
  self->ob_type->tp_free ((PyObject *) self);
}


static PyObject *
GSS_new (PyTypeObject * type, PyObject * args, PyObject * kwds)
{
  GSS *self;

  self = (GSS *) type->tp_alloc (type, 0);
  if (self != NULL)
    {
      self->number = 0;
    }

  return (PyObject *) self;
}


static int
GSS_init (GSS * self, PyObject * args, PyObject * kwds)
{
  PyObject *first = NULL, *last = NULL, *tmp;

  static char *kwlist[] = { "number", NULL };

  if (!PyArg_ParseTupleAndKeywords (args, kwds, "|i", kwlist, &self->number))
    return -1;

  return 0;
}


static PyObject *
GSS_get_number (GSS * self)
{
  return PyInt_FromLong (self->number);
}


static PyMethodDef GSS_methods[] = {
  {"get_number", (PyCFunction) GSS_get_number, METH_NOARGS,
   "Return the number"},
  {NULL}                        /* Sentinel */
};

static PyTypeObject GSSType = {
  PyObject_HEAD_INIT (NULL) 0,  /*ob_size */
  "gss.GSS",                    /*tp_name */
  sizeof (GSS),                 /*tp_basicsize */
  0,                            /*tp_itemsize */
  (destructor) GSS_dealloc,     /*tp_dealloc */
  0,                            /*tp_print */
  0,                            /*tp_getattr */
  0,                            /*tp_setattr */
  0,                            /*tp_compare */
  0,                            /*tp_repr */
  0,                            /*tp_as_number */
  0,                            /*tp_as_sequence */
  0,                            /*tp_as_mapping */
  0,                            /*tp_hash */
  0,                            /*tp_call */
  0,                            /*tp_str */
  0,                            /*tp_getattro */
  0,                            /*tp_setattro */
  0,                            /*tp_as_buffer */
  Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,     /*tp_flags */
  "GSS object",                 /* tp_doc */
  0,                            /* tp_traverse */
  0,                            /* tp_clear */
  0,                            /* tp_richcompare */
  0,                            /* tp_weaklistoffset */
  0,                            /* tp_iter */
  0,                            /* tp_iternext */
  GSS_methods,                  /* tp_methods */
  0,                            /* tp_members */
  0,                            /* tp_getset */
  0,                            /* tp_base */
  0,                            /* tp_dict */
  0,                            /* tp_descr_get */
  0,                            /* tp_descr_set */
  0,                            /* tp_dictoffset */
  (initproc) GSS_init,          /* tp_init */
  0,                            /* tp_alloc */
  GSS_new,                      /* tp_new */
};

static PyMethodDef module_methods[] = {
  {NULL}                        /* Sentinel */
};

#ifndef PyMODINIT_FUNC          /* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
initgss (void)
{
  PyObject *m;

  if (PyType_Ready (&GSSType) < 0)
    return;

  m = Py_InitModule3 ("gss", module_methods,
                      "A fast implementation of a GSS.");

  if (m == NULL)
    return;

  Py_INCREF (&GSSType);
  PyModule_AddObject (m, "GSS", (PyObject *) & GSSType);
}

#include <Python.h>
#include "structmember.h"


/************************
 * An iterator for Node *
 ************************/

typedef struct
{
  PyObject_HEAD
  PyObject * node;
  unsigned children_number;
  PyObject **current_child;
  unsigned current_position;
} NodeIterator;


static void
NodeIterator_dealloc (NodeIterator * self)
{
  Py_XDECREF (self->node);
  self->ob_type->tp_free ((PyObject *) self);
}


static PyObject *
NodeIterator_next (NodeIterator * self)
{
  PyObject *child;

  /* The End ? */
  if (self->current_position >= self->children_number)
    return NULL;

  /* All OK */
  child = *(self->current_child);
  self->current_child++;
  self->current_position++;

  Py_INCREF (child);
  return child;
}


static PyTypeObject NodeIteratorType = {
  PyObject_HEAD_INIT (NULL) 0,  /*ob_size */
  "gss.NodeIterator",           /*tp_name */
  sizeof (NodeIterator),        /*tp_basicsize */
  0,                            /*tp_itemsize */
  (destructor) NodeIterator_dealloc,    /*tp_dealloc */
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
  Py_TPFLAGS_DEFAULT,           /*tp_flags */
  "NodeIterator object",        /* tp_doc */
  0,                            /* tp_traverse */
  0,                            /* tp_clear */
  0,                            /* tp_richcompare */
  0,                            /* tp_weaklistoffset */
  PyObject_SelfIter,            /* tp_iter */
  (iternextfunc) NodeIterator_next,     /* tp_iternext */
  0,                            /* tp_methods */
  0                             /* tp_members */
};


/*******************
 * The Node object *
 *******************/

typedef struct
{
  PyObject_HEAD
  PyObject * data;
  PyObject **children;
  unsigned children_number;
} Node;

static PyTypeObject NodeType;


static PyObject *
Node_new (PyTypeObject * type, PyObject * args, PyObject * kwds)
{
  Node *self;

  self = (Node *) type->tp_alloc (type, 0);
  if (self != NULL)
    {
      /* We store None by default */
      Py_INCREF (Py_None);
      self->data = Py_None;

      /* 0 child by default */
      self->children = NULL;
      self->children_number = 0;
    }

  return (PyObject *) self;
}


static void
Node_dealloc (Node * self)
{
  unsigned i;
  PyObject **child_pt;

  /* data */
  Py_XDECREF (self->data);

  /* The children */
  if (self->children)
    for (i = 0, child_pt = self->children;
         i < self->children_number;
         i++, child_pt++)
      Py_DECREF (*child_pt);
  PyMem_Free (self->children);

  /* The object itself */
  self->ob_type->tp_free ((PyObject *) self);
}


static int
Node_init (Node * self, PyObject * args, PyObject * kwds)
{
  PyObject *data = NULL, *tmp;
  static char *kwlist[] = { "data", NULL };

  if (!PyArg_ParseTupleAndKeywords (args, kwds, "|O", kwlist, &data))
    return -1;

  if (data)
    {
      tmp = self->data;
      Py_INCREF (data);
      self->data = data;
      Py_XDECREF (tmp);
    }

  return 0;
}


static PyObject *
Node_append (Node * self, PyObject * args)
{
  Node *child;
  PyObject **children;
  unsigned children_number;

  /* child is a Node ? */
  if (!PyArg_ParseTuple (args, "O!", &NodeType, (PyObject *)&child))
    return NULL;

  /* child OK */
  children = child->children;
  children_number = child->children_number;

  /* Make place for the new child */
  children = (PyObject **) PyMem_Realloc (children,
                                          (children_number + 1) *
                                          sizeof (PyObject *));
  if (children == NULL)
    return PyErr_NoMemory ();

  /* All OK */
  children[children_number] = (PyObject *)self;
  child->children = children;
  child->children_number = children_number + 1;
  Py_INCREF (self);

  Py_RETURN_NONE;
}


static PyObject *
Node_iter (Node * self)
{
  NodeIterator *iter;

  /* Creation */
  iter = PyObject_New (NodeIterator, &NodeIteratorType);
  if (!iter)
    return NULL;

  /* Save the node */
  Py_INCREF (self);
  iter->node = (PyObject *) self;

  /* Set the parameters */
  iter->children_number = self->children_number;
  iter->current_child = self->children;
  iter->current_position = 0;

  return (PyObject *) iter;
}


static PyMethodDef Node_methods[] = {
  {"append", (PyCFunction) Node_append, METH_VARARGS,
   "Append a new child (a Node)."},
  {NULL}                        /* Sentinel */
};


static PyMemberDef Node_members[] = {
  {"data", T_OBJECT_EX, offsetof (Node, data), 0, "data"},
  {NULL}                        /* Sentinel */
};


static PyTypeObject NodeType = {
  PyObject_HEAD_INIT (NULL) 0,  /*ob_size */
  "gss.Node",                   /*tp_name */
  sizeof (Node),                /*tp_basicsize */
  0,                            /*tp_itemsize */
  (destructor) Node_dealloc,    /*tp_dealloc */
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
  "Node object",                /* tp_doc */
  0,                            /* tp_traverse */
  0,                            /* tp_clear */
  0,                            /* tp_richcompare */
  0,                            /* tp_weaklistoffset */
  (getiterfunc) Node_iter,      /* tp_iter */
  0,                            /* tp_iternext */
  Node_methods,                 /* tp_methods */
  Node_members,                 /* tp_members */
  0,                            /* tp_getset */
  0,                            /* tp_base */
  0,                            /* tp_dict */
  0,                            /* tp_descr_get */
  0,                            /* tp_descr_set */
  0,                            /* tp_dictoffset */
  (initproc) Node_init,         /* tp_init */
  0,                            /* tp_alloc */
  Node_new,                     /* tp_new */
};


/**********************
 * Module declaration *
 **********************/

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

  if (PyType_Ready (&NodeType) < 0)
    return;

  m = Py_InitModule3 ("gss", module_methods,
                      "A fast implementation of a GSS.");

  if (m == NULL)
    return;

  Py_INCREF (&NodeType);
  PyModule_AddObject (m, "Node", (PyObject *) & NodeType);

  PyType_Ready (&NodeIteratorType);
}

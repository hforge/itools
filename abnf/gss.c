/*
 * Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

/* The GLib */
#include <glib.h>
/* Python */
#include <Python.h>
#include "structmember.h"

#define NODE_TO_PY_ID(node) PyInt_FromLong(GPOINTER_TO_UINT((gpointer)node))
#define GET_NODE_BY_PY_ID(py_id) \
    (Node*)GUINT_TO_POINTER(PyInt_AsUnsignedLongMask(py_id))


/* Replaces the pointer at the given index by a new one, returns the old one.
 * XXX This function should be included in the GLib.
 */
gpointer
g_ptr_array_replace(GPtrArray *array, guint index, gpointer data) {
    gpointer result;

    g_return_val_if_fail(array, NULL);
    g_return_val_if_fail(index < array->len, NULL);

    result = array->pdata[index];
    array->pdata[index] = data;
    return result;
}


/* Define the nodes of the Graph Structured Stack (GSS). */
typedef struct {
    GPtrArray* prev_nodes; /* Pointers to the previous nodes. */
    PyObject* py_state;
    PyObject* py_data;     /* The stored (Python) data. */
    guint refcount;        /* How many other nodes point to me. */
} Node;


/* Creates, intializes and returns new node. */
Node*
Node_new(PyObject* py_state, PyObject* py_data) {
    Node* node;

    /* Allocate memory. */
    node = malloc(sizeof(Node));
    /* Initialize members. */
    node->prev_nodes = g_ptr_array_new();
    node->py_state = py_state;
    Py_INCREF(py_state);
    node->py_data = py_data;
    Py_INCREF(py_data);
    node->refcount = 1;

    return node;
}


/* The Graph Structured Stack. */
typedef struct {
    PyObject_HEAD
    GPtrArray* top_nodes;
} GSS;


/* Called when a GSS object is created. */
static PyObject*
GSS_new(PyTypeObject* type, PyObject* args, PyObject* kw) {
    GSS* self;

    /* Python's boilerplate. */
    self = (GSS*)type->tp_alloc(type, 0);
    if (self == NULL) return NULL;

    /* Specifics. */
    self->top_nodes = g_ptr_array_sized_new(10);

    return (PyObject*)self;
}


/* Private: reduces the refcount of the given node.  If it reaches "0" the
 * node is freed, and the same function is applied recursively to its
 * previous nodes.
 *
 * Returns True if th node was freed, False otherwise.
 */
gboolean
free_node(GSS* self, Node* node) {
    guint i;
    Node* prev_node;

    /* Reduce refcount. */
    node->refcount--;
    if (node->refcount > 0)
        return FALSE;

    /* Free previous nodes. */
    for (i=0; i < node->prev_nodes->len; i++) {
        prev_node = (Node*)g_ptr_array_index(node->prev_nodes, i);
        free_node(self, prev_node);
    }
    /* Free this node. */
    g_ptr_array_free(node->prev_nodes, TRUE);
    Py_DECREF(node->py_state);
    Py_DECREF(node->py_data);
    free(node);

    return TRUE;
}


/* Private: reset the GSS (used by dealloc and init). */
void
GSS_reset(GSS* self) {
    Node *node;
    guint idx;

    /* Free all the nodes. */
    for (idx=0; idx < self->top_nodes->len; idx++) {
        node = (Node*)g_ptr_array_index(self->top_nodes, idx);
        free_node(self, node);
    }
    g_ptr_array_set_size(self->top_nodes, 0);
}


/* Called when a GSS object is destroyed. */
static void
GSS_dealloc(GSS* self) {
    GSS_reset(self);
    g_ptr_array_free(self->top_nodes, TRUE);

    /* Python's boilerplate. */
    self->ob_type->tp_free((PyObject*)self);
}


/* Called to initialize the GSS object (the "__init__" method). */
static int
GSS_init(GSS* self, PyObject* args, PyObject* kw) {
    PyObject *py_state, *py_data;
    Node* node;
    int ok;

    /* Reset the stack state. */
    GSS_reset(self);

    /* Parse the input parameters. */
    ok = PyArg_ParseTuple(args, "O!O", &PyInt_Type, &py_state, &py_data);
    if (!ok)
        return -1;

    /* Create and push the root node. */
    node = Node_new(py_state, py_data);
    g_ptr_array_add(self->top_nodes, (gpointer)node);

    return 0;
}


/* Public: shift the given token in all the stacks. */
guint
py_int_hash(gconstpointer py_value) {
    return (guint)PyInt_AsLong((PyObject*)py_value);
}

gboolean
py_int_equal(gconstpointer py_v1, gconstpointer py_v2) {
    return PyInt_AsLong((PyObject*)py_v1) == PyInt_AsLong((PyObject*)py_v2);
}


static PyObject*
GSS_shift_token(GSS* self, PyObject* args) {
    PyObject *py_token, *py_table, *py_data, *py_key, *py_state;
    GHashTable *map;
    gboolean error;
    guint idx;
    Node *last_node, *next_node;
    int contains;

    /* Parse the input parameters. */
    error = PyArg_ParseTuple(args, "O!O!O", &PyInt_Type, &py_token,
            &PyDict_Type, &py_table, &py_data);
    if (error) return NULL;

    /* Keep a map from states to nodes (to have common suffixes). */
    map = g_hash_table_new((GHashFunc)py_int_hash, (GEqualFunc)py_int_equal);

    /* Iterate over each stack and shift the given token. */
    idx = 0;
    while (idx < self->top_nodes->len) {
        last_node = (Node*)g_ptr_array_index(self->top_nodes, idx);
        /* Table lookup. */
        py_key = PyTuple_Pack(2, last_node->py_state, py_token);
        if (py_key == NULL) return NULL;
        contains = PyDict_Contains(py_table, py_key);
        if (contains == -1) {
            Py_DECREF(py_key);
            return NULL;
        }
        /* Failure: drop branch. */
        if (contains == 0) {
            Py_DECREF(py_key);
            g_ptr_array_remove_index_fast(self->top_nodes, idx);
            free_node(self, last_node);
            continue;
        }
        /* Success: shift. */
        py_state = PyDict_GetItem(py_table, py_key);
        Py_DECREF(py_key);
        if (py_state == NULL) return NULL;
        next_node = g_hash_table_lookup(map, py_state);
        if (next_node == NULL) {
            /* Create and add the new node. */
            next_node = Node_new(py_state, py_data);
            g_ptr_array_replace(self->top_nodes, idx, (gpointer)next_node);
        }
        /* Update the top stack and continue. */
        g_ptr_array_add(next_node->prev_nodes, (gpointer)last_node);
        idx++;
    }

    /* Free allocated memory. */
    g_hash_table_destroy(map);

    /* Return always None. */
    Py_INCREF(Py_None);
    return Py_None;
}


/* Public: returns the node id and state of the top node of the given stack
 * index.
 */
static PyObject*
GSS_get_top_node(GSS* self, PyObject* py_index) {
    PyObject *py_node_id, *py_result;
    guint index;
    Node* node;

    /* Parse the input parameters. */
    index = (guint)PyInt_AsLong(py_index);

    /* Check boundaries. */
    if (index >= self->top_nodes->len) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    /* Lookup and return. */
    node = (Node*)g_ptr_array_index(self->top_nodes, index);
    py_node_id = NODE_TO_PY_ID(node);
    py_result = PyTuple_Pack(2, py_node_id, node->py_state);
    Py_DECREF(py_node_id);

    return py_result;
}


/* Public: for a given node, make "n" steps back, and return all possible
 * paths.
 */
static PyObject*
GSS_reduce(GSS* self, PyObject* args) {
    PyObject* py_list, py_item, py_node_id, py_state, py_values;
    guint n;
    Node* node;
    int ok, error;

    /* Parse the input parameters. */
    ok = PyArg_ParseTuple(args, "O!I", &PyInt_Type, &py_node_id, &n);
    if (!ok) return NULL;

    /* Initialize the result. */
    py_list = PyList_New(0);
    g_return_val_if_fail(py_list, NULL);
    node = GET_NODE_BY_PY_ID(py_node_id);
    py_state = PyInt_FromLong(node->state);
    py_values = PyList_New(0);
    if (py_values == NULL) {
        Py_DECREF(py_list);
        Py_DECREF(py_state);
        return NULL;
    }
    error = PyList_Append(py_values, node->py_data);
    if (error) {
        Py_DECREF(py_list);
        Py_DECREF(py_state);
        Py_DECREF(py_values);
        return NULL;
    }
    py_item = PyTuple_Pack(3, py_node_id, py_state, py_values);
    if (py_item == NULL) {
        Py_DECREF(py_list);
        Py_DECREF(py_state);
        Py_DECREF(py_values);
        return NULL;
    }
    error = PyList_Append(py_list, py_item);
    if (error) {
        Py_DECREF(py_list);
        return NULL;
    }

    /* Step back. */
    while (n > 0) {

        /* Next. */
        n--;
    }
    /* Get start node. */
    node = (Node*)GUINT_TO_POINTER(node_id);



    return py_list;
}


/* XXX Public: return a Python list with the ids of the top nodes. */
static PyObject* GSS_get_top_node_ids(GSS* self) {
    PyObject* py_list;
    PyObject* py_node_id;
    gpointer node;
    guint i;
    int error;

    py_list = PyList_New(0);
    for (i=0; i < self->top_nodes->len; i++) {
        node = g_ptr_array_index(self->top_nodes, i);
        py_node_id = PyInt_FromLong(GPOINTER_TO_UINT(node));
        error = PyList_Append(py_list, py_node_id);
        Py_DECREF(py_node_id);
        if (error) {
            Py_DECREF(py_list);
            return NULL;
        }
    }

    return py_list;
}


/* XXX Public: return the data attached to the given node id. */
static PyObject* GSS_get_node_data(GSS* self, PyObject* py_node_id) {
    Node* node;

    node = GET_NODE_BY_ID(py_node_id);
    /* Return the data. */
    Py_INCREF(node->py_data);
    return node->py_data;
}


/* XXX Public: free the node identified by the given node id. */
static PyObject* GSS_free_node(GSS* self, PyObject* py_node_id) {
    Node* node;

    node = GET_NODE_BY_ID(py_node_id);
    /* Free the node. */
    if (free_node(self, node) == TRUE) {
        Py_INCREF(Py_True);
        return Py_True;
    }

    Py_INCREF(Py_False);
    return Py_False;
}


/**************************************************************************
 * Declaration of the GSS Python type.
 *************************************************************************/

/* The GSS object: members. */
static PyMemberDef GSS_members[] = {
    {NULL}
};


/* The GSS object: methods. */
static PyMethodDef GSS_methods[] = {
    {"shift_token", (PyCFunction)GSS_shift_token, METH_VARARGS,
     "Adds a new node to the stack, which becomes the new top."},
    {"get_top_node", (PyCFunction)GSS_get_top_node, METH_O,
     "Returns the top node of the given stack index."},
    {"reduce", (PyCFunction)GSS_reduce, METH_VARARGS,
     "Make n steps back from a given node, and return all possible paths."},

    {"get_top_node_ids", (PyCFunction)GSS_get_top_node_ids, METH_NOARGS,
     "Returns the data attached to the given node."},
    {"get_node_data", (PyCFunction)GSS_get_node_data, METH_O,
     "Returns the data attached to the given node."},
    {"free_node", (PyCFunction)GSS_free_node, METH_O,
     "Reduces the refcount of the node, if it reaches 0 the node is freed."},
    {NULL}
};


/* The GSS object. */
static PyTypeObject GSSType = {
    PyObject_HEAD_INIT(NULL)
    0,                              /* ob_size */
    "itools.abnf.gss.GSS",          /* tp_name */
    sizeof(GSS),                    /* tp_basicsize */
    0,                              /* tp_itemsize */
    (destructor)GSS_dealloc,        /* tp_dealloc */
    0,                              /* tp_print */
    0,                              /* tp_getattr */
    0,                              /* tp_setattr */
    0,                              /* tp_compare */
    0,                              /* tp_repr */
    0,                              /* tp_as_number */
    0,                              /* tp_as_sequence */
    0,                              /* tp_as_mapping */
    0,                              /* tp_hash */
    0,                              /* tp_call */
    0,                              /* tp_str */
    0,                              /* tp_getattro */
    0,                              /* tp_setattro */
    0,                              /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,             /* tp_flags */
    "Graph Structured Stack",       /* tp_doc */
    0,                              /* tp_traverse */
    0,                              /* tp_clear */
    0,                              /* tp_richcompare */
    0,                              /* tp_weaklistoffset */
    0,                              /* tp_iter */
    0,                              /* tp_iternext */
    GSS_methods,                    /* tp_methods */
    GSS_members,                    /* tp_members */
    0,                              /* tp_getset */
    0,                              /* tp_base */
    0,                              /* tp_dict */
    0,                              /* tp_descr_get */
    0,                              /* tp_descr_set */
    0,                              /* tp_dictoffset */
    (initproc)GSS_init,             /* tp_init */
    0,                              /* tp_alloc */
    GSS_new,                     /* tp_new */
};


/**************************************************************************
 * Initialization.
 *************************************************************************/

/* Definition of the module functions. */
static PyMethodDef module_methods[] = {
    {NULL}
};


/* declarations for DLL import/export. */
#ifndef PyMODINIT_FUNC
#define PyMODINIT_FUNC void
#endif


/* Function called to initialize the module. */
PyMODINIT_FUNC
initgss(void) {
    PyObject* module;

    if (PyType_Ready(&GSSType) < 0)
        return;

    /* Initialize the module */
    module = Py_InitModule3("gss", module_methods, "Graph Structured Stack");
    if (module == NULL)
        return;

    /* Register types */
    Py_INCREF(&GSSType);
    PyModule_AddObject(module, "GSS", (PyObject*)&GSSType);

}

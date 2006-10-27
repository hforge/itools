
#include <Python.h>
#include "structmember.h"
/* To call Python from C */
#include <import.h>
#include <graminit.h>
#include <pythonrun.h>

/* Tokens */
#define XML_DECL 0
#define DOCUMENT_TYPE 1
#define START_ELEMENT 2
#define END_ELEMENT 3
#define TEXT 4
#define COMMENT 5
#define PI 6
#define CHAR_REF 7
#define ENTITY_REF 8
#define CDATA 9
#define NAMESPACE 10

/* Errors */
#define BAD_XML_DECL "XML declaration not well-formed: line %d, column %d"
#define INVALID_TOKEN "not well-formed (invalid token): line %d, column %d"
#define MISMATCH "mismatched tag: line %d, column %d"
#define UNDEFINED_ENTITY "undefined entity: line %d, column %d"

#define ERROR(msg, line, column) PyErr_Format(XMLError, msg, line, column)

/* FIXME, limits to be removed */
#define TAG_STACK_SIZE 200 /* Maximum deepness of the element tree */
#define NS_INDEX_SIZE 10
#define TOKEN_STACK_SIZE 10


/**************************************************************************
 * Exceptions
 *************************************************************************/

static PyObject* XMLError;



/**************************************************************************
 * The data structure below defines the parser state. 
 **************************************************************************/
typedef struct {
    PyObject_HEAD
    /* Specific fields */
    char* data;
    char* cursor;
    int line_no;
    int column;
    /* Tag tag stack (used to check every open tag has a close tag) */
    PyObject* tag_stack[TAG_STACK_SIZE];
    int tag_stack_top;
    /* Namespace stack */
    PyObject* tag_ns_stack[TAG_STACK_SIZE]; /* FIXME: hardcoded limit */
    int tag_ns_index[NS_INDEX_SIZE]; /* FIXME: hardcoded limit */
    int tag_ns_index_top;
    PyObject* namespaces;
    /* Token stack */
    PyObject* token_stack[TOKEN_STACK_SIZE]; /* FIXME: hardcoded limit */
    int token_stack_top;
} Parser;


static void Parser_dealloc(Parser* self) {
    self->ob_type->tp_free((PyObject*)self);
}


static int Parser_init(Parser* self, PyObject* args) {
    /* Load the input data */
    if (!PyArg_ParseTuple(args, "s", &self->data))
        return -1;

    /* Initialize variables */
    self->cursor = self->data;
    self->line_no = 1;
    self->column = 1;

    /* The stacks are empty */
    self->tag_stack_top = 0;
    self->tag_ns_index_top = 0;
    self->token_stack_top = 0;

    self->namespaces = Py_BuildValue("{}");

    return 0;
}


/* Merges two dictionaries into a new one, when conflict happens the second
 * dict has priority. */
PyObject* merge_dicts(PyObject* a, PyObject* b) {
    PyObject* c;

    /* Make a copy of "a" */
    c = PyDict_Copy(a);
    if (c == NULL)
        return NULL;

    /* Update with "b" */
    if (PyDict_Update(c, b) == -1)
        return NULL;

    return c;
}


int push_tag(Parser* self, PyObject* value, PyObject* namespaces) {
    PyObject* new_namespaces;

    if (self->tag_stack_top >= TAG_STACK_SIZE)
        return -1;

    if (PyDict_Size(namespaces)) {
        if (self->tag_ns_index_top >= NS_INDEX_SIZE)
            return -1;
        /* Create the new namespaces */
        new_namespaces = merge_dicts(self->namespaces, namespaces);
        if (new_namespaces == NULL)
            return -1;
        /* Update the current namespaces */
        self->namespaces = new_namespaces;
        /* Update ns index */
        self->tag_ns_index[self->tag_ns_index_top] = self->tag_stack_top;
        self->tag_ns_index_top++;
    } else
        new_namespaces = NULL;

    Py_INCREF(value);
    self->tag_stack[self->tag_stack_top] = value;
    self->tag_ns_stack[self->tag_stack_top] = new_namespaces;
    self->tag_stack_top++;

    return 0;
}


PyObject* pop_tag(Parser* self, PyObject* value) {
    PyObject* last_open_tag;
    PyObject* uri;

    /* Check the stack is not empty */
    if (self->tag_stack_top == 0)
        return NULL;

    /* Pop the top value from the stack */
    self->tag_stack_top--;
    last_open_tag = self->tag_stack[self->tag_stack_top];
    Py_DECREF(last_open_tag);

    /* Check the values match */
    if (PyObject_Compare(value, last_open_tag))
        return NULL;

    /* Process namespace */
    uri = PyDict_GetItem(self->namespaces, PyTuple_GetItem(value, 0));
    if (uri == NULL)
        uri = Py_BuildValue("");

    /* Namespaces */
    if (self->tag_ns_stack[self->tag_stack_top]) {
        self->tag_ns_index_top--;
        Py_DECREF(self->namespaces);
        self->namespaces = self->tag_ns_stack[self->tag_ns_index[self->tag_ns_index_top - 1]];
    }

    return Py_BuildValue("(OO)", uri, PyTuple_GetItem(value, 1));
}


/* The token stack */
int push_token(Parser* self, PyObject* value) {
    if (self->token_stack_top >= TOKEN_STACK_SIZE)
        return -1;

    Py_INCREF(value);
    self->token_stack[self->token_stack_top] = value;
    self->token_stack_top++;

    return 0;
}


PyObject* pop_token(Parser* self) {
    PyObject* value;

    if (self->token_stack_top == 0)
        return NULL;

    self->token_stack_top--;
    value = self->token_stack[self->token_stack_top];
    Py_DECREF(value);

    return value;
}



/**************************************************************************
 * The parsing code
 **************************************************************************/

/* Move forward the cursor  */
void move_cursor(Parser* self) {
    if (*(self->cursor) == '\n') {
        self->line_no++;
        self->column = 1;
    } else
        self->column++;

    self->cursor++;
}


/* Tests wether the following data matches the "expected" string, and moves
 * the cursor forward if that is the case (updates the "column" index). The
 * variable "expected" must not contain new lines, the "line_no" index is
 * not updated. */
int read_string(Parser* self, char* expected) {
    int size;

    size = strlen(expected);
    if strncmp(self->cursor, expected, size)
        return -1;

    self->cursor += size;
    self->column += size;
    return 0;
}


/* Name (http://www.w3.org/TR/REC-xml/#NT-Name) */
PyObject* xml_name(Parser* self) {
    int size;
    char c;
    char* base;

    /* First character must be a letter */
    c = *(self->cursor);
    if (!isalpha(c))
        return NULL;

    /* Get the value */
    base = self->cursor;
    self->cursor++;
    self->column++;
    for (size=1; 1; size++, self->cursor++, self->column++) {
        c = *(self->cursor);
        if (isalnum(c))
            continue;
        if ((c == '.') || (c == '-') || (c == '_') || (c == ':'))
            continue;
        break;
    }

    /* Update the state */
    return Py_BuildValue("s#", base, size);
}


/* Prefix + Name (http://www.w3.org/TR/REC-xml-names/#ns-decl) */
PyObject* xml_prefix_name(Parser* self) {
    int size;
    char c;
    char* base;
    PyObject* prefix;
    PyObject* name;

    /* First character must be a letter */
    c = *(self->cursor);
    if (!isalpha(c))
        return NULL;

    /* Get the value */
    base = self->cursor;
    self->cursor++;
    self->column++;
    for (size=1; 1; size++, move_cursor(self)) {
        c = *(self->cursor);
        if (isalnum(c))
            continue;
        if ((c == '.') || (c == '-') || (c == '_'))
            continue;
        break;
    }

    if (c == ':') {
        /* With prefix */
        prefix = Py_BuildValue("s#", base, size);
        self->cursor++;
        self->column++;
        name = xml_name(self);
        if (name == NULL)
            return NULL;
    } else {
        /* No Prefix */
        prefix = Py_BuildValue("");
        name = Py_BuildValue("s#", base, size);
    }

    return Py_BuildValue("(OO)", prefix, name);
}


/* White Space (http://www.w3.org/TR/REC-xml/#NT-S) */
int xml_space(Parser* self) {
    for (; isspace(*(self->cursor)); move_cursor(self));
    return 0;
}


/* Equal (http://www.w3.org/TR/REC-xml/#NT-Eq) */
int xml_equal(Parser* self) {
    /* White Space */
    for (; isspace(*(self->cursor)); move_cursor(self));
    /* Equal */
    if (*(self->cursor) != '=')
        return -1;
    move_cursor(self);
    /* White Space */
    for (; isspace(*(self->cursor)); move_cursor(self));
    return 0;
}

/* Attribute Value (http://www.w3.org/TR/REC-xml/#NT-EntityRef) */
PyObject* xml_entity_reference(Parser* self) {
    PyObject* value;

    value = xml_name(self);
    if (value == NULL)
        return NULL;

    if (*(self->cursor) != ';')
        return NULL;

    self->cursor++;
    self->column++;

    return value;
}

/* Attribute Value (http://www.w3.org/TR/REC-xml/#NT-CharRef) */
PyObject* xml_char_reference(Parser* self) {
    char* base;
    int size;

    base = self->cursor;
    for (size=0; *(self->cursor) != ';'; size++, move_cursor(self));
    move_cursor(self);

    return Py_BuildValue("s#", base, size);
}



/* Attribute Value (http://www.w3.org/TR/REC-xml/#NT-AttValue) */
PyObject* xml_attr_value(Parser* self) {
    int size;
    char* base;
    char c;
    char delimiter;
    PyObject* value;

    /* The heading quote */
    delimiter = *(self->cursor);
    if ((delimiter != '"') && (delimiter != '\''))
        return NULL;

    move_cursor(self);

    /* The value */
    base = self->cursor;
    for (size=0; 1; size++, move_cursor(self)) {
        c = *(self->cursor);
        if (c == '&') {
            move_cursor(self);
            if (*(self->cursor) == '#') {
                move_cursor(self);
                value = xml_char_reference(self);
                /* TODO What to do with the value? */
            } else {
                value = xml_entity_reference(self);
                if (value == NULL)
                    return NULL;
                /* TODO What to do with the value? */
            }
            PyErr_SetString(PyExc_NotImplementedError,
                            "references inside attributes not yet supported");
            return NULL;
        } else if ((c == '\0') || (c == '<'))
            return NULL;

        /* Stop */
        if (c == delimiter)
            break;
    }

    /* Update state */
    move_cursor(self);
    return Py_BuildValue("s#", base, size);
}


/* XML Declaration */


/* Document Type */
PyObject* parse_document_type(Parser* self) {
    PyObject* name;
    PyObject* system_id;
    PyObject* public_id;
    PyObject* has_internal_subset;
    char c;

    if (read_string(self, "DOCTYPE"))
        return NULL;
    xml_space(self);

    /* Name */
    name = xml_name(self);
    if (name == NULL)
        return NULL;
    xml_space(self);
    /* External ID */
    c = *(self->cursor);
    if (c == 'S') {
        if (read_string(self, "SYSTEM"))
            return NULL;
        xml_space(self);
        /* PUBLIC ID */
        public_id = Py_BuildValue("");
        /* SYSTEM ID */
        system_id = xml_attr_value(self);
        if (system_id == NULL)
            return NULL;
    } else if (c == 'P') {
        if (read_string(self, "PUBLIC"))
            return NULL;
        xml_space(self);
        /* PUBLIC ID */
        public_id = xml_attr_value(self);
        if (public_id == NULL)
            return NULL;
        xml_space(self);
        /* SYSTEM ID */
        system_id = xml_attr_value(self);
        if (system_id == NULL)
            return NULL;
    } else
        return NULL;
    /* White Space */
    xml_space(self);
    /* Internal subset */
    c = *(self->cursor);
    if (c == '[') {
        /* XXX NOT IMPLEMENTED*/
        PyErr_SetString(PyExc_NotImplementedError,
                        "internal subset not yet supported");
        return NULL;
    } else
        has_internal_subset = Py_BuildValue("");
    /* End doctype declaration */
    if (c != '>')
        return NULL;

    self->cursor++;
    self->column++;

    return Py_BuildValue("(OOOO)", name, system_id, public_id,
                         has_internal_subset);
}


static PyObject* Parser_iter(PyObject* self) {
    return self;
}


static PyObject* Parser_iternext(Parser* self) {
    char c;
    int size;
    int line;
    int column;
    char* base;
    PyObject* token;
    PyObject* value;
    PyObject* tag_uri;
    PyObject* tag_name;
    int end_tag;
    /* To call Python from C */
    PyObject* p_schemas;
    PyObject* p_get_datatype_by_uri;
    PyObject* p_datatype;
    PyObject* p_datatype_decode;
    PyObject* p_htmlentitydefs;
    PyObject* p_name2codepoint;
    /* Attributes */
    PyObject* attr;
    PyObject* attr_name;
    PyObject* attr_prefix;
    PyObject* attr_uri;
    PyObject* attr_value;
    PyObject* attributes;
    PyObject* attributes_list;
    int attributes_n;
    int idx;
    PyObject* namespace_decls;
    PyObject* namespaces;
    /* XML declaration */
    PyObject* version;
    PyObject* encoding;
    PyObject* standalone;

    /* There are tokens waiting */
    if (self->token_stack_top)
        return pop_token(self);

    /* Import from Python */
    /* from itools.schemas import get_datatype_by_uri */
    p_schemas = PyImport_ImportModule("itools.schemas");
    p_get_datatype_by_uri = PyObject_GetAttrString(p_schemas, "get_datatype_by_uri");
    /* from htmlentitydefs import name2codepoint */
    p_htmlentitydefs = PyImport_ImportModule("htmlentitydefs");
    p_name2codepoint = PyObject_GetAttrString(p_htmlentitydefs, "name2codepoint");

    /* Check for EOF */
    /* FIXME, there are many places else we must check for EOF */
    c = *(self->cursor);
    if (c == '\0')
        return NULL;

    line = self->line_no;
    column = self->column;

    if (c == '<') {
        self->cursor++;
        self->column++;
        c = *(self->cursor);
        if (c == '/') {
            /* End Element (http://www.w3.org/TR/REC-xml/#NT-ETag) */
            self->cursor++;
            self->column++;
            /* Name */
            value = xml_prefix_name(self);
            if (value == NULL)
                return ERROR(INVALID_TOKEN, line, column);
            /* White Space */
            xml_space(self);
            /* Close */
            if (*(self->cursor) != '>')
                return ERROR(INVALID_TOKEN, line, column);
            self->cursor++;
            self->column++;
            /* Remove from the stack */
            value = pop_tag(self, value);
            if (value == NULL)
                return ERROR(MISMATCH, line, column);
 
            return Py_BuildValue("(iOi)", END_ELEMENT, value, line);
        } else if (c == '!') {
            /* "<!" */
            self->cursor++;
            self->column++;
            c = *(self->cursor);
            if (c == '-') {
                /* "<!-" */
                self->cursor++;
                self->column++;
                c = *(self->cursor);
                if (c != '-')
                    return ERROR(INVALID_TOKEN, line, column);

                /* Comment (http://www.w3.org/TR/REC-xml/#dt-comment) */
                self->cursor++;
                self->column++;
                base = self->cursor;
                for (size=0; 1; size++, move_cursor(self)) {
                    if (self->cursor[0] != '-')
                        continue;
                    if (self->cursor[1] != '-')
                        continue;

                    if (self->cursor[2] != '>')
                        return ERROR(INVALID_TOKEN, line, column);

                    self->cursor += 3;
                    self->column += 3;
                    return Py_BuildValue("(is#i)", COMMENT, base, size, line);
                }
            } else if (c == 'D') {
                /* Document Type */
                value = parse_document_type(self);
                if (value == NULL)
                    return ERROR(INVALID_TOKEN, line, column);
                return Py_BuildValue("(iOi)", DOCUMENT_TYPE, value, line);
            } else if (c == '[') {
                /* CData section */
                if (read_string(self, "[CDATA["))
                    return ERROR(INVALID_TOKEN, line, column);
                base = self->cursor;
                for (size=0; strncmp(self->cursor, "]]>", 3); size++, move_cursor(self));
                self->cursor += 3;
                self->column += 3;
                return Py_BuildValue("is#i", CDATA, base, size, line);
            } else
                return ERROR(INVALID_TOKEN, line, column);
        } else if (c == '?') {
            /* Processing Instruction (http://www.w3.org/TR/REC-xml/#dt-pi) */
            self->cursor++;
            self->column++;
            /* Target */
            if (!(strncmp(self->cursor, "xml", 3)) && isspace(self->cursor[3])) {
                /* XML decl (http://www.w3.org/TR/REC-xml/#NT-XMLDecl) */
                self->cursor += 3;
                self->column += 3;
                xml_space(self);
                /* The version */
                if (read_string(self, "version") == -1)
                    return ERROR(BAD_XML_DECL, line, column);
                if (xml_equal(self) == -1)
                    return ERROR(BAD_XML_DECL, line, column);
                version = xml_attr_value(self);
                if (version == NULL)
                    return ERROR(BAD_XML_DECL, line, column);
                xml_space(self);
                /* Encoding & Standalone */
                encoding = Py_BuildValue("s", "utf-8");
                standalone = Py_BuildValue("");
                if (strncmp(self->cursor, "?>", 2)) {
                    /* Encoding */
                    if (read_string(self, "encoding") == -1)
                        return ERROR(BAD_XML_DECL, line, column);
                    if (xml_equal(self) == -1)
                        return ERROR(BAD_XML_DECL, line, column);
                    encoding = xml_attr_value(self);
                    if (encoding == NULL)
                        return ERROR(BAD_XML_DECL, line, column);
                    xml_space(self);
                    if (strncmp(self->cursor, "?>", 2)) {
                        /* Standalone */
                        if (read_string(self, "standalone") == -1)
                            return ERROR(BAD_XML_DECL, line, column);
                        if (xml_equal(self) == -1)
                            return ERROR(BAD_XML_DECL, line, column);
                        standalone = xml_attr_value(self);
                        if (standalone == NULL)
                            return ERROR(BAD_XML_DECL, line, column);
                        xml_space(self);
                        if (strncmp(self->cursor, "?>", 2))
                            return ERROR(BAD_XML_DECL, line, column);
                    }
                }
                self->cursor++;
                self->column++;
                return Py_BuildValue("(i(OOO)i)", XML_DECL, version, encoding,
                                     standalone, line);
            } else {
                value = xml_name(self);
                if (value == NULL)
                    return ERROR(INVALID_TOKEN, line, column);
                /* White Space */
                xml_space(self);
                /* Value */
                base = self->cursor;
                for (size=0; 1; size++, move_cursor(self))
                    if ((self->cursor[0] == '?') && (self->cursor[1] == '>'))
                        break;
                self->cursor += 2;
                return Py_BuildValue("(i(Os#)i)", PI, value, base, size, line);
            }
        } else {
            /* Start Element */
            /* Name */
            value = xml_prefix_name(self);
            if (value == NULL)
                return ERROR(INVALID_TOKEN, line, column);
            /* Attributes */
            attributes_list = PyList_New(0);
            namespace_decls = PyDict_New();
            while (1) {
                xml_space(self);
                c = *(self->cursor);
                if (c == '>') {
                    self->cursor++;
                    self->column++;
                    /* Add to the stack */
                    if (push_tag(self, value, namespace_decls) == -1)
                        return PyErr_Format(PyExc_RuntimeError,
                                            "internal error");

                    end_tag = 0;
                    namespaces = self->namespaces;
                    break;
                } else if (c == '/') {
                    self->cursor++;
                    self->column++;
                    if (*(self->cursor) != '>')
                        return ERROR(INVALID_TOKEN, line, column);
                    self->cursor++;
                    self->column++;

                    end_tag = 1;
                    if (PyDict_Size(namespace_decls))
                        namespaces = merge_dicts(self->namespaces, namespace_decls);
                    else
                        namespaces = self->namespaces;

                    break;
                }
                /* Attributes */
                if (!(strncmp(self->cursor, "xmlns:", 6))) {
                    /* Namespace declaration */
                    self->cursor += 6;
                    self->column += 6;
                    /* The prefix */
                    attr_name = xml_name(self);
                    if (attr_name == NULL)
                        return ERROR(INVALID_TOKEN, line, column);
                    /* Eq */
                    if (xml_equal(self) == -1)
                        return ERROR(INVALID_TOKEN, line, column);
                    /* The URI */
                    attr_value = xml_attr_value(self);
                    if (attr_value == NULL)
                        return ERROR(INVALID_TOKEN, line, column);
                    /* Set the namespace */
                    PyDict_SetItem(namespace_decls, attr_name, attr_value);
                } else if ((!(strncmp(self->cursor, "xmlns", 5)))
                           && ((self->cursor[5] == '=')
                               || (isspace(self->cursor[5])))) {
                    /* Default namespace declaration */
                    self->cursor += 5;
                    self->column += 5;
                    /* Eq */
                    if (xml_equal(self) == -1)
                        return ERROR(INVALID_TOKEN, line, column);
                    /* The URI */
                    attr_value = xml_attr_value(self);
                    if (attr_value == NULL)
                        return ERROR(INVALID_TOKEN, line, column);
                    /* Set the default namespace */
                    PyDict_SetItem(namespace_decls, Py_BuildValue(""), attr_value);
                } else {
                    /* Attribute */
                    attr_name = xml_prefix_name(self);
                    if (attr_name == NULL)
                        return ERROR(INVALID_TOKEN, line, column);
                    /* Eq */
                    if (xml_equal(self) == -1)
                        return ERROR(INVALID_TOKEN, line, column);
                    /* Value */
                    attr_value = xml_attr_value(self);
                    if (attr_value == NULL)
                        return ERROR(INVALID_TOKEN, line, column);
                    /* Set the attribute */
                    PyList_Append(attributes_list,
                                  Py_BuildValue("(OO)", attr_name, attr_value));
                }
            }

            /* Tag */
            tag_uri = PyDict_GetItem(namespaces, PyTuple_GetItem(value, 0));
            if (tag_uri == NULL)
                tag_uri = Py_BuildValue("");
            tag_name = PyTuple_GetItem(value, 1);

            /* The END_ELEMENT token will be sent later */
            if (end_tag) {
                token = Py_BuildValue("(i(OO)i)", END_ELEMENT, tag_uri,
                                      tag_name, line);
                push_token(self, token);
            }

            /* Attributes */
            attributes = Py_BuildValue("{}");
            attributes_n = PyList_Size(attributes_list);
            for (idx=0; idx < attributes_n; idx++) {
                attr = PyList_GetItem(attributes_list, idx);
                /* Find out the attribute URI */
                attr_name = PyTuple_GetItem(attr, 0);
                attr_prefix = PyTuple_GetItem(attr_name, 0);
                attr_uri = PyDict_GetItem(namespaces, attr_prefix);
                /* Find out the attribute name */
                attr_name = PyTuple_GetItem(attr_name, 1);
                /* Find out the attribute value */
                attr_value = PyTuple_GetItem(attr, 1);
                /* Update to the dict */
                /* XXX Check for duplicates */
                attr_name = Py_BuildValue("(OO)", attr_uri, attr_name);
                p_datatype = PyEval_CallObject(p_get_datatype_by_uri, attr_name);
                p_datatype_decode = PyObject_GetAttrString(p_datatype, "decode");
                attr_value = Py_BuildValue("(O)", attr_value);
                attr_value = PyEval_CallObject(p_datatype_decode, attr_value);
                PyDict_SetItem(attributes, attr_name, attr_value);
            }

            return Py_BuildValue("(i(OOOO)i)", START_ELEMENT, tag_uri, tag_name,
                                 attributes, namespaces, line);
        }
    } else if (c == '&') {
        self->cursor++;
        self->column++;
        if (*(self->cursor) == '#') {
            /* Character reference */
            self->cursor++;
            self->column++;
            value = xml_char_reference(self);
            return Py_BuildValue("(iOi)", CHAR_REF, value, line);
        } else {
            /* Entity reference */
            value = xml_entity_reference(self);
            if (value == NULL)
                return ERROR(INVALID_TOKEN, line, column);
            /* htmlentitydefs.name2unicodepoint[value] */
            value = PyDict_GetItem(p_name2codepoint, value);
            if (value == NULL)
                return ERROR(UNDEFINED_ENTITY, line, column);
            /* unichr(codepoint).encode('utf-8') */
            value = PyUnicode_FromOrdinal(PyInt_AsLong(value));
            value = PyUnicode_AsUTF8String(value);
            return Py_BuildValue("(iOi)", ENTITY_REF, value, line);
        }
    } else {
        /* Text */
        base = self->cursor;
        for (size = 0; 1; size++, move_cursor(self)) {
            c = *(self->cursor);
            if ((c == '<') || (c == '&') || (c == '\0'))
                break;
        }
        return Py_BuildValue("(is#i)", TEXT, base, size, line);
    }

    /* Return None (just to avoid the compiler to complain) */
    return NULL;
}


/**************************************************************************
 * The Parser Type
 * ***********************************************************************/
static PyMemberDef Parser_members[] = {
    {"line_no", T_INT, offsetof(Parser, line_no), 0, "Line number"},
    {"column", T_INT, offsetof(Parser, column), 0, "Column"},
    {NULL}
};


static PyMethodDef Parser_methods[] = {
    {NULL, NULL, 0, NULL}
};


static PyTypeObject ParserType = {
    PyObject_HEAD_INIT(NULL)
    0,                              /* ob_size */
    "itools.xml._parser.Parser",    /* tp_name */
    sizeof(Parser),                 /* tp_basicsize */
    0,                              /* tp_itemsize */
    (destructor)Parser_dealloc,     /* tp_dealloc */
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
    "Parser state",                 /* tp_doc */
    0,                              /* tp_traverse */
    0,                              /* tp_clear */
    0,                              /* tp_richcompare */
    0,                              /* tp_weaklistoffset */
    Parser_iter,                    /* tp_iter */
    (iternextfunc)Parser_iternext,  /* tp_iternext */
    Parser_methods,                 /* tp_methods */
    Parser_members,                 /* tp_members */
    0,                              /* tp_getset */
    0,                              /* tp_base */
    0,                              /* tp_dict */
    0,                              /* tp_descr_get */
    0,                              /* tp_descr_set */
    0,                              /* tp_dictoffset */
    (initproc)Parser_init,          /* tp_init */
};


/**************************************************************************
 * Initialize the module
 * ***********************************************************************/

static PyMethodDef module_methods[] = {
    {NULL}
};

  
#ifndef PyMODINIT_FUNC    /* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif

PyMODINIT_FUNC
init_parser(void) {
    PyObject* module;

    ParserType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&ParserType) < 0)
        return;

    /* Initialize the module */
    module = Py_InitModule3("_parser", module_methods, "Low-level XML parser");
    if (module == NULL)
        return;

    /* Register types */
    Py_INCREF(&ParserType);
    PyModule_AddObject(module, "Parser", (PyObject *)&ParserType);

    /* Register exceptions */
    XMLError = PyErr_NewException("itools.xml._parser.XMLError", NULL, NULL);
    Py_INCREF(XMLError);
    PyModule_AddObject(module, "XMLError", XMLError);
}



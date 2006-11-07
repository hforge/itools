
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
#define CDATA 7

/* Errors */
#define BAD_XML_DECL "XML declaration not well-formed: line %d, column %d"
#define INVALID_TOKEN "not well-formed (invalid token): line %d, column %d"
#define MISMATCH "mismatched tag: line %d, column %d"
#define BAD_ENTITY_REF "error parsing entity reference: line %d, column %d"
#define BAD_CHAR_REF "error parsing character reference: line %d, column %d"

#define ERROR(msg, line, column) PyErr_Format(XMLError, msg, line, column)

/* FIXME, limits to be removed */
#define TAG_STACK_SIZE 200 /* Maximum deepness of the element tree */
#define NS_INDEX_SIZE 10


/**************************************************************************
 * Import from Python
 *************************************************************************/

PyObject* p_schemas;
PyObject* p_get_datatype_by_uri;

PyObject* p_htmlentitydefs;
PyObject* p_name2codepoint;


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
    PyObject* data;
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
    /* The end tag in an empty element */
    PyObject* left_token; /* FIXME: hardcoded limit */
} Parser;


static void Parser_dealloc(Parser* self) {
    Py_XDECREF(self->data);

    int idx;
    for (idx=0; idx<self->tag_stack_top; idx++) {
        Py_DECREF(self->tag_stack[idx]);
        Py_XDECREF(self->tag_ns_stack[idx]);
    }

    Py_XDECREF(self->left_token);

    self->ob_type->tp_free((PyObject*)self);
}


static PyObject* Parser_new(PyTypeObject* type, PyObject* args, PyObject* kw) {
    Parser* self;

    /* Allocate memory */
    self = (Parser*)type->tp_alloc(type, 0);
    if (self == NULL)
        return NULL;

    self->data = NULL;
    self->cursor = NULL;
    self->line_no = 1;
    self->column = 1;
    self->tag_stack_top = 0;
    self->tag_ns_index_top = 0;
    self->namespaces = NULL;
    self->left_token = NULL;

    return (PyObject*)self;
}


static int Parser_init(Parser* self, PyObject* args, PyObject* kw) {
    PyObject* data;

    /* Load the input data */
    if (!PyArg_ParseTuple(args, "S", &data))
        return -1;

    Py_XDECREF(self->data);
    Py_INCREF(data);
    self->data = data;

    /* Initialize variables */
    self->cursor = PyString_AsString(data);
    self->line_no = 1;
    self->column = 1;

    /* The stacks are empty */
    int idx;
    for (idx=0; idx<self->tag_stack_top; idx++) {
        Py_DECREF(self->tag_stack[idx]);
        Py_DECREF(self->tag_ns_stack[idx]);
    }
    self->tag_stack_top = 0;
    self->tag_ns_index_top = 0;

    /* For empty elements, "left_token" keeps the closing tag. */
    Py_XDECREF(self->left_token);
    self->left_token = NULL;

    /* Namespaces */
    self->namespaces = NULL;

    return 0;
}


/* Merges two dictionaries into a new one, when conflict happens the second
 * dict has priority. The first dictionary, "a", maybe NULL, then the second
 * dictionary, "b", is returned.
 *
 * Returns a new reference. The reference count of the items from the
 * source dicts that get into the new dict are incremented.
 */
PyObject* merge_dicts(PyObject* a, PyObject* b) {
    PyObject* c;

    /* If "a" is NULL return b */
    if (a == NULL) {
        Py_INCREF(b);
        return b;
    }

    /* Make a copy of "a" */
    c = PyDict_Copy(a);
    if (c == NULL)
        return NULL;

    /* Update with "b" */
    if (PyDict_Update(c, b) == -1) {
        Py_DECREF(c);
        return NULL;
    }

    return c;
}


/* Adds a new tag to the tag stack. Updates the namespaces structure.
 *
 * We take ownership of "value". */
int push_tag(Parser* self, PyObject* value, PyObject* namespaces) {
    if (self->tag_stack_top >= TAG_STACK_SIZE)
        return -1;

    PyObject* new_namespaces;
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


/* Pops the given tag, if it matches the last tag in the stack. Otherwise
 * return an error condition.
 * 
 * Steals the reference to "value". Returns a new reference. */
PyObject* pop_tag(Parser* self, PyObject* value) {
    /* Check the stack is not empty */
    if (self->tag_stack_top == 0) {
        Py_DECREF(value);
        return NULL;
    }

    /* Pop the top value from the stack */
    self->tag_stack_top--;
    PyObject* last_open_tag = self->tag_stack[self->tag_stack_top];
    PyObject* namespaces = self->tag_ns_stack[self->tag_stack_top];

    /* Check the values match */
    if (PyObject_Compare(value, last_open_tag)) {
        Py_DECREF(value);
        Py_DECREF(last_open_tag);
        Py_XDECREF(namespaces);
        return NULL;
    }

    /* Don't need the "last_open_tag" anymore */
    Py_DECREF(last_open_tag);

    /* Find out the URI from the prefix */
    PyObject* prefix = PyTuple_GetItem(value, 0);
    PyObject* uri;
    if (self->namespaces == NULL)
        uri = Py_None;
    else if (PyDict_Contains(self->namespaces, prefix)) {
        uri = PyDict_GetItem(self->namespaces, prefix);
        if (uri == NULL) {
            Py_DECREF(value);
            Py_XDECREF(namespaces);
            return NULL;
        }
    } else
        uri = Py_None;

    /* Build the return value */
    PyObject* name = PyTuple_GetItem(value, 1);
    PyObject* result = Py_BuildValue("(OO)", uri, name);

    /* Update the namespaces data structure if needed */
    if (namespaces) {
        self->tag_ns_index_top--;
        self->namespaces = self->tag_ns_stack[self->tag_ns_index[self->tag_ns_index_top - 1]];
        Py_DECREF(namespaces);
    }

    Py_DECREF(value);
    return result;
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


/* Name (http://www.w3.org/TR/REC-xml/#NT-Name)
 *
 * Returns a new reference. */
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


/* Prefix + Name (http://www.w3.org/TR/REC-xml-names/#ns-decl)
 *
 * Returns a new reference. */
PyObject* xml_prefix_name(Parser* self) {
    /* First character must be a letter */
    char c = *(self->cursor);
    if (!isalpha(c))
        return NULL;

    /* Get the value */
    char* base = self->cursor;
    self->cursor++;
    self->column++;
    int size;
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
        self->cursor++;
        self->column++;
        PyObject* name = xml_name(self);
        if (name == NULL)
            return NULL;
        PyObject* result = Py_BuildValue("(s#O)", base, size, name);
        Py_DECREF(name);
        return result;
    }

    /* No Prefix */
    return Py_BuildValue("(Os#)", Py_None, base, size);
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

/* Attribute Value (http://www.w3.org/TR/REC-xml/#NT-EntityRef)
 *
 * Returns a new reference. */
PyObject* xml_entity_reference(Parser* self) {
    /* Read the name */
    PyObject* value = xml_name(self);
    if (value == NULL)
        return NULL;

    /* Read ";" */
    if (*(self->cursor) != ';') {
        Py_DECREF(value);
        return NULL;
    }
    self->cursor++;
    self->column++;

    /* To codepoint */
    /* XXX Specific to HTML */
    /* htmlentitydefs.name2unicodepoint[value] */
    PyObject* cp = PyDict_GetItem(p_name2codepoint, value);
    Py_DECREF(value);
    if (cp == NULL)
        return NULL;

    /* unichr(codepoint) */
    PyObject* u_char = PyUnicode_FromOrdinal(PyInt_AS_LONG(cp));

    /* value.encode('utf-8') */
    value = PyUnicode_AsUTF8String(u_char);
    Py_DECREF(u_char);

    return value;
}

/* Attribute Value (http://www.w3.org/TR/REC-xml/#NT-CharRef)
 *
 * Returns a new reference. */
PyObject* xml_char_reference(Parser* self) {
    int cp = 0;

    char c = *(self->cursor);
    if (c == 'x') {
        /* Read "x" */
        self->cursor++;
        self->column++;
        /* Check there is ate least one digit */
        c = *(self->cursor);
        if (!isxdigit(c))
            return NULL;
        /* Hex */
        for (; 1; self->cursor++, self->column++) {
            c = *(self->cursor);
            if (c == ';')
                break;
            /* Decode char */
            cp = cp * 16;
            if (c >= '0' && c <= '9')
                cp = cp + (c - '0');
            else if (c >= 'A' && c <= 'F')
                cp = cp + (c - 'A') + 10;
            else if (c >= 'a' && c <= 'f')
                cp = cp + (c - 'a') + 10;
            else
                return NULL;
        }
    } else {
        /* Check there is ate least one digit */
        if (!isdigit(c)) {
            return NULL;
        }
        /* Dec */
        for (; 1; self->cursor++, self->column++) {
            c = *(self->cursor);
            if (c == ';')
                break;
            /* Decode char */
            cp = cp * 10;
            if (c >= '0' && c <= '9')
                cp = cp + (c - '0');
            else
                return NULL;
        }
    }

    /* Read ";" */
    self->cursor++;
    self->column++;

    /* unichr(codepoint) */
    PyObject* u_char = PyUnicode_FromOrdinal(cp);
    /* value.encode('utf-8') */
    PyObject* value = PyUnicode_AsUTF8String(u_char);
    Py_DECREF(u_char);

    return value;
}



/* Attribute Value (http://www.w3.org/TR/REC-xml/#NT-AttValue)
 *
 * Returns a new reference. */
PyObject* xml_attr_value(Parser* self) {
    PyObject* result = NULL;
    PyObject* ref;

    /* The heading quote */
    char delimiter = *(self->cursor);
    if ((delimiter != '"') && (delimiter != '\''))
        return NULL;

    self->cursor++;
    self->column++;

    /* The value */
    char* base = self->cursor;
    int size;
    for (size=0; 1;) {
        char c = *(self->cursor);

        /* Stop */
        if (c == delimiter)
            break;

        /* Forbidden characters */
        if ((c == '\0') || (c == '<'))
            return NULL;

        /* Entity or Character Reference */
        if (c == '&') {
            self->cursor++;
            self->column++;
            if (*(self->cursor) == '#') {
                self->cursor++;
                self->column++;
                ref = xml_char_reference(self);
                if (ref == NULL)
                    return NULL;
            } else {
                ref = xml_entity_reference(self);
                if (ref == NULL)
                    return NULL;
            }
            /* Concat */
            if (size > 0) {
                result = Py_BuildValue("s#", base, size);
                PyString_ConcatAndDel(&result, ref);
            } else {
                result = ref;
            }
            /* Reset */
            base = self->cursor;
            size = 0;
        } else {
            size++;
            move_cursor(self);
        }
    }

    /* Read delimiter */
    self->cursor++;
    self->column++;

    /* Post-process */
    if (result == NULL)
        return Py_BuildValue("s#", base, size);

    ref = Py_BuildValue("s#", base, size);
    PyString_ConcatAndDel(&result, ref);

    return result;
}



/* Document Type
 *
 * Return a new reference. */
PyObject* parse_document_type(Parser* self) {
    PyObject* system_id;
    PyObject* public_id;
    PyObject* has_internal_subset;
    char c;

    if (read_string(self, "DOCTYPE"))
        return NULL;
    xml_space(self);

    /* Name */
    PyObject* name = xml_name(self);
    if (name == NULL)
        return NULL;
    xml_space(self);
    /* External ID */
    c = *(self->cursor);
    if (c == 'S') {
        if (read_string(self, "SYSTEM")) {
            Py_DECREF(name);
            return NULL;
        }
        xml_space(self);
        /* PUBLIC ID */
        public_id = Py_None;
        /* SYSTEM ID */
        system_id = xml_attr_value(self);
        if (system_id == NULL) {
            Py_DECREF(name);
            return NULL;
        }
        Py_INCREF(public_id);
    } else if (c == 'P') {
        if (read_string(self, "PUBLIC")) {
            Py_DECREF(name);
            return NULL;
        }
        xml_space(self);
        /* PUBLIC ID */
        public_id = xml_attr_value(self);
        if (public_id == NULL) {
            Py_DECREF(name);
            return NULL;
        }
        xml_space(self);
        /* SYSTEM ID */
        system_id = xml_attr_value(self);
        if (system_id == NULL) {
            Py_DECREF(name);
            Py_DECREF(public_id);
            return NULL;
        }
    } else {
        Py_DECREF(name);
        return NULL;
    }
    /* White Space */
    xml_space(self);
    /* Internal subset */
    c = *(self->cursor);
    if (c == '[') {
        /* XXX NOT IMPLEMENTED*/
        Py_DECREF(name);
        Py_DECREF(public_id);
        Py_DECREF(system_id);
        PyErr_SetString(PyExc_NotImplementedError,
                        "internal subset not yet supported");
        return NULL;
    } else
        has_internal_subset = Py_None;
    /* End doctype declaration */
    if (c != '>') {
        Py_DECREF(name);
        Py_DECREF(public_id);
        Py_DECREF(system_id);
        return NULL;
    }

    self->cursor++;
    self->column++;

    PyObject* result = Py_BuildValue("(OOOO)", name, system_id, public_id,
                                     has_internal_subset);
    Py_DECREF(name);
    Py_DECREF(public_id);
    Py_DECREF(system_id);
    return result;
}


/* Returns a new reference */
static PyObject* Parser_iternext(Parser* self) {
    int size;
    char* base;
    PyObject* value;
    PyObject* tag_uri;
    PyObject* tag_name;
    int end_tag;
    PyObject* result;
    /* To call Python from C */
    PyObject* p_datatype;
    PyObject* p_datatype_decode;
    /* Attributes */
    PyObject* attr;
    PyObject* attr_name;
    PyObject* attr_prefix;
    PyObject* attr_uri;
    PyObject* attr_value;
    PyObject* attr_value2;
    PyObject* attributes_list;
    PyObject* namespace_decls;
    PyObject* namespaces;
    /* XML declaration */
    PyObject* version;
    PyObject* encoding;
    PyObject* standalone;

    /* There are tokens waiting */
    if (self->left_token) {
        value = self->left_token;
        self->left_token = NULL;
        return value;
    }

    /* Check for EOF */
    /* FIXME, there are many places else we must check for EOF */
    char c = *(self->cursor);
    if (c == '\0')
        return NULL;

    int line = self->line_no;
    int column = self->column;

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
            if (*(self->cursor) != '>') {
                Py_DECREF(value);
                return ERROR(INVALID_TOKEN, line, column);
            }
            self->cursor++;
            self->column++;
            /* Remove from the stack */
            value = pop_tag(self, value);
            if (value == NULL)
                return ERROR(MISMATCH, line, column);
 
            result = Py_BuildValue("(iOi)", END_ELEMENT, value, line);
            Py_DECREF(value);
            return result;
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
                result = Py_BuildValue("(iOi)", DOCUMENT_TYPE, value, line);
                Py_DECREF(value);
                return result;
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
                    Py_DECREF(encoding);
                    /* Encoding */
                    if (read_string(self, "encoding") == -1) {
                        Py_DECREF(version);
                        Py_DECREF(standalone);
                        return ERROR(BAD_XML_DECL, line, column);
                    }
                    if (xml_equal(self) == -1) {
                        Py_DECREF(version);
                        Py_DECREF(standalone);
                        return ERROR(BAD_XML_DECL, line, column);
                    }
                    encoding = xml_attr_value(self);
                    if (encoding == NULL) {
                        Py_DECREF(version);
                        Py_DECREF(standalone);
                        return ERROR(BAD_XML_DECL, line, column);
                    }
                    xml_space(self);
                    if (strncmp(self->cursor, "?>", 2)) {
                        Py_DECREF(standalone);
                        /* Standalone */
                        if (read_string(self, "standalone") == -1) {
                            Py_DECREF(version);
                            Py_DECREF(encoding);
                            return ERROR(BAD_XML_DECL, line, column);
                        }
                        if (xml_equal(self) == -1) {
                            Py_DECREF(version);
                            Py_DECREF(encoding);
                            return ERROR(BAD_XML_DECL, line, column);
                        }
                        standalone = xml_attr_value(self);
                        if (standalone == NULL) {
                            Py_DECREF(version);
                            Py_DECREF(encoding);
                            return ERROR(BAD_XML_DECL, line, column);
                        }
                        xml_space(self);
                        if (strncmp(self->cursor, "?>", 2)) {
                            Py_DECREF(version);
                            Py_DECREF(encoding);
                            Py_DECREF(standalone);
                            return ERROR(BAD_XML_DECL, line, column);
                        }
                    }
                }
                self->cursor += 2;
                self->column += 2;
                result = Py_BuildValue("(i(OOO)i)", XML_DECL, version, encoding,
                                       standalone, line);
                Py_DECREF(version);
                Py_DECREF(encoding);
                Py_DECREF(standalone);
                return result;
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
                    if (push_tag(self, value, namespace_decls) == -1) {
                        Py_DECREF(value);
                        Py_DECREF(attributes_list);
                        Py_DECREF(namespace_decls);
                        return PyErr_Format(PyExc_RuntimeError,
                                            "internal error");
                    }

                    end_tag = 0;
                    namespaces = self->namespaces;
                    Py_XINCREF(namespaces);
                    break;
                } else if (c == '/') {
                    self->cursor++;
                    self->column++;
                    if (*(self->cursor) != '>') {
                        Py_DECREF(value);
                        Py_DECREF(attributes_list);
                        Py_DECREF(namespace_decls);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    self->cursor++;
                    self->column++;

                    end_tag = 1;
                    if (PyDict_Size(namespace_decls))
                        namespaces = merge_dicts(self->namespaces, namespace_decls);
                    else {
                        namespaces = self->namespaces;
                        Py_XINCREF(namespaces);
                    }

                    break;
                }
                /* Attributes */
                if (!(strncmp(self->cursor, "xmlns:", 6))) {
                    /* Namespace declaration */
                    self->cursor += 6;
                    self->column += 6;
                    /* The prefix */
                    attr_name = xml_name(self);
                    if (attr_name == NULL) {
                        Py_DECREF(value);
                        Py_DECREF(attributes_list);
                        Py_DECREF(namespace_decls);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* Eq */
                    if (xml_equal(self) == -1) {
                        Py_DECREF(value);
                        Py_DECREF(attributes_list);
                        Py_DECREF(namespace_decls);
                        Py_DECREF(attr_name);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* The URI */
                    attr_value = xml_attr_value(self);
                    if (attr_value == NULL) {
                        Py_DECREF(value);
                        Py_DECREF(attributes_list);
                        Py_DECREF(namespace_decls);
                        Py_DECREF(attr_name);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* Set the namespace */
                    PyDict_SetItem(namespace_decls, attr_name, attr_value);
                    Py_DECREF(attr_name);
                    Py_DECREF(attr_value);
                } else if ((!(strncmp(self->cursor, "xmlns", 5)))
                           && ((self->cursor[5] == '=')
                               || (isspace(self->cursor[5])))) {
                    /* Default namespace declaration */
                    self->cursor += 5;
                    self->column += 5;
                    /* Eq */
                    if (xml_equal(self) == -1) {
                        Py_DECREF(value);
                        Py_DECREF(attributes_list);
                        Py_DECREF(namespace_decls);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* The URI */
                    attr_value = xml_attr_value(self);
                    if (attr_value == NULL) {
                        Py_DECREF(value);
                        Py_DECREF(attributes_list);
                        Py_DECREF(namespace_decls);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* Set the default namespace */
                    PyDict_SetItem(namespace_decls, Py_None, attr_value);
                    Py_DECREF(attr_value);
                } else {
                    /* Attribute */
                    attr_name = xml_prefix_name(self);
                    if (attr_name == NULL) {
                        Py_DECREF(value);
                        Py_DECREF(attributes_list);
                        Py_DECREF(namespace_decls);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* Eq */
                    if (xml_equal(self) == -1) {
                        Py_DECREF(value);
                        Py_DECREF(attributes_list);
                        Py_DECREF(namespace_decls);
                        Py_DECREF(attr_name);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* Value */
                    attr_value = xml_attr_value(self);
                    if (attr_value == NULL) {
                        Py_DECREF(value);
                        Py_DECREF(attributes_list);
                        Py_DECREF(namespace_decls);
                        Py_DECREF(attr_name);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* Set the attribute */
                    PyList_Append(attributes_list,
                                  Py_BuildValue("(OO)", attr_name, attr_value));
                    Py_DECREF(attr_name);
                    Py_DECREF(attr_value);
                }
            }

            /* Tag */
            if (namespaces == NULL)
                tag_uri = Py_None;
            else {
                tag_uri = PyDict_GetItem(namespaces, PyTuple_GetItem(value, 0));
                if (tag_uri == NULL)
                    tag_uri = Py_None;
            }
            tag_name = PyTuple_GetItem(value, 1);

            /* The END_ELEMENT token will be sent later */
            if (end_tag)
                self->left_token = Py_BuildValue("(i(OO)i)", END_ELEMENT,
                                                 tag_uri, tag_name, line);

            /* Attributes */
            PyObject* attributes = PyDict_New();
            int attributes_n = PyList_Size(attributes_list);
            int idx;
            for (idx=0; idx < attributes_n; idx++) {
                attr = PyList_GetItem(attributes_list, idx);
                /* Find out the attribute URI */
                attr_name = PyTuple_GetItem(attr, 0);
                attr_prefix = PyTuple_GetItem(attr_name, 0);
                if (namespaces == NULL)
                    attr_uri = Py_None;
                else {
                    attr_uri = PyDict_GetItem(namespaces, attr_prefix);
                    if (attr_uri == NULL)
                        attr_uri = Py_None;
                }
                /* Find out the attribute name */
                attr_name = PyTuple_GetItem(attr_name, 1);
                /* Find out the attribute value */
                attr_value = PyTuple_GetItem(attr, 1);
                /* Update to the dict */
                /* XXX Check for duplicates */
                attr_name = Py_BuildValue("(OO)", attr_uri, attr_name);
                p_datatype = PyObject_CallObject(p_get_datatype_by_uri, attr_name);
                p_datatype_decode = PyObject_GetAttrString(p_datatype, "decode");
                attr_value = Py_BuildValue("(O)", attr_value);
                attr_value2 = PyObject_CallObject(p_datatype_decode, attr_value);
                Py_DECREF(attr_value);
                if (attr_value2 == NULL) {
                    Py_DECREF(attr_name);
                    Py_DECREF(p_datatype);
                    Py_DECREF(p_datatype_decode);
                    Py_DECREF(value);
                    Py_DECREF(attributes_list);
                    Py_DECREF(namespace_decls);
                    Py_DECREF(attributes);
                    Py_XDECREF(namespaces);
                    return NULL;
                }
                PyDict_SetItem(attributes, attr_name, attr_value2);
                Py_DECREF(attr_name);
                Py_DECREF(p_datatype);
                Py_DECREF(p_datatype_decode);
                Py_DECREF(attr_value2);
            }

            if (namespaces == NULL)
                result = Py_BuildValue("(i(OOO{})i)", START_ELEMENT, tag_uri,
                                       tag_name, attributes, line);
            else {
                result = Py_BuildValue("(i(OOOO)i)", START_ELEMENT, tag_uri,
                                       tag_name, attributes, namespaces, line);
                Py_DECREF(namespaces);
            }
            Py_DECREF(value);
            Py_DECREF(attributes_list);
            Py_DECREF(namespace_decls);
            Py_DECREF(attributes);
            return result;
        }
    } else if (c == '&') {
        self->cursor++;
        self->column++;
        if (*(self->cursor) == '#') {
            /* Character reference */
            self->cursor++;
            self->column++;
            value = xml_char_reference(self);
            if (value == NULL)
                return ERROR(BAD_CHAR_REF, line, column);
            result = Py_BuildValue("(iOi)", TEXT, value, line);
            Py_DECREF(value);
            return result;
        } else {
            /* Entity reference */
            value = xml_entity_reference(self);
            if (value == NULL)
                return ERROR(BAD_ENTITY_REF, line, column);
            result = Py_BuildValue("(iOi)", TEXT, value, line);
            Py_DECREF(value);
            return result;
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
    "itools.xml.parser.Parser",     /* tp_name */
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
    "XML Parser",                   /* tp_doc */
    0,                              /* tp_traverse */
    0,                              /* tp_clear */
    0,                              /* tp_richcompare */
    0,                              /* tp_weaklistoffset */
    PyObject_SelfIter,              /* tp_iter */
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
    0,                              /* tp_alloc */
    Parser_new,                     /* tp_new */
};


/**************************************************************************
 * Initialize the module
 * ***********************************************************************/

static PyMethodDef module_methods[] = {
    /* {"method name", method, METH_VARARGS | METH_KEYWORDS | METH_NOARGS,
        "doc string"} */
    {NULL}
};

  
#ifndef PyMODINIT_FUNC    /* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif

PyMODINIT_FUNC
initparser(void) {
    PyObject* module;

    if (PyType_Ready(&ParserType) < 0)
        return;

    /* Import from Python */
    /* from itools.schemas import get_datatype_by_uri */
    p_schemas = PyImport_ImportModule("itools.schemas");
    p_get_datatype_by_uri = PyObject_GetAttrString(p_schemas, "get_datatype_by_uri");
    /* from htmlentitydefs import name2codepoint */
    p_htmlentitydefs = PyImport_ImportModule("htmlentitydefs");
    p_name2codepoint = PyObject_GetAttrString(p_htmlentitydefs, "name2codepoint");

    /* Initialize the module */
    module = Py_InitModule3("parser", module_methods, "Low-level XML parser");
    if (module == NULL)
        return;

    /* Register types */
    Py_INCREF(&ParserType);
    PyModule_AddObject(module, "Parser", (PyObject *)&ParserType);

    /* Register exceptions */
    XMLError = PyErr_NewException("itools.xml.parser.XMLError", NULL, NULL);
    Py_INCREF(XMLError);
    PyModule_AddObject(module, "XMLError", XMLError);

    /* Register constants */
    PyModule_AddIntConstant(module, "XML_DECL", XML_DECL);
    PyModule_AddIntConstant(module, "DOCUMENT_TYPE", DOCUMENT_TYPE);
    PyModule_AddIntConstant(module, "START_ELEMENT", START_ELEMENT);
    PyModule_AddIntConstant(module, "END_ELEMENT", END_ELEMENT);
    PyModule_AddIntConstant(module, "TEXT", TEXT);
    PyModule_AddIntConstant(module, "COMMENT", COMMENT);
    PyModule_AddIntConstant(module, "PI", PI);
    PyModule_AddIntConstant(module, "CDATA", CDATA);
}



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
#define MISSING "expected end tag is missing: line %d, column %d"
#define BAD_ENTITY_REF "error parsing entity reference: line %d, column %d"
#define BAD_CHAR_REF "error parsing character reference: line %d, column %d"
#define DUP_ATTR "duplicate attribute: line %d, column %d"

#define ERROR(msg, line, column) PyErr_Format(XMLError, msg, line, column)

/* Macros */
#define IS_NC_NAME_CHAR(c) \
    (isalnum(c) || (c == '.') || (c == '-') || (c == '_'))
#define IS_NAME_CHAR(c) \
    (isalnum(c) || (c == '.') || (c == '-') || (c == '_') || (c == ':'))

/* FIXME, limits to be removed */
#define TAG_STACK_SIZE 200 /* Maximum deepness of the element tree */
#define NS_INDEX_SIZE 10



/**************************************************************************
 * Data Types
 *************************************************************************/

/* Define a sub-string of a C-string as a char pointer to some position
 * within the C-string and its size. */
typedef struct {
    char* base;
    size_t size;
} SubString;


/**************************************************************************
 * Global variables
 *************************************************************************/

/* Import from Python */
PyObject* p_htmlentitydefs;
PyObject* p_name2codepoint;


/* Exceptions */
static PyObject* XMLError;


/* Constants */
PyObject* xml_prefix;
PyObject* xml_ns;
PyObject* xmlns_prefix;
PyObject* xmlns_uri;



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
    SubString tag_stack[TAG_STACK_SIZE*2];
    int tag_stack_top;
    /* Namespace stack */
    PyObject* tag_ns_stack[TAG_STACK_SIZE]; /* FIXME: hardcoded limit */
    int tag_ns_index[NS_INDEX_SIZE]; /* FIXME: hardcoded limit */
    int tag_ns_index_top;
    PyObject* namespaces;
    PyObject* default_namespaces;
    /* The end tag in an empty element */
    PyObject* left_token; /* FIXME: hardcoded limit */
} Parser;


static void Parser_dealloc(Parser* self) {
    int idx;

    Py_XDECREF(self->data);
    for (idx=0; idx<self->tag_stack_top; idx++)
        Py_XDECREF(self->tag_ns_stack[idx]);

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
    self->default_namespaces = NULL;
    self->left_token = NULL;

    return (PyObject*)self;
}


static int Parser_init(Parser* self, PyObject* args, PyObject* kw) {
    PyObject* data;
    PyObject* namespaces;
    int idx;

    /* Load the input data */
    namespaces = NULL;
    if (!PyArg_ParseTuple(args, "S|O!", &data, &PyDict_Type, &namespaces))
        return -1;

    Py_XDECREF(self->data);
    Py_INCREF(data);
    self->data = data;

    /* Initialize variables */
    self->cursor = PyString_AsString(data);
    self->line_no = 1;
    self->column = 1;

    /* The stacks are empty */
    for (idx=0; idx<self->tag_stack_top; idx++)
        Py_XDECREF(self->tag_ns_stack[idx]);
    self->tag_stack_top = 0;
    self->tag_ns_index_top = 0;

    /* For empty elements, "left_token" keeps the closing tag. */
    Py_XDECREF(self->left_token);
    self->left_token = NULL;

    /* Namespaces */
    self->namespaces = namespaces;
    Py_XDECREF(self->default_namespaces);
    Py_XINCREF(namespaces);
    self->default_namespaces = namespaces;

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


/* Adds a new tag to the tag stack, where a tag is defined by a couple of
 * sub-strings (tag prefix and name).  Updates the namespaces structure.
 *
 * Returns a new Python value, a tuple of the prefix and name. */
int push_tag(Parser* self, SubString* prefix, SubString* name,
             PyObject* namespaces) {
    PyObject* new_namespaces;
    int index;

    /* Check the stack is not full */
    if (self->tag_stack_top >= TAG_STACK_SIZE)
        return 1;

    /* Update the namespaces */
    if (PyDict_Size(namespaces)) {
        if (self->tag_ns_index_top >= NS_INDEX_SIZE)
            return 1;
        /* Create the new namespaces */
        new_namespaces = merge_dicts(self->namespaces, namespaces);
        if (new_namespaces == NULL)
            return 1;
        /* Update the current namespaces */
        self->namespaces = new_namespaces;
        /* Update ns index */
        self->tag_ns_index[self->tag_ns_index_top] = self->tag_stack_top;
        self->tag_ns_index_top++;
    } else
        new_namespaces = NULL;
    /* Push into "tag_ns_stack" */
    self->tag_ns_stack[self->tag_stack_top] = new_namespaces;

    /* Push into "tag_stack" */
    index = 2 * (self->tag_stack_top);
    self->tag_stack[index].base = prefix->base;
    self->tag_stack[index].size = prefix->size;
    index++;
    self->tag_stack[index].base = name->base;
    self->tag_stack[index].size = name->size;
    /* Increment index */
    self->tag_stack_top++;

    return 0;
}


/* Checks that the given tag, defined by a couple of sub-strings (tag prefix
 * and name), matches the last start tag in the stack.
 *
 * Updates (pops) the tag and namespace stacks.
 *
 * On error returns a NULL pointer.  On success returns a new Python value,
 * with the tag expressed as a tuple of two elements, the tag uri and name.
 */
PyObject* pop_tag(Parser* self, SubString* prefix, SubString* name) {
    int index;
    int has_prefix;
    SubString start_prefix;
    SubString start_name;
    PyObject* py_namespaces;
    PyObject* py_prefix;
    PyObject* py_uri;

    /* Check the stack is not empty */
    if (self->tag_stack_top == 0)
        return NULL;

    /* Check the given (end) tag matches the last start tag */
    index = self->tag_stack_top;
    index = 2 * (index - 1);
    start_prefix = self->tag_stack[index];
    start_name = self->tag_stack[index+1];
    if (prefix->size != start_prefix.size)
        return NULL;
    if (name->size != start_name.size)
        return NULL;
    if (memcmp(prefix->base, start_prefix.base, prefix->size) != 0)
        return NULL;
    if (memcmp(name->base, start_name.base, name->size) != 0)
        return NULL;

    /* Pop the top value from the stack */
    self->tag_stack_top--;
    py_namespaces = self->tag_ns_stack[self->tag_stack_top];

    /* Find out the URI from the prefix */
    if (self->namespaces == NULL)
        py_uri = Py_None;
    else {
        py_prefix = Py_BuildValue("s#", prefix->base, prefix->size);
        has_prefix = PyDict_Contains(self->namespaces, py_prefix);
        /* Check "dict.get" did not fail */
        if (has_prefix == -1) {
            Py_DECREF(py_prefix);
            Py_XDECREF(py_namespaces);
            return NULL;
        }
        if (has_prefix == 1) {
            /* Hit */
            py_uri = PyDict_GetItem(self->namespaces, py_prefix);
            if (py_uri == NULL) {
                Py_DECREF(py_prefix);
                Py_XDECREF(py_namespaces);
                return NULL;
            }
        } else
            py_uri = Py_None;

        Py_DECREF(py_prefix);
    }

    /* Update the namespaces data structure if needed */
    if (py_namespaces) {
        self->tag_ns_index_top--;
        self->namespaces = self->tag_ns_stack[self->tag_ns_index[self->tag_ns_index_top - 1]];
        Py_DECREF(py_namespaces);
    } else if (self->tag_ns_index_top == 0) {
        self->namespaces = self->default_namespaces;
    }

    /* Build the return value */
    return Py_BuildValue("(Os#)", py_uri, name->base, name->size);
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
    if (strncmp(self->cursor, expected, size))
        return -1;

    self->cursor += size;
    self->column += size;
    return 0;
}


/* Name (http://www.w3.org/TR/REC-xml/#NT-Name)
 *
 * Returns 0 (success) or 1 (error). */
int xml_name(Parser* self, SubString* name) {
    /* First character must be a letter */
    if (!isalpha(*(self->cursor)))
        return 1;

    /* Initialize pointer */
    name->base = self->cursor;
    self->cursor++;

    /* Read as much as possible */
    for (; IS_NAME_CHAR(*(self->cursor)); self->cursor++) {}

    /* Set return values */
    name->size = (self->cursor) - (name->base);
    self->column += name->size;

    /* Return on success */
    return 0;
}


/* Prefix + Name (http://www.w3.org/TR/REC-xml-names/#ns-decl)
 *
 * Returns 0 (success) or 1 (error). */
int xml_prefix_name(Parser* self, SubString* prefix, SubString* name) {
    int error;

    /* First character must be a letter */
    if (!isalpha(*(self->cursor)))
        return 1;

    /* Initialize the prefix */
    prefix->base = self->cursor;
    self->cursor++;

    /* Read as much as possible */
    for (; IS_NC_NAME_CHAR(*(self->cursor)); self->cursor++) {}

    if (*(self->cursor) == ':') {
        /* With prefix */
        prefix->size = (self->cursor) - (prefix->base);
        self->column += prefix->size;
        /* Read the ':' char */
        self->cursor++;
        self->column++;
        /* Read the name */
        error = xml_name(self, name);
        if (error)
            return 1;
    } else {
        /* No Prefix */
        name->base = prefix->base;
        name->size = (self->cursor) - (name->base);
        prefix->base = NULL;
        prefix->size = 0;
        self->column += name->size;
    }

    return 0;
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
    SubString name;
    int error;
    PyObject* value;
    PyObject* cp;
    PyObject* u_char;

    /* Read the name */
    error = xml_name(self, &name);
    if (error)
        return NULL;

    /* Read ";" */
    if (*(self->cursor) != ';')
        return NULL;
    self->cursor++;
    self->column++;

    /* To codepoint */
    /* FIXME Specific to HTML */
    /* htmlentitydefs.name2unicodepoint[value] */
    value = Py_BuildValue("s#", name.base, name.size);
    cp = PyDict_GetItem(p_name2codepoint, value);
    Py_DECREF(value);
    if (cp == NULL)
        return NULL;

    /* unichr(codepoint) */
    u_char = PyUnicode_FromOrdinal(PyInt_AS_LONG(cp));

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
    char c;
    PyObject* u_char;
    PyObject* value;

    c = *(self->cursor);
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
    u_char = PyUnicode_FromOrdinal(cp);
    /* value.encode('utf-8') */
    value = PyUnicode_AsUTF8String(u_char);
    Py_DECREF(u_char);

    return value;
}



/* Attribute Value (http://www.w3.org/TR/REC-xml/#NT-AttValue)
 *
 * Returns a new reference. */
PyObject* xml_attr_value(Parser* self) {
    PyObject* aux = NULL;
    PyObject* result = NULL;
    PyObject* ref;
    char delimiter;
    char* base;
    int size;

    /* The heading quote */
    delimiter = *(self->cursor);
    if ((delimiter != '"') && (delimiter != '\''))
        return NULL;

    self->cursor++;
    self->column++;

    /* The value */
    base = self->cursor;
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
            /* result = result + buffer */
            if (size > 0) {
                aux = Py_BuildValue("s#", base, size);
                if (result == NULL) {
                    result = aux;
                } else {
                    PyString_ConcatAndDel(&result, aux);
                }
            }
            /* result = result + reference */
            if (result == NULL) {
                result = ref;
            } else {
                PyString_ConcatAndDel(&result, ref);
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

    aux = Py_BuildValue("s#", base, size);
    PyString_ConcatAndDel(&result, aux);

    return result;
}



/* Document Type
 *
 * Return a new reference. */
PyObject* parse_document_type(Parser* self) {
    SubString name;
    int error;
    PyObject* public_id;
    PyObject* system_id;
    PyObject* has_internal_subset;
    char c;

    if (read_string(self, "DOCTYPE"))
        return NULL;
    xml_space(self);

    /* Name */
    error = xml_name(self, &name);
    if (error)
        return NULL;
    xml_space(self);
    /* External ID */
    c = *(self->cursor);
    if (c == 'S') {
        if (read_string(self, "SYSTEM"))
            return NULL;
        xml_space(self);
        /* PUBLIC ID */
        public_id = Py_None;
        /* SYSTEM ID */
        system_id = xml_attr_value(self);
        if (system_id == NULL)
            return NULL;
        Py_INCREF(public_id);
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
        if (system_id == NULL) {
            Py_DECREF(public_id);
            return NULL;
        }
    } else {
        return NULL;
    }
    /* White Space */
    xml_space(self);
    /* Internal subset */
    c = *(self->cursor);
    if (c == '[') {
        /* XXX NOT IMPLEMENTED*/
        Py_DECREF(public_id);
        Py_DECREF(system_id);
        PyErr_SetString(PyExc_NotImplementedError,
                        "internal subset not yet supported");
        return NULL;
    } else
        has_internal_subset = Py_None;
    /* End doctype declaration */
    if (c != '>') {
        Py_DECREF(public_id);
        Py_DECREF(system_id);
        return NULL;
    }

    self->cursor++;
    self->column++;

    return Py_BuildValue("(s#NNO)", name.base, name.size, system_id,
                         public_id, has_internal_subset);
}


/* Returns a new reference */
static PyObject* Parser_iternext(Parser* self) {
    int size;
    char* base;
    int error;
    SubString tag_prefix;
    SubString tag_name;
    PyObject* py_value;
    PyObject* py_tag_prefix;
    PyObject* py_tag_uri;
    PyObject* py_tag_name;
    int end_tag;
    PyObject* py_result;
    /* Attributes */
    SubString attr_prefix;
    SubString attr_name;
    PyObject* py_attr;
    PyObject* py_attr_name;
    PyObject* py_attr_prefix;
    PyObject* py_attr_uri;
    PyObject* py_attr_value;
    PyObject* py_attributes_list;
    PyObject* py_namespace_decls;
    PyObject* py_namespaces;
    /* XML declaration */
    PyObject* py_version;
    PyObject* py_encoding;
    PyObject* py_standalone;
    char c;
    int line;
    int column;
    PyObject* py_attributes;
    int attributes_n;
    int idx;

    /* There are tokens waiting */
    if (self->left_token) {
        py_value = self->left_token;
        self->left_token = NULL;
        return py_value;
    }

    line = self->line_no;
    column = self->column;

    /* Check for EOF */
    /* FIXME, there are many places else we must check for EOF */
    c = *(self->cursor);
    if (c == '\0') {
        /* Check the open tags are closed. */
        if (self->tag_stack_top > 0)
            return ERROR(MISSING, line, column);
        return NULL;
    }

    if (c == '<') {
        self->cursor++;
        self->column++;
        c = *(self->cursor);
        if (c == '/') {
            /* End Element (http://www.w3.org/TR/REC-xml/#NT-ETag) */
            self->cursor++;
            self->column++;
            /* Name */
            error = xml_prefix_name(self, &tag_prefix, &tag_name);
            if (error)
                return ERROR(INVALID_TOKEN, line, column);
            /* White Space */
            xml_space(self);
            /* Close */
            if (*(self->cursor) != '>')
                return ERROR(INVALID_TOKEN, line, column);
            self->cursor++;
            self->column++;
            /* Remove from the stack */
            py_value = pop_tag(self, &tag_prefix, &tag_name);
            if (py_value == NULL)
                return ERROR(MISSING, line, column);
 
            return Py_BuildValue("(iNi)", END_ELEMENT, py_value, line);
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
                py_value = parse_document_type(self);
                if (py_value == NULL)
                    return ERROR(INVALID_TOKEN, line, column);
                return Py_BuildValue("(iNi)", DOCUMENT_TYPE, py_value, line);
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
                py_version = xml_attr_value(self);
                if (py_version == NULL)
                    return ERROR(BAD_XML_DECL, line, column);
                xml_space(self);
                /* Encoding & Standalone */
                py_encoding = Py_BuildValue("s", "utf-8");
                py_standalone = Py_BuildValue("");
                if (strncmp(self->cursor, "?>", 2)) {
                    Py_DECREF(py_encoding);
                    /* Encoding */
                    if (read_string(self, "encoding") == -1) {
                        Py_DECREF(py_version);
                        Py_DECREF(py_standalone);
                        return ERROR(BAD_XML_DECL, line, column);
                    }
                    if (xml_equal(self) == -1) {
                        Py_DECREF(py_version);
                        Py_DECREF(py_standalone);
                        return ERROR(BAD_XML_DECL, line, column);
                    }
                    py_encoding = xml_attr_value(self);
                    if (py_encoding == NULL) {
                        Py_DECREF(py_version);
                        Py_DECREF(py_standalone);
                        return ERROR(BAD_XML_DECL, line, column);
                    }
                    xml_space(self);
                    if (strncmp(self->cursor, "?>", 2)) {
                        Py_DECREF(py_standalone);
                        /* Standalone */
                        if (read_string(self, "standalone") == -1) {
                            Py_DECREF(py_version);
                            Py_DECREF(py_encoding);
                            return ERROR(BAD_XML_DECL, line, column);
                        }
                        if (xml_equal(self) == -1) {
                            Py_DECREF(py_version);
                            Py_DECREF(py_encoding);
                            return ERROR(BAD_XML_DECL, line, column);
                        }
                        py_standalone = xml_attr_value(self);
                        if (py_standalone == NULL) {
                            Py_DECREF(py_version);
                            Py_DECREF(py_encoding);
                            return ERROR(BAD_XML_DECL, line, column);
                        }
                        xml_space(self);
                        if (strncmp(self->cursor, "?>", 2)) {
                            Py_DECREF(py_version);
                            Py_DECREF(py_encoding);
                            Py_DECREF(py_standalone);
                            return ERROR(BAD_XML_DECL, line, column);
                        }
                    }
                }
                self->cursor += 2;
                self->column += 2;
                return Py_BuildValue("(i(NNN)i)", XML_DECL, py_version,
                                     py_encoding, py_standalone, line);
            } else {
                error = xml_name(self, &tag_name);
                if (error)
                    return ERROR(INVALID_TOKEN, line, column);
                /* White Space */
                xml_space(self);
                /* Value */
                base = self->cursor;
                for (size=0; 1; size++, move_cursor(self))
                    if ((self->cursor[0] == '?') && (self->cursor[1] == '>'))
                        break;
                self->cursor += 2;
                return Py_BuildValue("(i(s#s#)i)", PI, tag_name.base,
                                     tag_name.size, base, size, line);
            }
        } else {
            /* Start Element */
            /* Name */
            error = xml_prefix_name(self, &tag_prefix, &tag_name);
            if (error)
                return ERROR(INVALID_TOKEN, line, column);
            py_tag_prefix = Py_BuildValue("s#", tag_prefix.base,
                                          tag_prefix.size);
            /* Attributes */
            py_attributes_list = PyList_New(0);
            py_namespace_decls = PyDict_New();
            while (1) {
                xml_space(self);
                c = *(self->cursor);
                if (c == '>') {
                    self->cursor++;
                    self->column++;
                    /* Add to the stack */
                    error = push_tag(self, &tag_prefix, &tag_name,
                                     py_namespace_decls);
                    if (error) {
                        Py_DECREF(py_attributes_list);
                        Py_DECREF(py_namespace_decls);
                        return PyErr_Format(PyExc_RuntimeError,
                                            "internal error");
                    }

                    end_tag = 0;
                    py_namespaces = self->namespaces;
                    Py_XINCREF(py_namespaces);
                    break;
                } else if (c == '/') {
                    self->cursor++;
                    self->column++;
                    if (*(self->cursor) != '>') {
                        Py_DECREF(py_attributes_list);
                        Py_DECREF(py_namespace_decls);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    self->cursor++;
                    self->column++;

                    end_tag = 1;
                    if (PyDict_Size(py_namespace_decls))
                        py_namespaces = merge_dicts(self->namespaces,
                                                    py_namespace_decls);
                    else {
                        py_namespaces = self->namespaces;
                        Py_XINCREF(py_namespaces);
                    }

                    break;
                }
                /* Attributes */
                if (!(strncmp(self->cursor, "xmlns:", 6))) {
                    /* Namespace declaration */
                    self->cursor += 6;
                    self->column += 6;
                    /* The prefix */
                    error = xml_name(self, &attr_name);
                    if (error) {
                        Py_DECREF(py_attributes_list);
                        Py_DECREF(py_namespace_decls);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* Eq */
                    if (xml_equal(self) == -1) {
                        Py_DECREF(py_attributes_list);
                        Py_DECREF(py_namespace_decls);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* The URI */
                    py_attr_value = xml_attr_value(self);
                    if (py_attr_value == NULL) {
                        Py_DECREF(py_attributes_list);
                        Py_DECREF(py_namespace_decls);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* Check for duplicates */
                    py_attr_name = Py_BuildValue("s#", attr_name.base,
                                                 attr_name.size);
                    if (PyDict_Contains(py_namespace_decls, py_attr_name)) {
                        Py_DECREF(py_attributes_list);
                        Py_DECREF(py_namespace_decls);
                        Py_DECREF(py_attr_name);
                        Py_DECREF(py_attr_value);
                        return ERROR(DUP_ATTR, line, column);
                    }
                    /* Set the namespace */
                    PyDict_SetItem(py_namespace_decls, py_attr_name,
                                   py_attr_value);
                    /* Set the attribute */
                    py_attr = Py_BuildValue("((OO)N)", xmlns_prefix,
                              py_attr_name, py_attr_value);
                    PyList_Append(py_attributes_list, py_attr);
                    /* Decref */
                    Py_DECREF(py_attr);
                } else if ((!(strncmp(self->cursor, "xmlns", 5)))
                           && ((self->cursor[5] == '=')
                               || (isspace(self->cursor[5])))) {
                    /* Default namespace declaration */
                    self->cursor += 5;
                    self->column += 5;
                    /* Eq */
                    if (xml_equal(self) == -1) {
                        Py_DECREF(py_attributes_list);
                        Py_DECREF(py_namespace_decls);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* The URI */
                    py_attr_value = xml_attr_value(self);
                    if (py_attr_value == NULL) {
                        Py_DECREF(py_attributes_list);
                        Py_DECREF(py_namespace_decls);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* Check for duplicates */
                    if (PyDict_Contains(py_namespace_decls, Py_None)) {
                        Py_DECREF(py_attributes_list);
                        Py_DECREF(py_namespace_decls);
                        Py_DECREF(py_attr_value);
                        return ERROR(DUP_ATTR, line, column);
                    }
                    /* Set the default namespace */
                    PyDict_SetItem(py_namespace_decls, Py_None, py_attr_value);
                    /* Set the attribute */
                    py_attr = Py_BuildValue("((OO)N)", xmlns_prefix, Py_None,
                              py_attr_value);
                    PyList_Append(py_attributes_list, py_attr);
                    /* Decref */
                    Py_DECREF(py_attr);
                } else {
                    /* Attribute */
                    error = xml_prefix_name(self, &attr_prefix, &attr_name);
                    if (error) {
                        Py_DECREF(py_attributes_list);
                        Py_DECREF(py_namespace_decls);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* Eq */
                    if (xml_equal(self) == -1) {
                        Py_DECREF(py_attributes_list);
                        Py_DECREF(py_namespace_decls);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* Value */
                    py_attr_value = xml_attr_value(self);
                    if (py_attr_value == NULL) {
                        Py_DECREF(py_attributes_list);
                        Py_DECREF(py_namespace_decls);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* Set the attribute */
                    if (attr_prefix.size == 0)
                        py_attr = Py_BuildValue("((Os#)N)", py_tag_prefix,
                                  attr_name.base, attr_name.size,
                                  py_attr_value);
                    else
                        py_attr = Py_BuildValue("((s#s#)N)", attr_prefix.base,
                                  attr_prefix.size, attr_name.base,
                                  attr_name.size, py_attr_value);
                    PyList_Append(py_attributes_list, py_attr);
                    Py_DECREF(py_attr);
                }
            }

            /* Tag */
            if (py_namespaces == NULL)
                py_tag_uri = Py_None;
            else {
                py_tag_uri = PyDict_GetItem(py_namespaces, py_tag_prefix);
                if (py_tag_uri == NULL)
                    py_tag_uri = Py_None;
            }
            py_tag_name = Py_BuildValue("s#", tag_name.base, tag_name.size);

            /* The END_ELEMENT token will be sent later */
            if (end_tag)
                self->left_token = Py_BuildValue("(i(OO)i)", END_ELEMENT,
                                   py_tag_uri, py_tag_name, line);

            /* Attributes */
            py_attributes = PyDict_New();
            attributes_n = PyList_Size(py_attributes_list);
            for (idx=0; idx < attributes_n; idx++) {
                py_attr = PyList_GetItem(py_attributes_list, idx);
                /* Find out the attribute URI */
                py_attr_name = PyTuple_GetItem(py_attr, 0);
                py_attr_prefix = PyTuple_GetItem(py_attr_name, 0);
                if (PyObject_Compare(py_attr_prefix, xml_prefix) == 0)
                    py_attr_uri = xml_ns;
                else if (PyObject_Compare(py_attr_prefix, xmlns_prefix) == 0)
                    py_attr_uri = xmlns_uri;
                else if (py_namespaces == NULL)
                    py_attr_uri = Py_None;
                else {
                    py_attr_uri = PyDict_GetItem(py_namespaces,
                                                 py_attr_prefix);
                    if (py_attr_uri == NULL)
                        py_attr_uri = Py_None;
                }
                /* Find out the attribute name */
                py_attr_name = PyTuple_GetItem(py_attr_name, 1);
                /* Find out the attribute value */
                py_attr_value = PyTuple_GetItem(py_attr, 1);
                /* Check for duplicates */
                py_attr_name = Py_BuildValue("(OO)", py_attr_uri,
                               py_attr_name);
                if (PyDict_Contains(py_attributes, py_attr_name)) {
                    Py_DECREF(py_attr_name);
                    Py_DECREF(py_tag_name);
                    Py_DECREF(py_attributes_list);
                    Py_DECREF(py_namespace_decls);
                    Py_DECREF(py_attributes);
                    Py_XDECREF(py_namespaces);
                    return ERROR(DUP_ATTR, line, column);
                }
                /* Update the dict */
                PyDict_SetItem(py_attributes, py_attr_name, py_attr_value);
                Py_DECREF(py_attr_name);
            }

            py_result = Py_BuildValue("(i(ONN)i)", START_ELEMENT, py_tag_uri,
                        py_tag_name, py_attributes, line);
            Py_DECREF(py_attributes_list);
            Py_DECREF(py_namespace_decls);
            return py_result;
        }
    } else if (c == '&') {
        self->cursor++;
        self->column++;
        if (*(self->cursor) == '#') {
            /* Character reference */
            self->cursor++;
            self->column++;
            py_value = xml_char_reference(self);
            if (py_value == NULL)
                return ERROR(BAD_CHAR_REF, line, column);
            return Py_BuildValue("(iNi)", TEXT, py_value, line);
        } else {
            /* Entity reference */
            py_value = xml_entity_reference(self);
            if (py_value == NULL)
                return ERROR(BAD_ENTITY_REF, line, column);
            return Py_BuildValue("(iNi)", TEXT, py_value, line);
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
    "itools.xml.parser.XMLParser",  /* tp_name */
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
    0, /* XXX set later: PyObject_SelfIter, */     /*tp_iter*/
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

    /* XXX Fix tp_Iter for cygwin */
    ParserType.tp_iter = PyObject_SelfIter;

    if (PyType_Ready(&ParserType) < 0)
        return;

    /* Import from Python */
    /* from htmlentitydefs import name2codepoint */
    p_htmlentitydefs = PyImport_ImportModule("htmlentitydefs");
    p_name2codepoint = PyObject_GetAttrString(p_htmlentitydefs, "name2codepoint");

    /* Constants */
    xml_prefix = PyString_FromString("xml");
    xml_ns = PyString_FromString("http://www.w3.org/XML/1998/namespace");
    xmlns_prefix = PyString_FromString("xmlns");
    xmlns_uri = PyString_FromString("http://www.w3.org/2000/xmlns/");

    /* Initialize the module */
    module = Py_InitModule3("parser", module_methods, "Low-level XML parser");
    if (module == NULL)
        return;

    /* Register types */
    Py_INCREF(&ParserType);
    PyModule_AddObject(module, "XMLParser", (PyObject *)&ParserType);

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


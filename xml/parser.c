/*
 * Copyright (C) 2007-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
 * Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
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


/**************************************************************************
 * The Prolog
 *************************************************************************/
#include <string.h>
#include <stdlib.h>
#include <ctype.h>

#include "parser.h"

#define IS_NC_NAME_CHAR(c) \
    (isalnum(c) || (c == '.') || (c == '-') || (c == '_'))
#define IS_NAME_CHAR(c) \
    (isalnum(c) || (c == '.') || (c == '-') || (c == '_') || (c == ':'))


/**************************************************************************
 * The internal functions/objects
 *************************************************************************/

/**********
 * Errors *
 * ********/

#define BAD_XML_DECL      "XML declaration not well-formed"
#define INVALID_TOKEN     "not well-formed (invalid token)"
#define MISSING           "expected end tag is missing"
#define BAD_ENTITY        "error parsing entity reference"
#define DUP_ATTR          "duplicate attribute"
#define INVALID_NAMESPACE "invalid namespace"


/**********************
 * The internal types *
 **********************/

/***************************
 * An auto realloc pointer *
 ***************************/

typedef struct
{
  gchar *data;
  gint length;

  gsize object_size;
  void (*constructor) (gpointer object);
  void (*destructor) (gpointer object);
} Arp;


Arp *
arp_new (gsize object_size, void (*constructor) (gpointer object),
         void (*destructor) (gpointer object))
{
  Arp *arp;
  gchar *pointer;
  gint idx;

  arp = g_new (Arp, 1);

  arp->object_size = object_size;
  arp->constructor = constructor;
  arp->destructor = destructor;
  arp->length = 16;

  /* Allocation of 16 objects */
  arp->data = (gchar *) g_malloc (16 * object_size);

  if (constructor)
    for (pointer = arp->data, idx = 0; idx < 16;
         pointer += object_size, idx++)
      (*constructor) (pointer);

  return arp;
}


gchar *
arp_get_index (Arp * arp, gint index)
{
  gchar *pointer;
  gint idx;

  if (index >= arp->length)
    {
      arp->data = (gchar *) g_realloc (arp->data,
                                       (arp->length +
                                        16) * (arp->object_size));

      if (arp->constructor != NULL)
        for (pointer = arp->data + arp->length * arp->object_size, idx = 0;
             idx < 16; pointer += arp->object_size, idx++)
          (*(arp->constructor)) (pointer);
      arp->length += 16;
    }

  return arp->data + index * arp->object_size;
}


void
arp_free (Arp * arp)
{
  gchar *pointer;
  gint idx;

  if (arp->destructor != NULL)
    {
      for (pointer = arp->data, idx = 0; idx < arp->length;
           pointer += arp->object_size, idx++)
        (*(arp->destructor)) (pointer);
    }

  g_free (arp->data);
  g_free (arp);
}


/*********************
 * The parser type ! *
 *********************/

struct _Parser
{
  /* Source */
  union
  {
    gchar *cursor;
    FILE *file;
  } source;
    gchar (*get_char) (struct _Parser *);
  gint source_row;
  gint source_col;

  /* Streams management */
  gchar cursor_char;
  Arp *streams_stack;
  gint streams_stack_size;
  gboolean in_doctype;

  /* Four buffers (to do everything) */
  GString *buffer1;
  GString *buffer2;
  GString *buffer3;
  GString *buffer4;

  /* A strings storage place */
  GStringChunk *strings_storage;

  /* Attributes management */
  Arp *attr_storage;

  /* Tag stack */
  Arp *tags_stack;
  gint tags_stack_size;
  gboolean end_tag;
  gchar *end_tag_uri;
  gchar *end_tag_name;

  /* Namespaces management */
  Arp *ns_stack;
  gint ns_stack_size;
  gchar *default_ns;

  /* Entities management */
  GHashTable *GE_table;
  GHashTable *PE_table;
};


/************
 * HStrTree *
 ************/

/* The String Tree is a data structure that allows to store compactly a set
 * of strings.  The lookup or insertion of a string is O(n) where "n" is the
 * length of the string.
 */

typedef struct _HStrTree HStrTree;
struct _HStrTree
{
  gchar *data;
  HStrTree *children[256];

  /* Needed to rebuild the string. */
  HStrTree *parent;
  gchar chr;
};


HStrTree *
h_str_tree_new (void)
{
  return g_new0 (HStrTree, 1);
}


void
h_str_tree_free (HStrTree * tree)
{
  HStrTree *child;
  int idx;

  for (idx = 0; idx < 256; idx++)
    {
      child = tree->children[idx];
      if (child)
        h_str_tree_free (child);
    }
  g_free (tree);
}


HStrTree *
h_str_tree_traverse (HStrTree * tree, gchar chr)
{
  HStrTree *child;
  guint idx;

  idx = (guint) chr;

  child = tree->children[idx];

  /* New ? */
  if (!child)
    {
      child = h_str_tree_new ();

      child->parent = tree;
      child->chr = chr;
      tree->children[idx] = child;
    }

  return child;
}


/********************
 * Interned strings *
 ********************/

G_LOCK_DEFINE_STATIC (interned_strings);
HStrTree *interned_strings_tree = NULL;
GStringChunk *interned_strings = NULL;

/* Some values */
gchar *intern_empty;
gchar *intern_xmlns;


gchar *
intern_string (gchar * str)
{
  HStrTree *node;
  gchar *cursor;

  node = interned_strings_tree;

  /* Get the node */
  for (cursor = str; *cursor != '\0'; cursor++)
    node = h_str_tree_traverse (node, *cursor);

  /* New string? */
  if (!(node->data))
    node->data = g_string_chunk_insert (interned_strings, str);

  return node->data;
}


/*************
 * Attribute *
 *************/

void
parser_attr_constructor (gpointer pointer)
{
  ((Attribute *) pointer)->value = g_string_sized_new (32);
}


void
parser_attr_destructor (gpointer pointer)
{
  g_string_free (((Attribute *) pointer)->value, TRUE);
}

/************
 * Stream   *
 ************/

typedef struct
{
  gchar *cursor;
} Stream;


/*******
 * Tag *
 *******/

typedef struct
{
  gchar *uri;
  gchar *name;
  gint ns_number;
} Tag;


/*************
 * Namespace *
 *************/

typedef struct
{
  gchar *prefix;
  gchar *uri;
} Namespace;


/************
 * Entities *
 ************/

GHashTable *parser_builtin_entities;

#define SET_ENTITY(str, codepoint) \
    g_hash_table_insert(parser_builtin_entities, str, \
                        (gpointer)(gulong)(codepoint))

/*
http://en.wikipedia.org/wiki/List_of_XML_and_HTML_character_entity_references
*/
void
parser_init_builtin_entities (void)
{
  gunichar index;
  gchar *str;

  /* Some Definitions */
  gchar *html_20_32[] = {
    "nbsp", "iexcl", "cent", "pound", "curren", "yen", "brvbar", "sect",
    "uml", "copy", "ordf", "laquo", "not", "shy", "reg", "macr", "deg",
    "plusmn", "sup2", "sup3", "acute", "micro", "para", "middot", "cedil",
    "sup1", "ordm", "raquo", "frac14", "frac12", "frac34", "iquest",
    "Agrave", "Aacute", "Acirc", "Atilde", "Auml", "Aring", "AElig",
    "Ccedil", "Egrave", "Eacute", "Ecirc", "Euml", "Igrave", "Iacute",
    "Icirc", "Iuml", "ETH", "Ntilde", "Ograve", "Oacute", "Ocirc",
    "Otilde", "Ouml", "times", "Oslash", "Ugrave", "Uacute", "Ucirc",
    "Uuml", "Yacute", "THORN", "szlig", "agrave", "aacute", "acirc",
    "atilde", "auml", "aring", "aelig", "ccedil", "egrave", "eacute",
    "ecirc", "euml", "igrave", "iacute", "icirc", "iuml", "eth", "ntilde",
    "ograve", "oacute", "ocirc", "otilde", "ouml", "divide", "oslash",
    "ugrave", "uacute", "ucirc", "uuml", "yacute", "thorn", "yuml"
  };
  gchar *greek_letters[] = {
    "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta",
    "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi", "Omicron", "Pi", "Rho",
    NULL, "Sigma", "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega", NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, "alpha", "beta", "gamma", "delta",
    "epsilon", "zeta", "eta", "theta", "iota", "kappa", "lambda", "mu",
    "nu", "xi", "omicron", "pi", "rho", "sigmaf", "sigma", "tau",
    "upsilon", "phi", "chi", "psi", "omega", NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, "thetasym", "upsih", NULL, NULL, NULL, "piv"
  };
  gchar *range_8194_8260[] = {
    "ensp", "emsp", NULL, NULL, NULL, NULL, NULL, "thinsp", NULL, NULL,
    "zwnj", "zwj", "lrm", "rlm", NULL, NULL, NULL, "ndash", "mdash", NULL,
    NULL, NULL, "lsquo", "rsquo", "sbquo", NULL, "ldquo", "rdquo",
    "bdquo", NULL, "dagger", "Dagger", "bull", NULL, NULL, NULL, "hellip",
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, "permil", NULL,
    "prime", "Prime", NULL, NULL, NULL, NULL, NULL, "lsaquo", "rsaquo",
    NULL, NULL, NULL, "oline", NULL, NULL, NULL, NULL, NULL, "frasl"
  };
  gchar *math_symbols[] = {
    "forall", NULL, "part", "exist", NULL, "empty", NULL, "nabla", "isin",
    "notin", NULL, "ni", NULL, NULL, NULL, "prod", NULL, "sum", "minus",
    NULL, NULL, NULL, NULL, "lowast", NULL, NULL, "radic", NULL, NULL,
    "prop", "infin", NULL, "ang", NULL, NULL, NULL, NULL, NULL, NULL,
    "and", "or", "cap", "cup", "int", NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, "there4", NULL, NULL, NULL, NULL, NULL, NULL, NULL, "sim",
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, "cong", NULL, NULL,
    "asymp", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, "ne", "equiv", NULL, NULL, "le", "ge", NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, "sub", "sup", "nsub", NULL, "sube", "supe"
  };

  /* Create the hash table */
  parser_builtin_entities = g_hash_table_new (g_str_hash, g_str_equal);

  /* And store the entities! */

  /* XML */
  SET_ENTITY ("quot", 34);
  SET_ENTITY ("amp", 38);
  SET_ENTITY ("apos", 39);
  SET_ENTITY ("lt", 60);
  SET_ENTITY ("gt", 62);

  /* HTML 2.0 & 3.2 */
  for (index = 160; index <= 255; index++)
    SET_ENTITY (html_20_32[index - 160], index);

  /* HTML 4.0 */
  SET_ENTITY ("OElig", 338);
  SET_ENTITY ("oelig", 339);
  SET_ENTITY ("Scaron", 352);
  SET_ENTITY ("scaron", 353);
  SET_ENTITY ("Yuml", 376);
  SET_ENTITY ("fnof", 402);
  SET_ENTITY ("circ", 710);
  SET_ENTITY ("tilde", 732);
  for (index = 913; index <= 982; index++)
    {
      str = greek_letters[index - 913];
      if (str != NULL)
        SET_ENTITY (str, index);
    }
  for (index = 8194; index <= 8260; index++)
    {
      str = range_8194_8260[index - 8194];
      if (str != NULL)
        SET_ENTITY (str, index);
    }
  SET_ENTITY ("euro", 8364);
  SET_ENTITY ("image", 8465);
  SET_ENTITY ("weierp", 8472);
  SET_ENTITY ("real", 8476);
  SET_ENTITY ("trade", 8482);
  SET_ENTITY ("alefsym", 8501);
  SET_ENTITY ("larr", 8592);
  SET_ENTITY ("uarr", 8593);
  SET_ENTITY ("rarr", 8594);
  SET_ENTITY ("darr", 8595);
  SET_ENTITY ("harr", 8596);
  SET_ENTITY ("crarr", 8629);
  SET_ENTITY ("lArr", 8656);
  SET_ENTITY ("uArr", 8657);
  SET_ENTITY ("rArr", 8658);
  SET_ENTITY ("dArr", 8659);
  SET_ENTITY ("hArr", 8660);
  for (index = 8704; index <= 8839; index++)
    {
      str = math_symbols[index - 8704];
      if (str != NULL)
        SET_ENTITY (str, index);
    }
  SET_ENTITY ("oplus", 8853);
  SET_ENTITY ("otimes", 8855);
  SET_ENTITY ("perp", 8869);
  SET_ENTITY ("sdot", 8901);
  SET_ENTITY ("lceil", 8968);
  SET_ENTITY ("rceil", 8969);
  SET_ENTITY ("lfloor", 8970);
  SET_ENTITY ("rfloor", 8971);
  SET_ENTITY ("lang", 9001);
  SET_ENTITY ("rang", 9002);
  SET_ENTITY ("loz", 9674);
  SET_ENTITY ("spades", 9824);
  SET_ENTITY ("clubs", 9827);
  SET_ENTITY ("hearts", 9829);
  SET_ENTITY ("diams", 9830);
}


/*********************
 * Cursor management *
 *********************/

gchar
get_char_from_data (Parser * parser)
{
  return (gchar) (*(parser->source.cursor++));
}


gchar
get_char_from_file (Parser * parser)
{
  int c;

  /* Error or End Of File =>  EOF */
  c = fgetc (parser->source.file);
  if (c == EOF)
    c = '\0';

  return (gchar) c;
}

gchar
move_cursor (Parser * parser)
{
  Stream *stream;
  gchar next_char;
  gint size;

  /* Not currently in the source ? */
  if (parser->streams_stack_size > 0)
    {
      for (;;)
        {
          stream = (Stream *) arp_get_index (parser->streams_stack,
                                             parser->streams_stack_size - 1);
          next_char = *(++(stream->cursor));
          /* This stream is not empty */
          if (next_char != '\0')
            return parser->cursor_char = next_char;

          /* It is empty :-( */
          size = --(parser->streams_stack_size);

          /* No more stream ? */
          if (!size)
            break;
        }
    }

  /* In the source ! */
  if (parser->cursor_char == '\n')
    {
      parser->source_row++;
      parser->source_col = 1;
    }
  else
    parser->source_col++;

  return parser->cursor_char = (*(parser->get_char)) (parser);
}


/**********************
 * Internal functions *
 **********************/

gchar *
parser_search_namespace (Parser * parser, gchar * prefix)
{
  gint idx;
  Namespace *namespace;

  for (idx = parser->ns_stack_size - 1,
       namespace = (Namespace *) arp_get_index (parser->ns_stack, idx);
       idx >= 0; idx--, namespace--)
    {
      if (namespace->prefix == prefix)
        return namespace->uri;
    }

  return NULL;
}


void
parser_push_namespace (Parser * parser, gchar * prefix, gchar * uri)
{
  Namespace *namespace;

  namespace = (Namespace *) arp_get_index (parser->ns_stack,
                                           parser->ns_stack_size);

  namespace->prefix = prefix;
  namespace->uri = g_string_chunk_insert_const (parser->strings_storage, uri);

  parser->ns_stack_size++;

  /* Default ? */
  if (prefix == intern_empty)
    parser->default_ns = namespace->uri;
}


/*********************
 * Parsing functions *
 *********************/

/* parser_error */
gboolean
_parser_error (Parser * parser, ErrorEvent * event, gchar * msg)
{
  event->description = (gchar *) msg;
  event->error_row = parser->source_row;
  event->error_column = parser->source_col;
  event->type = XML_ERROR;
  return ERROR;
}

#define PARSER_ERROR(msg) _parser_error(parser, (ErrorEvent *)(event), msg)


/* Warning this function uses parser->buffer4
 */
gboolean
parser_read_parameter_entity (Parser * parser)
{
  gpointer value;
  Stream *stream;

  /* Read the '%' */
  move_cursor (parser);

  /* Read the entity name */
  g_string_set_size (parser->buffer4, 0);
  for (;;)
    {
      switch (parser->cursor_char)
        {
        case ';':
          goto for_end;
        case '\0':
          return ERROR;
        default:
          g_string_append_c (parser->buffer4, parser->cursor_char);
        }
      move_cursor (parser);
    }
for_end:

  /* We must find it in the PE_table ! */
  value = g_hash_table_lookup (parser->PE_table, parser->buffer4->str);
  if (value)
    {
      stream = (Stream *) arp_get_index (parser->streams_stack,
                                         (parser->streams_stack_size)++);
      stream->cursor = (gchar *) value;
      parser->cursor_char = *((gchar *) value);
      return ALL_OK;
    }

  return ERROR;
}


gboolean
parser_read_value_entity (Parser * parser, GString * buffer)
{
  gunichar code = 0;

  /* Hexadecimal ? */
  if (move_cursor (parser) == 'x')
    {
      /* Yes */

      /* At least one character! */
      if (move_cursor (parser) == ';')
        return ERROR;

      for (;; move_cursor (parser))
        {
          /* 0 -> 9 */
          if (isdigit (parser->cursor_char))
            {
              code = code * 16 + parser->cursor_char - '0';
              continue;
            }
          /* a -> f */
          if ('a' <= parser->cursor_char && parser->cursor_char <= 'f')
            {
              code = code * 16 + parser->cursor_char - 'a' + 10;
              continue;
            }
          /* A -> F */
          if ('A' <= parser->cursor_char && parser->cursor_char <= 'F')
            {
              code = code * 16 + parser->cursor_char - 'A' + 10;
              continue;
            }
          break;
        }
    }
  else
    {
      /* No => decimal */

      /* At least one character! */
      if (parser->cursor_char == ';')
        return ERROR;

      for (; isdigit (parser->cursor_char); move_cursor (parser))
        {
          code = code * 10 + parser->cursor_char - '0';
          continue;
        }
    }

  /* Read the ';' */
  if (parser->cursor_char != ';')
    return ERROR;
  move_cursor (parser);

  /* From codepoint to str (UTF-8). */
  g_string_append_unichar (buffer, code);

  return ALL_OK;
}


/* Warning this function uses parser->buffer4
 */
gboolean
parser_read_entity (Parser * parser, GString * buffer)
{
  gpointer value;
  Stream *stream;

  /* By value ? */
  if (move_cursor (parser) == '#')
    return parser_read_value_entity (parser, buffer);

  /* No, so read the entity name */
  g_string_set_size (parser->buffer4, 0);
  for (;;)
    {
      switch (parser->cursor_char)
        {
        case ';':
          goto for_end;
        case '\0':
          return ERROR;
        default:
          g_string_append_c (parser->buffer4, parser->cursor_char);
        }
      move_cursor (parser);
    }
for_end:

  /* In doctype, we only copy the name */
  if (parser->in_doctype)
    {
      g_string_append_c (buffer, '&');
      g_string_append (buffer, parser->buffer4->str);
      g_string_append_c (buffer, ';');

      /* Read the ';' */
      move_cursor (parser);
      return ALL_OK;
    }

  /* Looking for in the builtin entities */
  value = g_hash_table_lookup (parser_builtin_entities, parser->buffer4->str);
  if (value)
    {
      /* Yes */
      g_string_append_unichar (buffer, (gunichar) (gulong) value);

      /* Read the ';' */
      move_cursor (parser);
      return ALL_OK;
    }

  /* We must find it in the GE_table ! */
  value = g_hash_table_lookup (parser->GE_table, parser->buffer4->str);
  if (value)
    {
      stream = (Stream *) arp_get_index (parser->streams_stack,
                                         (parser->streams_stack_size)++);
      stream->cursor = (gchar *) value;
      parser->cursor_char = *((gchar *) value);
      return ALL_OK;
    }

  return ERROR;
}


/* After this function,
 * cursor_char = the last character of the expected string
 */
gboolean
parser_read_string (Parser * parser, gchar * expected)
{
  gchar *cursor;
  for (cursor = expected; *cursor != '\0'; cursor++)
    {
      if (*cursor != move_cursor (parser))
        return ERROR;
    }
  return ALL_OK;
}


/* http://www.w3.org/TR/REC-xml/#NT-S
 * Warning, we parse here "S?"
 */
#define parser_read_S(parser) while(isspace((parser)->cursor_char))\
                                {move_cursor(parser);}


/* http://www.w3.org/TR/REC-xml/#dt-comment */
gboolean
parser_read_Comment (Parser * parser, TextEvent * event)
{
  if (move_cursor (parser) != '-')
    return PARSER_ERROR (INVALID_TOKEN);

  g_string_set_size (parser->buffer1, 0);
  for (;;)
    {
      /* Stop condition: "-->" */
      if (move_cursor (parser) == '-')
        {
          if (move_cursor (parser) == '-')
            {
              if (move_cursor (parser) != '>')
                return PARSER_ERROR (INVALID_TOKEN);

              /* Read '>' */
              move_cursor (parser);

              /* All OK */
              event->text = parser->buffer1->str;
              event->type = COMMENT;
              return ALL_OK;
            }
          else
            g_string_append_c (parser->buffer1, '-');
        }

      /* Something else. */
      if (parser->cursor_char == '\0')
        return PARSER_ERROR (INVALID_TOKEN);
      g_string_append_c (parser->buffer1, parser->cursor_char);
    }
}


/* http://www.w3.org/TR/REC-xml/#NT-CDSect */
gboolean
parser_read_CDSect (Parser * parser, TextEvent * event)
{
  if (parser_read_string (parser, "CDATA["))
    return PARSER_ERROR (INVALID_TOKEN);

  g_string_set_size (parser->buffer1, 0);

  for (;;)
    {
      /* Stop condition: "]]>" */
      if (move_cursor (parser) == ']')
        {
          if (move_cursor (parser) == ']')
            {
              if (move_cursor (parser) == '>')
                {
                  /* Read '>' */
                  move_cursor (parser);

                  /* All OK */
                  event->text = parser->buffer1->str;
                  event->type = CDATA;
                  return ALL_OK;
                }
              g_string_append_c (parser->buffer1, ']');
            }
          g_string_append_c (parser->buffer1, ']');
        }

      /* Something else. */
      if (parser->cursor_char == '\0')
        return PARSER_ERROR (INVALID_TOKEN);
      g_string_append_c (parser->buffer1, parser->cursor_char);
    }
}


/* The first character is under cursor_char
 */
void
parser_read_Name (Parser * parser, GString * name)
{
  g_string_set_size (name, 0);

  /* Read as much as possible */
  while (IS_NAME_CHAR (parser->cursor_char))
    {
      g_string_append_c (name, parser->cursor_char);
      move_cursor (parser);
    }
}


gboolean
parser_read_value (Parser * parser, GString * value)
{
  gchar delimiter;

  switch (parser->cursor_char)
    {
    case '"':
    case '\'':
      delimiter = parser->cursor_char;
      /* And read it */
      move_cursor (parser);
      break;
    default:
      return ERROR;
    }

  g_string_set_size (value, 0);

  for (;;)
    {
      if (parser->cursor_char == delimiter)
        {
          /* Read the delimiter */
          move_cursor (parser);
          return ALL_OK;
        }

      switch (parser->cursor_char)
        {
        case '\0':
          return ERROR;
        case '&':
          if (parser_read_entity (parser, value))
            return ERROR;
          continue;
        case '%':
          if (parser->in_doctype)
            {
              if (parser_read_parameter_entity (parser))
                return ERROR;
              continue;
            }
        default:
          g_string_append_c (value, parser->cursor_char);
          move_cursor (parser);
          break;
        }
    }
}



/* The first character is under cursor_char
 * Warning: This function uses parser->buffer1
 */
gboolean
parser_read_QName (Parser * parser, gchar ** prefix, gchar ** name)
{
  HStrTree *tree;
  HStrTree *parent;
  gchar *str;

  G_LOCK (interned_strings);

  /* Read the prefix. */
  tree = interned_strings_tree;
  while (IS_NC_NAME_CHAR (parser->cursor_char))
    {
      tree = h_str_tree_traverse (tree, parser->cursor_char);
      move_cursor (parser);
    }

  /* Test the string is not missing. */
  if (tree == interned_strings_tree)
    {
      G_UNLOCK (interned_strings);
      return ERROR;
    }

  /* Get the value. */
  if (!(tree->data))
    {
      g_string_set_size (parser->buffer1, 0);
      parent = tree;
      while (parent->parent)
        {
          g_string_prepend_c (parser->buffer1, parent->chr);
          parent = parent->parent;
        }
      str = g_string_chunk_insert (interned_strings, parser->buffer1->str);
      tree->data = str;
    }
  else
    {
      str = tree->data;
    }

  /* Just the name ? */
  if (parser->cursor_char != ':')
    {
      *prefix = intern_empty;
      *name = str;
      G_UNLOCK (interned_strings);
      return ALL_OK;
    }

  /* => Prefix = str */
  *prefix = str;

  /* Read the ':' */
  move_cursor (parser);

  /* Read the name */
  tree = interned_strings_tree;
  while (IS_NAME_CHAR (parser->cursor_char))
    {
      tree = h_str_tree_traverse (tree, parser->cursor_char);
      move_cursor (parser);
    }

  /* Test the string is not missing. */
  if (tree == interned_strings_tree)
    {
      G_UNLOCK (interned_strings);
      return ERROR;
    }

  /* Get the value. */
  if (!(tree->data))
    {
      g_string_set_size (parser->buffer1, 0);
      parent = tree;
      while (parent->parent)
        {
          g_string_prepend_c (parser->buffer1, parent->chr);
          parent = parent->parent;
        }
      str = g_string_chunk_insert (interned_strings, parser->buffer1->str);
      tree->data = str;
    }
  else
    {
      str = tree->data;
    }

  /* Store the result */
  *name = str;

  G_UNLOCK (interned_strings);
  return ALL_OK;
}


/* http://www.w3.org/TR/REC-xml/#NT-Eq */
gboolean
parser_read_Eq (Parser * parser)
{
  parser_read_S (parser);

  if (parser->cursor_char != '=')
    return ERROR;
  move_cursor (parser);

  parser_read_S (parser);

  return ALL_OK;
}


gboolean
parser_read_STag (Parser * parser, StartTagEvent * event)
{
  Attribute *attribute;
  gint attributes_number = 0;
  gboolean end_tag;
  gint idx;
  gint ns_number = 0;
  Tag *tag;
  gchar *tag_uri, *tag_name;

  /* prefix and name */
  if (parser_read_QName (parser, &tag_uri, &tag_name))
    return PARSER_ERROR (INVALID_TOKEN);

  /* Read the attributes */
  for (;;)
    {
      parser_read_S (parser);

      switch (parser->cursor_char)
        {
        case '/':
          if (move_cursor (parser) != '>')
            return PARSER_ERROR (INVALID_TOKEN);
          move_cursor (parser);
          end_tag = TRUE;
          goto for_end;
        case '>':
          move_cursor (parser);
          end_tag = FALSE;
          goto for_end;
        case '\0':
          return PARSER_ERROR (INVALID_TOKEN);
        default:
          /* New attribute */
          attribute = (Attribute *) arp_get_index (parser->attr_storage,
                                                   attributes_number);

          /* prefix and name */
          if (parser_read_QName (parser, &(attribute->uri),
                                 &(attribute->name)))
            return PARSER_ERROR (INVALID_TOKEN);

          /* Eq */
          if (parser_read_Eq (parser))
            return PARSER_ERROR (INVALID_TOKEN);

          /* Value */
          if (parser_read_value (parser, attribute->value))
            return PARSER_ERROR (INVALID_TOKEN);

          /* Namespaces management */
          /* xmlns="..." => default namespace */
          if (attribute->uri == intern_empty &&
              attribute->name == intern_xmlns)
            {
              ns_number++;
              parser_push_namespace (parser, intern_empty,
                                     attribute->value->str);
              /* XXX: with the continue, this "attribute" is not sent */
              /* continue; */
            }
          /* xmlns:prefix="..." => define a new prefix */
          if (attribute->uri == intern_xmlns)
            {
              ns_number++;
              parser_push_namespace (parser, attribute->name,
                                     attribute->value->str);
              /* XXX: with the continue, this "attribute" is not sent */
              /* continue; */
            }
        }
      attributes_number++;
    }
for_end:

  /* Tag URI/NAME */
  if (tag_uri == intern_empty)
    tag_uri = parser->default_ns;
  else
    {
      tag_uri = parser_search_namespace (parser, tag_uri);
      if (!(tag_uri))
        return PARSER_ERROR (INVALID_NAMESPACE);
    }
  event->uri = tag_uri;
  event->name = tag_name;

  /* Attributes URI */
  for (attribute = (Attribute *) parser->attr_storage->data, idx = 0;
       idx < attributes_number; attribute++, idx++)
    {
      if (attribute->uri == intern_empty)
        attribute->uri = tag_uri;
      else
        {
          attribute->uri = parser_search_namespace (parser, attribute->uri);
          if (!(attribute->uri))
            return PARSER_ERROR (INVALID_NAMESPACE);
        }
    }

  /* Prepare the EndTagEvent */
  if (end_tag)
    {
      /* Delete the namespaces */
      if (ns_number > 0)
        {
          parser->ns_stack_size -= ns_number;
          parser->default_ns = parser_search_namespace (parser, "");
          if (!(parser->default_ns))
            parser->default_ns = intern_empty;
        }

      /* Make the next event */
      parser->end_tag = TRUE;
      parser->end_tag_uri = tag_uri;
      parser->end_tag_name = tag_name;
    }
  else
    {
      tag =
        (Tag *) arp_get_index (parser->tags_stack, parser->tags_stack_size);

      /* Push the current tag */
      tag->uri = tag_uri;
      tag->name = tag_name;
      tag->ns_number = ns_number;

      (parser->tags_stack_size)++;
    }

  /* All OK */
  event->type = START_ELEMENT;
  event->attributes = (Attribute *) parser->attr_storage->data;
  event->attributes_number = attributes_number;

  return ALL_OK;
}


/* http://www.w3.org/TR/REC-xml/#NT-ETag */
gboolean
parser_read_ETag (Parser * parser, EndTagEvent * event)
{
  Tag *tag;
  gchar *tag_uri, *tag_name;

  /* Read '/' */
  move_cursor (parser);

  /* prefix and name */
  if (parser_read_QName (parser, &tag_uri, &tag_name))
    return PARSER_ERROR (INVALID_TOKEN);

  /* prefix -> URI */
  if (tag_uri == intern_empty)
    tag_uri = parser->default_ns;
  else
    {
      tag_uri = parser_search_namespace (parser, tag_uri);
      if (!(tag_uri))
        return PARSER_ERROR (INVALID_NAMESPACE);
    }

  parser_read_S (parser);

  /* Read '>' */
  if (parser->cursor_char != '>')
    return PARSER_ERROR (INVALID_TOKEN);
  move_cursor (parser);

  /* Pop the tag */
  if (parser->tags_stack_size <= 0)
    return PARSER_ERROR (INVALID_TOKEN);
  (parser->tags_stack_size)--;
  tag = (Tag *) arp_get_index (parser->tags_stack, parser->tags_stack_size);

  /* Verification */
  if (tag_uri != tag->uri || tag_name != tag->name)
    return PARSER_ERROR (INVALID_TOKEN);

  /* Delete the namespaces */
  if (tag->ns_number > 0)
    {
      parser->ns_stack_size -= tag->ns_number;
      parser->default_ns = parser_search_namespace (parser, "");
      if (!(parser->default_ns))
        parser->default_ns = intern_empty;
    }

  /* All OK */
  event->uri = tag_uri;
  event->name = tag_name;
  event->type = END_ELEMENT;
  return ALL_OK;
}


/* http://www.w3.org/TR/REC-xml/#NT-content */
gboolean
parser_read_content (Parser * parser, TextEvent * event)
{
  g_string_set_size (parser->buffer1, 0);

  for (;;)
    {
      switch (parser->cursor_char)
        {
        case '\0':
        case '<':
          goto for_end;
        case '&':
          if (parser_read_entity (parser, parser->buffer1))
            return PARSER_ERROR (BAD_ENTITY);
          continue;
        default:
          g_string_append_c (parser->buffer1, parser->cursor_char);
          move_cursor (parser);
          break;
        }
    }
for_end:

  /* All OK */
  event->text = parser->buffer1->str;
  event->type = TEXT;
  return ALL_OK;
}


/* http://www.w3.org/TR/REC-xml/#NT-XMLDecl */
gboolean
parser_read_XMLDecl (Parser * parser, DeclEvent * event)
{
  parser_read_S (parser);

  /* Version (in buffer1) */
  if (parser->cursor_char != 'v')
    return PARSER_ERROR (INVALID_TOKEN);
  if (parser_read_string (parser, "ersion"))
    return PARSER_ERROR (INVALID_TOKEN);
  move_cursor (parser);

  if (parser_read_Eq (parser))
    return PARSER_ERROR (INVALID_TOKEN);

  if (parser_read_value (parser, parser->buffer1))
    return PARSER_ERROR (INVALID_TOKEN);

  parser_read_S (parser);

  /* Encoding? (in buffer2) */
  g_string_assign (parser->buffer2, "utf-8");
  if (parser->cursor_char == 'e')
    {
      if (parser_read_string (parser, "ncoding"))
        return PARSER_ERROR (INVALID_TOKEN);
      move_cursor (parser);

      if (parser_read_Eq (parser))
        return PARSER_ERROR (INVALID_TOKEN);

      if (parser_read_value (parser, parser->buffer2))
        return PARSER_ERROR (INVALID_TOKEN);

      parser_read_S (parser);
    }

  /* SDDecl? */
  g_string_set_size (parser->buffer3, 0);
  if (parser->cursor_char == 's')
    {
      if (parser_read_string (parser, "tandalone"))
        return PARSER_ERROR (INVALID_TOKEN);
      move_cursor (parser);

      if (parser_read_Eq (parser))
        return PARSER_ERROR (INVALID_TOKEN);

      if (parser_read_value (parser, parser->buffer3))
        return PARSER_ERROR (INVALID_TOKEN);

      parser_read_S (parser);
    }

  /* Read '?>' */
  if (parser->cursor_char != '?')
    return PARSER_ERROR (INVALID_TOKEN);
  if (move_cursor (parser) != '>')
    return PARSER_ERROR (INVALID_TOKEN);
  move_cursor (parser);

  /* All OK */
  event->version = parser->buffer1->str;
  event->encoding = parser->buffer2->str;
  event->standalone = parser->buffer3->str;
  event->type = XML_DECL;
  return ALL_OK;
}


gboolean
parser_read_PI_or_XMLDecl (Parser * parser, Event * event)
{
  /* Read the '?' */
  move_cursor (parser);

  /* Read the Name */
  parser_read_Name (parser, parser->buffer1);

  if (!strcmp (parser->buffer1->str, "xml"))
    {
      /* XMLDecl */
      return parser_read_XMLDecl (parser, (DeclEvent *) event);
    }

  /* PI */
  parser_read_S (parser);

  /* Read content */
  g_string_set_size (parser->buffer2, 0);
  for (;;)
    {
      /* Stop condition: "?>" */
      if (parser->cursor_char == '?')
        {
          if (move_cursor (parser) == '>')
            {
              /* Read '>' */
              move_cursor (parser);

              /* All OK */
              ((PIEvent *) event)->pi_target = parser->buffer1->str;
              ((PIEvent *) event)->content = parser->buffer2->str;
              event->type = PI;
              return ALL_OK;
            }
          else
            g_string_append_c (parser->buffer2, '?');
        }

      /* Something else. */
      if (parser->cursor_char == '\0')
        return PARSER_ERROR (INVALID_TOKEN);
      g_string_append_c (parser->buffer2, parser->cursor_char);
      move_cursor (parser);
    }
}


gboolean
parser_goto_gt (Parser * parser)
{
  /* TODO: handle the string */

  /* Search for '>' */
  while (parser->cursor_char != '>' && parser->cursor_char != '\0')
    move_cursor (parser);

  if (parser->cursor_char == '\0')
    return ERROR;

  /* Read '>' */
  move_cursor (parser);

  return ALL_OK;
}


gboolean
parser_read_EntityDecl (Parser * parser)
{
  gboolean PE = FALSE;
  gchar *name, *value;

  /* Read 'ENTITY' */
  if (parser_read_string (parser, "TITY"))
    return ERROR;
  move_cursor (parser);

  parser_read_S (parser);

  /* PE? */
  if (parser->cursor_char == '%')
    {
      move_cursor (parser);
      parser_read_S (parser);
      PE = TRUE;
    }

  /* Name (in buffer1) */
  parser_read_Name (parser, parser->buffer1);

  parser_read_S (parser);

  /* Read the value */
  switch (parser->cursor_char)
    {
    case '\'':
    case '"':
      /* Read value (in buffer2) */
      if (parser_read_value (parser, parser->buffer2))
        return ERROR;
      break;
    case 'S':
    case 'P':
      /* 'SYSTEM' or 'PUBLIC' => TODO */
      return parser_goto_gt (parser);
    default:
      return ERROR;
    }

  parser_read_S (parser);

  /* Read the '>' */
  if (parser->cursor_char != '>')
    return ERROR;
  move_cursor (parser);

  /* Save */
  name =
    g_string_chunk_insert (parser->strings_storage, parser->buffer1->str);
  value =
    g_string_chunk_insert (parser->strings_storage, parser->buffer2->str);

  if (PE)
    g_hash_table_insert (parser->PE_table, (gpointer) name, (gpointer) value);
  else
    g_hash_table_insert (parser->GE_table, (gpointer) name, (gpointer) value);

  return ALL_OK;
}


gboolean
parser_read_intSubset (Parser * parser)
{
  /* Read the '[' */
  move_cursor (parser);

  for (;;)
    switch (parser->cursor_char)
      {
      case '\0':
        return ERROR;
      case ']':
        /* Read ']' */
        move_cursor (parser);
        return ALL_OK;
      case '\n':
      case '\r':
      case ' ':
      case '\t':
        /* Read S */
        move_cursor (parser);
        continue;
      case '%':
        if (parser_read_parameter_entity (parser))
          return ERROR;
        continue;
      case '<':
        /* We parse only the ENTITIES */
        if (move_cursor (parser) == '!')
          if (move_cursor (parser) == 'E')
            if (move_cursor (parser) == 'N')
              {
                if (parser_read_EntityDecl (parser))
                  return ERROR;
                continue;
              }
        if (parser_goto_gt (parser))
          return ERROR;
        continue;
      default:
        return ERROR;
      }
}

void
parser_compute_urn (gchar * source, GString * target)
{
  g_string_assign (target, "urn:publicid:");
  for (; *source != '\0'; source++)
    {
      switch (*source)
        {
        case ' ':
          if (*(source + 1) != ' ')
            g_string_append_c (target, '+');
          break;
        case '/':
          if (*(source + 1) == '/')
            {
              g_string_append_c (target, ':');
              source++;
            }
          else
            g_string_append (target, "%2F");
          break;
        case ':':
          if (*(source + 1) == ':')
            {
              g_string_append_c (target, ';');
              source++;
            }
          else
            g_string_append (target, "%3A");
          break;
        case ';':
          g_string_append (target, "%3B");
          break;
        case '\'':
          g_string_append (target, "%27");
          break;
        case '?':
          g_string_append (target, "%3F");
          break;
        case '#':
          g_string_append (target, "%23");
          break;
        case '%':
          g_string_append (target, "%25");
          break;
        default:
          g_string_append_c (target, *source);
          break;
        }
    }
}


gboolean
parser_read_public_doctype (Parser * parser, gchar * public_id,
                            gchar * system_id)
{
  parser_compute_urn (public_id, parser->buffer1);


  return ALL_OK;
}


/* http://www.w3.org/TR/REC-xml/#NT-doctypedecl */
gboolean
parser_read_doctypedecl (Parser * parser)
{
  if (parser_read_string (parser, "OCTYPE"))
    return ERROR;
  move_cursor (parser);

  /* We are in the doctypes */
  parser->in_doctype = TRUE;

  parser_read_S (parser);

  /* Read Name (in buffer1 => not verified) */
  parser_read_Name (parser, parser->buffer1);
  parser_read_S (parser);

  /* ('SYSTEM' S  SystemLiteral) ? */
  if (parser->cursor_char == 'S')
    {
      if (parser_read_string (parser, "YSTEM"))
        return ERROR;
      move_cursor (parser);

      parser_read_S (parser);

      /* Read SystemLiteral (in buffer2) */
      if (parser_read_value (parser, parser->buffer2))
        return ERROR;

      /* Read the system doctype */
      /* XXX: Finish me */

      parser_read_S (parser);
    }
  else
    /* ('PUBLIC' S PubidLiteral S SystemLiteral) ? */
  if (parser->cursor_char == 'P')
    {
      if (parser_read_string (parser, "UBLIC"))
        return ERROR;
      move_cursor (parser);

      parser_read_S (parser);

      /* Read PubidLiteral (in buffer3) */
      if (parser_read_value (parser, parser->buffer3))
        return ERROR;

      parser_read_S (parser);

      /* Read SystemLiteral (in buffer2) */
      if (parser_read_value (parser, parser->buffer2))
        return ERROR;

      /* Read the public doctype */
      if (parser_read_public_doctype (parser, parser->buffer3->str,
                                      parser->buffer2->str))
        return ERROR;

      parser_read_S (parser);
    }

  /* intSubset ? */
  if (parser->cursor_char == '[')
    {
      /* Read '[' */
      move_cursor (parser);

      /* Read the doctype */
      if (parser_read_intSubset (parser))
        return ERROR;

      parser_read_S (parser);
    }

  /* Read '>' */
  if (parser->cursor_char != '>')
    return ERROR;
  move_cursor (parser);

  /* All OK */
  parser->in_doctype = FALSE;
  return ALL_OK;
}


void
parser_read_BOM (Parser * parser)
{
  /* XXX: We detect only the UTF-8 Byte Order Mark */
  /* If an error occurs the bytes are not replaced in the stream */
  if ((unsigned char) parser->cursor_char == 0xEF)
    if ((unsigned char) move_cursor (parser) == 0xBB)
      if ((unsigned char) move_cursor (parser) == 0xBF)
        move_cursor (parser);
}


/**************************************************************************
 * The API
 *************************************************************************/

void
parser_initialize (void)
{
  /* Initialize interned strings (prefix & name). */
  G_LOCK (interned_strings);
  interned_strings_tree = h_str_tree_new ();
  interned_strings = g_string_chunk_new (64);
  intern_empty = intern_string ("");
  intern_xmlns = intern_string ("xmlns");
  intern_string ("xml");
  G_UNLOCK (interned_strings);

  /* Initialize the built-in entity references. */
  parser_init_builtin_entities ();
}


void
parser_destroy (void)
{
  h_str_tree_free (interned_strings_tree);
  g_string_chunk_free (interned_strings);
  g_hash_table_destroy (parser_builtin_entities);
}


Parser *
parser_new (gchar * data, FILE * file)
{
  Parser *parser;

  /* Arguments verification */
  if ((data == NULL && file == NULL) || (data != NULL && file != NULL))
    return NULL;


  /* Memory allocation */
  parser = g_new (Parser, 1);

  /* The Glib objects */
  parser->buffer1 = g_string_sized_new (256);
  parser->buffer2 = g_string_sized_new (256);
  parser->buffer3 = g_string_sized_new (256);
  parser->buffer4 = g_string_sized_new (256);
  parser->strings_storage = g_string_chunk_new (64);
  parser->GE_table = g_hash_table_new (g_str_hash, g_str_equal);
  parser->PE_table = g_hash_table_new (g_str_hash, g_str_equal);

  /* Document management */
  parser->streams_stack = arp_new (sizeof (Stream), NULL, NULL);
  parser->streams_stack_size = 0;
  parser->in_doctype = FALSE;

  /* Attributes */
  parser->attr_storage = arp_new (sizeof (Attribute), parser_attr_constructor,
                                  parser_attr_destructor);

  /* Tags */
  parser->tags_stack = arp_new (sizeof (Tag), NULL, NULL);
  parser->tags_stack_size = 0;
  parser->end_tag = FALSE;

  /* Namespaces */
  parser->ns_stack = arp_new (sizeof (Namespace), NULL, NULL);
  parser->ns_stack_size = 0;
  parser->default_ns = intern_empty;

  /* Set the default namespaces */
  parser_add_namespace (parser, "xml",
                        "http://www.w3.org/XML/1998/namespace");
  parser_add_namespace (parser, "xmlns", "http://www.w3.org/2000/xmlns/");

  /* Set the good handler */
  if (data)
    {
      parser->source.cursor = data;
      parser->get_char = &get_char_from_data;
    }
  else
    {
      parser->source.file = file;
      parser->get_char = &get_char_from_file;
    }

  /* Prepare some variables */
  parser->source_row = 1;
  parser->source_col = 1;
  parser->cursor_char = (*(parser->get_char)) (parser);

  /* And read the BOM */
  parser_read_BOM (parser);

  return parser;
}


void
parser_free (Parser * parser)
{
  /* Delete the Glib objects */
  g_string_free (parser->buffer1, TRUE);
  g_string_free (parser->buffer2, TRUE);
  g_string_free (parser->buffer3, TRUE);
  g_string_free (parser->buffer4, TRUE);
  g_string_chunk_free (parser->strings_storage);
  g_hash_table_destroy (parser->GE_table);
  g_hash_table_destroy (parser->PE_table);

  /* Delete the arp objects */
  arp_free (parser->streams_stack);
  arp_free (parser->attr_storage);
  arp_free (parser->tags_stack);
  arp_free (parser->ns_stack);

  /* And delete the parser object */
  g_free (parser);
}


void
parser_add_namespace (Parser * parser, gchar * prefix, gchar * uri)
{
  parser_push_namespace (parser, intern_string (prefix), uri);
}


gboolean
parser_next (Parser * parser, Event * event)
{
  /* End tag ? */
  if (parser->end_tag)
    {
      event->common_event.row = parser->source_row;
      event->common_event.column = parser->source_col;

      parser->end_tag = FALSE;

      ((EndTagEvent *) event)->uri = parser->end_tag_uri;
      ((EndTagEvent *) event)->name = parser->end_tag_name;
      event->type = END_ELEMENT;
      return ALL_OK;
    }

  for (;;)
    {
      /* Event position = starting point of the event in the source */
      event->common_event.row = parser->source_row;
      event->common_event.column = parser->source_col;

      /* Main switch */
      switch (parser->cursor_char)
        {
        case '\0':
          /* The end ? The open tags must be closed. */
          if (parser->tags_stack_size > 0)
            return PARSER_ERROR (MISSING);
          /* All OK */
          event->type = END_DOCUMENT;
          return ALL_OK;
        case '<':
          /* "<" */
          switch (move_cursor (parser))
            {
            case '!':
              /* "<!" */
              switch (move_cursor (parser))
                {
                case '-':
                  /* "<!-" */
                  return parser_read_Comment (parser, (TextEvent *) event);
                case 'D':
                  /* "<!D" => DOCTYPE */
                  if (parser_read_doctypedecl (parser))
                    return PARSER_ERROR (INVALID_TOKEN);
                  continue;
                case '[':
                  /* "<![" */
                  return parser_read_CDSect (parser, (TextEvent *) event);
                default:
                  return PARSER_ERROR (INVALID_TOKEN);
                }
            case '?':
              return parser_read_PI_or_XMLDecl (parser, event);
            case '/':
              /* "</" */
              return parser_read_ETag (parser, (EndTagEvent *) event);
            default:
              /* "<..." */
              return parser_read_STag (parser, (StartTagEvent *) event);
            }
        default:
          return parser_read_content (parser, (TextEvent *) event);
        }
    }
}

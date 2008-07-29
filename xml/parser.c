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

#include <string.h>
#include <stdlib.h>
#include <ctype.h>
#include <stdio.h>

#include "parser.h"
#include "arp.h"


#define IS_NC_NAME_CHAR(c) \
    (isalnum(c) || (c == '.') || (c == '-') || (c == '_'))
#define IS_NAME_CHAR(c) \
    (isalnum(c) || (c == '.') || (c == '-') || (c == '_') || (c == ':'))


/**************************************************************************
 *  Error messages
 *************************************************************************/

#define BAD_XML_DECL      "XML declaration not well-formed"
#define INVALID_TOKEN     "not well-formed (invalid token)"
#define MISSING           "expected end tag is missing"
#define BAD_ENTITY        "error parsing entity reference"
#define BAD_DTD           "error during parsing the DTD"
#define DUP_DOCTYPE       "a document can only have one doctype"
#define INVALID_NAMESPACE "invalid namespace"


/**************************************************************************
 * Some functions/objects
 *************************************************************************/

/*********************
 * The Parser object *
 *********************/
struct _Parser
{
  /* Source */
  gint source_type;
  union
  {
    gchar *cursor;
    FILE *file;
  } source;
  gint source_row;
  gint source_col;
  gboolean new_line;

  /* Streams management */
  gchar cursor_char;
  Arp *streams_stack;
  gint streams_stack_size;

  /* Four buffers (to do everything) */
  GString *buffer1;
  GString *buffer2;
  GString *buffer3;
  GString *buffer4;

  /* An error buffer */
  GString *err_buffer;

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
  GString *ns_buffer;
  Arp *ns_stack;
  gint ns_stack_size;
  gchar *default_ns;

  /* Entities/DocType management */
  GString *ent_buffer;
  DocType *doctype;
};


/*********************
 * Cursor management *
 *********************/
typedef gchar *Stream;

gchar
move_cursor (Parser * parser)
{
  gint output;
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
          next_char = *((*stream)++);

          /* This stream is not empty */
          if (next_char != '\0')
            return parser->cursor_char = next_char;

          /* It is empty, pop the stream */
          size = --(parser->streams_stack_size);

          /* No more stream ? */
          if (!size)
            break;
        }
    }

  /* In the source ! */
  if (parser->new_line)
    {
      parser->source_row++;
      parser->source_col = 1;
      parser->new_line = FALSE;
    }
  else
    parser->source_col++;

  /* Read the next character */
  if (parser->source_type)
    {
      /* data */
      next_char = *(parser->source.cursor++);
    }
  else
    {
      /* file */
      output = fgetc (parser->source.file);
      next_char = (gchar) (output == EOF ? '\0' : output);
    }

  if (next_char == '\n')
    parser->new_line = TRUE;

  return parser->cursor_char = next_char;
}


void
parser_stream_push (Parser * parser, gchar * data)
{
  Stream *stream;

  /* A place */
  stream = (Stream *) arp_get_index (parser->streams_stack,
                                     (parser->streams_stack_size)++);

  /* Prepare the stream */
  *stream = data;

  /* And prepare the first caracter */
  move_cursor (parser);
}


/************
 * HStrTree *
 ************/

/* The String Tree is a data structure that allows to store compactly a set
 * of strings.  The lookup or insertion of a string is O(n) where "n" is the
 * length of the string.
 */

typedef struct _HStrTree
{
  gchar *data;
  struct _HStrTree *children[256];

  /* Needed to rebuild the string. */
  struct _HStrTree *parent;
  gchar chr;
} HStrTree;


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


/*************
 * Attribute *
 *************/

/* The Attribute object is defined in parser.h
 */

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


/**************************************************************************
 *  Global variables
 *************************************************************************/

/* Initialised ? */
gboolean parser_initialized = FALSE;

/* A global strings storage place */
G_LOCK_DEFINE_STATIC (parser_global_strings);
GStringChunk *parser_global_strings = NULL;

/* Internal entities */
GHashTable *parser_default_entities;

/* Interned string */
HStrTree *intern_strings_tree = NULL;
gchar *intern_empty;
gchar *intern_xmlns;


/**************************************************************************
 * Parser private API
 *************************************************************************/

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


gchar *
intern_string (gchar * str)
{
  HStrTree *node;
  gchar *cursor;

  node = intern_strings_tree;

  /* Get the node */
  for (cursor = str; *cursor != '\0'; cursor++)
    node = h_str_tree_traverse (node, *cursor);

  /* New string? */
  if (!(node->data))
    node->data = g_string_chunk_insert (parser_global_strings, str);

  return node->data;
}


void
parser_initialize (void)
{
  if (!parser_initialized)
    {
      G_LOCK (parser_global_strings);

      /* Glib objects */
      parser_global_strings = g_string_chunk_new (64);
      parser_default_entities = g_hash_table_new (g_str_hash, g_str_equal);

      /* Initialize interned strings (prefix & name). */
      intern_strings_tree = h_str_tree_new ();
      intern_empty = intern_string ("");
      intern_xmlns = intern_string ("xmlns");
      intern_string ("xml");

      /* Set the default entities */
      g_hash_table_insert (parser_default_entities, "lt", "&#60;");
      g_hash_table_insert (parser_default_entities, "gt", ">");
      g_hash_table_insert (parser_default_entities, "amp", "&#38;");
      g_hash_table_insert (parser_default_entities, "apos", "'");
      g_hash_table_insert (parser_default_entities, "quot", "\"");

      G_UNLOCK (parser_global_strings);

      parser_initialized = TRUE;
    }
}


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


/********************************************
 * Parser private general parsing functions *
 ********************************************/
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


gboolean
parser_read_entity (Parser * parser, GString * buffer)
{
  gchar *value;

  /* By value ? */
  if (move_cursor (parser) == '#')
    return parser_read_value_entity (parser, buffer);

  /* No, so read the entity name */
  g_string_set_size (parser->ent_buffer, 0);
  for (;;)
    {
      switch (parser->cursor_char)
        {
        case ';':
          goto for_end;
        case '\0':
          return ERROR;
        default:
          g_string_append_c (parser->ent_buffer, parser->cursor_char);
        }
      move_cursor (parser);
    }
for_end:

  /* In the internal entities ? */
  value = (gchar *) g_hash_table_lookup (parser_default_entities,
                                         parser->ent_buffer->str);
  if (value)
    {
      parser_stream_push (parser, value);
      return ALL_OK;
    }

  /* In the doctype ? */
  if (parser->doctype)
    {
      value = doctype_get_entity_value (parser->doctype,
                                        parser->ent_buffer->str);
      if (value)
        {
          parser_stream_push (parser, value);
          return ALL_OK;
        }
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
        default:
          g_string_append_c (value, parser->cursor_char);
          move_cursor (parser);
          break;
        }
    }
}


gboolean
parser_read_QName (Parser * parser, gchar ** prefix, gchar ** name)
{
  HStrTree *tree;
  HStrTree *parent;
  gchar *str;

  G_LOCK (parser_global_strings);

  /* Read the prefix. */
  tree = intern_strings_tree;
  while (IS_NC_NAME_CHAR (parser->cursor_char))
    {
      tree = h_str_tree_traverse (tree, parser->cursor_char);
      move_cursor (parser);
    }

  /* Test the string is not missing. */
  if (tree == intern_strings_tree)
    {
      G_UNLOCK (parser_global_strings);
      return ERROR;
    }

  /* Get the value. */
  if (!(tree->data))
    {
      g_string_set_size (parser->ns_buffer, 0);
      parent = tree;
      while (parent->parent)
        {
          g_string_prepend_c (parser->ns_buffer, parent->chr);
          parent = parent->parent;
        }
      str =
        g_string_chunk_insert (parser_global_strings, parser->ns_buffer->str);
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
      G_UNLOCK (parser_global_strings);
      return ALL_OK;
    }

  /* => Prefix = str */
  *prefix = str;

  /* Read the ':' */
  move_cursor (parser);

  /* Read the name */
  tree = intern_strings_tree;
  while (IS_NAME_CHAR (parser->cursor_char))
    {
      tree = h_str_tree_traverse (tree, parser->cursor_char);
      move_cursor (parser);
    }

  /* Test the string is not missing. */
  if (tree == intern_strings_tree)
    {
      G_UNLOCK (parser_global_strings);
      return ERROR;
    }

  /* Get the value. */
  if (!(tree->data))
    {
      g_string_set_size (parser->ns_buffer, 0);
      parent = tree;
      while (parent->parent)
        {
          g_string_prepend_c (parser->ns_buffer, parent->chr);
          parent = parent->parent;
        }
      str =
        g_string_chunk_insert (parser_global_strings, parser->ns_buffer->str);
      tree->data = str;
    }
  else
    {
      str = tree->data;
    }

  /* Store the result */
  *name = str;

  G_UNLOCK (parser_global_strings);
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
    if (attribute->uri != intern_empty)
      {
        attribute->uri = parser_search_namespace (parser, attribute->uri);
        if (!(attribute->uri))
          return PARSER_ERROR (INVALID_NAMESPACE);
      }

  /* Prepare the EndTagEvent */
  if (end_tag)
    {
      /* Delete the namespaces */
      if (ns_number > 0)
        {
          parser->ns_stack_size -= ns_number;
          parser->default_ns = parser_search_namespace (parser, intern_empty);
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
      parser->default_ns = parser_search_namespace (parser, intern_empty);
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


/* http://www.w3.org/TR/REC-xml/#NT-doctypedecl */
gboolean
parser_read_doctypedecl (Parser * parser, DocTypeEvent * event)
{
  gchar *PubidLiteral = NULL;
  gchar *SystemLiteral = NULL;
  gchar *intSubset = NULL;
  gchar delimiter;
  DocType *doctype;
  gchar *error_msg;

  /* Read 'OCTYPE' */
  if (parser_read_string (parser, "OCTYPE"))
    return PARSER_ERROR (INVALID_TOKEN);
  move_cursor (parser);

  parser_read_S (parser);

  /* Read Name (in buffer1) */
  parser_read_Name (parser, parser->buffer1);

  parser_read_S (parser);

  /* ('SYSTEM' S  SystemLiteral) ? */
  if (parser->cursor_char == 'S')
    {
      if (parser_read_string (parser, "YSTEM"))
        return PARSER_ERROR (INVALID_TOKEN);
      move_cursor (parser);

      parser_read_S (parser);

      /* Read SystemLiteral */
      if (parser_read_value (parser, parser->buffer2))
        return PARSER_ERROR (INVALID_TOKEN);
      SystemLiteral = parser->buffer2->str;

      parser_read_S (parser);
    }
  else
    /* ('PUBLIC' S PubidLiteral S SystemLiteral) ? */
  if (parser->cursor_char == 'P')
    {
      if (parser_read_string (parser, "UBLIC"))
        return PARSER_ERROR (INVALID_TOKEN);
      move_cursor (parser);

      parser_read_S (parser);

      /* Read PubidLiteral */
      if (parser_read_value (parser, parser->buffer2))
        return PARSER_ERROR (INVALID_TOKEN);
      PubidLiteral = parser->buffer2->str;

      parser_read_S (parser);

      /* Read SystemLiteral */
      if (parser_read_value (parser, parser->buffer3))
        return PARSER_ERROR (INVALID_TOKEN);
      SystemLiteral = parser->buffer3->str;

      parser_read_S (parser);
    }


  /* intSubset ? */
  if (parser->cursor_char == '[')
    {
      /* Make the string */
      g_string_set_size (parser->buffer4, 0);
      for (;;)
        {
          switch (move_cursor (parser))
            {
            case '\'':
            case '"':
              delimiter = parser->cursor_char;
              g_string_append_c (parser->buffer4, delimiter);
              do
                {
                  g_string_append_c (parser->buffer4, move_cursor (parser));
                }
              while (parser->cursor_char != delimiter &&
                     parser->cursor_char != '\0');
              if (parser->cursor_char == '\0')
                return PARSER_ERROR (BAD_DTD);
              break;
            case ']':
              /* Read the ']' */
              move_cursor (parser);
              goto for_end;
            default:
              g_string_append_c (parser->buffer4, parser->cursor_char);
              break;
            }
        }
    for_end:
      intSubset = parser->buffer4->str;

      parser_read_S (parser);
    }

  /* Read '>' */
  if (parser->cursor_char != '>')
    return PARSER_ERROR (INVALID_TOKEN);
  move_cursor (parser);

  /* Create a new DocType object */
  doctype = doctype_new (PubidLiteral, SystemLiteral, intSubset, &error_msg);
  if (!doctype)
    return PARSER_ERROR (error_msg);

  /* Auto associate the doctype to the current document */
  if (parser->doctype)
    {
      doctype_free (doctype);
      return PARSER_ERROR (DUP_DOCTYPE);
    }
  parser->doctype = doctype;

  /* All OK */
  event->name = parser->buffer1->str;
  event->doctype = doctype;
  event->type = DOCUMENT_TYPE;
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
 * Parser public API
 *************************************************************************/

Parser *
parser_new (gchar * data, FILE * file, DocType * doctype)
{
  Parser *parser;

  /* Arguments verification */
  if ((data == NULL && file == NULL) || (data != NULL && file != NULL))
    return NULL;

  /* Initialized ? */
  if (!parser_initialized)
    parser_initialize ();

  /* Memory allocation */
  parser = g_new0 (Parser, 1);

  /* The Glib objects */
  parser->buffer1 = g_string_sized_new (256);
  parser->buffer2 = g_string_sized_new (256);
  parser->buffer3 = g_string_sized_new (256);
  parser->buffer4 = g_string_sized_new (256);
  parser->err_buffer = g_string_sized_new (256);
  parser->strings_storage = g_string_chunk_new (64);
  parser->ns_buffer = g_string_sized_new (256);
  parser->ent_buffer = g_string_sized_new (256);

  /* Streams management */
  parser->streams_stack = arp_new (sizeof (Stream), NULL, NULL);
  parser->streams_stack_size = 0;

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

  /* Source management */
  parser->source_row = 1;
  parser->source_col = 1;
  parser->new_line = FALSE;
  if (data)
    {
      parser->source.cursor = data;
      parser->source_type = 1;
    }
  else
    {
      parser->source.file = file;
      parser->source_type = 0;
    }
  move_cursor (parser);

  /* A DocType ? */
  parser->doctype = doctype;

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
  g_string_free (parser->err_buffer, TRUE);
  g_string_chunk_free (parser->strings_storage);
  g_string_free (parser->ns_buffer, TRUE);
  g_string_free (parser->ent_buffer, TRUE);

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
  /* Event position = starting point of the event in the source */
  event->common_event.row = parser->source_row;
  event->common_event.column = parser->source_col;

  /* End tag ? */
  if (parser->end_tag)
    {
      parser->end_tag = FALSE;

      ((EndTagEvent *) event)->uri = parser->end_tag_uri;
      ((EndTagEvent *) event)->name = parser->end_tag_name;
      event->type = END_ELEMENT;
      return ALL_OK;
    }

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
              return parser_read_doctypedecl (parser, (DocTypeEvent *) event);
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


void
parser_global_reset (void)
{
  if (parser_initialized)
    {
      parser_initialized = FALSE;

      g_string_chunk_free (parser_global_strings);
      g_hash_table_destroy (parser_default_entities);

      h_str_tree_free (intern_strings_tree);
    }
}

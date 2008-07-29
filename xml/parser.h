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

#ifndef PARSER_H
#define PARSER_H

#include <stdio.h>
#include <glib.h>

/**************************************************************************
 * The objects
 *************************************************************************/

/******************************
 * The Parser/DocType objects *
 *       (opaque types)       *
 ******************************/
typedef struct _Parser Parser;
typedef struct _DocType DocType;


/**************
 * The events *
 **************/

/* An attribute */
typedef struct
{
  gchar *uri;
  gchar *name;
  GString *value;
} Attribute;

/* Event types */
#define XML_DECL        0
#define DOCUMENT_TYPE   1
#define START_ELEMENT   2
#define END_ELEMENT     3
#define TEXT            4
#define COMMENT         5
#define PI              6
#define CDATA           7
#define END_DOCUMENT    8
#define XML_ERROR       9


#define EventHeader \
          gint type; \
          gint row; \
          gint column

/* CommonEvent/END_DOCUMENT */
typedef struct
{
  EventHeader;
} CommonEvent;

/* XML_DECL */
typedef struct
{
  EventHeader;
  gchar *version;
  gchar *encoding;
  gchar *standalone;
} DeclEvent;

/* DOCUMENT_TYPE */
typedef struct
{
  EventHeader;
  gchar *name;
  DocType *doctype;
} DocTypeEvent;

/* START_ELEMENT */
typedef struct
{
  EventHeader;
  gchar *uri;
  gchar *name;
  Attribute *attributes;
  guint attributes_number;
} StartTagEvent;

/* END_ELEMENT */
typedef struct
{
  EventHeader;
  gchar *uri;
  gchar *name;
} EndTagEvent;

/* TEXT/COMMENT/CDATA */
typedef struct
{
  EventHeader;
  gchar *text;
} TextEvent;

/* PI */
typedef struct
{
  EventHeader;
  gchar *pi_target;
  gchar *content;
} PIEvent;

/* XML_ERROR */
typedef struct
{
  EventHeader;
  gchar *description;
  gint error_row;
  gint error_column;
} ErrorEvent;

typedef union
{
  int type;

  CommonEvent common_event;
  DeclEvent decl_event;
  DocTypeEvent doctype_event;
  StartTagEvent start_tag_event;
  EndTagEvent end_tag_event;
  TextEvent text_event;
  PIEvent pi_event;
  ErrorEvent error_event;
} Event;


/**************************************************************************
 * The Parser API
 *************************************************************************/

#define ERROR TRUE
#define ALL_OK FALSE


/*******************
 * New/Free Parser *
 *******************/

/* if data != NULL source = data
 * else            source = file
 */
Parser *parser_new (gchar * data, FILE * file, DocType * doctype);
void parser_free (Parser * parser);


/**********************************************
 * Add a prefix/namespace in namespaces table *
 **********************************************/
void parser_add_namespace (Parser * parser, gchar * prefix, gchar * uri);


/*********************
 * The main function *
 *********************/

/*Fill the event and return ALL_OK when there was no error, or ERROR otherwise
 */
gboolean parser_next (Parser * parser, Event * event);


/******************************************************
 * Destroy all data initialised by all Parser objects *
 ******************************************************/
void parser_global_reset (void);


/**************************************************************************
 * The DocType API
 *************************************************************************/

/********************
 * New/Free DocType *
 ********************/
DocType *doctype_new (gchar * PubidLiteral, gchar * SystemLiteral,
                      gchar * intSubset, gchar ** error_msg);
void doctype_free (DocType * doctype);


/******************
 * DocType to str *
 ******************/
gchar *doctype_to_str (DocType * doctype);


/***********************
 * Get an entity value *
 ***********************/
gchar *doctype_get_entity_value (DocType * doctype, gchar * entity_name);


/***********************************
 * Add a urn/filename in URN table *
 ***********************************/
void doctype_register_dtd (gchar * urn, gchar * filename);


/*******************************************************
 * Destroy all data initialised by all DocType objects *
 *******************************************************/
void doctype_global_reset (void);


#endif

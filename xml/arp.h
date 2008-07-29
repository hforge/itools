/*
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

#ifndef ARP_H
#define ARP_H

#include <glib.h>

/**************************************************************************
 * An auto realloc pointer
 *************************************************************************/

/******************
 * The Arp object *
 ******************/
typedef struct
{
  gchar *data;
  gint length;

  gsize object_size;
  void (*constructor) (gpointer object);
  void (*destructor) (gpointer object);
} Arp;


/**************************************************************************
 * The Arp API
 *************************************************************************/

/****************
 * New/Free Arp *
 ****************/
Arp *arp_new (gsize object_size, void (*constructor) (gpointer object),
              void (*destructor) (gpointer object));
void arp_free (Arp * arp);


/***************************************
 * Get a pointer on the <index> object *
 ***************************************/
gchar *arp_get_index (Arp * arp, gint index);


#endif

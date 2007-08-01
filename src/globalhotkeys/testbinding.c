/*
 * Copyright (C) 2007 Lincoln de Sousa <lincoln@archlinux-br.org>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public
 * License along with this program; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "keybinder.h"

#include <gtk/gtk.h>

typedef struct _BindedKey BindedKey;
struct _BindedKey
{
  char *key;
  void *callback;
};

void
handler (char *keystring, gpointer user_data)
{
  printf ("binded key: %s\n", keystring);
}

void
unbind (GtkWidget *bnt, BindedKey *b)
{
  keybinder_unbind (b->key, b->callback);
  printf ("unbinded\n");
}

int
main (int argc, char **argv)
{
  GtkWidget *window;
  GtkWidget *label;
  GtkWidget *vbox;
  GtkWidget *button;
  BindedKey *binded = malloc (sizeof (BindedKey *));

  gtk_init (&argc, &argv);

  binded->key = strdup ("<Ctrl><Alt>e");
  binded->callback = handler;

  keybinder_bind ("<Ctrl><Alt>e", handler, NULL);
  keybinder_init ();

  window = gtk_window_new (GTK_WINDOW_TOPLEVEL);
  gtk_window_set_position (GTK_WINDOW (window), GTK_WIN_POS_CENTER);
  gtk_container_set_border_width (GTK_CONTAINER (window), 10);
  g_signal_connect (G_OBJECT (window), "delete_event",
      G_CALLBACK (exit), 0);

  label = gtk_label_new (NULL);
  gtk_label_set_markup (GTK_LABEL (label),
      "<big>Pres <b>&lt;Ctrl&gt;&lt;Alt&gt;e</b> and "
      "see what is happening in your terminal =D</big>");

  button = gtk_button_new_with_label ("Unbind Key!");
  g_signal_connect (G_OBJECT (button), "clicked",  G_CALLBACK (unbind),
      binded);

  vbox = gtk_vbox_new (1, 10);
  gtk_box_pack_start (GTK_BOX (vbox), label, 1, 1, 0);
  gtk_box_pack_start (GTK_BOX (vbox), button, 1, 1, 0);

  gtk_container_add (GTK_CONTAINER (window), vbox);

  gtk_widget_show_all (window);
  gtk_main ();

  return 0;
}

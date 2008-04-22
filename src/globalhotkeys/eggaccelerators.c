/* eggaccelerators.c
 * Copyright (C) 2002  Red Hat, Inc.; Copyright 1998, 2001 Tim Janik
 * Developed by Havoc Pennington, Tim Janik
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Library General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Library General Public License for more details.
 *
 * You should have received a copy of the GNU Library General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

#include "eggaccelerators.h"

#include <stdlib.h>
#include <string.h>
#include <gdk/gdkx.h>
#include <gdk/gdkkeysyms.h>
#include <gtk/gtkaccelgroup.h>

enum
{
  EGG_MODMAP_ENTRY_SHIFT   = 0,
  EGG_MODMAP_ENTRY_LOCK    = 1,
  EGG_MODMAP_ENTRY_CONTROL = 2,
  EGG_MODMAP_ENTRY_MOD1    = 3,
  EGG_MODMAP_ENTRY_MOD2    = 4,
  EGG_MODMAP_ENTRY_MOD3    = 5,
  EGG_MODMAP_ENTRY_MOD4    = 6,
  EGG_MODMAP_ENTRY_MOD5    = 7,
  EGG_MODMAP_ENTRY_LAST    = 8
};

#define MODMAP_ENTRY_TO_MODIFIER(x) (1 << (x))

typedef struct
{
  EggVirtualModifierType mapping[EGG_MODMAP_ENTRY_LAST];

} EggModmap;

const EggModmap* egg_keymap_get_modmap (GdkKeymap *keymap);

static inline gboolean
is_alt (const gchar *string)
{
  return ((string[0] == '<') &&
	  (string[1] == 'a' || string[1] == 'A') &&
	  (string[2] == 'l' || string[2] == 'L') &&
	  (string[3] == 't' || string[3] == 'T') &&
	  (string[4] == '>'));
}

static inline gboolean
is_ctl (const gchar *string)
{
  return ((string[0] == '<') &&
	  (string[1] == 'c' || string[1] == 'C') &&
	  (string[2] == 't' || string[2] == 'T') &&
	  (string[3] == 'l' || string[3] == 'L') &&
	  (string[4] == '>'));
}

static inline gboolean
is_modx (const gchar *string)
{
  return ((string[0] == '<') &&
	  (string[1] == 'm' || string[1] == 'M') &&
	  (string[2] == 'o' || string[2] == 'O') &&
	  (string[3] == 'd' || string[3] == 'D') &&
	  (string[4] >= '1' && string[4] <= '5') &&
	  (string[5] == '>'));
}

static inline gboolean
is_ctrl (const gchar *string)
{
  return ((string[0] == '<') &&
	  (string[1] == 'c' || string[1] == 'C') &&
	  (string[2] == 't' || string[2] == 'T') &&
	  (string[3] == 'r' || string[3] == 'R') &&
	  (string[4] == 'l' || string[4] == 'L') &&
	  (string[5] == '>'));
}

static inline gboolean
is_shft (const gchar *string)
{
  return ((string[0] == '<') &&
	  (string[1] == 's' || string[1] == 'S') &&
	  (string[2] == 'h' || string[2] == 'H') &&
	  (string[3] == 'f' || string[3] == 'F') &&
	  (string[4] == 't' || string[4] == 'T') &&
	  (string[5] == '>'));
}

static inline gboolean
is_shift (const gchar *string)
{
  return ((string[0] == '<') &&
	  (string[1] == 's' || string[1] == 'S') &&
	  (string[2] == 'h' || string[2] == 'H') &&
	  (string[3] == 'i' || string[3] == 'I') &&
	  (string[4] == 'f' || string[4] == 'F') &&
	  (string[5] == 't' || string[5] == 'T') &&
	  (string[6] == '>'));
}

static inline gboolean
is_control (const gchar *string)
{
  return ((string[0] == '<') &&
	  (string[1] == 'c' || string[1] == 'C') &&
	  (string[2] == 'o' || string[2] == 'O') &&
	  (string[3] == 'n' || string[3] == 'N') &&
	  (string[4] == 't' || string[4] == 'T') &&
	  (string[5] == 'r' || string[5] == 'R') &&
	  (string[6] == 'o' || string[6] == 'O') &&
	  (string[7] == 'l' || string[7] == 'L') &&
	  (string[8] == '>'));
}

static inline gboolean
is_release (const gchar *string)
{
  return ((string[0] == '<') &&
	  (string[1] == 'r' || string[1] == 'R') &&
	  (string[2] == 'e' || string[2] == 'E') &&
	  (string[3] == 'l' || string[3] == 'L') &&
	  (string[4] == 'e' || string[4] == 'E') &&
	  (string[5] == 'a' || string[5] == 'A') &&
	  (string[6] == 's' || string[6] == 'S') &&
	  (string[7] == 'e' || string[7] == 'E') &&
	  (string[8] == '>'));
}

static inline gboolean
is_meta (const gchar *string)
{
  return ((string[0] == '<') &&
	  (string[1] == 'm' || string[1] == 'M') &&
	  (string[2] == 'e' || string[2] == 'E') &&
	  (string[3] == 't' || string[3] == 'T') &&
	  (string[4] == 'a' || string[4] == 'A') &&
	  (string[5] == '>'));
}

static inline gboolean
is_super (const gchar *string)
{
  return ((string[0] == '<') &&
	  (string[1] == 's' || string[1] == 'S') &&
	  (string[2] == 'u' || string[2] == 'U') &&
	  (string[3] == 'p' || string[3] == 'P') &&
	  (string[4] == 'e' || string[4] == 'E') &&
	  (string[5] == 'r' || string[5] == 'R') &&
	  (string[6] == '>'));
}

static inline gboolean
is_hyper (const gchar *string)
{
  return ((string[0] == '<') &&
	  (string[1] == 'h' || string[1] == 'H') &&
	  (string[2] == 'y' || string[2] == 'Y') &&
	  (string[3] == 'p' || string[3] == 'P') &&
	  (string[4] == 'e' || string[4] == 'E') &&
	  (string[5] == 'r' || string[5] == 'R') &&
	  (string[6] == '>'));
}

static inline gboolean
is_keycode (const gchar *string)
{
  return ((string[0] == '0') &&
	  (string[1] == 'x'));
}

/**
 * egg_accelerator_parse_virtual:
 * @accelerator:      string representing an accelerator
 * @accelerator_key:  return location for accelerator keyval
 * @accelerator_mods: return location for accelerator modifier mask
 *
 * Parses a string representing a virtual accelerator. The format
 * looks like "&lt;Control&gt;a" or "&lt;Shift&gt;&lt;Alt&gt;F1" or
 * "&lt;Release&gt;z" (the last one is for key release).  The parser
 * is fairly liberal and allows lower or upper case, and also
 * abbreviations such as "&lt;Ctl&gt;" and "&lt;Ctrl&gt;".
 *
 * If the parse fails, @accelerator_key and @accelerator_mods will
 * be set to 0 (zero) and %FALSE will be returned. If the string contains
 * only modifiers, @accelerator_key will be set to 0 but %TRUE will be
 * returned.
 *
 * The virtual vs. concrete accelerator distinction is a relic of
 * how the X Window System works; there are modifiers Mod2-Mod5 that
 * can represent various keyboard keys (numlock, meta, hyper, etc.),
 * the virtual modifier represents the keyboard key, the concrete
 * modifier the actual Mod2-Mod5 bits in the key press event.
 * 
 * Returns: %TRUE on success.
 */
gboolean
egg_accelerator_parse_virtual (const gchar            *accelerator,
                               guint                  *accelerator_key,
			       guint                  *keycode,
                               EggVirtualModifierType *accelerator_mods)
{
  guint keyval;
  GdkModifierType mods;
  gint len;
  gboolean bad_keyval;
  
  if (accelerator_key)
    *accelerator_key = 0;
  if (accelerator_mods)
    *accelerator_mods = 0;
  if (keycode)
    *keycode = 0;

  g_return_val_if_fail (accelerator != NULL, FALSE);

  bad_keyval = FALSE;
  
  keyval = 0;
  mods = 0;
  len = strlen (accelerator);
  while (len)
    {
      if (*accelerator == '<')
	{
	  if (len >= 9 && is_release (accelerator))
	    {
	      accelerator += 9;
	      len -= 9;
	      mods |= EGG_VIRTUAL_RELEASE_MASK;
	    }
	  else if (len >= 9 && is_control (accelerator))
	    {
	      accelerator += 9;
	      len -= 9;
	      mods |= EGG_VIRTUAL_CONTROL_MASK;
	    }
	  else if (len >= 7 && is_shift (accelerator))
	    {
	      accelerator += 7;
	      len -= 7;
	      mods |= EGG_VIRTUAL_SHIFT_MASK;
	    }
	  else if (len >= 6 && is_shft (accelerator))
	    {
	      accelerator += 6;
	      len -= 6;
	      mods |= EGG_VIRTUAL_SHIFT_MASK;
	    }
	  else if (len >= 6 && is_ctrl (accelerator))
	    {
	      accelerator += 6;
	      len -= 6;
	      mods |= EGG_VIRTUAL_CONTROL_MASK;
	    }
	  else if (len >= 6 && is_modx (accelerator))
	    {
	      static const guint mod_vals[] = {
		EGG_VIRTUAL_ALT_MASK, EGG_VIRTUAL_MOD2_MASK, EGG_VIRTUAL_MOD3_MASK,
		EGG_VIRTUAL_MOD4_MASK, EGG_VIRTUAL_MOD5_MASK
	      };

	      len -= 6;
	      accelerator += 4;
	      mods |= mod_vals[*accelerator - '1'];
	      accelerator += 2;
	    }
	  else if (len >= 5 && is_ctl (accelerator))
	    {
	      accelerator += 5;
	      len -= 5;
	      mods |= EGG_VIRTUAL_CONTROL_MASK;
	    }
	  else if (len >= 5 && is_alt (accelerator))
	    {
	      accelerator += 5;
	      len -= 5;
	      mods |= EGG_VIRTUAL_ALT_MASK;
	    }
          else if (len >= 6 && is_meta (accelerator))
	    {
	      accelerator += 6;
	      len -= 6;
	      mods |= EGG_VIRTUAL_META_MASK;
	    }
          else if (len >= 7 && is_hyper (accelerator))
	    {
	      accelerator += 7;
	      len -= 7;
	      mods |= EGG_VIRTUAL_HYPER_MASK;
	    }
          else if (len >= 7 && is_super (accelerator))
	    {
	      accelerator += 7;
	      len -= 7;
	      mods |= EGG_VIRTUAL_SUPER_MASK;
	    }
	  else
	    {
	      gchar last_ch;
	      
	      last_ch = *accelerator;
	      while (last_ch && last_ch != '>')
		{
		  last_ch = *accelerator;
		  accelerator += 1;
		  len -= 1;
		}
	    }
	}
      else
	{
          keyval = gdk_keyval_from_name (accelerator);

          if (keyval == 0)
	    {
	      /* If keyval is 0, than maybe it's a keycode.  Check for 0x## */
	      if (len >= 4 && is_keycode (accelerator))
		{
		  char keystring[5];
		  gchar *endptr;
		  gint tmp_keycode;

		  memcpy (keystring, accelerator, 4);
		  keystring [4] = '\000';

		  tmp_keycode = strtol (keystring, &endptr, 16);

		  if (endptr == NULL || *endptr != '\000')
		    {
		      bad_keyval = TRUE;
		    }
		  else
		    {
		      *keycode = tmp_keycode;
		      /* 0x00 is an invalid keycode too. */
		      if (*keycode == 0)
			bad_keyval = TRUE;
		    }
		}
	    }

          accelerator += len;
          len -= len;
	}
    }
  
  if (accelerator_key)
    *accelerator_key = gdk_keyval_to_lower (keyval);
  if (accelerator_mods)
    *accelerator_mods = mods;

  return !bad_keyval;
}

/**
 * egg_virtual_accelerator_name:
 * @accelerator_key:  accelerator keyval
 * @accelerator_mods: accelerator modifier mask
 * @returns:          a newly-allocated accelerator name
 * 
 * Converts an accelerator keyval and modifier mask
 * into a string parseable by egg_accelerator_parse_virtual().
 * For example, if you pass in #GDK_q and #EGG_VIRTUAL_CONTROL_MASK,
 * this function returns "&lt;Control&gt;q".
 *
 * The caller of this function must free the returned string.
 */
gchar*
egg_virtual_accelerator_name (guint                  accelerator_key,
			      guint		     keycode,
                              EggVirtualModifierType accelerator_mods)
{
  static const gchar text_release[] = "<Release>";
  static const gchar text_shift[] = "<Shift>";
  static const gchar text_control[] = "<Control>";
  static const gchar text_mod1[] = "<Alt>";
  static const gchar text_mod2[] = "<Mod2>";
  static const gchar text_mod3[] = "<Mod3>";
  static const gchar text_mod4[] = "<Mod4>";
  static const gchar text_mod5[] = "<Mod5>";
  static const gchar text_meta[] = "<Meta>";
  static const gchar text_super[] = "<Super>";
  static const gchar text_hyper[] = "<Hyper>";
  guint l;
  gchar *keyval_name, *str = NULL;
  gchar *accelerator;

  accelerator_mods &= EGG_VIRTUAL_MODIFIER_MASK;

  if (!accelerator_key)
    {
      str = g_strdup_printf ("0x%02x", keycode);
      keyval_name = str;
    }
  else
    {
      keyval_name = gdk_keyval_name (gdk_keyval_to_lower (accelerator_key));
      if (!keyval_name)
        keyval_name = "";
    }

  l = 0;
  if (accelerator_mods & EGG_VIRTUAL_RELEASE_MASK)
    l += sizeof (text_release) - 1;
  if (accelerator_mods & EGG_VIRTUAL_SHIFT_MASK)
    l += sizeof (text_shift) - 1;
  if (accelerator_mods & EGG_VIRTUAL_CONTROL_MASK)
    l += sizeof (text_control) - 1;
  if (accelerator_mods & EGG_VIRTUAL_ALT_MASK)
    l += sizeof (text_mod1) - 1;
  if (accelerator_mods & EGG_VIRTUAL_MOD2_MASK)
    l += sizeof (text_mod2) - 1;
  if (accelerator_mods & EGG_VIRTUAL_MOD3_MASK)
    l += sizeof (text_mod3) - 1;
  if (accelerator_mods & EGG_VIRTUAL_MOD4_MASK)
    l += sizeof (text_mod4) - 1;
  if (accelerator_mods & EGG_VIRTUAL_MOD5_MASK)
    l += sizeof (text_mod5) - 1;
  if (accelerator_mods & EGG_VIRTUAL_META_MASK)
    l += sizeof (text_meta) - 1;
  if (accelerator_mods & EGG_VIRTUAL_HYPER_MASK)
    l += sizeof (text_hyper) - 1;
  if (accelerator_mods & EGG_VIRTUAL_SUPER_MASK)
    l += sizeof (text_super) - 1;
  l += strlen (keyval_name);

  accelerator = g_new (gchar, l + 1);

  l = 0;
  accelerator[l] = 0;
  if (accelerator_mods & EGG_VIRTUAL_RELEASE_MASK)
    {
      strcpy (accelerator + l, text_release);
      l += sizeof (text_release) - 1;
    }
  if (accelerator_mods & EGG_VIRTUAL_SHIFT_MASK)
    {
      strcpy (accelerator + l, text_shift);
      l += sizeof (text_shift) - 1;
    }
  if (accelerator_mods & EGG_VIRTUAL_CONTROL_MASK)
    {
      strcpy (accelerator + l, text_control);
      l += sizeof (text_control) - 1;
    }
  if (accelerator_mods & EGG_VIRTUAL_ALT_MASK)
    {
      strcpy (accelerator + l, text_mod1);
      l += sizeof (text_mod1) - 1;
    }
  if (accelerator_mods & EGG_VIRTUAL_MOD2_MASK)
    {
      strcpy (accelerator + l, text_mod2);
      l += sizeof (text_mod2) - 1;
    }
  if (accelerator_mods & EGG_VIRTUAL_MOD3_MASK)
    {
      strcpy (accelerator + l, text_mod3);
      l += sizeof (text_mod3) - 1;
    }
  if (accelerator_mods & EGG_VIRTUAL_MOD4_MASK)
    {
      strcpy (accelerator + l, text_mod4);
      l += sizeof (text_mod4) - 1;
    }
  if (accelerator_mods & EGG_VIRTUAL_MOD5_MASK)
    {
      strcpy (accelerator + l, text_mod5);
      l += sizeof (text_mod5) - 1;
    }
  if (accelerator_mods & EGG_VIRTUAL_META_MASK)
    {
      strcpy (accelerator + l, text_meta);
      l += sizeof (text_meta) - 1;
    }
  if (accelerator_mods & EGG_VIRTUAL_HYPER_MASK)
    {
      strcpy (accelerator + l, text_hyper);
      l += sizeof (text_hyper) - 1;
    }
  if (accelerator_mods & EGG_VIRTUAL_SUPER_MASK)
    {
      strcpy (accelerator + l, text_super);
      l += sizeof (text_super) - 1;
    }
  
  strcpy (accelerator + l, keyval_name);
  g_free (str);

  return accelerator;
}

/**
 * egg_virtual_accelerator_label:
 * @accelerator_key:  accelerator keyval
 * @accelerator_mods: accelerator modifier mask
 * @returns:          a newly-allocated accelerator label
 * 
 * Converts an accelerator keyval and modifier mask
 * into a (possibly translated) string that can be displayed to
 * a user.
 * For example, if you pass in #GDK_q and #EGG_VIRTUAL_CONTROL_MASK,
 * and you use a German locale, this function returns "Strg+Q".
 *
 * The caller of this function must free the returned string.
 */
gchar*
egg_virtual_accelerator_label (guint                  accelerator_key,
			       guint		      keycode,
			       EggVirtualModifierType accelerator_mods)
{
  gchar *gtk_label;
  GdkModifierType gdkmods;

  egg_keymap_resolve_virtual_modifiers (gdk_keymap_get_default (),
					accelerator_mods, &gdkmods);
  gtk_label = gtk_accelerator_get_label (accelerator_key, gdkmods);

  if (!accelerator_key)
    {
	gchar *label;
	label = g_strdup_printf ("%s0x%02x", gtk_label, keycode);
	g_free (gtk_label);
	return label;
    }

  return gtk_label;
}

void
egg_keymap_resolve_virtual_modifiers (GdkKeymap              *keymap,
                                      EggVirtualModifierType  virtual_mods,
                                      GdkModifierType        *concrete_mods)
{
  GdkModifierType concrete;
  int i;
  const EggModmap *modmap;

  g_return_if_fail (GDK_IS_KEYMAP (keymap));
  g_return_if_fail (concrete_mods != NULL);
  
  modmap = egg_keymap_get_modmap (keymap);
  
  /* Not so sure about this algorithm. */
  
  concrete = 0;
  i = 0;
  while (i < EGG_MODMAP_ENTRY_LAST)
    {
      if (modmap->mapping[i] & virtual_mods)
        concrete |= (1 << i);

      ++i;
    }

  *concrete_mods = concrete;
}

void
egg_keymap_virtualize_modifiers (GdkKeymap              *keymap,
                                 GdkModifierType         concrete_mods,
                                 EggVirtualModifierType *virtual_mods)
{
  GdkModifierType virtual;
  int i;
  const EggModmap *modmap;
  
  g_return_if_fail (GDK_IS_KEYMAP (keymap));
  g_return_if_fail (virtual_mods != NULL);

  modmap = egg_keymap_get_modmap (keymap);
  
  /* Not so sure about this algorithm. */
  
  virtual = 0;
  i = 0;
  while (i < EGG_MODMAP_ENTRY_LAST)
    {
      if ((1 << i) & concrete_mods)
        {
          EggVirtualModifierType cleaned;
          
          cleaned = modmap->mapping[i] & ~(EGG_VIRTUAL_MOD2_MASK |
                                           EGG_VIRTUAL_MOD3_MASK |
                                           EGG_VIRTUAL_MOD4_MASK |
                                           EGG_VIRTUAL_MOD5_MASK);
          
          if (cleaned != 0)
            {
              virtual |= cleaned;
            }
          else
            {
              /* Rather than dropping mod2->mod5 if not bound,
               * go ahead and use the concrete names
               */
              virtual |= modmap->mapping[i];
            }
        }
      
      ++i;
    }
  
  *virtual_mods = virtual;
}

static void
reload_modmap (GdkKeymap *keymap,
               EggModmap *modmap)
{
  XModifierKeymap *xmodmap;
  int map_size;
  int i;

  /* FIXME multihead */
  xmodmap = XGetModifierMapping (gdk_x11_get_default_xdisplay ());

  memset (modmap->mapping, 0, sizeof (modmap->mapping));
  
  /* there are 8 modifiers, and the first 3 are shift, shift lock,
   * and control
   */
  map_size = 8 * xmodmap->max_keypermod;
  i = 3 * xmodmap->max_keypermod;
  while (i < map_size)
    {
      /* get the key code at this point in the map,
       * see if its keysym is one we're interested in
       */
      int keycode = xmodmap->modifiermap[i];
      GdkKeymapKey *keys;
      guint *keyvals;
      int n_entries;
      int j;
      EggVirtualModifierType mask;
      
      keys = NULL;
      keyvals = NULL;
      n_entries = 0;

      gdk_keymap_get_entries_for_keycode (keymap,
                                          keycode,
                                          &keys, &keyvals, &n_entries);
      
      mask = 0;
      j = 0;
      while (j < n_entries)
        {          
          if (keyvals[j] == GDK_Num_Lock)
            mask |= EGG_VIRTUAL_NUM_LOCK_MASK;
          else if (keyvals[j] == GDK_Scroll_Lock)
            mask |= EGG_VIRTUAL_SCROLL_LOCK_MASK;
          else if (keyvals[j] == GDK_Meta_L ||
                   keyvals[j] == GDK_Meta_R)
            mask |= EGG_VIRTUAL_META_MASK;
          else if (keyvals[j] == GDK_Hyper_L ||
                   keyvals[j] == GDK_Hyper_R)
            mask |= EGG_VIRTUAL_HYPER_MASK;
          else if (keyvals[j] == GDK_Super_L ||
                   keyvals[j] == GDK_Super_R)
            mask |= EGG_VIRTUAL_SUPER_MASK;
          else if (keyvals[j] == GDK_Mode_switch)
            mask |= EGG_VIRTUAL_MODE_SWITCH_MASK;
          
          ++j;
        }

      /* Mod1Mask is 1 << 3 for example, i.e. the
       * fourth modifier, i / keyspermod is the modifier
       * index
       */      
      modmap->mapping[i/xmodmap->max_keypermod] |= mask;
      
      g_free (keyvals);
      g_free (keys);      
      
      ++i;
    }

  /* Add in the not-really-virtual fixed entries */
  modmap->mapping[EGG_MODMAP_ENTRY_SHIFT] |= EGG_VIRTUAL_SHIFT_MASK;
  modmap->mapping[EGG_MODMAP_ENTRY_CONTROL] |= EGG_VIRTUAL_CONTROL_MASK;
  modmap->mapping[EGG_MODMAP_ENTRY_LOCK] |= EGG_VIRTUAL_LOCK_MASK;
  modmap->mapping[EGG_MODMAP_ENTRY_MOD1] |= EGG_VIRTUAL_ALT_MASK;
  modmap->mapping[EGG_MODMAP_ENTRY_MOD2] |= EGG_VIRTUAL_MOD2_MASK;
  modmap->mapping[EGG_MODMAP_ENTRY_MOD3] |= EGG_VIRTUAL_MOD3_MASK;
  modmap->mapping[EGG_MODMAP_ENTRY_MOD4] |= EGG_VIRTUAL_MOD4_MASK;
  modmap->mapping[EGG_MODMAP_ENTRY_MOD5] |= EGG_VIRTUAL_MOD5_MASK;
  
  XFreeModifiermap (xmodmap);
}

const EggModmap*
egg_keymap_get_modmap (GdkKeymap *keymap)
{
  EggModmap *modmap;

  /* This is all a hack, much simpler when we can just
   * modify GDK directly.
   */
  
  modmap = g_object_get_data (G_OBJECT (keymap),
                              "egg-modmap");

  if (modmap == NULL)
    {
      modmap = g_new0 (EggModmap, 1);

      /* FIXME modify keymap change events with an event filter
       * and force a reload if we get one
       */
      
      reload_modmap (keymap, modmap);
      
      g_object_set_data_full (G_OBJECT (keymap),
                              "egg-modmap",
                              modmap,
                              g_free);
    }

  g_assert (modmap != NULL);
  
  return modmap;
}

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

#include <Python.h>

#if HAVE_CONFIG_H
#  include <config.h>
#endif /* HAVE_CONFIG_H */

#include <gtk/gtk.h>
#include "keybinder.h"

typedef struct _CallableObject CallableObject;
struct _CallableObject
{
  PyObject *callback;
  PyObject *params;
};

static void
caller (char *key, gpointer userdata)
{
  PyObject *retval;
  CallableObject *obj = (CallableObject *) userdata;
  PyGILState_STATE threadstate;

  threadstate = PyGILState_Ensure ();

#ifdef DEBUG
  printf (" -> global hotkeys called with *%s* key...\n"
      " -> using the following callable:\t", key);
  PyObject_Print (obj->callback, stdout, Py_PRINT_RAW);
  printf ("\n -> with the following params:\t\t");
  PyObject_Print (obj->params, stdout, Py_PRINT_RAW);
  printf ("\n");
#endif

  /* here is the magic place where magical things happens =D
   */
  retval = PyObject_CallObject (obj->callback, obj->params);
  if (!retval)
    PyErr_Print ();

  Py_DECREF (retval);
  PyGILState_Release (threadstate);
}

static PyObject *
_wrapped_keybinder_bind (PyObject *self, PyObject *args)
{
  const char *key;
  PyObject *extra = NULL;
  PyObject *tmp = NULL;
  CallableObject *co = malloc (sizeof (CallableObject));
  co->callback = NULL;
  co->params = NULL;

  if (!PyArg_ParseTuple (args, "sO|O", &key, &tmp, &extra))
    return NULL;

  Py_INCREF (tmp);
  co->callback = tmp;

  co->params = PyTuple_New (extra ? 2 : 1);
  PyTuple_SetItem (co->params, 0, PyString_FromString (key));
  if (extra)
    PyTuple_SetItem (co->params, 1, extra);

  if (PyCallable_Check (co->callback))
    {
      if (keybinder_bind (key, caller, co))
        return Py_BuildValue ("i", TRUE);
      else
        return Py_BuildValue ("i", FALSE);
    }

  PyErr_SetString (PyExc_TypeError, "First param must be callable.");
  Py_DECREF (extra);
  return FALSE;
}

static PyObject *
_wrapped_keybinder_unbind (PyObject *self, PyObject *args)
{
  char *key;

  if (!PyArg_ParseTuple (args, "s", &key))
    return NULL;
  keybinder_unbind (key, caller);
  return Py_BuildValue ("");
}

static PyObject *
_wrapped_keybinder_init (PyObject *self, PyObject *args)
{
  keybinder_init ();
  return Py_BuildValue ("");
}

static PyMethodDef GhMethods[] = {
  {"init", (PyCFunction) _wrapped_keybinder_init, METH_NOARGS, "Initializes global hotkey plugin."},
  {"bind", (PyCFunction) _wrapped_keybinder_bind, METH_VARARGS, "Called when the plugin is disabled."},
  {"unbind", (PyCFunction) _wrapped_keybinder_unbind, METH_VARARGS, "Shows a dialog to configure keyboard hotkeys."},
  {NULL, NULL, 0, NULL}        /* Sentinel */
};


PyMODINIT_FUNC
initglobalhotkeys (void)
{
  PyObject *m;
  m = Py_InitModule ("globalhotkeys", GhMethods);
}

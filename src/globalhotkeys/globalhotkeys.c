/* globalhotkeys.c - A python type to handle global X hotkeys
 *
 * Copyright (C) 2008 Lincoln de Sousa <lincoln@minaslivre.org>
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
#include <structmember.h>
#include <glib.h>

#if HAVE_CONFIG_H
#include <config.h>
#endif

#if PY_MINOR_VERSION < 5
#define Py_ssize_t size_t
#endif

#include "keybinder.h"

typedef struct {
  PyObject *callback;
  PyObject *params;
} CallableObject;

typedef struct {
  PyObject_HEAD;
  PyObject *binded;
} GlobalHotkey;

static void
caller (char *key, gpointer userdata)
{
  PyObject *retval;
  CallableObject *obj = (CallableObject *) userdata;
  PyGILState_STATE threadstate;

  threadstate = PyGILState_Ensure ();
  retval = PyObject_CallObject (obj->callback, obj->params);
  if (!retval)
    PyErr_Print ();
  else
    Py_DECREF (retval);
  PyGILState_Release (threadstate);
}

/* -- GlobalHotkey methods -- */

static void
GlobalHotkey_dealloc (GlobalHotkey *self)
{
  Py_XDECREF (self->binded);
  self->ob_type->tp_free ((PyObject *) self);
}

static PyObject *
GlobalHotkey_new (PyTypeObject *type,
                  PyObject     *args,
                  PyObject     *kwargs)
{
  GlobalHotkey *self;

  self = (GlobalHotkey *) type->tp_alloc (type, 0);
  if (self != NULL)
    {
      self->binded = PyDict_New ();
      if (self->binded == NULL)
        {
          Py_DECREF (self);
          return NULL;
        }
    }
  return (PyObject *) self;
}

static PyObject *
GlobalHotkey_init (GlobalHotkey *self,
                   PyObject     *args,
                   PyObject     *kwargs)
{
  PyObject *binded = NULL;

  binded = PyDict_New ();
  Py_INCREF (binded);
  self->binded = binded;

  return Py_BuildValue ("i", 1);
}

static PyObject *
GlobalHotkey_get_all_binded (GlobalHotkey *self)
{
  if (self->binded == NULL)
    {
      PyErr_SetString (PyExc_AttributeError, "binded");
      return NULL;
    }
  return self->binded;
}

static PyObject *
GlobalHotkey_unbind_all (GlobalHotkey *self)
{
  PyObject *key, *value;
  Py_ssize_t pos = 0;
  char *str_key;

  while (PyDict_Next (self->binded, &pos, &key, &value))
    {
      str_key = PyString_AsString (key);
      keybinder_unbind (str_key, caller);
    }

  PyDict_Clear (self->binded);
  return Py_BuildValue ("i", 1);
}

static PyObject *
GlobalHotkey_unbind (GlobalHotkey *self,
                     PyObject     *args)
{
  char *key;

  if (!PyArg_ParseTuple (args, "s", &key))
    return NULL;

  keybinder_unbind (key, caller);
  PyDict_DelItemString (self->binded, key);
  return Py_BuildValue ("");
}

static PyObject *
GlobalHotkey_bind (GlobalHotkey *self,
                   PyObject     *args)
{
  const char *key;
  PyObject *extra;
  PyObject *tmp;
  CallableObject *co;

  extra = NULL;
  tmp = NULL;
  co = malloc (sizeof (CallableObject));

  co->callback = NULL;
  co->params = PyTuple_New (extra ? 2 : 1);

  if (!PyArg_ParseTuple (args, "sO|O", &key, &tmp, &extra))
    return NULL;

  Py_INCREF (tmp);
  co->callback = tmp;

  /* Already binded keys should be unbinded before binding again */
  if (PyDict_GetItemString (self->binded, key) != NULL)
    PyErr_Format (PyExc_Exception, "Key %s already binded", key);

  PyTuple_SetItem (co->params, 0, PyString_FromString (key));
  if (extra)
    PyTuple_SetItem (co->params, 1, extra);

  /* Is it a valid python callback? */
  if (PyCallable_Check (co->callback))
    {
      /* Let's try to bind the key, if it is not possible, a False
         python value is returned. */
      if (keybinder_bind (key, caller, co))
        {
          /* If it is not possible to add the entry to the binded
             dict, we should not bind the key */
          if (PyDict_SetItemString (self->binded, key, co->callback) != 0)
            {
              keybinder_unbind (key, caller);
              return Py_BuildValue ("i", 0);
            }
          else
            return Py_BuildValue ("i", 1);
        }
      else
        return Py_BuildValue ("i", 0);
    }

  PyErr_SetString (PyExc_TypeError, "First param must be callable.");
  Py_DECREF (extra);

  return NULL;
}

static PyObject *
GlobalHotkey_get_current_event_time (GlobalHotkey *self)
{
  guint32 ret = keybinder_get_current_event_time ();
  return Py_BuildValue ("i", ret);
}

static struct PyMemberDef GlobalHotkey_members[] = {
  {"binded", T_OBJECT_EX, offsetof (GlobalHotkey, binded), 0,
   "Already binded hotkeys"},

  {NULL}                        /* Sentinel */
};

static PyMethodDef GlobalHotkey_methods[] = {
  {"get_all_binded", (PyCFunction) GlobalHotkey_get_all_binded,
   METH_NOARGS, "Returns a dict with all binded hotkeys"},

  {"unbind_all", (PyCFunction) GlobalHotkey_unbind_all,
   METH_NOARGS, "Unbind all binded keys"},

  {"unbind", (PyCFunction) GlobalHotkey_unbind,
   METH_VARARGS, "Unbind a binded key"},

  {"bind", (PyCFunction) GlobalHotkey_bind,
   METH_VARARGS, "Bind a key to a callable object"},

  {"get_current_event_time", (PyCFunction) GlobalHotkey_get_current_event_time,
   METH_NOARGS, "Returns the timestamp of the current event"},

  {NULL}                        /* sentinel */
};

static PyTypeObject GlobalHotkeyType = {
  PyObject_HEAD_INIT(NULL)
  0,                                        /* ob_size */
  "globalhotkeys.GlobalHotkey",              /* tp_name */
  sizeof (GlobalHotkey),                    /* tp_basicsize */
  0,                                        /* tp_itemsize */
  (destructor) GlobalHotkey_dealloc,        /* tp_dealloc */
  0,                                        /* tp_print */
  0,                                        /* tp_getattr */
  0,                                        /* tp_setattr */
  0,                                        /* tp_compare */
  0,                                        /* tp_repr */
  0,                                        /* tp_as_number */
  0,                                        /* tp_as_sequence */
  0,                                        /* tp_as_mapping */
  0,                                        /* tp_hash */
  0,                                        /* tp_call */
  0,                                        /* tp_str */
  0,                                        /* tp_getattro */
  0,                                        /* tp_setattro */
  0,                                        /* tp_as_buffer */
  Py_TPFLAGS_DEFAULT,                       /* tp_flags */
  "GlobalHotkey Objects",                   /* tp_doc */
  0,                                        /* tp_traverse */
  0,                                        /* tp_clear */
  0,                                        /* tp_richcompare */
  0,                                        /* tp_weaklistoffset */
  0,                                        /* tp_iter */
  0,                                        /* tp_iternext */
  GlobalHotkey_methods,                     /* tp_methods */
  GlobalHotkey_members,                     /* tp_members */
  0,                                        /* tp_getset */
  0,                                        /* tp_base */
  0,                                        /* tp_dict */
  0,                                        /* tp_descr_get */
  0,                                        /* tp_descr_set */
  0,                                        /* tp_dictoffset */
  (initproc) GlobalHotkey_init,             /* tp_init */
  0,                                        /* tp_alloc */
  GlobalHotkey_new,                         /* tp_new */
};

static PyObject *
module_init (PyObject *self,
             PyObject *args)
{
  keybinder_init ();
  return Py_BuildValue ("");
}

static PyMethodDef module_methods[] = {
  {"init", (PyCFunction) module_init, METH_NOARGS, ""},
  {NULL},                       /* Sentinel */
};

#ifndef PyMODINIT_FUNC
#define PyMODINIT_FUNC void
#endif

PyMODINIT_FUNC
initglobalhotkeys (void)
{
  PyObject *m;

  GlobalHotkeyType.tp_new = PyType_GenericNew;
  if (PyType_Ready (&GlobalHotkeyType) < 0)
    return;

  m = Py_InitModule3 ("globalhotkeys", module_methods,
                      "Global hotkey manager for X.");

  Py_INCREF (&GlobalHotkeyType);
  PyModule_AddObject (m, "GlobalHotkey", (PyObject *) &GlobalHotkeyType);
}

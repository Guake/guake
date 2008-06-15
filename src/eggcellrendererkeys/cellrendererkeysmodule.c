/* -*- Mode: C; c-basic-offset: 4 -*- */
#ifdef HAVE_CONFIG_H
#  include "config.h"
#endif
#include <Python.h>
#include <pygobject.h>

void pycellrendererkeys_register_classes(PyObject *d);
extern PyMethodDef pycellrendererkeys_functions[];

DL_EXPORT(void)
initcellrendererkeys(void)
{
    PyObject *m, *d;

    /* perform any initialisation required by the library here */

    init_pygobject();

    m = Py_InitModule("cellrendererkeys", pycellrendererkeys_functions);
    d = PyModule_GetDict(m);

    pycellrendererkeys_register_classes(d);
    pycellrendererkeys_add_constants(m, "EGG_");

    /* add anything else to the module dictionary (such as constants) */

    if (PyErr_Occurred())
        Py_FatalError("could not initialise module cellrendererkeys");
}

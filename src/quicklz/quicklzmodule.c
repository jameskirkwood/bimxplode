#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <stdio.h>
#include <stdlib.h>

#include "com.quicklz/quicklz.h"

static PyObject *quicklzmodule_impl_decompress(PyObject *self, PyObject *args) {

    const char *src;
    size_t src_size;
    if (!PyArg_ParseTuple(args, "y#", &src, &src_size)) return 0;
    if (src_size < 3) return PyErr_Format(PyExc_ValueError, "quicklz header missing");

    if (qlz_size_compressed(src) != src_size) {
        return PyErr_Format(PyExc_ValueError, "input size mismatch");
    }

    size_t dst_size = qlz_size_decompressed(src);
    char *dst = malloc(dst_size);
    if (!dst) return PyErr_NoMemory();

    PyObject *result = 0;

    qlz_state_decompress *sd = malloc(sizeof(qlz_state_decompress));
    if (!sd) PyErr_NoMemory();
    else {
        memset(sd, 0, sizeof(qlz_state_decompress));

        if (qlz_decompress(src, dst, sd) == dst_size) {
            result = Py_BuildValue("y#", dst, dst_size);
        }
        free(sd);
    }
    free(dst);
    return result;
}

static PyMethodDef quicklzmodule_methods[] = {
    {"decompress",  quicklzmodule_impl_decompress, METH_VARARGS,
        "Decompress bytes compressed using QuickLZ level 3."},
    {}
};

PyDoc_STRVAR(quicklzmodule_doc,
"Bindings for the QuickLZ compression library version 1.5.0 (http://www.quicklz.com/)\n"
"\n"
"QuickLZ is distributed under the terms of the GNU GPL version 1, 2 or 3.\n"
"\n"
"Only `decompress' is implemented, and level 3 is always used.\n");

static struct PyModuleDef quicklz = {
    PyModuleDef_HEAD_INIT,
    "quicklz",
    quicklzmodule_doc,
    -1,
    quicklzmodule_methods
};

PyMODINIT_FUNC PyInit_quicklz() {
    return PyModule_Create(&quicklz);
}

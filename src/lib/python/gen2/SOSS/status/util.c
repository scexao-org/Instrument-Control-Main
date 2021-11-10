/*
 * util.c
 *
 * Eric Jeschke (eric@naoj.org)  
 * last edit: 2008-04-20
 *
 * SOSS status utility functions for python.
 */

#include "Python.h"

static PyObject *
bigDToLittleD (PyObject *self, PyObject *args)
{
    int         i = 0;
    double      result = 0.0;
    char        byte[8], *s = (char *)NULL;
 
    if (!PyArg_ParseTuple(args, "s", &s))
    {
        return NULL;
    }

    if (NULL == (void *)s)
    {
        return NULL;
    }
  

    /* 8 bytes are input at least check whether the byte */
    for (i = 0; i <= 7; i++) 
    {
        if (*(s+i) == 0x00) 
        {
            /* OSScomn_errOut ( "", 1011, __FILE__, __LINE__, "too few byte size [% d]", i); */
            return Py_BuildValue("d", result);
        }   
    }    

    /* Do big-endian -> little endian conversion. */
    for (i = 7; i >= 0; i--)
    {   /* extract a character type for each byte */
        byte[7 - i] = *(s + i);
    } 

    memcpy(&result, byte, sizeof(result));

    return Py_BuildValue("d", result);
}

static PyMethodDef UtilMethods[] = {
    { "bigDToLittleD",  
       bigDToLittleD,  
       METH_VARARGS,
      "Convert a big-endian C string to a Python double." },

    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
initutil(void)
{
    (void) Py_InitModule("util", UtilMethods);
}

/* end */

/*
 * rtd.c -- Python interface to RTD server.
 *
 * Eric Jeschke (eric@naoj.org)
 * Last edit: Thu Mar 31 15:41:49 HST 2011
 * Subaru Telescope, NAOJ 
 *
 */
#include "Python.h"
#include <numpy/arrayobject.h>
#include <unistd.h>
#include <math.h>
#include <sys/types.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <sys/sem.h>
#include <time.h>

#include "rtd/rtdSem.h" 
#include "rtd/rtdImageEvent.h" 

#define DEBUG 0
/*
 * See http://archive.eso.org/skycat/docs/rtd/rtd.c.html
 *   for information on the RTD interface.
 */

typedef struct {
    PyObject_HEAD
    /* Type-specific fields go here. */
    rtdIMAGE_EVT_HNDL  eventHndl; 
    rtdShm             shmInfo;
    int                shmkey;
    int                semkey;
    rtdIMAGE_INFO      imageInfo; 
    char *             name;
    unsigned int       width; 
    unsigned int       height; 
    unsigned int       datasize; 
    unsigned int       bufsize; 
    unsigned int       num_buf; 
    unsigned int       buf_idx; 
    unsigned int       img_idx;
} rtdObject;

static void
rtd_dealloc(rtdObject* self)
{
    /* Free shared memory segment. */
    rtdShmDelete(&(self->shmInfo)); 

    self->ob_type->tp_free((PyObject*)self);
}

static PyObject *
rtd_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    rtdObject *self;

    self = (rtdObject *)type->tp_alloc(type, 0);
    if (self != NULL) {
        /* default initialization of object */
    }

    return (PyObject *)self;
}

static int
rtd_init(rtdObject *self, PyObject *args, PyObject *kwds)
{
    int i, shmId, semId;
    static char *kwlist[] = {"name", "width", "height", "datasize",
                             "buffers", "shmkey", "semkey", NULL};

    /* set defaults for optional keywords */
    self->num_buf = 1;
    self->shmkey  = -1;
    self->semkey  = -1;
    
    if (! PyArg_ParseTupleAndKeywords(args, kwds, "siii|iii", kwlist,
                                      &self->name, &self->width, &self->height,
                                      &self->datasize, &self->num_buf,
                                      &self->shmkey, &self->semkey)) 
    {
        return -1;
    }

    memset((void *)&self->imageInfo, '\0', sizeof(rtdIMAGE_INFO)); 

    self->buf_idx = 0;
    self->img_idx = 0;
    self->bufsize = self->width * self->height * (abs(self->datasize) / 8);

#if(DEBUG>0)
    fprintf(stderr, "num_buf = %d\n", self->num_buf);
#endif    
    if (self->num_buf < 1) 
    {
        self->num_buf = 1;
    }

    if (rtdInitImageEvt(self->name, &(self->eventHndl), NULL) == RTD_ERROR) { 
        /* ... handle error ... */
        PyErr_SetString(PyExc_ValueError,
                        "rtdInitImageEvt: couldn't connect to RTD server");
        return -1;
    } 

    /* If the user specified a shmkey, then try to use it to look up the shm
       segments and make them if not already created.
     */
#if(DEBUG>0)
    fprintf(stderr, "shmkey = %d\n", self->shmkey);
#endif    
    if (self->shmkey > 0) 
    {
        self->shmInfo.shmWidth = self->width;
        self->shmInfo.shmHeight = self->height;
        self->shmInfo.shmImageType = self->datasize;
        self->shmInfo.num = self->num_buf;

        /*
         * Create new shared memory areas and allocate memory for the IDs.
         */
        if ((self->shmInfo.shmId = (int *)calloc(self->num_buf, sizeof(int))) == NULL) {
            PyErr_SetString(PyExc_ValueError,
                            "Unable to allocate memory for shmId array");
            return -1;
        }

        for (i = 0; i < self->num_buf; i++) {
            shmId = shmget(self->shmkey+i, self->bufsize,  RTD_PERMS | IPC_CREAT);
            if (shmId  == -1) {
                PyErr_SetString(PyExc_ValueError,
                                "(shmget): error in creating shared memory buffers");    
                return -1;
            }
            self->shmInfo.shmId[i] = shmId;
        }
    
#if(DEBUG>0)
        fprintf(stderr, "semkey = %d\n", self->semkey);
#endif    
        if (self->semkey <= 0) 
        {
            self->semkey = IPC_PRIVATE;
        }
        /*
         * Create the set of semaphores (one for each shared memory area)
         */
        semId = semget(self->semkey, self->num_buf, RTD_PERMS | IPC_CREAT);
        if (semId == -1) {
            PyErr_SetString(PyExc_ValueError,
                            "(semget): error in creating semaphore set");    
            return -1;
        }
        self->shmInfo.semId = semId;
    
        /*
         * Allocate an array of timestamps for the semaphores
         */
        if ((self->shmInfo.timestamp = (double *)calloc(self->num_buf, sizeof(double))) == NULL) {
            PyErr_SetString(PyExc_ValueError,
                            "Unable to allocate timestamp data");
            return -1;
        }
    }
    else
    {
        memset((void *)&self->shmInfo, '\0', sizeof(rtdShm)); 
    }
    
    if (rtdShmCreate(self->num_buf, &(self->shmInfo),
                     self->width, self->height, self->datasize) == -1) { 
        /* ... handle error ... */ 
        PyErr_SetString(PyExc_ValueError,
                        "rtdShmCreate: couldn't create shared memory buffers");    
        return -1;
    }

    return 0;
}

static int
_rtd_update(rtdObject *self, void *buf, int buflen, int width, int height,
            int datasize, int bytes_per_pixel, int endian)
{
    int length, shmid;
    int i, filled;
    time_t start_time, elapsed_time, time_limit;
    void *shmaddr;
    char errmsg[512];

    length = width * height * abs(datasize)/8;
    if (length != buflen) 
    {
        //sprintf(errmsg, "buflen=%d calclen=%d", buflen, length);
        //PyErr_SetString(PyExc_ValueError, errmsg);
        //return -1;
    }

    if (buflen > self->bufsize) 
    {
        sprintf(errmsg, "Buffer length (%d) exceeds shared memory size (%d)",
                buflen, self->bufsize); 
        PyErr_SetString(PyExc_ValueError, errmsg);
        return -1;
    }

#if(DEBUG>0)
    fprintf(stderr, "shmfill (%d)...\n", self->buf_idx);
#endif    

    filled = 0;
    elapsed_time = 0.0;
    time_limit = 1.0;
    start_time = time((time_t *)NULL);
    
    while ((filled == 0) && (elapsed_time < time_limit)) 
    {
        for (i = 0; i < self->num_buf; ++i) 
        {
            if (rtdShmFill(self->buf_idx, (void *)NULL, &self->shmInfo, 0) == -1) 
            {
                self->buf_idx = (self->buf_idx + 1) % self->num_buf;
            }
            else
            {
                filled = 1;
#if(DEBUG>0)
                fprintf(stderr, "Filled buffer %d\n", self->buf_idx);
#endif    
            }
        }
        elapsed_time = time((time_t *)NULL) - start_time;
    }
    if (filled == 0)
    {
        PyErr_SetString(PyExc_ValueError,
                        "Couldn't find a free buffer in shared memory");
        return -1;
    }

    /* Get shared memory address. */
    shmid = self->shmInfo.shmId[self->buf_idx];
    shmaddr = shmat(shmid, (void *)NULL, 0);
    if (shmaddr == (void *) -1) {
        PyErr_SetString(PyExc_ValueError,
                        "Error getting shared memory address");
        return -1;
    }

    /* Copy buffer to shared memory area. */
    memcpy(shmaddr, (void *)buf, buflen);

#if(DEBUG>0)
    fprintf(stderr, "set image info...\n");    
#endif    
    self->imageInfo.dataType = datasize; 
    self->imageInfo.bytePerPixel = bytes_per_pixel;
    self->imageInfo.xPixels  = width; 
    self->imageInfo.yPixels  = height; 
    self->imageInfo.frameX   = 0; 
    self->imageInfo.frameY   = 0; 
    self->imageInfo.frameId  = 0;
    //self->imageInfo.frameId  = self->img_idx;
    self->img_idx++;
    //self->imageInfo.shmEndian=-1; /* 0=big 1=little -1=native */
    self->imageInfo.shmEndian = endian;
    //self->imageInfo.lowCut=; 
    //self->imageInfo.highCut=; 
    //self->imageInfo.binningX=; 
    //self->imageInfo.binningY=; 
    //self->imageInfo.timeStamp=; /* struct timeval -- time image was acquired */

    /* WCS parameters */
    //self->imageInfo.ra=; 
    //self->imageInfo.dec=; 
    //self->imageInfo.secpix=; 
    //self->imageInfo.xrefpix=; 
    //self->imageInfo.yrefpix=; 
    //self->imageInfo.rotate=; 
    //self->imageInfo.equinox=; 
    //self->imageInfo.epoch=;
    /* Projection: one of: "-SIN", "-TAN", "-ARC", "-NCP", "-GLS", "-MER",
     *    "-AIT", "-STG", "PLATE", "LINEAR", "PIXEL", ...
     *    (as supported by the wcs library: wcssubs, from Doug Mink)
     */
    //self->imageInfo.proj=; 
    
    /* Copy shm and sem information necessary for RTD server from
       shmInfo -> imageInfo . */
#if(DEBUG>0)
    fprintf(stderr, "shmstruct...\n");    
#endif    
    rtdShmStruct(self->buf_idx, &self->imageInfo, &self->shmInfo); 
 
    /* Send image information to RTD server. */ 
#if(DEBUG>0)
    fprintf(stderr, "sendimageinfo...\n");    
#endif    
    rtdSendImageInfo(&self->eventHndl, &self->imageInfo, NULL);

    return 0;
}


static PyObject *
rtd_update_buffer(rtdObject *self, PyObject *args, PyObject *kwds)
{
    const char * buf;
    int buflen;
    int width, height, datasize, bytes_per_pixel;
    int endian = 0;
    int status;
    PyObject * result;
    static char *kwlist[] = {"buf", "width", "height", "datasize",
                             "bytes_per_pixel", "endian", NULL};

#if(DEBUG>0)
    fprintf(stderr, "argparse\n");
#endif    
    /*
     * datasize: 8, -8, 16, -16, 32, -32, 64, -64  (BITPIX)
     */
    if (! PyArg_ParseTupleAndKeywords(args, kwds, "s#iiii|i", kwlist,
                                      &buf, &buflen, &width, &height,
                                      &datasize, &bytes_per_pixel,
                                      &endian)) 
    {
        return NULL;
    }

    status = _rtd_update(self, (void *)buf, buflen, width, height,
                         datasize, bytes_per_pixel, endian);
    if (status != 0) 
    {
        return NULL;   // exception should have been set
    }
    result = Py_BuildValue("i", status);
    return result;
}

static PyObject *
rtd_update_np(rtdObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *input;
    PyArrayObject *tmparr;
    int buflen, status, arrtype;
    int width, height, datasize, bytes_per_pixel;
    int eltsize, endian = -1;
    char errmsg[512];
    PyObject * result;
    static char *kwlist[] = {"arrin", "datasize", "bytes_per_pixel", NULL};

    /* Parse tuples separately since args will differ between C fcns */
#if(DEBUG>0)
    fprintf(stderr, "argparse\n");
#endif    
    if (! PyArg_ParseTupleAndKeywords(args, kwds, "O!ii", kwlist,
                                      &PyArray_Type, &input,
                                      &datasize, &bytes_per_pixel)) 
    {
        return NULL;
    }

    if (NULL == input) {
        return NULL;
    }
/*
    if (input->descr->type_num == NPY_DOUBLE) 
    {
    } elif 

        buflen = width * height * 
    
*/
    arrtype = PyArray_FLOAT;
    /* Make sure that array is contiguous! */
    tmparr = (PyArrayObject *)PyArray_ContiguousFromObject(input,
                                                           arrtype,
                                                           2, 2);
    if (tmparr == NULL) 
    {
        return NULL;
    }
    if (tmparr->nd != 2) 
    {
        sprintf(errmsg, "Array arity (%d) != 2", tmparr->nd); 
        PyErr_SetString(PyExc_ValueError, errmsg);
        return NULL;
    }

    // numpy stores arrays in column order
    width  = tmparr->dimensions[1];
    height = tmparr->dimensions[0];
    eltsize = tmparr->descr->elsize;
#if(DEBUG>0)
    fprintf(stderr, "Element size is %d\n", eltsize);
#endif    
    buflen = width * height * eltsize;

    /*
     * datasize: 8, -8, 16, -16, 32, -32, 64, -64  (BITPIX)
     */
    status = _rtd_update(self, (void *)tmparr->data, buflen, width, height,
                         datasize, bytes_per_pixel, endian);
    Py_DECREF(tmparr);
        
    if (status != 0) 
    {
        return NULL;   // exception should have been set
    }
    result = Py_BuildValue("i", status);
    return result;
}

static PyObject *
rtd_unlock(rtdObject *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {NULL};
    PyObject * result;

    /* Parse tuples separately since args will differ between C fcns */
    if (! PyArg_ParseTupleAndKeywords(args, kwds, "", kwlist)) 
    {
        return NULL;
    }

    rtdSemReset(self->shmInfo.semId, self->num_buf);

    result = Py_BuildValue("i", 0);
    return result;
}

static PyMethodDef Rtd_methods[] = {
    {"update_np", (PyCFunction)rtd_update_np, METH_VARARGS | METH_KEYWORDS,
     "Update the server with some data from a numpy array"
    },
    {"update_buffer", (PyCFunction)rtd_update_buffer, METH_VARARGS | METH_KEYWORDS,
     "Update the server with some data from a buffer"
    },
    {"unlock", (PyCFunction)rtd_unlock, METH_VARARGS | METH_KEYWORDS,
     "Reset the semaphores to zero"
    },
    {NULL}  /* Sentinel */
};

static PyTypeObject RtdType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "rtd.Rtd",                 /*tp_name*/
    sizeof(rtdObject),         /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor)rtd_dealloc,   /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,        /*tp_flags*/
    "rtd objects",             /* tp_doc */
    0,		               /* tp_traverse */
    0,		               /* tp_clear */
    0,		               /* tp_richcompare */
    0,		               /* tp_weaklistoffset */
    0,		               /* tp_iter */
    0,		               /* tp_iternext */
    Rtd_methods,               /* tp_methods */
    0,                         /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)rtd_init,        /* tp_init */
    0,                         /* tp_alloc */
    rtd_new,                   /* tp_new */
};

static PyMethodDef module_methods[] = {
    {NULL}  /* Sentinel */
};

#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
initrtd(void) 
{
    PyObject* m;

    if (PyType_Ready(&RtdType) < 0)
        return;

    m = Py_InitModule3("rtd", module_methods,
                       "Implements Real Time Display client objects.");

    if (m == NULL)
      return;

    // !! Required for numpy!!
    import_array();

    Py_INCREF(&RtdType);
    PyModule_AddObject(m, "Rtd", (PyObject *)&RtdType);
}


/*END*/

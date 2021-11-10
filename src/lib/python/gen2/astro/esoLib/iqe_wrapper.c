/*
 * iqe_wrapper.c
 *
 * Yasuhiko Sakakibara (yasu@SubaruTelescope.org)  
 * last edit: 2006-06-26
 *
 * The wrapper module to export ESO iqe functions
 * family (part of the Skycat rtdlib library) to
 * python Numarray. Uses high level Numarray C API to
 * access the numarray buffer from C function, 
 * which means that the memory efficiency is not 
 * always great.  However, since the Numarray project
 * may be superceded by NumPy project, it is important
 * to ensure easy migration path. Using high level API 
 * will make it easier to convert the array implementation.
 * Currenly, it is possible to use almost identical code 
 * to compile this wrpper for the Numeric array 
 * implementation. 
 */

#include "Python.h"
/* TODO: update to native numpy! */
#include "numpy/libnumarray.h"

static char *errors[] = {
    "OK",
    "background detection failed",
    "center detection/moment analysis failed",
    "sector analysis(major axis angle) failed",
    "2D gaussian fitting failed.",
};
    
int iqe(float* pfm, 
        float* pwm, 
        int mx, 
        int my, 
        float* parm, 
        float* sdev);

int iqebgv(float      *pfm,
           float      *pwm,
           int        mx,
           int        my,
           float      *bgm,
           float      *bgs,
           int        *nbg);

static char iqe_wrapper_error_message[128];

/**
 * A wrapper function to the ESO iqe() function. 
 * The args tuple needs to have three mandatory 
 * elements, inputArray, mx, my and one optional
 * element weightArray. The inputArray and 
 * weightArray are either  
 * numarray object or python sequence object that
 * has 1-D structure. mx is the number of pixels 
 * along the x axis and my is the number of the 
 * pixels along the y axis. 
 * This function returns seven tuple of two tuples, 
 * first element of each tuple is the value calculated
 * and the second element is the std dev of that value.
 * parm[0] = mean X position within array, first pixel = 0
 * parm[1] = FWHM in X
 * parm[2] = mean Y position within array, first pixel = 0
 * parm[3] = FWHM in Y
 * parm[4] = angle of major axis, degrees, along X = 0
 * parm[5] = peak value of object above background
 * parm[6] = mean background level
 */
static PyObject *
iqe_wrapper(PyObject *self, PyObject *args)
{
  PyArrayObject *oinputArray = NULL, 
                *oweightArray = NULL;
  int           mx, my;
  PyArrayObject *inputArray = NULL,  
                *weightArray = NULL;
  int           result;
  float         parm[7], sdev[7];
  float         *input  = NULL, 
                *weight = NULL;
  int           i, code;
  int           err = 0;
 
  if(!PyArg_ParseTuple(args, "Oii|O", &oinputArray,
                                      &mx,
                                      &my,
                                      &oweightArray)){
      /* When the PyArg_ParseTuple function fails, it sets 
       * an appropreate exception. Therefore, we do not 
       * need explicit PyErr_SetString call here.
        */
     return NULL;
  }

  if(!oinputArray || Py_None == (PyObject*)oinputArray){
     PyErr_SetString(PyExc_ValueError,
                     "Can not proceed with empty input array.");
     return NULL;
  }
  
  inputArray  = (float *)(NA_InputArray(oinputArray, tFloat32, NUM_C_ARRAY));
  if(inputArray->nd != 1){
     Py_XDECREF(inputArray);
     PyErr_SetString(PyExc_ValueError,
                     "The input must be 1-d array-like object");
     return NULL;
  }
  input = NA_OFFSETDATA(inputArray);

  if(oweightArray && Py_None != (PyObject*)oweightArray){
     weightArray = (float *)NA_InputArray(oweightArray, tFloat32, NUM_C_ARRAY); 
     if(weightArray->nd != 1){
        Py_XDECREF(weightArray);
        PyErr_SetString(PyExc_ValueError,
                        "The weight must be 1-d array-like object");
        return NULL;
     }
     weight = NA_OFFSETDATA(weightArray);
  }else{
     weight = (float*)NULL;
  }

  result = iqe(input,
               weight,
               mx,
               my,
               parm,
               sdev);
  /* de-reference the temporary objects to be garbage-collected */
  Py_XDECREF(inputArray);
  Py_XDECREF(weightArray);

  /*
   * if the result was
   * -1: background detection failed
   * -2: center detection/moment analysis failed
   * -3: sector analysis(major axis angle) failed
   * -4: 2D gaussian fitting failed.
   */
  if (result != 0) {
      code = -result;
      if ((code > 0) && (code < 5)) 
      {
          sprintf(iqe_wrapper_error_message, 
                  errors[code]);
      } else 
      {
          sprintf(iqe_wrapper_error_message, 
              "iqe() function returned error code %d.",
                  result);
      }
      /* Ok, this is thread UNSAFE. but how can I avoid? */
      PyErr_SetString(PyExc_ArithmeticError,
                      iqe_wrapper_error_message);
      return NULL;        
  }

/* 
  for(i =0 ; i<7; i++){
      printf("parm[%d]=%15.10f sdev[%d]=%15.10f\n", i, parm[i], i, sdev[i]);
  }
*/  
  return Py_BuildValue("((ff)(ff)(ff)(ff)(ff)(ff)(ff))", parm[0], sdev[0],
                                                          parm[1], sdev[1],
                                                          parm[2], sdev[2],
                                                          parm[3], sdev[3],
                                                          parm[4], sdev[4],
                                                          parm[5], sdev[5],
                                                          parm[6], sdev[6]);
}

static PyObject *
iqebgv_wrapper(PyObject *self, PyObject *args)
{
  PyArrayObject *oinputArray = NULL, 
                *oweightArray = NULL;
  int           mx, my;
  PyArrayObject *inputArray = NULL,  
                *weightArray = NULL;
  int           result;
  float         *input  = NULL, 
                *weight = NULL;
  float         bgv=0.0, bgs=0.0;
  int           nbg=0;
 
  if(!PyArg_ParseTuple(args, "Oii|O", &oinputArray,
                                      &mx,
                                      &my,
                                      &oweightArray))
     return NULL;

  if(Py_None == (PyObject*)oinputArray){
     return NULL;
  }
  
  inputArray  = (float *)NA_InputArray(oinputArray, tFloat32, NUM_C_ARRAY);
  if(inputArray->nd != 1){
     Py_XDECREF(inputArray);
     return NULL;
  }
  input = NA_OFFSETDATA(inputArray);

  if(oweightArray && Py_None != (PyObject*)oweightArray){
     weightArray = (float *)NA_InputArray(oweightArray, tFloat32, NUM_C_ARRAY);
     if(weightArray->nd != 1){
        Py_XDECREF(weightArray);
        return NULL;
     }
     weight = NA_OFFSETDATA(weightArray);
  }else{
     weight = (float*)0;
  }

  result = iqebgv(input,
                  weight,
                  mx,
                  my,
                  &bgv,
                  &bgs,
                  &nbg);

  Py_XDECREF(inputArray);
  Py_XDECREF(weightArray);

  if(result){
    return NULL;
  }
  return Py_BuildValue("(ddi)", bgv, bgs, nbg);
}

static PyMethodDef IqeMethods[] = {
    {"iqe",  
      iqe_wrapper,  
      METH_VARARGS,
     "Image quality estimate."},
    {"iqebgv",  
      iqebgv_wrapper,  
      METH_VARARGS,
     "Image background calculation"},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
initiqe(void)
{
    (void) Py_InitModule("iqe", IqeMethods);
    /* This call is VERY important. 
     * See numarray c-interface documentation
      */
    import_libnumarray();
}

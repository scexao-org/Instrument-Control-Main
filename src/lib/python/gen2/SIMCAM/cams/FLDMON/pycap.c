/*
 *
 * Capture Sample
 * 
 * original source by K.Motohara
 * 
 * modified 1/26/2005  .URAGUCHI
 * modified 2/11/2005  T.OZAWA
 * modified 9/27/2005  E. JESCHKE (eric@naoj.org)
 */

#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>

#include <linux/types.h>
#include <linux/videodev.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include <sys/time.h>
#include <time.h>

#include "Python.h"
#include "numpy/libnumarray.h"

// Define constant
#define COMPOSITE  1
#define SEPARATE   2
#define PAL        0
#define NTSC       1
#define SECAM      2
#define WAITTIME   10000


// Define parameter of capture device
#define WIDTH      320   // 480
#define HEIGHT     240   // 360
#define NPIX       WIDTH*HEIGHT

#define DEV        "/dev/video0"
#define FRAMEBUF   3
#define INTEGFRM   FRAMEBUF*10
#define CHANNEL    COMPOSITE
#define PROTCOL    NTSC

#define BRIGHTNESS 60000        // default = 32767, float=>60000, uint=> 40000
#define HUE        32767
#define COLOUR     32767
#define CONTRAST   64000        // default = 33000, float=>60000, uint=> 60000
#define WHITENESS  32767


// Define type of frame buffer
#define BUFTYP     u_int        // u_int, float
#define FITSIMGTYP TUINT       // TUINT,TFLOAT
#define BITPIX     16          // 8, -32
// Number of frames per FITS file generated
#define IMGSTACK   60


// TODO: move these into our own object as a struct
static int fd;
static struct video_capability vd;
static struct video_channel vc[10];
static struct video_picture vp;
static struct video_mmap vmm;
static struct video_mbuf vm;
static char *map;
static BUFTYP *imgbuf;
static int imgbuf_len;


void start_capture(int fd, struct video_mmap *vmm, int waittime)
{
    if(ioctl(fd, VIDIOCMCAPTURE, vmm)<0) {
        perror("ioctl(VIDIOCMCAPTURE)");
        exit(1);
    }

    usleep(waittime);
}

void end_capture(int fd, struct video_mbuf vm, int field, char *map,
                 BUFTYP *imgbuf)
{
    unsigned char *p;
    long i;
    BUFTYP *q;
  
    if(ioctl(fd, VIDIOCSYNC, &field)<0) {
        perror("ioctl(VIDIOCSYNC)");
        exit(1);
    }
    for (i=0, p=map+vm.offsets[field], q=imgbuf; i<NPIX; i++, q++, p++)
        *q += (BUFTYP)*p;
}

void do_capture(int fd, struct video_mbuf vm, struct video_mmap vmm,
                char *map, BUFTYP *imgbuf, int waittime)
{
    int i;

    for (i = 1; i < FRAMEBUF; i++)
    {
        vmm.frame = i;
        end_capture(fd, vm, vmm.frame, map, imgbuf);

        start_capture(fd, &vmm, waittime);
    }
}

PyObject *capture(PyObject *self, PyObject *args)
{
    int waittime, integ;
    PyObject *ret;
    PyArrayObject *ooutputArray = NULL;
    PyArrayObject *outputArray = NULL;
    BUFTYP  *output;
    register i;
    register BUFTYP *p, *q, divisor;


    if (!PyArg_ParseTuple(args, "Oii", &ooutputArray, &waittime, &integ)) 
    {
        return NULL;
    }

    if (!ooutputArray || Py_None == (PyObject*)ooutputArray){
        PyErr_SetString(PyExc_ValueError,
                        "Can not proceed with no array.");
        return NULL;
    }

    outputArray = NA_IoArray(ooutputArray, tInt32, NUM_C_ARRAY);
    if (!outputArray)
    {
        PyErr_SetString(PyExc_ValueError,
                        "Error in array well-behavedness.");
        return NULL;
    }

    if (outputArray->nd != 2)
    {
        Py_XDECREF(outputArray);
        PyErr_SetString(PyExc_ValueError,
                        "The array must be 2-D numarray");
        /* TODO: check width==WIDTH && height==HEIGHT
           inputArray->dimensions[0]
         */
        return NULL;
    }
    output = NA_OFFSETDATA(outputArray);

    /* Clear the image buffer.  TODO: use numarray function. */
    (void) memset((void *)imgbuf, 0, NPIX * sizeof(BUFTYP));
      
    /* Single frame image capture and integration */
    for(i = 0; i < integ; i++)
    {
        do_capture(fd, vm, vmm, map, imgbuf, waittime);
    }

    /* Integrate the individual frames */
    divisor = integ * FRAMEBUF;
    for(i = 0, p = imgbuf, q = output; i < NPIX; i++, p++, q++)
    {
        *p /= divisor;
        *q += *p;
    }

    /* Build the python version of this buffer (a string) */
    ret = Py_BuildValue("i", 0);

    Py_XDECREF(outputArray);
    return ret;
}


PyObject *setup(PyObject *self, PyObject *args)
{
    int brightness, hue, color, contrast, whiteness;
    int i;
    PyObject *ret;

    if (!PyArg_ParseTuple(args, "iiiii", &brightness, &hue, &color,
                          &contrast, &whiteness)) 
    {
        return NULL;
    }

    /* Device Open */
    if((fd=open(DEV, O_RDWR))<0) {
        perror("open");
        return NULL;
    }
  
    /* Get Specification from Device */
    if(ioctl(fd, VIDIOCGCAP, &vd)<0) {
        perror("ioctl(VIDIOCGCAP)");
        return NULL;
    }

    /* Get Specification of each Channels */
    for(i=0; i<vd.channels; i++) {
        vc[i].channel=i;
        if(ioctl(fd, VIDIOCGCHAN, &vc[i])<0) {
            perror("ioctl(VIDIOCGCHAN)");
            return NULL;
        }
    }
  
    /* Video Protcol Selection */
    vc[CHANNEL].norm=PROTCOL;
    if(ioctl(fd, VIDIOCSCHAN, &vc[CHANNEL])<0) {
        perror("ioctl(VIDIOCSCHAN)");
        return NULL;
    }
  
    /* Set Color Tone */
    vp.brightness  = brightness;
    vp.hue         = hue;
    vp.colour      = color;
    vp.contrast    = contrast;
    vp.whiteness   = whiteness;
  
    /* Color Pallete Define */
    /* Color Depth */
    vp.depth=8;
    /* Set Video Pallete */
    vp.palette=VIDEO_PALETTE_GREY;
    if(ioctl(fd, VIDIOCSPICT, &vp)) {
        perror("ioctl(VIDIOCSPICT)");
        return NULL;
    }
  
    /* Get mmap information */
    if(ioctl(fd, VIDIOCGMBUF, &vm)<0) {
        perror("ioctl(VIDIOCGMBUF)");
        return NULL;
    }
  
    /* Set up memory-mapped area */
    if((map = mmap(0, vm.size, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0))
       == (char *)-1) {
        perror("mmap");
        return NULL;
    }
  
    /* specify format for vmm */
    vmm.width=WIDTH;
    vmm.height=HEIGHT;
    vmm.format=VIDEO_PALETTE_GREY;

    // Allocate image buffer.
    imgbuf_len = NPIX * sizeof(BUFTYP);
    imgbuf = (BUFTYP *)malloc(imgbuf_len);

    /* Start Capture Video Image at frame # */
    /* frame capture(start) */
    for(i=0; i<FRAMEBUF; i++){
        vmm.frame=i;
        start_capture(fd, &vmm, WAITTIME);
    }

    /* Build the python return value. */
    ret = Py_BuildValue("i", 0);
    return ret;
}




/* Method table mapping names to wrappers */
static PyMethodDef pycap_methods[] = {
	{"setup", setup, METH_VARARGS},
	{"capture", capture, METH_VARARGS},
	{NULL, NULL, 0}
};

/* Module initialization function */
void initpycap(void)
{
    (void) Py_InitModule("pycap", pycap_methods);
    /* This call is VERY important.
     * See numarray c-interface documentation
     */
    import_libnumarray();
}

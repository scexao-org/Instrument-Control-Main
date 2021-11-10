import rtd
import time
import pyfits

datafile = '/gen2/data/agsim/AG512.fits'
camname  = "FOO"

rtd_server = rtd.Rtd(camname, 512, 512, -32, buffers=5)
fits_f = pyfits.open(datafile, 'readonly')
data = fits_f[0].data
buf = data.tostring()
fits_f.close()
print "Buffer is %d bytes" % len(buf)

for i in xrange(100):
    print "Buffer is %d bytes" % len(buf)
    #res = rtd_server.update_buffer(buf, 512, 512, -32, 2)
    res = rtd_server.update_np(data, -32, 2)
    print "result was %d" % res

    time.sleep(1.0)

#END



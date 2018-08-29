#!/usr/bin/env python

from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import pyqtgraph as pg
import pyqtgraph.ptime as ptime
import time
import os,sys

home = os.getenv('HOME')
sys.path.append(home+'/src/lib/python/')
from   scexao_shm   import shm

args = sys.argv[1:]
if args == []: 
    print "no shared memory provided"
else:
    imshm = shm("/tmp/"+args[0]+".im.shm")


# ------------------------------------------------------------------
#  another short hand to convert numpy array into image for display
# ------------------------------------------------------------------
def arr2im(arr, vmin=0., vmax=10000.0, pwr=1.0):
    
    arr2 = arr.astype('float')**pwr
    #mmin,mmax = arr2.min(), arr2.max()
    #mmax = np.percentile(arr2, 99)
    #arr2 -= mmin
    #arr2 /= (mmax-mmin)

    #test = mycmap(arr2)
    return(arr2)


## Create random image
#data = np.random.normal(size=(15, 50, 50), loc=128, scale=32).astype(np.uint8)
#i = 0

#updateTime = ptime.time()
#fps = 0

def updateData():
    global img, data, i, updateTime, fps

    ## Display the data
    temp = imshm.get_data()
    myim = arr2im(temp.transpose())
    img.setImage(myim)
    #i = (i+1) % data.shape[0]

    QtCore.QTimer.singleShot(50, updateData)
    #now = ptime.time()
    #fps2 = 1.0 / (now-updateTime)
    #time.sleep(0.04)
    #updateTime = now
    #fps = fps * 0.9 + fps2 * 0.1
    #print "%0.1f fps" % fps
    

temp = imshm.get_data(check=True)
myim = arr2im(temp.transpose())

app = QtGui.QApplication([])

## Create window with GraphicsView widget
win = pg.GraphicsLayoutWidget()
win.show()  ## show widget alone in its own window
win.setWindowTitle('pyqtgraph example: ImageItem')
view = win.addViewBox()

## lock the aspect ratio so pixels are always square
view.setAspectLocked(True)

## Create image item
img = pg.ImageItem()#border='r')
view.addItem(img)

## Set initial view bounds
view.setRange(QtCore.QRectF(0, 0, myim.shape[0], myim.shape[1]))

updateData()

## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

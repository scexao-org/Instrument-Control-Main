from astropy.io import fits
import numpy as np
import warnings

def load_header(header, extnum=0):
    """
    Attempt to load a header specified as a header, a string pointing to a FITS
    file, or a string pointing to a Header text file, or a string that contains
    the actual header
    """
    if hasattr(header,'get'):
        # dict or Header
        return fits.Header(header)
    try:
        # assume fits file first
        return fits.getheader(header, extnum=extnum)
    except IOError:
        # assume header textfile
        try:
            return fits.Header().fromtextfile(header)
        except IOError:
            return fits.Header().fromstring(header,'\n')

def load_data(data, extnum=0):
    """
    Attempt to load a header specified as a header, a string pointing to a FITS
    file, or a string pointing to a Header text file, or a string that contains
    the actual header
    """
    if isinstance(data,np.ndarray):
        return data
    try:
        # assume fits file first
        return fits.getdata(data, extnum=extnum)
    except IOError:
        # assume an HDU
        if hasattr(data,'data') and isinstance(data.data,np.ndarray):
            return data.data
        elif isinstance(data, fits.HDUList):
            warnings.warn("Using 0'th extension of HDUlist to extract data")
            return data[0].data


def get_cd(wcs, n=1):
    """
    Get the value of the change in world coordinate per pixel across a linear axis.
    Defaults to wcs.wcs.cd if present.  Does not support rotated headers (e.g., 
    with nonzero CDm_n where m!=n)
    """

    if hasattr(wcs.wcs,'cd'):
        if wcs.wcs.cd[n-1,n-1] != 0:
            return wcs.wcs.cd[n-1,n-1]
    else:
        return wcs.wcs.get_cdelt()[n-1]

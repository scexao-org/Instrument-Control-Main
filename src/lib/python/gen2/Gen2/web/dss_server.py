#!/usr/bin/env python
#
# Takeshi Inagaki
#
"""
Implementation of a Digital Sky Survey web server.
"""
import os
import sys
import pexpect
import subprocess 
import random
import re
import pyfits
import time
import ssdlog  
import astro.fitsutils as fits

#from BaseHTTPServer import HTTPServer
#from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn

# validate size. should be less than 100
#SIZE=re.compile(r"^[0-9][0-9]?(\.\d+)?$")
SIZE=re.compile(r"^[0-9]+(\.\d+)?$")

# validate RA/DEC
RA=re.compile(r"^([01][0-9]|2[0-4]):[0-5][0-9]:[0-5][0-9](\.\d{1,3})?$")
DEC=re.compile(r"^[+-]?[0-8][0-9]:[0-5][0-9]:[0-5][0-9](\.\d{1,2})?$")

logger=None

class ThreadingServer(ThreadingMixIn, HTTPServer):
    pass

class DssHandler(BaseHTTPRequestHandler):
  
    global logger
     
    def _create_dict(self, query_list):
        logger.debug("query_list<%s>" %(query_list))
        key=[]; val=[];
        for i in query_list:
            k,v=i.split('=')
            key.append(k);val.append(v);
        return dict(zip(key,val))     

    def _set_dss1_env(self):
        ''' set up dss1 environment values ''' 
        try:
            os.environ['DSS_MTPT']= os.environ['GEN2COMMON'] + '/dss/dss1'
            os.environ['DSS_JUKEBOX_SLOT_PREFIX']='dss1_'
            os.environ['DSS_JUKEBOX_SLOT_WIDTH']='4'
            os.environ['DSS_JUKEBOX_SLOT_OFFSET']='0'
            os.environ['DSS_HDRS']= os.environ['GEN2COMMON'] + '/dss/code/getimage/headers'   
            os.environ['DSS_EXTN']='hhh'                
            os.environ['DSS_PLTL']='lo_comp.lis'        
            os.environ['DSS_PLTL2']='hi_comp.lis'       
            os.environ['DSS_LBPF']='USA_AURA_STSI_DSS1' 
        except Exception as e:
            logger.error('error: fail to set up dss1 env. %s' %str(e)) 
            
    def _set_dss2b_env(self):
        ''' set up dss2 blue environment values '''
        try:
            #os.environ['DSS_MTPT']= os.environ['DATAHOME'] + '/dss/dss2B'
            os.environ['DSS_MTPT']= os.environ['GEN2COMMON'] + '/dss/dss2'
            os.environ['DSS_JUKEBOX_SLOT_PREFIX']='xdss_'
            os.environ['DSS_JUKEBOX_SLOT_WIDTH']='4'
            os.environ['DSS_JUKEBOX_SLOT_OFFSET']='0'
            os.environ['DSS_HDRS']= os.environ['GEN2COMMON'] + '/dss/code/getimage2_B/bheaders'   
            os.environ['DSS_EXTN']='hhh'                
            os.environ['DSS_PLTL']='xdssj.lis'       
            os.environ['DSS_PLTL2']='hi_comp.lis'        
            os.environ['DSS_LBPF']='USA_AURA_STSI_XDSS'
        except Exception as e:
            logger.error('fail to set up dss2_b env. %s' %str(e))      
       
    def _set_dss2i_env(self):
        ''' set up dss2 i environment values '''
        try:
            #os.environ['DSS_MTPT']= os.environ['DATAHOME'] + '/dss/dss2I'
            os.environ['DSS_MTPT']= os.environ['GEN2COMMON'] + '/dss/dss2'
            os.environ['DSS_JUKEBOX_SLOT_PREFIX']='xdss_'
            os.environ['DSS_JUKEBOX_SLOT_WIDTH']='4'
            os.environ['DSS_JUKEBOX_SLOT_OFFSET']='0'
            os.environ['DSS_HDRS']= os.environ['GEN2COMMON'] + '/dss/code/getimage2_I/iheaders'   
            os.environ['DSS_EXTN']='hhh'                
            os.environ['DSS_PLTL']='xdssiis.lis'      
            os.environ['DSS_PLTL2']='hi_comp.lis'        
            os.environ['DSS_LBPF']='USA_AURA_STSI_XDSS' 
        except Exception as e:
            logger.error('fail to set up dss2_i env. %s' %str(e))       
       
    def _set_dss2r_env(self):
        ''' set up dss2 red environment values '''
        try:
            #os.environ['DSS_MTPT']= os.environ['DATAHOME'] + '/dss/dss2R'
            os.environ['DSS_MTPT']= os.environ['GEN2COMMON'] + '/dss/dss2'
            os.environ['DSS_JUKEBOX_SLOT_PREFIX']='xdss_'
            os.environ['DSS_JUKEBOX_SLOT_WIDTH']='4'
            os.environ['DSS_JUKEBOX_SLOT_OFFSET']='0'
            os.environ['DSS_HDRS']= os.environ['GEN2COMMON'] + '/dss/code/getimage2_R/rheaders'   
            os.environ['DSS_EXTN']='hhh'                
            os.environ['DSS_PLTL']='xdss.lis'       
            os.environ['DSS_PLTL2']='hi_comp.lis'         
            os.environ['DSS_LBPF']='USA_AURA_STSI_XDSS'
        except Exception as e:
            logger.error('fail to set up dss2_r env. %s' %str(e))               
 
    def _set_dssenv(self, dss_type):
        ''' set env for ecah dss '''
        
        errmsg=[]
        
        dss_env_dict={'/dss1_subaru': self._set_dss1_env,
                       '/dss2b_subaru': self._set_dss2b_env,
                       '/dss2r_subaru': self._set_dss2r_env,
                       '/dss2i_subaru': self._set_dss2i_env}
        
        try:
            logger.debug('setting up dss env<%s>' %(dss_type))
            dss_env_dict[dss_type]()
        except Exception as e:
            errmsg.append("<P><B>ERROR:</B> Problem setting up dss env values [%s]\n" %(dss_type))
            logger.error('error: %s. %s' %(errmsg, str(e))) 
        
        return errmsg
    
    def _parse_string(self):
        try:
            dss_type, query_string = self.path.split('?', 1)
            #query_list=query_string.split('&')
            return (dss_type, self._create_dict(query_string.split('&')))
            #return (dss_type, args_dict)
        except Exception,e:
            logger.error('error: check parameters: <%s>.  %s' %(self.path, e))
            errmsg="<P><B>ERROR:</B> Problem with parameters [%s]\n" %(self.path)
            self._print_error_msg(errmsg)     

    def _format_ra_dec(self,ra, dec):
        ''' format R.A and Dec. '''
        
        h,m,s=ra.split(':')    # RA
        d,mm,ss=dec.split(':') # DEC
  
        if not int(h)%24:
            h='00'   
                        
        ra= '%s %s %06.3f' %(h,m,float(s))
        dec= '%s %s %05.2f' %(d,mm,float(ss))
         
        logger.debug('ra<%s> dec<%s>' %(ra, dec)) 
         
        return (ra,dec)
    
    def _validate_keys(self,params):
        ''' validate keys for values'''
        errmsg=[]
        keys=['ra', 'dec', 'mime-type', 'x', 'y']
 
        for k in params.keys():
            if not k in keys:
                errmsg.append("<P><B>ERROR:</B> Invalid key [%s].  Valid keys=%s\n" %(k, keys))
      
        #for k in keys:
        #    try:
        #        params[k]
        #    except KeyError,e:
        #        errmsg.append("<P><B>ERROR:</B> Invalid key. %s\n" %(k))
        return errmsg       
        
    def _validate_values(self,params):
        ''' validate the values of  Ra, Dec, and an image size X and Y'''
        
        errmsg=[]
        try:
            logger.debug("x<%s> y<%s>"  %( params['x'], params['y']))
            if not (SIZE.match(params['x']) and SIZE.match(params['y'])):
                errmsg.append("<P><B>ERROR:</B> invalid image size X or Y. X[%s]*Y[%s] < 1000 \n" %(params['x'], params['y'])) 
            elif float(params['x']) == 0 or float(params['y']) == 0:
                errmsg.append("<P><B>ERROR:</B> image size X or Y shouldn't be 0  [X:%s Y:%s]\n" %(params['x'], params['y']))
        except Exception as e:
            logger.error('error: %s. %s' %(errmsg, e))
            errmsg.append("<P><B>ERROR:</B> Problem retreiving the image size X and Y.\n")  
        try:
            logger.debug("RA<%s> DEC<%s>"  %( params['ra'], params['dec']))
            #print 'RA<%s> DEC<%s>' %(params['ra'], params['dec'])
            if not ( RA.match(params['ra'].strip()) and  DEC.match(params['dec'].strip()) ):
                errmsg.append("<P><B>ERROR:</B> check either R.A. or Dec. [%s %s] \n" %(params['ra'], params['dec']))
            else:
                params['ra'],params['dec']=self._format_ra_dec(params['ra'], params['dec'])
        except Exception as e:
            errmsg.append("<P><B>ERROR:</B> Problem retreiving R.A and Dec. \n")
            logger.error('error: %s  %s' %(errmsg, e))
        logger.debug('errmsg<%s>' %(errmsg))
         
        return errmsg
    
    def _print_error_msg(self,errmsg):
        ''' print an error msg '''
        logger.debug('printing an error msg...')       
        self.send_response(404)
        self.send_header('Content-type','text/html')
        self.end_headers()
       
        
        error_html="""<HTML><HEAD><TITLE>Digitized Sky Survey</TITLE></HEAD>
                      <BODY><H1>Digitized Sky Survey at Subaru(Summit)</H1>
                      <HR> %s <P><HR>
                      </BODY></HTML> """ %(errmsg)
        #self.send_error(404, error_html)
       
        logger.debug('error_mgs<%s>' %(error_html))  
        self.wfile.write(error_html)
        logger.debug('printing done.')
        return 
    
    def _set_getimage_args(self, args, gi_args_file):
               
        self._remove_file(gi_args_file)
        try:
            os.system("echo %s > %s" %(args, gi_args_file))
        except OSError as e:
            logger.error('error: fail to create /gen2/tmp/dss.txt for getimage.exe args. %s' %e)

    def _exec_getimage(self, params, fileid, gen2_tmp):
        ''' search and get a dss image '''      
        errmsg=[]
        
        gi_args_file=os.path.join(gen2_tmp, 'dss.txt')
        dssfits=os.path.join(gen2_tmp, fileid)
       
        # getimage -k +imagename /ge2/tmp/Xxxx.fits -i /gen2/tmp/xx.txt  
        getimage=os.path.join(os.environ['ARCHHOME'], 'bin', 'getimage.exe')
        args='%s %s %s  %s %s' %(fileid,params['ra'],params['dec'],params['x'],params['y'])
   
        try:
            logger.debug('writting args file <%s : %s>' %(gi_args_file, args))
            self._set_getimage_args(args, gi_args_file)
            cmd="%s -k +imagename %s -i %s -z" %(getimage, dssfits, gi_args_file)
            logger.debug('cmd:<%s>' %(cmd))
            #os.system(cmd)
            subprocess.call([getimage, '-k', '+imagename', dssfits, '-i', gi_args_file, '-z'])
            # using subprocess can't execute getimage.exe ?????
            #subprocess.call(['%s', '-k', '+imagename', '%s', '-i', '%s', '-z'] %(cmd, dssfits, gi_args_file))

        except OSError as e:
            logger.error('error: executing get-image error <%s>' %(e))
            errmsg.append("<P><B>ERROR:</B> Problem retreiving the image - Please go back and check your input.\n [ID:%s RA:%s DEC:%s X:%s  Y:%s]" %(fileid,params['ra'],params['dec'],params['x'],params['y']))
            logger.error('error: exeuting getimage.exe error msg<%s>' %(errmsg))   
        return  errmsg
 

    def _remove_file(self, filename):
        try:
            os.remove(filename)
            logger.debug('removed file<%s>' %(filename))
        except OSError as e:
            logger.warn("can't remove a file<%s>" %(filename))
            pass   

    def _send_image(self, size, dss_img):
         
        errmsg=[]    
        try:
            logger.debug('opening a dss img<%s>' %(dss_img))
            f=open(dss_img)
            try:
                self.send_response(200)
                self.send_header('Content-type','application/x-fits')
                self.send_header('Content-length','%s' %(str(size)))
                self.end_headers()
                self.wfile.write(f.read())
                logger.debug('sending a dss img<%s>' %(dss_img))
            except Exception as e:
                errmsg.append("<P><B>ERROR:</B> Problem sending dss_image <%s>" %(dss_img))
                logger.error('error: %s %s' %(errmsg, e))
                #self._print_error_msg(errmsg)
            finally:
                f.close()
        except IOError as  e:
            errmsg.append("<P><B>ERROR:</B> Problem opening dss_image <%s %s>" %(dss_img,e)) 
            logger.error('error: %s  %s' %(errmsg,e))
            #self._print_error_msg(errmsg)
        return errmsg   
 

    def _check_dssimg(self, dss_img):
        c=0
        found=os.path.exists(dss_img)
        while (not found) and c < 3:
            time.sleep(0.5)
            c+=1  
            found=os.path.exists(dss_img)
            print found
   
        return found

    def do_GET(self):
        
        logger.debug('do_GET starting ...  path<%s>' %(self.path))
        
        gen2_tmp='/gen2/tmp'
        
        # parse parameters,make a dictionary, and validate keys and values.
        if self.path.find('?') != -1:
            dss_type,params=self._parse_string()
            logger.debug('dss_type<%s> params<%s>' %(dss_type, params))
            errmsg=self._validate_keys(params)
            if len(errmsg):
                self._print_error_msg(''.join(errmsg))
                return       

            errmsg=self._validate_values(params)
            if len(errmsg):
                self._print_error_msg(''.join(errmsg))
                return
        else:
            errmsg="<P><B>ERROR:</B> Problem parsing the path - check your path<%s>" %(self.path) 
            self._print_error_msg(errmsg)
            return
       
        # set up dss environment variables
        res = self._set_dssenv(dss_type)
        if len(res):   
            self._print_error_msg(''.join(res))
            return

        # get a dss image      
        fileid='dss%04d' % random.randint(1,10000)
        dss_img=os.path.join(gen2_tmp, '%s.fits' %fileid)
        res=self._exec_getimage(params, fileid, gen2_tmp)
        if len(res):
            self._print_error_msg(''.join(res))
            return
        logger.debug('checking dss path<%s> ' %(dss_img))
        #if not self._check_dssimg(dss_img):
        if not os.path.exists(dss_img):
            logger.error('dss image not found path<%s> ' %(dss_img))
            errmsg = "<P><B>ERROR:</B> dss image not found. [%s]\n" %(dss_img)
            self._print_error_msg(errmsg)
            #self._remove_file(dss_img)
            return 
        
        logger.debug('checking mime-type<%s>' %(params['mime-type']))  
     
        # append WCS info to a dss image and send it 
        if params['mime-type']=='application/x-fits':
            logger.debug('calling append_WCS')           

            res=fits.append_wcs(dss_img, logger)
            if len(res):
                logger.error('appending wcs failed<%s> ' %(res)) 
                self._remove_file(dss_img)
                self._print_error_msg(''.join(res))
                return
            size=os.path.getsize(dss_img)
            
            res=self._send_image(size, dss_img)
            self._remove_file(dss_img)
            if len(res):
                logger.error('sending an image failed<%s> ' %(res)) 
                self._print_error_msg(''.join(res))
                return
        else:
            logger.debug('mime-type<%s>' %(params['mime-type']))
            self._remove_file(dss_img)

        return

#    def do_POST(self):
#        global rootnode
#        print 'post'
#        try:
#            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
#            if ctype == 'multipart/form-data':
#                query=cgi.parse_multipart(self.rfile, pdict)
#            self.send_response(301)
#            
#            self.end_headers()
#            upfilecontent = query.get('upfile')
#            print "filecontent", upfilecontent[0]
#            self.wfile.write("<HTML>POST OK.<BR><BR>");
#            self.wfile.write(upfilecontent[0]);
#            
#        except :
#            pass

def main(options, args):
  
    global logger
    # Create top level logger.
    svcname = ('dss_server_%d' % (options.port))
    logger = ssdlog.make_logger(svcname, options)

    try:
        server_address = (options.host, options.port)
        server = ThreadingServer(server_address, DssHandler)
        #server = HTTPServer(server_address, DssHandler)
     
        logger.debug("Starting dss_server...")
        server.serve_forever()
    except KeyboardInterrupt:
        logger.debug('^C received, shutting down server')
        server.socket.close()

if __name__ == '__main__':
    
    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("--debug", dest="debug", default=False,
                      action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("--host", dest="host",
                      default='',
                      help="Host to serve on Digital Sky Survey")
    optprs.add_option("--port", dest="port", type="int", default=30000,
                      help="Register using PORT", metavar="PORT")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    ssdlog.addlogopts(optprs)

    (options, args) = optprs.parse_args(sys.argv[1:])

    if options.debug:
        import pdb

        pdb.run('main(options, args)')

    # Are we profiling this?
    elif options.profile:
        import profile

        print "%s profile:" % sys.argv[0]
        profile.run('main(options, args)')

    else:
        main(options, args)

#END


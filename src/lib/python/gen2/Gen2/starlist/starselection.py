#!/usr/bin/env python


import os
import threading
import shlex, subprocess as sp
import ssdlog, logging
import cfg.g2soss as g2soss


binhome = os.path.join(os.environ['ARCHHOME'], 'bin')

class StarSelection(object):

    def __init__(self, logger):

        self.keys=['prefered_num', 'selected_stars']
        self.header=None
        self.body=None

        try:
            os.environ['QDASVGWHOME']=g2soss.qdasvgwhome
        except Exception as e:
            os.environ['QDASVGWHOME']='/gen2/conf/QDASVGW'
  
        self.logger=logger

    def __get_sh_cmd(self, kargs):
        ''' create sh cmd line '''   
        cmd_line="QDASvgwShStarSelection {ra:f} {dec:f}"
        cmd_line=os.path.join(binhome, cmd_line)
        cmd_line=cmd_line.format(**kargs)
        return cmd_line

    def __get_ag_cmd(self, kargs):
        ''' create ag cmd line ''' 
        cmd_line="QDASvgwStarSelection {ra:f} {dec:f} {probe_ra:f} {probe_dec:f} {focus:s} {ins:s} {probe_r:f} {probe_theta:f} {probe_x:f} {probe_y:f} {pa:f} {limitmag:f} {goodmag:f} {fov_pattern:s}" 
        cmd_line=os.path.join(binhome, cmd_line)
        cmd_line=cmd_line.format(**kargs)
        return cmd_line

    def __make_input(self, limitmag,  starlist, num_stars):

        # info needed for star-selection is max-mag, num-stars, and stars-list
        # other info is hard-coded 
        header="Subaru Star Catalog Search System\nby\nSubaru OCS Hilo, Hawaii\n\n\nFieldCenterRA=00:00:00.000\nFieldCenterDEC=+00:00:00.00\nEpoch=J2000.0\nFieldRangeRA(arcmin)=  0.0\nFieldRangeDEC(arcmin)=  0.0\nMinimumMagnitude= 0.0\nMaximumMagnitude={0:4.1f}\nStarNumber={1:5d}\nname    RA      DEC     mag     Flag    B-R     R-I     Preference\n----    --      ---     ---     ----    ---     ---     ----------\n{2:s}"

        body=[]
        append=body.append
        for num,star in enumerate(starlist):
            num+=1
#            self.logger.debug('star=%s' %str(star))
            append("{name:17s}\t{ra:9.5f}\t{dec:9.5f}\t{mag:4.1f}\t{flag:2d}\t{b_r:4.1f}\t{r_i:4.1f}\t{0:5d}".format(num, **star))

        body='\n'.join(body)
#        self.logger.debug('body=%s' %body )
        feed=header.format(limitmag, num_stars, body)

        return feed

    def __extract_prefered_num(self):
        start_line=18      
        end_line=19

        default_num=0

        # e.g. 'PreferedNumber=5'
        self.logger.debug('extracting prefered')
        try:
            preferednum_line=self.header[start_line:end_line]
            self.logger.debug('prefered num line=%s' %str(preferednum_line))
            preferednum_line=preferednum_line[0].split('=')
            default_num=int(preferednum_line[1])
            self.logger.debug('prefered num=%d' %default_num)
        except Exception as e:
            self.logger.error('error: prefered num  %s' %str(e))
        finally:
            return default_num


    def __separate_header_body(self, res):
        
        header_line=21  # num of header line  
        res=res.split('\n')
 
        self.header=res[:header_line] # extract  header
        self.body=res[header_line:] # extract body(a list of stars)


    def __extract_stars(self):

        filtered=[]
        append=filtered.append    

#        keys=['name', 'ra', 'dec', 'mag', 'flag', 'b_r', 'preference', 'priority', 'dst'] 

        self.logger.debug('filtering stars=%s' %str(self.body))
        for line in self.body:
            star=line.split()
            if star:
                self.logger.debug('filtered star=%s' %str(star))
                # name, ra, dec, mag, flag, b-r, preference, priority, dst(min)
                append({'name':star[0], 'ra':float(star[1]), 'dec':float(star[2]), 'mag':float(star[3]), 'flag':int(star[4]), 'b_r':float(star[5]), 'preference':float(star[6]), 'priority':int(star[7]), 'dst':float(star[8])})
      
#                append(dict(zip(keys, star)))

        return filtered  

    def __filter_stars(self, cmd_line, feed):
        ''' filter stars '''        
 
        args = shlex.split(cmd_line)
        self.logger.debug('args=%s' %args)
        
        try:
            p = sp.Popen(args, stdout=sp.PIPE,  stdin=sp.PIPE, stderr=sp.STDOUT)
            p.stdin.write(feed)
        except Exception as e:
            self.logger.error('error: executing %s' %str(e))
            stars=[]
        else:
            res=p.communicate()[0]
            self.__separate_header_body(res)

            self.logger.debug('res=%s' %res)

            stars=self.__extract_stars()
        finally:
            return stars 

    def __select_stars(self, cmd_line, kargs, starlist):

        try: 
            feed=self.__make_input(limitmag=kargs['limitmag'], starlist=starlist, num_stars=len(starlist))
            self.logger.debug('feed=%s' %feed)

            filtered_stars=self.__filter_stars(cmd_line, feed)
        except Exception as e:
            self.logger.error('error: filtering stars. %s' %e)   
            filtered_stars=[]           
        finally:
            return filtered_stars        

    def select_ag_stars(self, kargs, starlist):
        ''' select ag stars '''
        cmd_line=self.__get_ag_cmd(kargs)
        ag_stars=self.__select_stars(cmd_line, kargs, starlist) 
        prefered_num=self.__extract_prefered_num()  
        ag_star_info=dict(zip(self.keys,[prefered_num, ag_stars]))
#        print ag_star_info
     
        return ag_star_info        

    def select_sh_stars(self, kargs, starlist):
        ''' select sh stars '''
        cmd_line=self.__get_sh_cmd(kargs)
        sh_stars=self.__select_stars(cmd_line, kargs, starlist) 
        prefered_num=self.__extract_prefered_num()  

        sh_star_info=dict(zip(self.keys,[prefered_num, sh_stars]))
        return sh_star_info        

def main(options, args):
    ''' right now, this main is for testing purpose'''
    

    import starlist
    logname = 'star_selection'
    # Create top level logger.
    logger = ssdlog.make_logger(logname, options)
 
    sh_keys={'ra':10.1, 'dec':10.0, 'fov':0.076, 'limitmag':13.0}
    ag_keys={'ra':10.0, 'dec':20.0, 'fov':0.076, 'probe_ra':10.0, 'probe_dec':20.0, 'focus':'CS', 'ins':'MOIRCS',  'probe_r':0.0, 'probe_theta':0.0, 'probe_x':0.0, 'probe_y':0.0,  'pa':0.0, 'limitmag':15.0, 'goodmag':10.0, 'fov_pattern':'STANDARD'}

    try:
        catalog=starlist.CatalogSearch(logger)
        starlist=catalog.search_starcatalog(ra=sh_keys['ra'], dec=sh_keys['dec'], fov=sh_keys['fov'], limitmag=sh_keys['limitmag'])

        ss=StarSelection(logger)
        res=ss.select_sh_stars(sh_keys, starlist)
    
        # for star in res:
        #     print star['name']

#        starlist=catalog.search_starcatalog(ra=ag_keys['ra'], dec=ag_keys['dec'], fov=ag_keys['fov'], limitmag=ag_keys['limitmag'])
#        res=ss.select_ag_stars(ag_keys, starlist)
    
        print 'prefered=%d' %res.get('prefered_num')
        for star in res.get('selected_stars'):
            print star['name'], star['priority']

    except KeyboardInterrupt:
        print 'keyboard interrupting...'  
    except Exception as e:
        print 'excpetion %s' %e
        
if __name__ == "__main__":
    
    import sys
    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog -r 0 -d 0 -f 0 -l 10"
    parser = OptionParser(usage=usage, version=('%prog'))

    parser.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    
    parser.add_option("--ra", dest="ra", type="float",  
                      default=False,
                      help="RA(J2000.0) the center of a sight in degree")
    parser.add_option("--dec", dest="dec", type="float", 
                      default=False,
                      help="DEC(J2000.0) the center of a sight in degree")

    parser.add_option("--pra", dest="pra", type="float",  
                      default=False,
                      help="RA(J2000.0) the ag/sv probe position in degree")

    parser.add_option("--pdec", dest="pdec", type="float", 
                      default=False,
                      help="DEC(J2000.0) the ag/sv probe positon in degree")

    parser.add_option("--focus", dest="focus",
                      default=False,
                      help="Specify telescope focus")
    
    parser.add_option("--ins", dest="ins",
                      default=False,
                      help="Specify instrument")

    parser.add_option("--pr", dest="pr", type="float",  
                      default=False,
                      help="Specify the ag probe R value")

    parser.add_option("--pt", dest="pt", type="float",  
                      default=False,
                      help="Specify the ag probe Theta value")

    parser.add_option("--px", dest="px", type="float",  
                      default=False,
                      help="Specify the ag probe X value")

    parser.add_option("--py", dest="py", type="float",  
                      default=False,
                      help="Specify the ag probe Y value")

    parser.add_option("--rotate", dest="rotate", type="float",  
                      default=False,
                      help="Specify the instrument rotater value")

    parser.add_option("--limitmag", dest="limitmag", type="float",  
                      default=False,
                      help="Specify the limit magnitude")

    parser.add_option("--goodmag", dest="goodmag", type="float",  
                      default=False,
                      help="Specify the good magnitude")

    parser.add_option("--fovname", dest="fovname",
                      default=False,
                      help="Specify field of view name")
    
    parser.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
 
    
    ssdlog.addlogopts(parser)
    (options, args) = parser.parse_args(sys.argv[1:])
    
    if len(args) != 0:
        parser.error("incorrect number of arguments")
   
    # Are we debugging this?
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
    
    
    

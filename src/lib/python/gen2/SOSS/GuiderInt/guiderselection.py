#! /usr/bin/env python

import sys, os
import Tkinter
import math
import astro.radec as radec
import guidercatalog as catalog

import guiderconfig 
import agutil as ag



#  Argument
#    equinox        equinox
#    ra             alpha: hms
#    dec            delta: dms
#    focus          foci: P_OPT,P_IR,CS,CS_OPT,CS_IR,NS_OPT,NS_IR,NS_IR_OPTM2
#    probe_ra       pick up mirror probe position alpha:hms
#    probe_dec      pick up mirror probe position  delta:dms
#    pa             rotator position angle
#    probe_R        pick up mirror probe position R (CASS, NSOPT, NSIR)
#    probe_T        pick up mirror probe position Theata (CASS, NSOPT, NSIR)
#    probe_X        pick up mirror probe position X (POPT, PIR)
#    probe_Y        pick up mirror probe position Y (POPT, PIR) 
#    select_mode    guide star selection mode: AUTO, SEMIAUTO, MANUAL
#    dss_mode       dss_mode:  ON, OFF, DSS1, DSS2R, DSS2B, DSS2I
#    ag_kind        cetroid calculation region: AG1, AG2
#    instrument     instrument name
#    limitmag       lowest magnitude
#    goodmag        target magnitude 
#    fov_pattern    FOV pattern


##  send example
##  tcl.send('ag', "wm title .skycat1 FOO")



class GuiderSelection:
    
    
   
    '''
       EXEC VGW AG_AUTO_SELECT MOTOR=ON 
       EQUINOX=2000.0 RA=132436.534 DEC=+273055.00  PROBE_RA=132436.534 PROBE_DEC=+273055.00 F_SELECT=P_OPT 
       INSTRUMENT_NAME=SPCAM PROBE_R=0.0 PROBE_THETA=0.0 PROBE_X=0.0 PROBE_Y=0.0 AG_PA=0.0  SELECT_MODE=SEMIAUTO DSS_MODE=OFF AG_AREA=AG1 
       LIMITMAG=17.0 GOODMAG=13.0 FOV_PATTERN=STANDARD
    '''
    
    def __init__(self, equinox=2000.0, ra=None, dec=None, probe_ra=None, probe_dec=None, f_select=None, instrument_name=None, 
                  probe_r=0.0, probe_theta=0.0, probe_x=0.0, probe_y=0.0,  ag_pa=None, select_mode='semiauto', 
                  dss_mode='off', ag_area='ag1', limitmag=None, goodmag=None, fov_pattern='standard'):
        
        #self.tcl=Tkinter.Tk()
        
#       # skycat name
#       self.skycat_name=name
#        
#       # widget names
#        self.canvaspath=".skycat1.image.imagef.canvas"
#        self.imagepath=".skycat1.image"
#        self.pickpath=".skycat1.image.pick"
#        self.catmpath=".skycat1.ac1.menubar.catalogs.m"
#        self.searchpath=".skycat1.ac1.search"
#        self.menu_path=".skycat1.menubar.file.m"
#        
#        # file name
#        #self.graph_id_file="$env(HOME)/Desktop/VGW_SUB_SYSTEM/AG_AUTO_SELECT/file/graph_id.dat"
        
        self.equinox = equinox;  self.ra=ra;  self.dec=dec;    self.probe_ra=probe_ra;  self.probe_dec=probe_dec;                         
        self.f_select= f_select;     self.ins_name=instrument_name;  
        self.probe_r=probe_r;   self.probe_theta=probe_theta;   self.probe_x=probe_x;   self.probe_y=probe_y;   
        self.ag_pa= ag_pa;      
        self.select_mode=select_mode; self.dss_mode=dss_mode;     self.ag_area=ag_area;    self.limitmag=limitmag; 
        self.goodmag=goodmag;         self.fov_pattern=fov_pattern;
        
        self.focuslist={ 'CS_OPT' : 'CS', 'CS_IR'  : 'CS',  'NS_IR_OPTM2' : 'NS_IR' }
        
                
    def execute(self):
        print 'do execution'

        ''' 
            pass hms(121212.12) format and parse it to (12 12 12.12)
            pass dms(+121212.123) format and parse it to (+1 12 12 12.123)
        '''
        rH, rM, rS=radec.parseHMS(self.ra)
        sign, dD, dM, dS=radec.parseDMS(self.dec)
        
        print 'ra h:%d m:%d s:%f' %(rH, rM, rS)
        print 'dec sign:%d d:%d m:%d s:%f' %(sign, dD, dM, dS)
                
        '''  ra/dec to rad  '''
        ra_rad=radec.hmsToRad(rH, rM, rS)
        dec_rad=radec.dmsToRad(sign, dD, dM, dS)          
        
        ''' ra/dec to degree '''
        ra_deg=radec.hmsToDeg(rH, rM, rS)
        dec_deg=radec.dmsToDeg(sign, dD, dM, dS)
            
        print 'TARGET RA RAD:%f  DEG:%f' %(ra_rad, ra_deg)
        print 'TARGET DEC RAD:%f  DEG:%f' %(dec_rad, dec_deg)
            
#        if (not self.f_select) or self.f_select.upper()=='NOP' :
#            self.f_select = self.fetchOne('FITS.SBR.MAINOBCP')
#            if self.f_select.startswith('#'):
#                raise VGWTaskError("No instrument allocated!")    
                    
        '''  set up focus if CS_OPT & CS_IR are passed, then they will be CS
             if NS_IR_OPTM2 is passed, then it will be NS_IR '''
        try:
            self.f_select=self.focuslist[self.f_select]
        except:
            pass
            #self.f_select=f_select    

        if str(self.ag_pa).upper()=='NOP' or self.ag_pa==None:
            if self.f_select.startswith('P'):
                self.ag_ap = self.fetchOne('TSCL.INSROTPA_PF')
                if self.ag_ap.startswith('#'):
                    raise VGWTaskError("No p_opt/ir rotator status assigned") 
            else:
                self.ag_ap = self.fetchOne('TSCL.INSROTPA')
                if self.ag_ap.startswith('#'):
                    raise VGWTaskError("No p_opt/ir rotator status assigned")      
        
#        if (not self.instrument_name) or self.instrument_name.lower()=='NOP' :
#            self.instrument_name = self.fetchOne('FITS.SBR.MAINOBCP')
#            if self.instrument_name.startswith('#'):
#                raise VGWTaskError("No instrument allocated!")
        
        
        if str(self.limitmag).upper()=='NOP' or self.limitmag==None:
            if self.f_select=='P_OPT': self.limitmag=17.0
            else:                      self.limitmag = 20.0      
        
        if str(self.goodmag).upper()=='NOP' or self.goodmag==None:
            if self.f_select.startswith('P'): self.goodmag=13.0
            else:                             self.goodmag = 12.0       
                      
        '''  field of view  '''
        self.fov=guiderconfig.FOV[self.f_select]
        
        
        '''  search star catalog  '''        
        ag_stars=catalog.search_catalog(ra_deg, dec_deg, fov, self.limitmag)  
        
        
        for i in ag_stars:
            print i
#        
#        
#        
#        
#        
#        
#        
#        # set rotator angle
#        if 'P_' in self.f_select:
#            
#             # probe movable area  
#             self.fov_x0, self.fov_x1,self.fov_y0,self.fov_y1 =guiderconfig.PROBE[self.f_select]
#                          
#                                 
#             # Origin: East for PF (?)  Kosugi-san's comment
#             self.ag_pa=math.radians(ag_pa)  # positon angle to rad
#             #self.cosrot_rad=math.cos(self.ag_pa)
#             #self.sinrot_rad=math.sin(self.ag_pa)
#           
#             #self.dt=self.ag_pa
#             self.rotation_flag=0 
#            
#             #print 'ag pa:%f  rotation flag:%d  cosrot rad:%f  sinrot rad:%f' %(self.ag_pa,  self.rotation_flag, self.cosrot_rad, self.sinrot_rad)
#             print 'x0:%f  x1:%f  y0:%f  y1:%f' %(self.fov_x0, self.fov_x1, self.fov_y0, self.fov_y1) 
#        
#                   
#        elif (self.f_select == "CS") :
#            # Origin: West for Cs (!) 
#            #self.dt=self.ag_pa+180.0
#                self.rotation_flag=0
#        elif self.f_select == "NS_OPT":
#            print 'TO DO NS OPT'
#        elif self.f_select == "NS_IR":
#            print 'TO DO NS IR'
#                                  
#        
#        
#        try:
#             
#            self.maxprefnum=guiderconfig.MAXPREFNUM[self.f_select]   # get prefered number of stars
#            self.minsep=guiderconfig.MINSEP[self.f_select]           # get minumum separation value between stars (arcsec)
#            self.insfov=guiderconfig.INSFOV[self.ins_name]           # get instrument field of view (rad)
#            #self.evig=guiderconfig.EVIG[self.f_select]
#            self.pvig=guiderconfig.VIGNET[self.f_select]             # get probe vignet radious(rad) 
#            self.scale=guiderconfig.SCALE[self.f_select]             # get a value to convert degree to mm ??????
#                   
#        except:
#            print "fail to get fov or maxpref"
#            pass
#        
#        
#        '''
#            instrument field of viiew and probe vignet (radious in rad) 
#        '''
#        self.inner_fov=self.insfov+self.pvig
#           
#    
#        print 'foci', self.f_select, self.ins_name
#        print 'maxprefnum:%d  minsep:%f insfov:%f  pvig:%f  scale:%f' %( self.maxprefnum, self.minsep, self.insfov, self.pvig, self.scale ) 
#        
#        # minsep2 nad diffsep2 can be used to check the separation of guide stars 
#        # P_OPT minsep2 is 10sec         
#        #self.minsep2=math.pow((self.minsep/3600.0), 2.0)
#        #self.diffcatalog=guiderconfig.DIFFCATALOG
#        
#        #print 'minsep2:%10.10f  diffsep2:%10.10f' %(self.minsep2, self.diffsep2)
#   
#              
#        #self.catalog_stars=None
#
#        # test guide stars
#        self.catalog_stars=[
#                     
#                     { 'RA_RAD': 0.017453292519943295, 'DEC_RAD': 1.2217479296885507,'NAME': 'UB15999-00000001',  'MAG':11,   'FLAG':2,  'R_RAD':None, 'PREF': 10, },
#                     
#                     { 'RA_RAD': 0.017453292519943295, 'DEC_RAD':1.2391837689159739, 'NAME': 'GS15999-00000001',  'MAG':12.5, 'FLAG':0,  'R_RAD':None, 'PREF': 10, },
#                                          
#                     { 'RA_RAD': 0.017453292519943295, 'DEC_RAD':1.2217304763960306, 'NAME': 'UB15999-00000002',  'MAG':12.1, 'FLAG':99, 'R_RAD':None, 'REF': 10, },
#                     
#                     # ra 0  dec 0
#                     { 'RA_RAD': 0.0,                  'DEC_RAD':0.0,                'NAME': 'UB15999-00000003',  'MAG':14,   'FLAG':3,  'R_RAD':None, 'PREF': 10, },
#                     
#                     # ra 0  dec 0.05
#                     { 'RA_RAD': 0.0,                  'DEC_RAD':0.0008726646259971648,'NAME': 'UB15999-00000004', 'MAG':10,   'FLAG':3,  'R_RAD':None, 'PREF': 10, },
#                     
#                     # ra 0  dec 0.01
#                     { 'RA_RAD': 0.0,                  'DEC_RAD': 0.0001745329,'NAME': 'UB15999-00000005', 'MAG':10,   'FLAG':3,  'R_RAD':None, 'PREF': 10, },
#                     
#                     # ra 0.4  dec 0.075
#                     { 'RA_RAD': 0.0069813170079773184,                  'DEC_RAD': 0.0012217304763960308, 'NAME': 'UB15999-00000006', 'MAG':10,   'FLAG':3,  'R_RAD':None, 'PREF': 10, },
#                     
#        ]
##                   #, {'DEC': 70.2, 'NAME': 'UB15999-00000002', 'RA': 0.02}, {'DEC': 70.3, 'NAME': 'UB15999-00000003', 'RA': 359.9}]
#     
#        print self.catalog_stars
#     
#     
#        '''
#            set up Vignet mapping
#        '''  
#        self.vignet_map=ag.create_vignet_map(self.f_select, self.fov_pattern)
##              
##        
##        print self.vignet_map[0][0], self.vignet_map[71][0]
##
##        print self.vignet_map[3][75], self.vignet_map[60][75]
##
##        print self.vignet_map[46][76], self.vignet_map[55][76]
##
##        print self.vignet_map[11][129], self.vignet_map[22][129]
##        
##        print self.vignet_map[71][259], self.vignet_map[22][257]
##        
#        
#        
#        self.AG_NAME='NAME'; self.AG_RA_RAD='RA_RAD'; self.AG_DEC_RAD='DEC_RAD'
#        self.AG_MAG='MAG'; self.AG_FLAG='FLAG'; self.AG_R_RAD='R_RAD'; self.AG_PREF='PREF'
#    
#        
#        self.half_pi= math.pi / 2.0 
#    
#        self.degree_circle=360.0
#        self.ag_out_of_range=-1000
#        
#        

    
    def ag_star_list(self):
        
        
        print "AG STAR LIST CALLED" , self.ra_deg, self.dec_deg, self.fov, self.limitmag
        self.catalog_stars=catalog.search_catalog(self.ra_deg, self.dec_deg, self.fov, self.limitmag)
        
        for i in self.catalog_stars:
            print i
        
        
        
            
    
    def ag_star_selection(self ):
        
        count=0
        for g_star in self.catalog_stars:
            
            
            print 'GUIDE STAR ' , g_star
            
            
            ag_ra_rad=g_star[self.AG_RA_RAD]; ag_dec_rad=g_star[self.AG_DEC_RAD]
            
            
            #################################### 
            ###  this is for testing purpose
            #ag_ra_rad=math.radians(0.0); ag_dec_rad=math.radians(70.0)
            #print 'guider star ra_rad:%f   dec_rad:%f' %(ag_ra_rad, ag_dec_rad)
            
            
            ag_r_rad=ag.delta_stars(self.ra_rad, self.dec_rad, ag_ra_rad, ag_dec_rad)
            
            
            print 'target/ag star delta   AG R_RAD:%f' %(ag_r_rad)
            
            #print i
            pa=ag.pa_stars(self.ra_rad, self.dec_rad, ag_ra_rad, ag_dec_rad, ag_r_rad) 
            
            ag_theata_rad=self.half_pi-self.ag_pa-pa
            
            if ag_theata_rad < 0.0:
                print 'ag_theate_rad is negative'
                ag_theata_rad+=math.pi*2.0
                        
            print 'AG_PA:%f+1.57-PA_RAD:%f = AG_THEATA_RAD:%f' %(self.ag_pa, pa, ag_theata_rad)  
            print 'AG_R_DEC:%f   AG_THEATA_DEG:%f' %(math.degrees(ag_r_rad), math.degrees(ag_theata_rad)  )
            
                        
            # check if a candidate star is within FOV
            if 'P_' in self.f_select:
                
                #math.cos(ag_theata_rad)*math.sin(self.co)
                rx=ag_r_rad * math.cos(ag_theata_rad)
                ry=ag_r_rad * math.sin(ag_theata_rad)
                
                print 'rx rad:%f ry rad:%f' %(rx, ry)
                print 'rx deg:%f ry deg:%f' %(math.degrees(rx), math.degrees(ry) )
                                
                try:
                    # check if a guide star is in probe movable area
                    assert self.fov_x0 < rx < self.fov_x1
                    assert self.fov_y0 < ry < self.fov_y1
                   
                    print 'IN FOV   X0:%f <  rx:%f < X1:%f  Y0:%f < ry:%f < Y1:%f' %(self.fov_x0,rx, self.fov_x1, self.fov_y0,ry, self.fov_y1) 
                  
                except:
                    
                    # a guide star is out of fov; assigne -1000 not to choose this
                    g_star[self.AG_PREF]=None
                                        
                    print 'OUT FOV   X0:%f <  rx:%f  < X1:%f   Y0:%f <  ry:%f < Y1:%f' %(self.fov_x0, rx, self.fov_x1, self.fov_y0, ry, self.fov_y1) 
                    
                    print 'PRE:%s' %(g_star[self.AG_PREF])
                    
                    count+=1
                    continue
            
            else:
                ### CS NS ##
                print 'under construction'
                rx=ag_r_rad * math.cos(ag_theata_rad)
                
            
                
            '''
                a candidate star mag is refered to vignet map and adjust its mag 
            '''
            ag_r_deg=math.degrees(ag_r_rad)
            ag_theata_deg=math.degrees(ag_theata_rad)
            
            print "AG R_DEG:%f   AG THEATA DEG:%f " %(ag_r_deg, ag_theata_deg)
            print "AG THEATA DEG / 5.0 :%f" %(ag_theata_deg/5.0)
            
            '''
                r will be round to int value. e.g, 1.2->1, 1.5->2  (unit : mm) 
                r range should be between 0 to 125mmm; vignet map is 0 to 130mm 
                
                theata deg is divided by 5 because vignet map is 5 degree each. e.g, 0<->1 is 0 <-> 5 degree
                then theata  will be round to int  e.g, 10.2->10, 10.5->11
            '''
            r_round=int ( round( (rx/self.scale), 0 ) )
            theata_round= int(  round(  (math.degrees(ag_theata_rad)/5.0)  ,0 )  )
            
            '''
                if theata is round to 360 degree, assign 0 degree  
            '''
            if theata_round == 72: theata_round=0
                                
            print  'RX ROUND:%d'  % r_round
            print  'AG THEATA:%d' % theata_round
            
            '''
                add vignet mag to a candidate guides star mag
            '''                    
            g_star[self.AG_MAG]+=self.vignet_map[theata_round][r_round] 
            
            print "VIGNET MAP VALUE:%f   AG MAG:%f" %( self.vignet_map[theata_round][r_round], g_star[self.AG_MAG] )
                           
                
            # a canidate star is within ins + probe fov
            if ag_r_rad < self.inner_fov:
                # if a candidate guide star is closer to the center of ins fov,
                # more preference value will be substracted and the star is considered as improper guide star. 
                preference=(self.inner_fov - ag_r_rad)/self.insfov * guiderconfig.INITPREFERENCE * 5.0
                
                g_star[self.AG_PREF]-= preference
            
                print 'WITHIN INS FOV  PRE AdUST:%f    10-PRE:%f'  %(g_star[self.AG_PREF], preference )
            
            
            # check if difference between a mag of candidate star and  target mag is less than 1 or not
            # if there is more than 1mag difference, subtract 10 from star preferece, if not, subtract diff between target mag and candidata mag  
            diffmag=self.goodmag-g_star[self.AG_MAG]                 
            if ( diffmag > guiderconfig.BRIGHTEND ):
                g_star[self.AG_PREF] -= guiderconfig.INITPREFERENCE
                print 'goodmag:%f - g_starmag:%f > 1   preference:%f' %(self.goodmag, g_star[self.AG_MAG], g_star[self.AG_PREF] )  
                       
            else:
                g_star[self.AG_PREF] -= math.fabs(diffmag) 
                print 'goodmag:%f - g_starmag:%f < 1   preference:%f' %(self.goodmag, g_star[self.AG_MAG], g_star[self.AG_PREF] ) 

            
            '''
               check a flag that indicates if a star is more like star or not
               best flag is 2                
            '''
            g_star[self.AG_PREF]-=math.fabs(guiderconfig.BESTFLAG - g_star[self.AG_FLAG])
            print 'bestflag:2.0 - g_star flag:%f    preference:%f' %( g_star[self.AG_FLAG], g_star[self.AG_PREF] ) 
            
            
            
            for cmp_star in range(count):
                
                print 'IN  CMP STAR LOOP  name:%s  count:%d' %(self.catalog_stars[cmp_star][self.AG_NAME], count)
                
                
                if self.catalog_stars[cmp_star][self.AG_PREF]==None:
                    print 'FOR SEPCHECK name:%s  pref:%s' %(self.catalog_stars[cmp_star][self.AG_NAME],   self.catalog_stars[cmp_star][self.AG_PREF]   )
                    
                    continue
                
                else:
                                                         
                    delta_stars=ag.delta_stars(ag_ra_rad, ag_dec_rad, self.catalog_stars[cmp_star][self.AG_RA_RAD], self.catalog_stars[cmp_star][self.AG_DEC_RAD] )
                    
                    if self.minsep > delta_stars:
                        print 'MINSEP:%f > DELTA STARSs:%f' %(self.minsep, delta_stars)
                        
                        if ( guiderconfig.DIFFCATALOG < delta_stars) or ( g_star[self.AG_NAME][0]==self.catalog_stars[cmp_star][self.AG_NAME][0]):
                            print 'diffcatalog:%f  < delta stars:%f or same name:%s:%s' %(guiderconfig.DIFFCATALOG, delta_stars, g_star[self.AG_NAME], self.catalog_stars[cmp_star][self.AG_NAME] )
                            
                            g_star[self.AG_PREF]-=guiderconfig.INITPREFERENCE
                            self.catalog_stars[cmp_star][self.AG_PREF]-=guiderconfig.INITPREFERENCE
                            
                            print 'IN DIFFCATALOG g star pref:%f  cmp star pref:%f' %( g_star[self.AG_PREF], self.catalog_stars[cmp_star][self.AG_PREF] )
                            
                            
                        else:
                            print 'diffcatalog:%f  > delta stars:%f' %(guiderconfig.DIFFCATALOG, delta_stars)    
                    else:
                        print  'minsep:%f < delta stars:%f' %(self.minsep, delta_stars)   
                    
            count+=1        
            #guiderconfig.DIFFCATALOG
        
        
        #sorted_stars=self.sort_by_preference()
        #self.sort_by_preference()
               
        try:
            for pref, star in self.sort_by_preference():
                print pref, star[self.AG_NAME], star[self.AG_RA_RAD], star[self.AG_DEC_RAD], star[self.AG_MAG], star[self.AG_FLAG], star[self.AG_R_RAD]
        except:
            print "NO GUIDE STAR FOUND"         
    
    def sort_by_preference(self):
        
        print "sort by preference called"
        
        decorated = [ (guide_star[self.AG_PREF], guide_star ) for guide_star in self.catalog_stars if guide_star[self.AG_PREF] is not None ]
               
        decorated.sort(reverse=True)
        
        return decorated
        #print decorated
        
        #return decorated.sort(reverse=True)    
    
    def ag_auto_select(self):
        
        print 'under costruction'
 
        
            
    def clear_drawing(self):
        print "might need this implementaion later "
                

if __name__ == "__main__":
    
    
    
                               # name  equinox  ra  dec  probe_ra  probe_dec
                               # focus ins   probe_R  probe_T probe_X probe_Y  pa  
                               # select_mode dss_mode  ag_kind  limitmag  goodmag fov_pattern    
    
    #guiderselect=GuiderSelection("ag", 2000.0, 000000.00, +700000.000, 000000.00, +700000.000, 
    #                             'P_OPT', 'SPCAM', 0.0, 0.0, 0.0, 0.0, 0.0, 
    #                             'AUTO', 'OFF', 'AG1', 21.0, 12.0, 'STANDARD' )
    
       
    guiderselect=GuiderSelection(equinox=2000.0, ra=000000.00, dec=+000000.000, probe_ra=000000.00, probe_dec=+000000.000, 
                                 f_select='P_OPT', instrument_name='SPCAM', probe_r=0.0, probe_theta=0.0, probe_x=0.0, probe_y=0.0, 
                                 ag_pa=0.0, select_mode='AUTO', dss_mode='OFF', ag_area='AG1', limitmag=11.0, goodmag=10.0, fov_pattern='STANDARD' )
    
    
    
    #guiderselect.ag_star_list()
       
    guiderselect.execute()
       
    #guiderselect.ag_star_list() 
       
    
    #guiderselect.ag_auto_select(2000.0, 121132.481,  +121655.78,  'P_OPT', 121132.0,  +121655.00,  0.0,  0.0,  0.0,  0.0,  0.0,  'MANUAL', 'OFF', 'AG1', 'SPCAM', 17, 15, 'STANDARD' ) 
    
    






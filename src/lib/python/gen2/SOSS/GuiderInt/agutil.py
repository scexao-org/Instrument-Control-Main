import os, sys
import math

import guiderconfig as config

import astro.radec as radec
 
        
def ag_star_selection(catalog_stars, ra_rad, dec_rad, ag_pa, instrument_name, f_selct, goodmag, fov_pattern):
    
    
    ''' get ag probe movable area (rad)'''
    if f_select.startswith('P'):
        fov_x0, fov_x1, fov_y0, fov_y1 =config.PROBE[f_select]
        
    insfov=config.INSFOV[instrument_name]           # get instrument field of view (rad)
    pvig=config.VIGNET[f_select]                    # get probe vignet radious(rad)
    
    inner_fov=insfov+pvig
        
    minsep=config.MINSEP[f_select]           # get minumum separation value between stars (arcsec)
    
    ''' 
       minsep2 nad diffsep2 can be used to check the separation of guide stars 
       P_OPT minsep2 is 10sec 
    '''
    minsep2=math.pow((minsep/3600.0), 2.0)

    ''' create vignet map '''   
    vignet_map=create_vignet_map(f_select, fov_pattern)    
        
    AG_NAME='NAME'; AG_RA_RAD='RA_RAD'; AG_DEC_RAD='DEC_RAD';
    AG_MAG='MAG';   AG_FLAG='FLAG';     AG_R_RAD='R_RAD';  AG_PREF='PREF';

    HALF_PI = math.pi / 2.0 
    
    CIRCLE_PI=math.pi * 2.0
   
    count=0
    
    for g_star in self.catalog_stars:
        
        print 'GUIDE STAR ' , g_star
        
        ag_ra_rad=g_star[AG_RA_RAD]; ag_dec_rad=g_star[AG_DEC_RAD];
        
        ag_r_rad=radec.delta_stars(ra_rad, dec_rad, ag_ra_rad, ag_dec_rad)
       
        #print 'target/ag star delta   AG R_RAD:%f' %(ag_r_rad)
    
        pa=radec.pa_stars(ra_rad, dec_rad, ag_ra_rad, ag_dec_rad, ag_r_rad)
        
        ag_theata_rad=HALF_PI - ag_pa - pa
        
        if ag_theata_rad < 0.0:
            #print 'ag_theate_rad is negative'
            ag_theata_rad+=CIRCLE_PI
            
        #print 'AG_PA:%f+1.57-PA_RAD:%f = AG_THEATA_RAD:%f' %(ag_pa, pa, ag_theata_rad)  
        #print 'AG_R_DEC:%f   AG_THEATA_DEG:%f' %(math.degrees(ag_r_rad), math.degrees(ag_theata_rad)  )
    
        ''' check if a candidate star is within FOV  '''
        if f_select.startswith('P'):
            #math.cos(ag_theata_rad)*math.sin(self.co)
            rx=ag_r_rad * math.cos(ag_theata_rad)
            ry=ag_r_rad * math.sin(ag_theata_rad)
            
            print 'rx rad:%f ry rad:%f' %(rx, ry)
            print 'rx deg:%f ry deg:%f' %(math.degrees(rx), math.degrees(ry) )
            
            try:
                # check if a guide star is in probe movable area
                assert fov_x0 < rx < fov_x1
                assert fov_y0 < ry < fov_y1
                
                #print 'IN FOV   X0:%f <  rx:%f < X1:%f  Y0:%f < ry:%f < Y1:%f' %(fov_x0,rx, fov_x1, fov_y0,ry, fov_y1) 
            except:
                # a guide star is out of fov; assigne -1000 not to choose this
                g_star[AG_PREF]=None
                
                #print 'OUT FOV   X0:%f <  rx:%f  < X1:%f   Y0:%f <  ry:%f < Y1:%f' %(fov_x0, rx, fov_x1, fov_y0, ry, fov_y1) 
                #print 'PRE:%s' %(g_star[AG_PREF])
                count+=1
                continue
        else:
            ### CS NS ##
            print 'under construction'
            #rx=ag_r_rad * math.cos(ag_theata_rad)
       
        '''
           mag values of vignet map are messaured at the cross point of array. 
           each star needs to refere to the closest point of a mag value on vignet map
           
           r will be round to int value. e.g, 1.2->1, 1.5->2  (unit : mm)  because r delta is 1mm each 
           r range should be between 0 to 125mmm(vignet map is 0 to 130mm) if P_OPT  
        
           theata deg is divided by 5 because vignet map is 5 degree each. e.g, 0 -> 0 to 5 degree  1 -> 5 to 10 degree
           then theata  will be round to int  e.g, 10.2(51deg)->10(50deg), 10.5(52.5deg)->11(55deg)
        '''
        ag_r_deg=math.degrees(ag_r_rad)
        ag_theata_deg=math.degrees(ag_theata_rad)
        
        #print "AG R_DEG:%f   AG THEATA DEG:%f " %(ag_r_deg, ag_theata_deg)
        #print "AG THEATA DEG / 5.0 :%f" %(ag_theata_deg/5.0)        
               
        r_round=int ( round( (rx/self.scale), 0 ) )
        theata_round= int(  round(  (math.degrees(ag_theata_rad)/5.0)  ,0 )  )
    
        ''' if theata is round to 360 degree, assign 0 degree '''
        if theata_round == 72: theata_round=0
        
        #print  'RX ROUND:%d'  % r_round
        #print  'AG THEATA:%d' % theata_round

        '''
           a candidate star's mag will be adjusted by refering to vignet map   
           vignet map is 130(mm) x 72(degree) array if P_OPT
        '''
        g_star[AG_MAG]+=vignet_map[theata_round][r_round] 
    
        print "VIGNET MAP VALUE:%f   AG MAG:%f" %( vignet_map[theata_round][r_round], g_star[AG_MAG] )
        
        ''' a canidate star is within ins + probe fov  '''
        if ag_r_rad < inner_fov:
            
            ''' if a candidate guide star is closer to the center of ins fov,
                more preference value will be substracted and the star is considered as improper guide star. '''
            g_star[AG_PREF]-=(inner_fov - ag_r_rad)/insfov * config.INITPREFERENCE * 5.0
                       
            print 'WITHIN INS FOV  PRE AdUST:%f    10-PRE:%f'  %(g_star[AG_PREF], preference )
   
        '''
           check if difference between a mag of candidate star and  target mag is less than 1 or not
           if there is more than 1mag difference, subtract 10 from star preferece, if not, subtract diff between target mag and candidata mag
        '''
        diffmag=goodmag-g_star[AG_MAG] 
        if ( diffmag > config.BRIGHTEND ):
            g_star[AG_PREF] -= config.INITPREFERENCE
            print 'goodmag:%f - g_starmag:%f > 1   preference:%f' %(goodmag, g_star[AG_MAG], g_star[AG_PREF] )  
        else:
            g_star[AG_PREF] -= math.fabs(diffmag)
            print 'goodmag:%f - g_starmag:%f < 1   preference:%f' %(goodmag, g_star[AG_MAG], g_star[AG_PREF] ) 
        
        
        '''
           check a flag that indicates if a star is more like star or not
           best flag is 2                
        '''
        g_star[AG_PREF]-=math.fabs(config.BESTFLAG - g_star[AG_FLAG])
        #print 'bestflag:2.0 - g_star flag:%f    preference:%f' %( g_star[AG_FLAG], g_star[AG_PREF] ) 
        
         
        for cmp_star in range(count):
            print 'IN  CMP STAR LOOP  name:%s  count:%d' %(self.catalog_stars[cmp_star][self.AG_NAME], count)
            
            if catalog_stars[cmp_star][AG_PREF]==None:
                print 'FOR SEPCHECK name:%s  pref:%s' %(catalog_stars[cmp_star][AG_NAME],  catalog_stars[cmp_star][AG_PREF])
                continue
            else:
                delta_stars=radec.delta_stars(ag_ra_rad, ag_dec_rad, catalog_stars[cmp_star][AG_RA_RAD], catalog_stars[cmp_star][AG_DEC_RAD] )
                
                if minsep > delta_stars:
                    print 'MINSEP:%f > DELTA STARSs:%f' %(minsep, delta_stars)
                    
                    if ( config.DIFFCATALOG < delta_stars) or ( g_star[AG_NAME][0]==catalog_stars[cmp_star][AG_NAME][0]):
                        print 'diffcatalog:%f  < delta stars:%f or same name:%s:%s' %(config.DIFFCATALOG, delta_stars, g_star[AG_NAME], catalog_stars[cmp_star][AG_NAME] )
                        
                        g_star[AG_PREF]-=config.INITPREFERENCE
                        catalog_stars[cmp_star][AG_PREF]-=config.INITPREFERENCE
                        
                        print 'IN DIFFCATALOG g star pref:%f  cmp star pref:%f' %( g_star[AG_PREF], self.catalog_stars[cmp_star][AG_PREF] )
                
                    else:
                        print 'diffcatalog:%f  > delta stars:%f' %(config.DIFFCATALOG, delta_stars)    
                else:
                    print  'minsep:%f < delta stars:%f' %(self.minsep, delta_stars)   
        
        count+=1        
       #config.DIFFCATALOG


#sorted_stars=self.sort_by_preference()
#self.sort_by_preference()
    try:
        for pref, star in sort_by_preference():
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








# create vignet map
def create_vignet_map(f_select, fov_pattern):
        
    # probe position interval 
    probe_pos_delta=config.PROBE_POS_DELTA[f_select]

    vignet_map=[]   
    tmp_vig_map=[]

    # theata range 0 to 355 in degree: 5 degree each
    for angle in range(0,360,5):
        
        # % of mag is defiend depending on probe positon and theata
        mag_probe_position=config.VIGNET_TABLE[f_select][fov_pattern][angle]
        
        # the number of probe position defiend in VIGNET_TABLE 
        num_probe_position=len(mag_probe_position)-1   
    
        #print "angle:%d  probe_points:%s  num of probe points:%d"  %(angle, mag_probe_position, num_probe_position)
  
        #  for each degree, set up vignet map up to 130mm    
        for mm_delta in range(num_probe_position):
            # get mag reference values 
            current_mag=mag_probe_position[mm_delta]
            next_mag=mag_probe_position[mm_delta+1]
        
            #print "mm_delta:%d out of 27   probe_pos:%f  next pos:%f" %(mm_delta, current_mag, next_mag )
            
            # magnitude of FOV is not changed between probe positions
            if current_mag == next_mag:
                mag_val= current_mag / 100.0
                
                #print 'pos:%f = current_mag:%f / 100.0' %(mag_val, current_mag)
                
                # if mag val is 0, that can not calculate mag. 
                # therefore mag 50 is assigned. this value gives more unpreferable as a guide star                 
                if mag_val==0:
                    res=50
                    print 'pos is 0 res=50'
                else:
                    # calculate actual mag 
                    res= -2.5*math.log10(mag_val)
                    #print 'mag val:%f is not 0  res:%f' %(mag_val,res)
                
                    eqaul_flag=True
            else:
                #print 'mag_probe pos is not eqaul'
                                 
                res = (current_mag - next_mag)  / probe_pos_delta    
                #print "res:%f = currnt mag:%f - next mag:%f / probe delta:%f"  %(res, current_mag, next_mag, probe_pos_delta)
            
                eqaul_flag=False
        
            # for probe position in mm each, set up vignet map 
            for mm in range( int(probe_pos_delta) ):
                #print 'flag:%s' %(eqaul_flag)
                
                
                if eqaul_flag:
                    tmp_vig_map.append(res)
                        #print 'mag:%s' %(TMP)
                else:
                    #print 'current mag in mm:%f' %(current_mag)
                    mag_val=current_mag/100.0
                    
                    try:
                        tmp_vig_map.append( -2.5*math.log10(mag_val)   )
                    except:
                        #print 'j:%d is 130mm'
                        # in case, 130mm gets exception, assign 50 
                        tmp_vig_map.append(50)
                    current_mag-=res    

        vignet_map.append(tmp_vig_map)        

    return vignet_map


''' 
   distance on the sphere between two points in radias
   from ( az1, el1, az2, el2 )
   or two instances of same coordinate system 
   
   Copyright:: Copyright (C) 2004 Daigo Tomono <dtomono at freeshell.org>
   License::   GPL
   
   (unit rad)
'''
def delta_stars(ra0, dec0, ra1, dec1):
     
    dra, ddec0,ddec1=delta_ra_dec(ra0, dec0, ra1, dec1)
    
    #print 'dra%f  ddec0:%f  ddec1%f' %(dra, ddec0, ddec1)
     
    delta = math.acos(\
                  math.cos( ddec0 )*math.cos( ddec1 ) + \
                  math.sin( ddec0 )*math.sin( ddec1 )*math.cos( dra ) )  # distance
    
    #print 'd:%f' %(d)
    
    #if delta==0: return 'SAME_STAR'
    #else:    return d

    return delta
    

''' 
   calculate the delta ra/dec
   (unit rad)
'''
def delta_ra_dec(ra0, dec0, ra1, dec1):
    
    ddec0 = math.pi/2.0 - dec0
    ddec1 = math.pi/2.0 - dec1
    dra = ra1 - ra0

    return (dra, ddec0, ddec1)


''' 
   position angle (angle from north/zenith to east/right)
   of point1 seen from point0 in radius
   from ( az0, el0, az1, el1 )
   or two instances of same coordiante system 
   
   Copyright:: Copyright (C) 2004 Daigo Tomono <dtomono at freeshell.org>
   License::   GPL
 
   (unit rad)
'''
def pa_stars(ra0, dec0, ra1, dec1, delta=None ):
    
    # if star is the same postion as the zenith
    if math.fabs(dec0) == math.pi/2.0:
        ra0=ra1,ra1=ra0; 
        dec0=dec1,dec1=dec0;
        swap=1
    else: swap=0
    
    # if stars' delta is not figued out yet    
    if delta == None:
        delta=delta_stars(ra0, dec0, ra1, dec1)
        #print 'delta_stars called  d:%f' %(d)

    if delta==0:
        print 'pa stars d==0'     
        return  delta

   
    # find out ra/dec delta 
    dra, ddec0,ddec1=delta_ra_dec(ra0, dec0, ra1, dec1)
    #print 'dra, ddec0, ddec1', dra, ddec0, ddec1
    
    y=math.sin(ddec1)*math.sin(dra)/math.sin(delta)
    x=(math.cos(ddec1) - math.cos(ddec0)*math.cos(delta))/(math.sin(ddec0)*math.sin(delta))
    
    #print 'x:%f  y:%f' %(x, y) 
    pa = math.atan2( y, x )
    
    # turn around 180 degree
    if swap:
        #print 'swap'
        if pa < 0.0: pa+=math.pi    
        else:            pa-=math.pi
    
    #print 'pa %10.20f' %(pa)    
    return pa
    

#
#
#ra0=math.radians(359.9)  # 0 degree 
#dec0=math.radians(-0.1)  # 0 degree
#
#ra1= math.radians(0.0)   # 1degree
#dec1=math.radians(0.0)   #80 degree
#
#
#pa=pa_stars(ra0, dec0, ra1, dec1 )
#
#theata_rad=math.pi/2.0-pa
#pa_deg=math.degrees(pa)
#theata_deg=90.0-pa_deg
#
#if theata_rad < 0.0:
#    print 'theata rad:%f is less than 0' %(theata_rad)
#    theata_rad=math.pi+theata_rad
#    theata_deg=90.0+pa_deg
#    
#    
#
#r=delta_stars_rad=delta_stars(ra0, dec0, ra1, dec1)
#r_deg=math.degrees(r)
#
#print 'pa rad:%.10f   pa deg:%.10f  theata rad:%f  90-%f= %f' % (pa, pa_deg, theata_rad, pa_deg, theata_deg)
#
#print 'R rad :%20.20f   R deg :%f' %(r, r_deg)
#
#print 'deg val:%.10f' %(r_deg*theata_deg)
#


#
#print 'X degree :%f  Y degree :%f' %( r_deg*math.cos(theata_rad), r_deg*math.sin(theata_rad)   )
#
#print math.radians( r_deg*math.cos(theata_rad)  ), math.radians(  r_deg*math.sin(theata_rad)  )
#
#print 'X rad :%f  Y rad :%f' %( r*math.cos(theata_rad), r*math.sin(theata_rad)   )























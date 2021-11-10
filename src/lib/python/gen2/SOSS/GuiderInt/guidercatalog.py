#! /usr/bin/env python

import cx_Oracle
import math

import astro.radec as radec


ora_userName = 'catalog'
ora_password = 'naojorg'
ora_TNS1      = '(DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(PROTOCOL=TCP)(HOST=mdbs1)(PORT=1521)))(CONNECT_DATA=(SID=catalog)))'
ora_TNS2     = '(DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(PROTOCOL=TCP)(HOST=mdbs2)(PORT=1521)))(CONNECT_DATA=(SID=catalog)))'


degPerHMSHour = 15.0      #360/24
degPerHMSMin  = 0.25      #360.0/24/60
degPerHMSSec  = 1.0/240.0 #360.0/24/60/60

HMSHourPerDeg = 1.0/15.0
HMSMinPerDeg  = 4.0
HMSSecPerDeg  = 240.0


'''
   keys to create a list of stars selected from catalog   
'''
KEYS=['NAME', 'RA_RAD', 'DEC_RAD', 'MAG', 'FLAG', 'R_RAD', 'PREF']


def search_catalog(ra_deg, dec_deg, fov, limitmag):

    # connect to ORACLE DB 
    try:
        connection = cx_Oracle.connect(ora_userName, ora_password, ora_TNS1)
        cursor = connection.cursor()
    except:
        try:
            connection = cx_Oracle.connect(ora_userName, ora_password, ora_TNS2)
            cursor = connection.cursor()
            print 'connection to ORA DB1 failed: try to access DB2'
        except:
            print 'connection to ORA DB failed'
            pass
            # need to report ??????
        
    # find out ra/dec search range    
    (ra)= ra_min_max(ra_deg, dec_deg, fov)
    (dec)=dec_min_max(dec_deg, fov)
    #(ra,dec)=get_ra_dec_range(ra_lower, ra_upper, dec_lower, dec_upper)
        
    # find out mag range
    (mag) = mag_min_max(limitmag) 
    
    #print "catalog ra, dec, mag", ra, dec, mag

    usnob=search_usnob( ra, dec, mag, cursor)
    saoj200=search_saoj2000( ra, dec, mag, cursor)
    gsc=search_gsc( ra, dec, mag, cursor)   
    
    # close connection
    try:
        cursor.close()
        connection.close() 
    except:
        print 'connection close to ORA DB failed '
        pass
        # need to report    
    
    return usnob+gsc+saoj200


def search_usnob( ra, dec, mag, cursor):
    
    #(ra,dec)=StarList.get_ra_dec_range(ra_lower, ra_upper, dec_lower, dec_upper)
    mag_crit_template = " (r1mag between %f and %f) "
    sql_where=generate_sql(ra, dec, mag, mag_crit_template)
        
    '''  search USNOB table '''
    try:
        cursor.execute("SELECT NAME, RA, DEC, B1MAG, B2MAG, R1MAG, R2MAG, IMAG, FLAGSGB1, FLAGSGB2,  FLAGSGR1, FLAGSGR2 FROM USNOB_STAGE %s "%(sql_where))              
        row = cursor.fetchone()
    except:
        pass
        # need to report ?????
     
    usnob=[]
    
    # if no star is found, tell no star found.  otherwise, display the result
    if row == None:
        pass
    else:
        while row != None:
            
            '''
              row[0]   [1] [2]  [3]    [4]    [5]    [6]    [7]   [8]       [9]       [10]      [11]        
                name   ra  dec  b1mag  b2mag  r1mag  r2mag  imag  flagsgb1  flagsgb2  flagsgr1  flagsgr2  
            '''
            name=row[0]; ra_rad=math.radians(row[1]); dec_rad=math.radians(row[2]);
                                   
            '''
               b1mag and b2mag are used to calculate bmag values in takasa-san's star list program
               but this calculated value is not used for star selection.  '''
            #                  b1mag   b2mag
            #  bmag=usnob_mag( row[3], row[4] )
                        
            '''  rmag is used as star mag and is the one of reference for selection a guide star  '''                  
            #               r1mag   r2mag
            rmag=usnob_mag( row[5], row[6] )
                       
            '''
               imag is used to calculate b_r, r_i values in takasa-san's star list program
               but those calculated values are not used for star selection.  '''    
            # if imag > 25.0: imag=99.9
            
            #                flagsgb1 flagsgb2 flagsgr1 flagsgr2
            flag=usnob_flag( row[8],  row[9],  row[10], row[11] )
                       
            #print "USNOB name:%s ra:%f dec:%f  rmag:%f  flag:%f "  %( name, ra_rad, dec_rad, rmag, flag)
                                  
            '''  values b_r and r_i are not used for ag selection but implemented in takata-san's ag auto list  '''
            # if bmag < 99.9 and rmag < 99.9:  b_r = bmag-rmag
            # else:                            b_r = 99.9
            # if imag < 99.9 and rmag < 99.9:  r_i = rmag-imag
            # else:                            r_i = 99.9
                 
            '''  name, ra(rad), dec(rad), mag, flag, delta, initail preference  '''
            vals=[name,ra_rad, dec_rad, rmag, flag, None, 10]        
            
            '''  make usnob star dictionary  '''
            usnob.append( dict( zip(KEYS, vals))  )

            row = cursor.fetchone()
    
    return usnob


def search_gsc( ra, dec, mag, cursor ):
    
       
    mag_crit_template = " (mag between %f and %f) "
    sql_where=generate_sql(ra, dec, mag, mag_crit_template)
    
       
    '''  search GSC  '''
    try:
        cursor.execute("SELECT RA, DEC, MAG, CLASS FROM GSC %s "%(sql_where))              
        row = cursor.fetchone()
    except:
        pass
        #####  TO DO 
        #####  report error
        
    gsc=[]
    
    # if no star is found, tell no star found.  otherwise, display the result
    if row == None:
        pass
    else:
        while row != None:
           
            '''  row[0]  [1]   [2]  [3]            
                    ra   dec   mag  class  '''
            
            '''
               convert ra  degree to hour:min:sec
               convert dec degree to deg:min:sec   '''
            (rah, ramin, rasec) = radec.degToHms(row[0])
            rahms= radec.raHmsToString(rah, ramin, rasec)
            (sign, decd, decmin, decsec) = radec.degToDms(row[1])
            decdms= radec.decDmsToString(sign, decd, decmin, int(decsec))

            '''  make GSC star name  '''
            name='GSC' + rahms + decdms
            
            '''
               covert ra deg to ra rad
               covert dec deg to dec rad  '''
            ra_rad=math.radians(row[0]); dec_rad=math.radians(row[1]);
            
            '''  set up flag  '''
            #             class
            flag=gsc_flag(row[3])
                        
            #print "GSC name:%s ra:%f dec:%f  mag:%f  flag:%d "  %( name, ra_rad, dec_rad, row[2], flag)
            
            '''  name, ra(rad), dec(rad), mag, flag,  stars delta, initail preference  '''
            vals=[name,ra_rad, dec_rad, row[2], flag, None, 10]        
            
            '''  make gsc star dictionary  '''
            gsc.append( dict( zip(KEYS, vals))  )
            
            row = cursor.fetchone()
    
    return gsc  
        


def search_saoj2000( ra, dec, mag, cursor):
     
    mag_crit_template = " (mag between %f and %f) "
    sql_where=generate_sql(ra, dec, mag, mag_crit_template)
     
        
    '''  search SAOJ2000 table  '''
    try:
        cursor.execute("SELECT NAME, RA, DEC, MAG, TYPE FROM SAOJ2000 %s "%(sql_where))              
        row = cursor.fetchone()
    except:
        pass
        # need to report ????
    
    saoj2000=[]
    
    # if no star is found, tell no star found.  otherwise, display the result
    if row == None:
        pass
    else:
        while row != None:
            
            '''  row[0]   [1]  [2]   [3]  [4]          
                 name     ra   dec   mag  type '''
            
            ''' 
               covert ra deg to ra rad
               covert dec deg to dec rad  '''
            name=row[0]; ra_rad=math.radians(row[1]); dec_rad=math.radians(row[2]);            
                                 
            #              type
            flag=saoj2000_color(row[4])

            #print "SAO name:%s ra:%f dec:%f  mag:%f  flag:%f "  %( name, ra_rad, dec_rad, row[3], flag)
            
            '''  name, ra(rad), dec(rad), mag, flag, star delta, initail preference  '''
            vals=[name, ra_rad, dec_rad, row[3], flag, None, 10]     
            
            '''  make sao star dictionary  '''
            saoj2000.append( dict( zip(KEYS, vals ))  )
                      
            row = cursor.fetchone()
    
    return saoj2000
    
    
    
def gsc_flag(cl):
    if cl==0:    return 2    
    elif cl==3:  return -1
    else:        return -9

   
def saoj2000_color(type):
    
    if   type.startswith('A'):  return 0.1
    elif type.startswith('B'):  return -0.2
    elif type.startswith('O'):  return -0.4
    elif type.startswith('F'):  return 0.4
    elif type.startswith('G'):  return 0.6
    elif type.startswith('K'):  return 1.1
    elif type.startswith('M'):  return 1.5
    else:                       return 0.0
    
def usnob_flag( flagb1, flagb2, flagr1, flagr2 ):
    
    if flagr1 <= 11 and flagr2 <= 11:   flag=(flagr1+flagr2)//2.0
    elif flagr1 > 11 and flagr2 <= 11:  flag=flagr2
    elif flagr1 <= 11 and flagr2 > 11:  flag=flagr1
    else:
        if flagb1 <= 11 and flagb2 <= 11:   flag=(flagb1+flagb2)//2.0
        elif flagb1 > 11 and flagb2 <= 11:  flag=flagb2
        elif flagb1 <= 11 and flagb2 > 11:  flag=flagb1
        else:                               flag=0
   
    '''  Transforming Flag to Classical USNO-A1.0 Yasuda Version  '''
    if flag <= 11 and flag >=8:   flag=1
    elif flag <= 3 and flag >=0:  flag=7
    else:                         flag=10-flag
    
    return flag

def usnob_mag(mag1, mag2):
    if mag1 > 25.0 and mag2 > 25.0:
        mag=99.9
    elif mag1 > 25.0 and mag2 <= 25.0:
        mag=mag2
    elif mag1 <= 25.0 and mag2 > 25.0:
        mag=mag1
    else:
        mag=(mag1+mag2)/2.0
        
    return mag                 


def mag_min_max(limitmag):
       
    if limitmag > 0:
        max_mag=limitmag
        min_mag=0
    else:
        min_mag=limitmag
        max_mag=0    
 
    return (min_mag, max_mag) 


def generate_sql(ra, dec, mag, mag_crit_template):
    ra_crit_template  = " (ra between %f and %f) "
    dec_crit_template = " (dec between %f and %f) "
    
    ra_crit_list = []
    for aTuple in ra:
        ra_crit_list.append(ra_crit_template % aTuple)

    ra_crit  = " or ".join(ra_crit_list)
    dec_crit = dec_crit_template % dec
    mag_crit=mag_crit_template %mag 
    #print 'generate sql', ra_crit, dec_crit, mag_crit
    
    criteria = "where (%s) and %s and %s" %(ra_crit, dec_crit, mag_crit)
    
    #print 'sql where statment', criteria
    return criteria


def ra_min_max(ra_center, dec_center, ra_range):
    ra_range = ra_range/math.cos(math.radians(dec_center))
    
    return get_ra_range(ra_center - ra_range, ra_center + ra_range)

def dec_min_max(dec_center, dec_range):
   
    
    return get_dec_range(dec_center - dec_range, dec_center + dec_range)    

# Returns tuple of tuples of ra_min and ra_max
def get_ra_range(ra_min, 
                 ra_max):
      # Convert RA (degree) to positive betwen 0 and 360
      ra_min = ra_min % 360.0
      ra_max = ra_max % 360.0
      if ra_min > ra_max:
          return ((ra_min, 360.0), (0.0, ra_max),)
      else:
          return ((ra_min, ra_max),)


def get_dec_range(dec_min,
                  dec_max):
      # not a good logic but we need to be compatible with
      # the old software
      if dec_max > 89.8:
         return (min(dec_min, 180.0 - dec_max), 90.0)

      if dec_min < -89.8:
         return (-90.0, max(dec_max, -(180.0 + dec_min)))

      return (dec_min, dec_max)

def get_ra_dec_range(ra_min, ra_max,
                     dec_min, dec_max):
       if dec_max > 89.8 or dec_min < -89.8:
           ra = ((0, 360.0),)
       else:
           ra = get_ra_range(ra_min, ra_max)
        
       dec = get_dec_range(dec_min, dec_max)
       return (ra, dec)


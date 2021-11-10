OBS has the following kinds of RPC messages:

'CT' messages:
  - initiate a command to OSS from (obcp, etc.)
  Subtypes:
  'CD' subtype:
    - initiating command from remote entity (e.g. obcp)
    - payload is command,arg1,arg2,... (??), e.g.:
(from obs)
EXEC MOIRCS HAWAII2 MODE=WIPE DATTYPE=NOP FRAME=NOP NFRAME=NOP
INTTIME=NOP NADD=NOP AREA1=NOP AREA2=NOP PRD1MINV=NOP PRD1MINH=NOP
PRD1RNGV=NOP PRD1RNGH=NOP PRD2MINV=NOP PRD2MINH=NOP PRD2RNGV=NOP
PRD2RNGH=NOP READCH=NOP SMPMODE=NOP NSAMPLE=NOP NRESET=NOP NDUMMY=NOP
SPEED=NOP SHUTTER=NOP
  
(to obs)
STATUS,$FITS.SBR.DOM-WND $FITS.SBR.OUT-WND $FITS.SBR.DOM-TMP
$FITS.SBR.OUT-TMP $FITS.SBR.DOM-HUM $FITS.SBR.OUT-HUM $FITS.SBR.DOM-PRS
$FITS.SBR.OUT-PRS $FITS.SBR.WEATHER $FITS.SBR.SEEING $FITS.SBR.AIRMASS
$FITS.SBR.AZIMUTH $FITS.SBR.ALTITUDE $FITS.SBR.RA $FITS.SBR.DEC
$TSCL.WINDD 

  'AB' subtype:
    - ack reply from SOSS (i.e. obs)
    - payload is "%d,%d" (seq_num, result)
      - Result code interpretation:
        0: OK
        1: Packet format error
        2: Internal error
        3: Sequence number mismatch

  'EN' subtype:
    - end command notification from SOSS (i.e. obs)
    - payload is (seq_num, status, result) (result has a variety of
       formats), e.g.: 
(to obs)
00000001,   0,COMPLETE    ,EXEC MOIRCS HAWAII2 MODE=WIPE DATTYPE=NOP
FRAME=NOP NFRAME=NOP INTTIME=NOP NADD=NOP AREA1=NOP AREA2=NOP
PRD1MINV=NOP PRD1MINH=NOP PRD1RNGV=NOP PRD1RNGH=NOP PRD2MINV=NOP
PRD2MINH=NOP PRD2RNGV=NOP PRD2RNGH=NOP READCH=NOP SMPMODE=NOP
NSAMPLE=NOP NRESET=NOP NDUMMY=NOP SPEED=NOP SHUTTER=NOP 

(from obs)
00000001,   0,COMPLETE,0.00          277.95        ...

    - initial value is separated from rest of return values by a comma,
      but rest of values are packed, not comma-separated (they may be
      padded). 

    - Result code interpretation:
      0: OK
      1: Packet format error
      2: Internal error

'FT' messages:
  - handle commands from OSS to STARS hosts (s1/s2, etc.)
  Subtypes:
  'FS' subtype:
    - initiating command to STARS (e.g. s1)
    - payload is <path to fits file>,<fits file size in bytes>,<frame
        number>,<prop-id>,<>,<>,<path to
        index file>,<index file size in bytes>

send    20060616051848.930 OK        241,20060616051848.912,SUBARUV1,   33510,obc1-a2 ,10002,     ,     ,s01-a2  ,FT,FS,       113,                           /mdata/fits/obcp17/MCSA00035560.fits,16796160,MCSA00035560,o03020,sdata01,S01,/mdata/index/MCSA00035560.index,400
recieve 20060616051848.938 OK        141,20060616051848.930,SUBARUV1,10011878,s01-a2  ,10002,     ,     ,obc1-a2 ,FT,AB,        13,                              33510,   0
recieve 20060616051850.550 OK        151,20060616051850.544,SUBARUV1,10011879,s01-a2  ,10002,     ,     ,obc1-a2 ,FT,FE,        23,                              33510,   0,   0,   0
send    20060616051934.524 OK        240,20060616051934.503,SUBARUV1,   33524,obc1-a2 ,10002,     ,     ,s01-a2  ,FT,FS,       112,                           /mdata/fits/obcp13/SKYA00637498.fits,1005120,SKYA00637498,o98017,sdata01,S01,/mdata/index/SKYA00637498.index,400
recieve 20060616051934.531 OK        141,20060616051934.523,SUBARUV1,10011880,s01-a2  ,10002,     ,     ,obc1-a2 ,FT,AB,        13,                              33524,   0
recieve 20060616051935.208 OK        151,20060616051935.200,SUBARUV1,10011881,s01-a2  ,10002,     ,     ,obc1-a2 ,FT,FE,        23,                              33524,   0,   0,   0
send    20060616053524.980 OK        241,20060616053524.966,SUBARUV1,   33652,obc1-a2 ,10002,     ,     ,s01-a2  ,FT,FS,       113,                           /mdata/fits/obcp17/MCSA00035565.fits,16796160,MCSA00035565,o03020,sdata01,S01,/mdata/index/MCSA00035565.index,400
recieve 20060616053524.988 OK        141,20060616053524.981,SUBARUV1,10011882,s01-a2  ,10002,     ,     ,obc1-a2 ,FT,AB,        13,                              33652,   0
recieve 20060616053527.169 OK        151,20060616053527.162,SUBARUV1,10011883,s01-a2  ,10002,     ,     ,obc1-a2 ,FT,FE,        23,                              33652,   0,   0,   0
send    20060616061811.412 OK        241,20060616061811.383,SUBARUV1,   34014,obc1-a2 ,10002,     ,     ,s01-a2  ,FT,FS,       113,                           /mdata/fits/obcp17/MCSA00035590.fits,16796160,MCSA00035590,o03020,sdata01,S01,/mdata/index/MCSA00035590.index,400
recieve 20060616061811.420 OK        141,20060616061811.412,SUBARUV1,10011884,s01-a2  ,10002,     ,     ,obc1-a2 ,FT,AB,        13,                              34014,   0
recieve 20060616061813.437 OK        151,20060616061813.430,SUBARUV1,10011885,s01-a2  ,10002,     ,     ,obc1-a2 ,FT,FE,        23,                              34014,   0,   0,   0

FOR LOG FILES:
send    20060616075340.402 OK        240,20060616075340.363,SUBARUV1,   34724,obc1-a2 ,10002,     ,     ,s01-a2  ,FT,FS,       112,                           /oss_data/OBS_NFS/ANAD20060615,1942656,ANAD20060615,summitlog,sdata01,S01,/oss_data/OBS_NFS/ANAD20060615.inf,224
recieve 20060616075340.409 OK        141,20060616075340.404,SUBARUV1,10011896,s01-a2  ,10002,     ,     ,obc1-a2 ,FT,AB,        13,                              34724,   0
recieve 20060616075341.610 OK        151,20060616075341.605,SUBARUV1,10011897,s01-a2  ,10002,     ,     ,obc1-a2 ,FT,FE,        23,                              34724,   0,   0,   0
send    20060616075342.943 OK        246,20060616075342.934,SUBARUV1,   34725,obc1-a2 ,10002,     ,     ,s01-a2  ,FT,FS,       118,                           /oss_data/OBS_NFS/ANAQMCS20060615,5760,ANAQMCS20060615,summitlog,sdata01,S01,/oss_data/OBS_NFS/ANAQMCS20060615.inf,233
recieve 20060616075342.950 OK        141,20060616075342.945,SUBARUV1,10011898,s01-a2  ,10002,     ,     ,obc1-a2 ,FT,AB,        13,                              34725,   0
recieve 20060616075343.593 OK        151,20060616075343.589,SUBARUV1,10011899,s01-a2  ,10002,     ,     ,obc1-a2 ,FT,FE,        23,                              34725,   0,   0,   0
send    20060616075344.965 OK        252,20060616075344.956,SUBARUV1,   34727,obc1-a2 ,10002,     ,     ,s01-a2  ,FT,FS,       124,                           /oss_data/OBS_NFS/AOSS000120060615,1363382,AOSS000120060615,summitlog,sdata01,S01,/oss_data/OBS_NFS/AOSS000120060615.inf,236

...

send    20060616081626.601 OK        274,20060616081626.593,SUBARUV1,   34937,obc1-a2 ,10002,     ,     ,s01-a2  ,FT,FS,       146,                           /oss_data/OBS_NFS/todaytmp.d/SCH_20060616.log,1574359,SCH_20060616.log,summitlog,sdata01,S01,/oss_data/OBS_NFS/todaytmp.d/SCH_20060616.log.inf,247
recieve 20060616081626.607 OK        141,20060616081626.602,SUBARUV1,10012048,s01-a2  ,10002,     ,     ,obc1-a2 ,FT,AB,        13,                              34937,   0
recieve 20060616081627.225 OK        151,20060616081627.220,SUBARUV1,10012049,s01-a2  ,10002,     ,     ,obc1-a2 ,FT,FE,        23,                              34937,   0,   0,   0
send    20060616081630.458 OK        236,20060616081630.447,SUBARUV1,   34938,obc1-a2 ,10002,     ,     ,s01-a2  ,FT,FS,       108,                           /oss_data/OBS_NFS/todaytmp.d/ENDLOG,0,ENDLOG,summitlog,sdata01,S01,/oss_data/OBS_NFS/todaytmp.d/ENDLOG.inf,0
recieve 20060616081630.464 OK        141,20060616081630.459,SUBARUV1,10012050,s01-a2  ,10002,     ,     ,obc1-a2 ,FT,AB,        13,                              34938,   0
recieve 20060616081630.676 OK        151,20060616081630.670,SUBARUV1,10012051,s01-a2  ,10002,     ,     ,obc1-a2 ,FT,FE,        23,                              34938,   0,   0,   0
send    20060616131815.146 OK        214,20060616131815.122,SUBARUV1,   36750,obc1-a2 ,10002,     ,     ,s01-a2  ,FT,FS,        86,                           /oss_data/OBS_NFS/ENDLOG,0,ENDLOG,summitlog,sdata02,S01,/oss_data/OBS_NFS/ENDLOG.inf,0
recieve 20060616131815.154 OK        141,20060616131815.148,SUBARUV1,10012052,s01-a2  ,10002,     ,     ,obc1-a2 ,FT,AB,        13,                              36750,   0
recieve 20060616131815.561 OK        151,20060616131815.557,SUBARUV1,10012053,s01-a2  ,10002,     ,     ,obc1-a2 ,FT,FE,        23,                              36750,   0,   0,   0
send    20060616162055.240 OK        214,20060616162055.224,SUBARUV1,   37896,obc1-a2 ,10002,     ,     ,s01-a2  ,FT,FS,        86,                           /oss_data/OBS_NFS/ENDLOG,0,ENDLOG,summitlog,sdata02,S01,/oss_data/OBS_NFS/ENDLOG.inf,0
recieve 20060616162055.248 OK        141,20060616162055.242,SUBARUV1,10012054,s01-a2  ,10002,     ,     ,obc1-a2 ,FT,AB,        13,                              37896,   0
recieve 20060616162055.507 OK        151,20060616162055.503,SUBARUV1,10012055,s01-a2  ,10002,     ,     ,obc1-a2 ,FT,FE,        23,                              37896,   0,   0,   0


  'AB' subtype:
    - ack reply from SOSS (i.e. obs)
    - payload is "%d,%d" (seq_num, result)

  'FE' subtype:
    - end command notification from SOSS (i.e. obs)
    - payload is (seq_num, result, val,val1 val2,...) (??), e.g.:

    - initial value is separated from rest of return values by a comma,
      but rest of values are packed, not comma-separated (they may be padded).

'ST' messages:
  - used in the status distribution subsystem
  Subtype:
  'SD' subtype (only one):
    - used to transmit a block of raw status table
    - payload is "%-8.8s,%s" (table name, status data)

(example)
0000004848,20051020000001.765,SUBARUV1,   56137,mobs1   , 5000,  300,  300,mobs1   ,ST,SD,      4720,                           OBS1C   ,20051020000001.765,R,         ; 5000,20051020000001.765,R,
  26060, ; 5001,20051020000001.035,R,     26183, ;     ,                  , ,          , ;     ,
               , ,          , ;     ,                  , ,          , ;     ,                  , ,
         , ; 5002,20051019235952.325,R,     26121, ; ...    

---------------------------------------------------------------
OCS side:		    INST side:

5 (kinds of) servers	    3 servers
3 (kinds of) clients	    5 clients
5+ protocols

OBS                         OBCP
---                         ----
OSSC_ComClnt (?)	    -> DAQtkCmdRcv
OSSC_ComSvc (?)		    <- DAQtkCmdSnd

OSSC_ComClnt (?)	    -> DAQtkThroughRcv
OSSC_ComSvc (?)		    <- DAQtkThroughSnd

OSSC_ComClnt (?)	    -> DAQtkGetRcv
OSSC_ComSvc (?)		    <- DAQtkGetSnd
OSSC_ComSvc (?)		    <- DAQtkStatSnd

OBC
---
DAQobcComRpcSnd		    -> DAQtkDatRcv
DAQobcGetRcv		    <- DAQtkDatSnd
DAQobcGetFitsRcv	    <- DAQtkDatSndMem


PROGRAM NUMBERS:
/* Status TSCS (udp) */
0x20000013, 0x21030126, 0x21030226, 0x21030326, 0x21030426, 0x21030526,

/* Status TSCL (udp) */
0x20000014, 0x21030127, 0x21030227, 0x21030327, 0x21030427, 0x21030527,

/* Status TSCV (tcp) */
0x20000015, 0x21030128, 0x21030228, 0x21030328, 0x21030428, 0x21030528,

OBS status monitoring units correspond to:
0x2103002x = 1-5):
i.e. 0x21030021, 0x21030022, 0x21030023, 0x21030024, 0x21030025,
Q: how does instrument know which one to use?

What are these?
   SEND        RCV (perspective of OBS)
0x21010001, 0x21020001,  /* OBS -> OSSA0  */
0x21010101, 0x21020101,  /* OBS -> OSSA1  */
0x21010201, 0x21020201,  /* OBS -> OSSA2  */
0x21010301, 0x21020301,  /* OBS -> OSSA3  */
0x21010401, 0x21020401,  /* OBS -> OSSA4  */
0x21010501, 0x21020501,  /* OBS -> OSSA5  */
0x21010601, 0x21020601,  /* OBS -> OSSA6  */
0x21010701, 0x21020701,  /* OBS -> OSSA7  */
0x21010801, 0x21020801,  /* OBS -> OSSA8  */
0x21010901, 0x21020901,  /* OBS -> OSSA9  */
0x21010002, 0x21020002,  /* OBS -> OSSB0  */
0x21010102, 0x21020102,  /* OBS -> OSSB1  */
0x21010202, 0x21020202,  /* OBS -> OSSB2  */
0x21010302, 0x21020302,  /* OBS -> OSSB3  */
0x21010402, 0x21020402,  /* OBS -> OSSB4  */
0x21010502, 0x21020502,  /* OBS -> OSSB5  */
0x21010602, 0x21020602,  /* OBS -> OSSB6  */
0x21010702, 0x21020702,  /* OBS -> OSSB7  */
0x21010802, 0x21020802,  /* OBS -> OSSB8  */
0x21010902, 0x21020902,  /* OBS -> OSSB9  */

OBS <--> OBCP
   SEND        RCV (perspective of OBS)
0x21010103, 0x21020103,  /* OBS -> OBCP1  */
0x21010203, 0x21020203,  /* OBS -> OBCP2  */
0x21010303, 0x21020303,  /* OBS -> OBCP3  */
0x21010403, 0x21020403,  /* OBS -> OBCP4  */
0x21010503, 0x21020503,  /* OBS -> OBCP5  */
0x21010603, 0x21020603,  /* OBS -> OBCP6  */
0x21010703, 0x21020703,  /* OBS -> OBCP7  */
0x21010803, 0x21020803,  /* OBS -> OBCP8  */
0x21010903, 0x21020903,  /* OBS -> OBCP9  */
0x21010a03, 0x21020a03,  /* OBS -> OBCP10 */
0x21010b03, 0x21020b03,  /* OBS -> OBCP11 */
0x21010c03, 0x21020c03,  /* OBS -> OBCP12 */
0x21010d03, 0x21020d03,  /* OBS -> OBCP13 */
0x21010e03, 0x21020e03,  /* OBS -> OBCP14 */
0x21010f03, 0x21020f03,  /* OBS -> OBCP15 */
0x21011003, 0x21021003,  /* OBS -> OBCP16 */
0x21011103, 0x21021103,  /* OBS -> OBCP17 */
0x21011203, 0x21021203,  /* OBS -> OBCP18 */
0x21011303, 0x21021303,  /* OBS -> OBCP19 */
0x21011403, 0x21021403,  /* OBS -> OBCP20 */
0x21011503, 0x21021503,  /* OBS -> OBCP21 */
0x21011603, 0x21021603,  /* OBS -> OBCP22 */
0x21011703, 0x21021703,  /* OBS -> OBCP23 */
0x21011803, 0x21021803,  /* OBS -> OBCP24 */
0x21011903, 0x21021903,  /* OBS -> OBCP25 */
0x21011a03, 0x21021a03,  /* OBS -> OBCP26 */
0x21011b03, 0x21021b03,  /* OBS -> OBCP27 */
0x21011c03, 0x21021c03,  /* OBS -> OBCP28 */
0x21011d03, 0x21021d03,  /* OBS -> OBCP29 */
0x21011e03, 0x21021e03,  /* OBS -> OBCP30 */
0x21011f03, 0x21021f03,  /* OBS -> OBCP31 */
0x21012003, 0x21022003,  /* OBS -> OBCP32 */


0x21010011, 0x21020011,  /* OWS,OBC,VGW,OBCP -> OBS(Executer) */
0x21010012, 0x21020012,  /* OWS,OBC,VGW,OBCP -> OBS(Distributor) */


/* ComC toward TSC (tcp) */
0x20000011, 0x21010104, 0x21010204, 0x21010304, 0x21010404, 0x21010504
/* ComR from TSC (tcp) */
0x20000012, 0x21020104, 0x21020204, 0x21020304, 0x21020404, 0x21020504


OBC
---
For DAQobcGetRcv are 0x2101xx41, where 'xx' = 01-is the number of the obcp
IN HEX (e.g. IRCS=0x21010141, COMICS=0x21010741, FLDMON=0x21011341, etc)

For DAQobcGetFitsRcv are 0x2101xx51



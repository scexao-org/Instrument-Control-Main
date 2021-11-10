Third hex digit from end encodes sending/receiving channel:
DAQobcSndStartRcv.x: 0x22000x01 (0x22000101, 0x22000201, ...)
DAQobcSndEndRcv.x:   0x22000x02 (0x22000102, 0x22000202, ...)


From obc1:/app/OBC/log/s1.log:
send    20051116062916.253 OK        240,20051116062916.238,SUBARUV1,  246934,obc1-a1 ,10002,     ,     ,s01-a1  ,FT,FS,       112,                           /mdata/fits/obcp03/CIAA00156042.fits,4216320,CIAA00156042,o05321,sdata01,S01,/mdata/index/CIAA00156042.index,400
recieve 20051116062916.262 OK        141,20051116062916.251,SUBARUV1,   61564,s01-a1  ,10002,     ,     ,obc1-a1 ,FT,AB,        13, 246934,   0
recieve 20051116062917.034 OK        151,20051116062917.017,SUBARUV1,   61565,s01-a1  ,10002,     ,     ,obc1-a1 ,FT,FE,        23, 246934,   0,   0,   0


From obc1:/app/OBC/log/s2.log:
send    20051111213837.247 OK        240,20051111213837.225,SUBARUV1,  189925,obc1-a2 ,10002,     ,     ,s01-a2  ,FT,FS,       112,                           /mdata/fits/obcp13/SKYA00556280.fits,1005120,SKYA00556280,o98017,sdata01,S01,/mdata/index/SKYA00556280.index,400
recieve 20051111213837.261 OK        141,20051111213837.248,SUBARUV1,10009064,s01-a2  ,10002,     ,     ,obc1-a2 ,FT,AB,        13, 189925,   0
recieve 20051111213837.884 OK        151,20051111213837.879,SUBARUV1,10009065,s01-a2  ,10002,     ,     ,obc1-a2 ,FT,FE,        23, 189925,   0,   0,   0


From mobc1:/app/OBC/log/s5.log:
send    20051027120814.150 OK        239,20051027120814.137,SUBARUV1,    9423,mobc1-a1,10002,     ,     ,s02-a1  ,FT,FS,       111,                           /mdata/fits/obcp09/SUKA90207973.fits,256320,SUKA90207973,o98003,sdata04,S01,/mdata/index/SUKA90207973.index,400
recieve 20051027120814.159 OK        141,20051027120814.237,SUBARUV1,40000138,s02-a1  ,10002,     ,     ,mobc1-a1,FT,AB,        13,
  9423,   0
recieve 20051027120814.688 OK        151,20051027120814.770,SUBARUV1,40000139,s02-a1  ,10002,     ,     ,mobc1-a1,FT,FE,        23,
  9423,   0,   0,   0


From mobc1:/app/OBC/log/s6.log:
(does this show examples of multiple outstanding requests?)

send    2005101211
4111.639 NG        237,20051012114011.618,SUBARUV1,      25,mobc1-a2,10002,
,     ,s02-a2  ,FT,FS,       109,                           /mdata/fits/vgw/VGWA90053312.fits,1059840,VGWA90053312,o98016,sdata04,S01,/mdata/index/VGWA90053312.index,400
send    20051012114211.669 NG        237,20051012114111.656,SUBARUV1,      33,mobc1-a2,10002,     ,     ,s02-a2  ,FT,FS,       109,                           /mdata/fits/vgw/VGWA90053313.fits,1059840,VGWA90053313,o98016,sdata04,S01,/mdata/index/VGWA90053313.index,400
send    20051012114614.020 NG        237,20051012114514.008,SUBARUV1,      63,mobc1-a2,10002,     ,     ,s02-a2  ,FT,FS,       109,                           /mdata/fits/vgw/VGWA90053315.fits,1059840,VGWA90053315,o98016,sdata04,S01,/mdata/index/VGWA90053315.index,400
send    20051012114714.060 NG        237,20051012114614.038,SUBARUV1,      79,mobc1-a2,10002,     ,     ,s02-a2  ,FT,FS,       109,                           /mdata/fits/vgw/VGWA90053317.fits,1059840,VGWA90053317,o98016,sdata04,S01,/mdata/index/VGWA90053317.index,400
send    20051012114814.100 NG        237,20051012114714.077,SUBARUV1,      87,mobc1-a2,10002,     ,     ,s02-a2  ,FT,FS,       109,                           /mdata/fits/vgw/VGWA90053319.fits,1059840,VGWA90053319,o98016,sdata04,S01,/mdata/index/VGWA90053319.index,400
send    20051012115604.202 NG        237,20051012115504.191,SUBARUV1,     140,mobc1-a2,10002,     ,     ,s02-a2  ,FT,FS,       109,                           /mdata/fits/vgw/VGWA90053321.fits,1059840,VGWA90053321,o98016,sdata04,S01,/mdata/index/VGWA90053321.index,400
send    20051012115754.543 NG        237,20051012115654.524,SUBARUV1,     157,mobc1-a2,10002,     ,     ,s02-a2  ,FT,FS,       109,                           /mdata/fits/vgw/VGWA90053323.fits,1059840,VGWA90053323,o98016,sdata04,S01,/mdata/index/VGWA90053323.index,400
send    20051012133639.746 NG        237,20051012133539.738,SUBARUV1,     782,mobc1-a2,10002,     ,     ,s02-a2  ,FT,FS,       109,                           /mdata/fits/vgw/VGWA90053325.fits,1059840,VGWA90053325,o98016,sdata03,S01,/mdata/index/VGWA90053325.index,400
send    20051012133739.778 NG        237,20051012133639.767,SUBARUV1,     796,mobc1-a2,10002,     ,     ,s02-a2  ,FT,FS,       109,                           /mdata/fits/vgw/VGWA90053327.fits,1059840,VGWA90053327,o98016,sdata03,S01,/mdata/index/VGWA90053327.index,400
send    20051012133839.816 NG        237,20051012133739.801,SUBARUV1,     814,mobc1-a2,10002,     ,     ,s02-a2  ,FT,FS,       109,                           /mdata/fits/vgw/VGWA90053329.fits,1059840,VGWA90053329,o98016,sdata03,S01,/mdata/index/VGWA90053329.index,400
send    20051012133939.847 NG        237,20051012133839.831,SUBARUV1,     822,mobc1-a2,10002,     ,     ,s02-a2  ,FT,FS,       109,                           /mdata/fits/vgw/VGWA90053331.fits,1059840,VGWA90053331,o98016,sdata03,S01,/mdata/index/VGWA90053331.index,400
send    20051012134139.907 NG        237,20051012134039.891,SUBARUV1,     848,mobc1-a2,10002,     ,     ,s02-a2  ,FT,FS,       109,                           /mdata/fits/vgw/VGWA90053335.fits,1059840,VGWA90053335,o98016,sdata03,S01,/mdata/index/VGWA90053335.index,400
send    20051012134239.937 NG        237,20051012134139.923,SUBARUV1,     856,mobc1-a2,10002,     ,     ,s02-a2  ,FT,FS,       109,                           /mdata/fits/vgw/VGWA90053337.fits,1059840,VGWA90053337,o98016,sdata03,S01,/mdata/index/VGWA90053337.index,400
send    20051012135759.891 NG        237,20051012135659.876,SUBARUV1,     958,mobc1-a2,10002,     ,     ,s02-a2  ,FT,FS,       109,                           /mdata/fits/vgw/VGWA90053341.fits,1059840,VGWA90053341,o98016,sdata03,S01,/mdata/index/VGWA90053341.index,400
send    20051012145529.841 NG        237,20051012145429.825,SUBARUV1,    1312,mobc1-a2,10002,     ,     ,s02-a2  ,FT,FS,       109,                           /mdata/fits/vgw/VGWA90053344.fits,1059840,VGWA90053344,o98016,sdata03,S01,/mdata/index/VGWA90053344.index,400
send    20051013092446.575 OK        237,20051013092446.546,SUBARUV1,    7989,mobc1-a2,10002,     ,     ,s02-a2  ,FT,FS,       109,                           /mdata/fits/vgw/VGWA90053312.fits,1059840,VGWA90053312,o98016,sdata03,S01,/mdata/index/VGWA90053312.index,400
recieve 20051013092446.608 OK        141,20051013092446.679,SUBARUV1,50000000,s02-a2  ,10002,     ,     ,mobc1-a2,FT,AB,        13,
  7989,   0
recieve 20051013092447.339 OK        151,20051013092447.417,SUBARUV1,50000001,s02-a2  ,10002,     ,     ,mobc1-a2,FT,FE,        23,
  7989,   0,   0,   0
send    20051013092447.376 OK        237,20051013092447.362,SUBARUV1,    7990,mobc1-a2,10002,     ,     ,s02-a2  ,FT,FS,       109,                           /mdata/fits/vgw/VGWA90053313.fits,1059840,VGWA90053313,o98016,sdata03,S01,/mdata/index/VGWA90053313.index,400
recieve 20051013092447.381 OK        141,20051013092447.463,SUBARUV1,50000002,s02-a2  ,10002,     ,     ,mobc1-a2,FT,AB,        13,
  7990,   0
recieve 20051013092447.931 OK        151,20051013092448.011,SUBARUV1,50000003,s02-a2  ,10002,     ,     ,mobc1-a2,FT,FE,        23,
  7990,   0,   0,   0

Log sending examples:
send    20060920075722.479 OK        251,20060920075722.470,SUBARUV1,    9217,obc1-a2 ,10002,     ,
  ,s01-a2  ,FT,FS,       123,                           /oss_data/OBS_NFS/AOSS000120060919,199554,AOSS000120060919,summitlog,sdata01,S01,/oss_data/OBS_NFS/AOSS000120060919.inf,236
recieve 20060920075722.485 OK        141,20060920075722.484,SUBARUV1,10021504,s01-a2  ,10002,     ,
  ,obc1-a2 ,FT,AB,        13,                               9217,   0
recieve 20060920075723.061 OK        151,20060920075723.060,SUBARUV1,10021505,s01-a2  ,10002,     ,
  ,obc1-a2 ,FT,FE,        23,                               9217,   0,   0,   0

at end of log sending
  ,s01-a2  ,FT,FS,       108,                           /oss_data/OBS_NFS/todaytmp.d/ENDLOG,0,ENDLOG,summitlog,sdata01,S01,/oss_data/OBS_NFS/todaytmp.d/ENDLOG.inf,0
recieve 20060920082422.670 OK        141,20060920082422.667,SUBARUV1,10021666,s01-a2  ,10002,     ,
  ,obc1-a2 ,FT,AB,        13,                               9460,   0
recieve 20060920082422.874 OK        151,20060920082422.870,SUBARUV1,10021667,s01-a2  ,10002,     ,
  ,obc1-a2 ,FT,FE,        23,                               9460,   0,   0,   0

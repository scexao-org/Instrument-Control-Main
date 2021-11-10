/*********************************************
     AG_CalcPreference.c

     Created by George KOSUGI    1998/12/25
     Modified by George KOSUGI   1999/02/23 ProbeVignet, EdgeVignet
     Modified by George KOSUGI   1999/02/23 DifferentCatalog & SameStar
     Modified by George KOSUGI   1999/09/23 Primary Focus
     Modified by George KOSUGI   2001/12/17 Change Interface
				      gmag=GoodMag => AGC.GoodMag
     Modified by George KOSUGI   2002/04/09 Change Config File Format
     Modified by George KOSUGI   2003/12/12 Change Config File Format (VignettingMap)

*********************************************/

#include"AG_StarSelection.h"
#include"prototype.h"


extern struct AG_List *AGL;
extern struct AG_CmdLine AGC;


void AG_CalcPreference(int Num){
	int i, j, rotation_flag;
	double minsep, minsep2, gmag, dpref, ins, fovtel;
	double evig, pvig, sep, diffsep2, rx, ry, cosrot, sinrot, dt;
	struct AG_PFPRM PFPRM;
	double Vignet[73][200];

	if(NG==AG_ReadCfgDbl(AGC.TelFocus, "MINSEP", &minsep)){
		AG_MsgLog("AG_CalcPreference", "Cannot find parameter MINSEP");
		exit(1);
	}
	minsep2=minsep*minsep/3600./3600.;
	diffsep2=DiffCatalog*DiffCatalog/3600./3600.;
	gmag=AGC.GoodMag;
/* 2001/12/17 : Comment out
	if(NG==AG_ReadCfgDbl(AGC.TelFocus, "GOODMAG", &gmag)){
		AG_MsgLog("AG_CalcPreference", "Cannot find parameter GOODMAG");
		exit(1);
	}
*/
	if(NG==AG_ReadCfgDbl(AGC.TelFocus, AGC.Instrument, &ins)){
		AG_MsgLog("AG_CalcPreference", "Cannot find parameter INSFOV");
		exit(1);
	}
/* 2002/04/09 : Comment Out
	if(NG==AG_ReadCfgDbl(AGC.TelFocus, "FOVTEL", &fovtel)){
		AG_MsgLog("AG_CalcPreference", "Cannot find parameter FOVTEL");
		exit(1);
	}
*/
	if(NG==AG_ReadCfgDbl(AGC.TelFocus, "EVIG", &evig)){
		AG_MsgLog("AG_CalcPreference", "Cannot find parameter EVIG");
		exit(1);
	}
	if(NG==AG_ReadCfgDbl(AGC.TelFocus, "VIGNET", &pvig)){
		AG_MsgLog("AG_CalcPreference", "Cannot find parameter VIGNET");
		exit(1);
	}
	if(NG==AG_ReadCfgDbl(AGC.TelFocus, "SCALE", &AGC.Scale)){
		AG_MsgLog("AG_CalcPreference", "Cannot find parameter SCALE");
		exit(1);
	}
	if(NG==AG_ReadCfgVignet(AGC.TelFocus, AGC.FOV_NAME, Vignet)){
		AG_MsgLog("AG_CalcPreference", "Cannot Create Vignetting Map");
		exit(1);
	}
	if(0==strncasecmp(AGC.TelFocus, "P_", 2)){
		if(NG==AG_ReadPFParam(AGC.TelFocus, "FOV", &PFPRM)){
			AG_MsgLog("AG_CalcPreference", "Cannot find parameter FOV for Prime Focus");
			exit(1);
		}
		cosrot=cos(AGC.Rotate*DEGtoRAD);
		sinrot=sin(AGC.Rotate*DEGtoRAD);
/* Origin: East for PF (?) */
		dt=AGC.Rotate+0.0;
		rotation_flag=0;
	}else if(0==strncasecmp(AGC.TelFocus, "CS", 2)){
/* Origin: West for Cs (!) */
		dt=AGC.Rotate+180.0;
		rotation_flag=0;
	}else if(0==strncasecmp(AGC.TelFocus, "NS_I", 4)){
/* Origin: East for Ns_IR (!) */
		dt=-2.0*AGC.Rotate+0.0;
		rotation_flag=1;
	}else{
/* Origin: West for Ns_Opt (?) */
		dt=2.0*AGC.Rotate+180.0;
		rotation_flag=0;
	}

	for(i=0; i<Num; i++){
		AGL[i].r=sqrt(AGL[i].dx*AGL[i].dx+AGL[i].dy*AGL[i].dy);
		AGL[i].t=fmod(atan2(AGL[i].dy, AGL[i].dx) / DEGtoRAD - dt + 3600.0, 360.0);
		if(rotation_flag==1) AGL[i].t = 360.0 - AGL[i].t;
/*	printf("DEBUG: AGL.r=%lf  AGL.t=%lf\n", AGL[i].r, AGL[i].t);*/
		if((AGL[i].r / AGC.Scale)>199.0) AGL[i].r=199.0*AGC.Scale;
/***************************************
          Separation Check
	  DiffCatalog   1999/02/23 G.K.
***************************************/
		for(j=0; j<i; j++){
			if(minsep2>(sep=(AGL[i].dx-AGL[j].dx)*(AGL[i].dx-AGL[j].dx)+(AGL[i].dy-AGL[j].dy)*(AGL[i].dy-AGL[j].dy))){
				if((diffsep2<sep)||(0==strncasecmp(AGL[i].name, AGL[j].name, 2))){
					AGL[i].Pref-=InitPreference;
					AGL[j].Pref-=InitPreference;
				}
			}
		}
/***************************************
          Magnitude Modification
	                1999/02/23 G.K.
	  VignettingMap 2002/04/09 G.K.
	  Change the Map format 10.0 -> 5.0
			2003/12/12 G.K.
***************************************/
/*		if(fovtel<(AGL[i].r)) AGL[i].Mag+=(AGL[i].r-fovtel)/(AGC.RangeFOV-fovtel)*evig;*/
/*	printf("DEBUG: %d  %d\n", (int)(AGL[i].t/10.0),(int)(AGL[i].r/AGC.Scale));*/
/*		AGL[i].Mag += Vignet[(int)(AGL[i].t/10.0)][(int)(AGL[i].r/AGC.Scale)];*/
		AGL[i].Mag += Vignet[(int)(AGL[i].t/5.0)][(int)(AGL[i].r/AGC.Scale)];
/***************************************
          Position Check
	  CS / NS only: 1998/12/17 G.K.
	  Modified:     1999/02/23 G.K.
	  PF added:     1999/09/23 G.K.
***************************************/
		if(0!=strncasecmp(AGC.TelFocus, "P_", 2)){
			if(AGC.RangeFOV<AGL[i].r) AGL[i].Pref-=InitPreference*10;
			else if((ins+pvig)>AGL[i].r) AGL[i].Pref-=(ins+pvig-AGL[i].r)/ins*InitPreference*5.0;
		}else{
			rx=AGL[i].dx*cosrot+AGL[i].dy*sinrot;
			ry=AGL[i].dy*cosrot-AGL[i].dx*sinrot;
			if((rx<PFPRM.x0)||(rx>PFPRM.x1)||(ry<PFPRM.y0)||(ry>PFPRM.y1)) AGL[i].Pref-=InitPreference*10;
			else if((ins+pvig)>AGL[i].r) AGL[i].Pref-=(ins+pvig-AGL[i].r)/ins*InitPreference*5.0;
		}
/***************************************
          Magnitude Check
***************************************/
		AGL[i].Pref-=((gmag-AGL[i].Mag)>BrightEnd)?InitPreference:fabs(gmag-AGL[i].Mag);
/***************************************
          Star Flag Check
***************************************/
		AGL[i].Pref-=fabs(BestFlag-(double)AGL[i].Flag);
	}
	return;
}

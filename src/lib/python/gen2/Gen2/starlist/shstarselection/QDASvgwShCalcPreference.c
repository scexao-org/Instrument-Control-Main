/*********************************************
     SH_CalcPreference.c

     Created by George KOSUGI    1999/05/25

*********************************************/

#include"SH_StarSelection.h"
#include"prototype.h"


extern struct SH_List *SHL;
extern struct SH_CmdLine SHC;


void SH_CalcPreference(int Num){
	int i, j;
	double minsep, minsep2, dpref, gmag, r, ins, fovtel;
	double evig, pvig, sep, diffsep2;

	if(NG==SH_ReadCfgDbl("GOODMAG", &gmag)){
		SH_MsgLog("SH_CalcPreference", "Cannot find parameter GOODMAG");
		exit(1);
	}

	for(i=0; i<Num; i++){
/***************************************
          Position Check
	  CS / NS only: 1998/12/17 G.K.
	  Modified      1999/02/23 G.K.
***************************************/
		SHL[i].r=sqrt(SHL[i].dx*SHL[i].dx+SHL[i].dy*SHL[i].dy);
		SHL[i].Pref-=SHL[i].r*10.0;
/***************************************
          Magnitude Check
***************************************/
		SHL[i].Pref-=((gmag-SHL[i].Mag)>BrightEnd)?InitPreference:fabs((gmag-SHL[i].Mag)*5.0);
	}
	return;
}

/*****************************************************/
/*              QDASvgwStarSelection                 */
/*                                                   */
/*        Modified by G.Kosugi 2001/12/17            */
/*               add parameters argv[12]=LimitMag    */
/*                              argv[13]=GoodMag     */
/*                              argv[14]=FOV_NAME    */
/*                                                   */
/*****************************************************/

#include <stdio.h>
#include"AG_StarSelection.h"
#include"prototype.h"


struct AG_List *AGL;
struct AG_CmdLine AGC;


static int AG_Func(struct AG_List* ag1, struct AG_List* ag2){
	if(ag1->Pref > ag2->Pref) return(-1);
	if(ag1->Pref < ag2->Pref) return(1);
	return(0);
}


void main(int argc, char **argv){

	struct AG_Keyword AGK[KeyNumber];
	struct AG_Struct AGS;

	int i, candnum, outflag, maxprefnum, priority;
	char line[128];
	double diff;

	if(argc<15){
		AG_MsgLog("main", "Command Line Parameter Error");
		exit(1);
	}
	sscanf(argv[1], "%lf", &AGC.TelRA);
	sscanf(argv[2], "%lf", &AGC.TelDEC);
	sscanf(argv[3], "%lf", &AGC.PrbRA);
	sscanf(argv[4], "%lf", &AGC.PrbDEC);
	sscanf(argv[5], "%s", AGC.TelFocus);
	sscanf(argv[6], "%s", AGC.Instrument);
	sscanf(argv[7], "%lf", &AGC.PrbR);
	sscanf(argv[8], "%lf", &AGC.PrbT);
	sscanf(argv[9], "%lf", &AGC.PrbX);
	sscanf(argv[10], "%lf", &AGC.PrbY);
	sscanf(argv[11], "%lf", &AGC.Rotate);
	sscanf(argv[12], "%lf", &AGC.LimitMag);
	sscanf(argv[13], "%lf", &AGC.GoodMag);
	sscanf(argv[14], "%s", AGC.FOV_NAME);
	if(NG==AG_ReadCfgDbl(AGC.TelFocus, "FOV", &AGC.RangeFOV)){
		AG_MsgLog("main", "Cannot find parameter FOV");
		exit(1);
	}
/* Comment out : 2001/12/17
	if(NG==AG_ReadCfgDbl(AGC.TelFocus, "LIMITMAG", &AGC.LimitMag)){
		AG_MsgLog("main", "Cannot find parameter LIMITMAG");
		exit(1);
	}
*/
	if(NG==AG_ReadCfgInt(AGC.TelFocus, "NUMBER", &AGC.StarNum)){
		AG_MsgLog("main", "Cannot find parameter NUMBER");
		exit(1);
	}
	if(NG==AG_ReadCfgInt(AGC.TelFocus, "MAXPREFNUM", &maxprefnum)){
		AG_MsgLog("main", "Cannot find parameter MAXPREFNUM");
		exit(1);
	}
#if(DEBUG>100)
printf("TelRA=%lf\nTelDEC=%lf\nRangeFOV=%lf\nLimitMag=%lf\nStarNum=%d\nPrbRA=%lf\nPrbDEC=%lf\nTelFocus=%s\nInstrument=%s\nPrbR=%lf\nPrbT=%lf\nPrbX=%lf\nPrbY=%lf\nRotate=%lf\n", AGC.TelRA, AGC.TelDEC, AGC.RangeFOV, AGC.LimitMag, AGC.StarNum, AGC.PrbRA, AGC.PrbDEC, AGC.TelFocus, AGC.Instrument, AGC.PrbR, AGC.PrbT, AGC.PrbX, AGC.PrbY, AGC.Rotate);
#endif

/**********************************************
Initialization
**********************************************/
	for(i=0; i<KeyNumber; i++) AGK[i].flag=0;
	i=0;
	strcpy(AGK[i++].Key, sCentRA);
	strcpy(AGK[i++].Key, sCentDEC);
	strcpy(AGK[i++].Key, sRangeRA);
	strcpy(AGK[i++].Key, sRangeDEC);
	strcpy(AGK[i++].Key, sMinMag);
	strcpy(AGK[i++].Key, sMaxMag);
	strcpy(AGK[i++].Key, sStarNum);
	strcpy(AGK[i++].Key, sInsert);
	strcpy(AGK[i++].Key, sBeginBody);

/**********************************************
HeaderHandling & Output part1
**********************************************/
	puts(sHeader01);
	puts(sHeader02);
	puts(sHeader03);
	puts(sHeader04);
	while(NULL != fgets(line, sizeof(line), stdin)){
                line[strlen(line)-1] = '\0'; /* strip \n */
 
		outflag=1;
		for(i=0; i<KeyNumber; i++){
			if(0==strncasecmp(AGK[i].Key, line, strlen(AGK[i].Key))){
				AGK[i].flag=1;
				switch(i){
					case 0:	AGS.CentRA=AG_ToolRAtoDeg(line);
						break;
					case 1:	AGS.CentDEC=AG_ToolDECtoDeg(line);
						break;
					case 2:	AGS.RangeRA=AG_ToolMintoDeg(line);
						break;
					case 3:	AGS.RangeDEC=AG_ToolMintoDeg(line);
						break;
					case 4:	AGS.MinMag=AG_ToolChartoDbl(line);
						break;
					case 5:	AGS.MaxMag=AG_ToolChartoDbl(line);
						break;
					case 6:	AGS.StarNum=AG_ToolChartoInt(line);
						outflag=0;
						break;
					case 7:	outflag=0;
						break;
					case 8:	outflag=0;
						break;
					default:break;
				}
			}
		}
		if(outflag!=0) puts(line);
		if((AGK[KeyNumber-1].flag==1) && (AGK[KeyNumber-2].flag==1)) break;
	}
#if(DEBUG>100)
printf("CentRA=%lf\nCentDEC=%lf\nRangeRA=%lf\nRangeDEC=%lf\nMinMag=%lf\nMaxMag=%lf\nStarNum=%d\n%s\n%s\n", AGS.CentRA, AGS.CentDEC, AGS.RangeRA, AGS.RangeDEC, AGS.MinMag, AGS.MaxMag, AGS.StarNum, sHeaderField01, sHeaderField02);
#endif

/**********************************************
BodyHandling
**********************************************/
	if(NULL==(AGL=malloc(sizeof(struct AG_List)*AGS.StarNum))){
		AG_MsgLog("main", "Memory Allocation Failure");
		exit(1);
	}
	for(i=0; i<AGS.StarNum, NULL != fgets(line, sizeof(line), stdin); i++){
                line[strlen(line)-1] = '\0'; /* strip \n */

		sscanf(line, "%s\t%lf\t%lf\t%lf\t%d\t%lf", AGL[i].name, &AGL[i].RA, &AGL[i].DEC, &AGL[i].Mag, &AGL[i].Flag, &AGL[i].BR);
		diff=AGL[i].RA-AGC.TelRA;
		if(diff>180.0) diff-=360.0;
		else if(diff<-180.0) diff+=360.0;
		AGL[i].dx=diff*cos(AGC.TelDEC*DEGtoRAD);
		AGL[i].dy=AGL[i].DEC-AGC.TelDEC;
		AGL[i].Pref=InitPreference;
	}
	AGS.StarNum=i;

	AG_CalcPreference(AGS.StarNum);

	qsort((char*)AGL, AGS.StarNum, sizeof(struct AG_List), AG_Func);

/* 2004/01/27 by G.K for Max Magnitude */
	for(i=0, candnum=0; i<AGS.StarNum; i++){
		if((AGL[i].Mag <= AGS.MaxMag) && (AGL[i].Pref > -100.0)) candnum++;
		else AGL[i].Pref=-100.0;
	}
	if(AGC.StarNum<candnum) candnum=AGC.StarNum;
	for(i=0, AGS.PrefNum=0; i<AGS.StarNum; i++) if(AGL[i].Pref>0.0) AGS.PrefNum++;
	if(AGS.PrefNum>maxprefnum) AGS.PrefNum=maxprefnum;

/* 2005/12/01 by Eric Jeschke: to fix error in preferred num.  It cannot be
   bigger than the number of stars. */
	if(AGS.PrefNum>candnum) AGS.PrefNum=1;
         
/**********************************************
HeaderOutput part2
**********************************************/
	sprintf(line, "%s=%d", sStarNum, candnum);
	puts(line);
	sprintf(line, "%s=%d", sPrefNum, AGS.PrefNum);
	puts(line);
	puts(sHeaderField01);
	puts(sHeaderField02);

/**********************************************
BodyOutput
**********************************************/
	for(i=0, priority=1; (i<AGS.StarNum)&&(priority<=candnum); i++){
		if(AGL[i].Pref>-100.0){
			sprintf(line, "%s\t%lf\t%lf\t%lf\t%d\t%lf\t%lf\t%d\t%lf", AGL[i].name, AGL[i].RA, AGL[i].DEC, AGL[i].Mag, AGL[i].Flag, AGL[i].BR, AGL[i].Pref, priority++, AGL[i].r*60.0);
			puts(line);
		}
	}

	free(AGL);
	exit(0);
}

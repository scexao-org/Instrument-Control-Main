#include"SH_StarSelection.h"
#include"prototype.h"


struct SH_List *SHL;
struct SH_CmdLine SHC;


static int SH_Func(struct SH_List* ag1, struct SH_List* ag2){
	if(ag1->Pref > ag2->Pref) return(-1);
	if(ag1->Pref < ag2->Pref) return(1);
	return(0);
}


void main(int argc, char **argv){

	struct SH_Keyword SHK[KeyNumber];
	struct SH_Struct SHS;

	int i, outflag, maxprefnum;
	char line[128];
	double diff;

	if(argc<3){
		SH_MsgLog("main", "Command Line Parameter Error");
		exit(1);
	}
	sscanf(argv[1], "%lf", &SHC.TelRA);
	sscanf(argv[2], "%lf", &SHC.TelDEC);
	if(NG==SH_ReadCfgDbl("LIMITMAG", &SHC.LimitMag)){
		SH_MsgLog("main", "Cannot find parameter LIMITMAG");
		exit(1);
	}
	if(NG==SH_ReadCfgInt("NUMBER", &SHC.StarNum)){
		SH_MsgLog("main", "Cannot find parameter NUMBER");
		exit(1);
	}
	if(NG==SH_ReadCfgInt("MAXPREFNUM", &maxprefnum)){
		SH_MsgLog("main", "Cannot find parameter MAXPREFNUM");
		exit(1);
	}
#if(DEBUG>100)
printf("TelRA=%lf\nTelDEC=%lf\nLimitMag=%lf\nStarNum=%d\n", SHC.TelRA, SHC.TelDEC, SHC.LimitMag, SHC.StarNum);
#endif

/**********************************************
Initialization
**********************************************/
	for(i=0; i<KeyNumber; i++) SHK[i].flag=0;
	i=0;
	strcpy(SHK[i++].Key, sCentRA);
	strcpy(SHK[i++].Key, sCentDEC);
	strcpy(SHK[i++].Key, sRangeRA);
	strcpy(SHK[i++].Key, sRangeDEC);
	strcpy(SHK[i++].Key, sMinMag);
	strcpy(SHK[i++].Key, sMaxMag);
	strcpy(SHK[i++].Key, sStarNum);
	strcpy(SHK[i++].Key, sInsert);
	strcpy(SHK[i++].Key, sBeginBody);

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
			if(0==strncasecmp(SHK[i].Key, line, strlen(SHK[i].Key))){
				SHK[i].flag=1;
				switch(i){
					case 0:	SHS.CentRA=SH_ToolRAtoDeg(line);
						break;
					case 1:	SHS.CentDEC=SH_ToolDECtoDeg(line);
						break;
					case 2:	SHS.RangeRA=SH_ToolMintoDeg(line);
						break;
					case 3:	SHS.RangeDEC=SH_ToolMintoDeg(line);
						break;
					case 4:	SHS.MinMag=SH_ToolChartoDbl(line);
						break;
					case 5:	SHS.MaxMag=SH_ToolChartoDbl(line);
						break;
					case 6:	SHS.StarNum=SH_ToolChartoInt(line);
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
		if((SHK[KeyNumber-1].flag==1) && (SHK[KeyNumber-2].flag==1)) break;
	}
#if(DEBUG>100)
printf("CentRA=%lf\nCentDEC=%lf\nRangeRA=%lf\nRangeDEC=%lf\nMinMag=%lf\nMaxMag=%lf\nStarNum=%d\n%s\n%s\n", SHS.CentRA, SHS.CentDEC, SHS.RangeRA, SHS.RangeDEC, SHS.MinMag, SHS.MaxMag, SHS.StarNum, sHeaderField01, sHeaderField02);
#endif

/**********************************************
BodyHandling
**********************************************/
	if(NULL==(SHL=malloc(sizeof(struct SH_List)*SHS.StarNum))){
		SH_MsgLog("main", "Memory Allocation Failure");
		exit(1);
	}
	for(i=0; i<SHS.StarNum, NULL != fgets(line, sizeof(line), stdin); i++){
		line[strlen(line)-1] = '\0'; /* strip \n */
        sscanf(line, "%s\t%lf\t%lf\t%lf\t%d\t%lf", SHL[i].name, &SHL[i].RA, &SHL[i].DEC, &SHL[i].Mag, &SHL[i].Flag, &SHL[i].BR);
		diff=SHL[i].RA-SHC.TelRA;
		if(diff<-180.0) diff+=360.0;
		else if(diff>180.0) diff-=360.0;
		SHL[i].dx=diff*cos(SHC.TelDEC*DEGtoRAD);
		SHL[i].dy=SHL[i].DEC-SHC.TelDEC;
		SHL[i].Pref=InitPreference;
	}
	SHS.StarNum=i;

	SH_CalcPreference(SHS.StarNum);

	qsort((char*)SHL, SHS.StarNum, sizeof(struct SH_List), SH_Func);
	if(SHC.StarNum<SHS.StarNum) SHS.StarNum=SHC.StarNum;
	for(i=0, SHS.PrefNum=0; i<SHS.StarNum; i++) if(SHL[i].Pref>0.0) SHS.PrefNum++;
	if(SHS.PrefNum>maxprefnum) SHS.PrefNum=maxprefnum;
/**********************************************
HeaderOutput part2
**********************************************/
	sprintf(line, "%s=%d", sStarNum, SHS.StarNum);
	puts(line);
	sprintf(line, "%s=%d", sPrefNum, SHS.PrefNum);
	puts(line);
	puts(sHeaderField01);
	puts(sHeaderField02);

/**********************************************
BodyOutput
**********************************************/
/*	for(i=0; i<SHC.StarNum; i++){*/

	for(i=0; i<SHS.StarNum; i++){
		sprintf(line, "%s\t%lf\t%lf\t%lf\t%d\t%lf\t%lf\t%d\t%lf", SHL[i].name, SHL[i].RA, SHL[i].DEC, SHL[i].Mag, SHL[i].Flag, SHL[i].BR, SHL[i].Pref, i+1,SHL[i].r);
		puts(line);
	}

	free(SHL);
	exit(0);
}

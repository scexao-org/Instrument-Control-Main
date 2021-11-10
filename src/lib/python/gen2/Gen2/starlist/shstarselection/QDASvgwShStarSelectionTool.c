#include"SH_StarSelection.h"
#include"prototype.h"


void SH_MsgLog(char* subroutine, char* msg){
	fprintf(stdout, "SHSS:%-16s:%s\n", subroutine, msg);
}


double SH_ToolRAtoDeg(char*line){
	char *p;
	double hh, mm, ss, deg;

	if(NULL==(p=strstr(line, "="))){
		SH_MsgLog("SH_ToolRAtoDeg", "Format Error");
		exit(1);
	}
	sscanf(p, "%*c%2lf:%2lf:%lf", &hh, &mm, &ss);
	deg=15.0*hh + 15.0*mm/60.0 + 15.0*ss/3600.0;
	if((deg>360.0) || (deg<0.0)){
		SH_MsgLog("SH_ToolRAtoDeg", "RA Range Error");
		exit(1);
	}

	return(deg);
}


double SH_ToolDECtoDeg(char*line){
	char *p;
	double deg, hh, mm, ss, sign;

	if(NULL==(p=strstr(line, "="))){
		SH_MsgLog("SH_ToolDECtoDeg", "Format Error");
		exit(1);
	}
	p++;
	if(0==strncmp(p, "-", 1)) sign=-1.0;
	else sign=1.0;
	sscanf(p, "%*c%2lf:%2lf:%lf", &hh, &mm, &ss);
	deg=sign*(hh + mm/60.0 + ss/3600.0);
	if((deg>90.0) || (deg<-90.0)){
		SH_MsgLog("SH_ToolDECtoDeg", "DEC Range Error");
		exit(1);
	}

	return(deg);
}


double SH_ToolMintoDeg(char*line){
	char *p;
	double deg, mm;

	if(NULL==(p=strstr(line, "="))){
		SH_MsgLog("SH_ToolMintoDeg", "Format Error");
		exit(1);
	}
	sscanf(p, "%*c%lf", &mm);
	deg=mm/60.0;
	if(deg<0.0){
		SH_MsgLog("SH_ToolMintoDeg", "Range Error");
		exit(1);
	}

	return(deg);
}


double SH_ToolChartoDbl(char*line){
	char *p;
	double dbl;

	if(NULL==(p=strstr(line, "="))){
		SH_MsgLog("SH_ToolChartoDbl", "Format Error");
		exit(1);
	}
	sscanf(p, "%*c%lf", &dbl);

	return(dbl);
}


int SH_ToolChartoInt(char*line){
	char *p;
	int val;

	if(NULL==(p=strstr(line, "="))){
		SH_MsgLog("SH_ToolChartoInt", "Format Error");
		exit(1);
	}
	sscanf(p, "%*c%d", &val);

	return(val);
}

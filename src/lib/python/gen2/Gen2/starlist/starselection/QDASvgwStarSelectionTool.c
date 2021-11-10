#include"AG_StarSelection.h"
#include"prototype.h"


void AG_MsgLog(char* subroutine, char* msg){
	fprintf(stdout, "AGSS:%-16s:%s\n", subroutine, msg);
}


double AG_ToolRAtoDeg(char*line){
	char *p;
	double hh, mm, ss, deg;

	if(NULL==(p=strstr(line, "="))){
		AG_MsgLog("AG_ToolRAtoDeg", "Format Error");
		exit(1);
	}
	sscanf(p, "%*c%2lf:%2lf:%lf", &hh, &mm, &ss);
	deg=15.0*hh + 15.0*mm/60.0 + 15.0*ss/3600.0;
	if((deg>360.0) || (deg<0.0)){
		AG_MsgLog("AG_ToolRAtoDeg", "RA Range Error");
		exit(1);
	}

	return(deg);
}


double AG_ToolDECtoDeg(char*line){
	char *p;
	double deg, hh, mm, ss, sign;

	if(NULL==(p=strstr(line, "="))){
		AG_MsgLog("AG_ToolDECtoDeg", "Format Error");
		exit(1);
	}
	p++;
	if(0==strncmp(p, "-", 1)) sign=-1.0;
	else sign=1.0;
	sscanf(p, "%*c%2lf:%2lf:%lf", &hh, &mm, &ss);
	deg=sign*(hh + mm/60.0 + ss/3600.0);
	if((deg>90.0) || (deg<-90.0)){
		AG_MsgLog("AG_ToolDECtoDeg", "DEC Range Error");
		exit(1);
	}

	return(deg);
}


double AG_ToolMintoDeg(char*line){
	char *p;
	double deg, mm;

	if(NULL==(p=strstr(line, "="))){
		AG_MsgLog("AG_ToolMintoDeg", "Format Error");
		exit(1);
	}
	sscanf(p, "%*c%lf", &mm);
	deg=mm/60.0;
	if((deg>1.0) || (deg<0.0)){
		AG_MsgLog("AG_ToolMintoDeg", "Range Error");
		exit(1);
	}

	return(deg);
}


double AG_ToolChartoDbl(char*line){
	char *p;
	double dbl;

	if(NULL==(p=strstr(line, "="))){
		AG_MsgLog("AG_ToolChartoDbl", "Format Error");
		exit(1);
	}
	sscanf(p, "%*c%lf", &dbl);

	return(dbl);
}


int AG_ToolChartoInt(char*line){
	char *p;
	int val;

	if(NULL==(p=strstr(line, "="))){
		AG_MsgLog("AG_ToolChartoInt", "Format Error");
		exit(1);
	}
	sscanf(p, "%*c%d", &val);

	return(val);
}

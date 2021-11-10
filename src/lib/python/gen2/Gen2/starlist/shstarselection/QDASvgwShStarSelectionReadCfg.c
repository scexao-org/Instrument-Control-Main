#include"SH_StarSelection.h"
#include"prototype.h"


int SH_ReadCfgInt(char* item, int* ret){
	FILE *p;
	char *CfgEnv, CfgFile[255], line[255];

        CfgEnv=getenv("QDASVGWHOME");
        if(CfgEnv==(char*)NULL){
                SH_MsgLog("SH_ReadCfgInt", "QDASVGWHOME environment Error");
                exit(1);
        }
        sprintf(CfgFile, "%s%s", CfgEnv, SHSS_CFG);
        if(NULL==(p=fopen(CfgFile, "r"))){
		printf("%s\n", CfgFile);
                SH_MsgLog("SH_ReadCfgInt", "Cannot Open ShAutoSelect.cfg");
                exit(1);
        }
	while(NULL!=fgets(line, 255, p)){
		if((line[0]!='#') && (NULL!=strstr(line, item))){
			sscanf(line, "%*s %d", ret);
			fclose(p);
			return(OK);
		}
	}
        fclose(p);
	return(NG);
}
 

int SH_ReadCfgDbl(char* item, double* ret){
	FILE *p;
	char *CfgEnv, CfgFile[255], line[255];

        CfgEnv=getenv("QDASVGWHOME");
        if(CfgEnv==(char*)NULL){
                SH_MsgLog("SH_ReadCfgDbl", "QDASVGWHOME environment Error");
                exit(1);
        }
        sprintf(CfgFile, "%s%s", CfgEnv, SHSS_CFG);
        if(NULL==(p=fopen(CfgFile, "r"))){
		printf("%s\n", CfgFile);
                SH_MsgLog("SH_ReadCfgDbl", "Cannot Open ShAutoSelect.cfg");
                exit(1);
        }
	while(NULL!=fgets(line, 255, p)){
		if((line[0]!='#') && (NULL!=strstr(line, item))){
			sscanf(line, "%*s %lf", ret);
			fclose(p);
			return(OK);
		}
	}
        fclose(p);
	return(NG);
} 


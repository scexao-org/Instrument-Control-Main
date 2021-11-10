#include"AG_StarSelection.h"
#include"prototype.h"


int AG_ReadCfgInt(char* fcs, char* item, int* ret){
	FILE *p;
	char *CfgEnv, CfgFile[255], line[255];

        CfgEnv=getenv("QDASVGWHOME");
        if(CfgEnv==(char*)NULL){
                AG_MsgLog("AG_ReadCfgInt", "QDASVGWHOME environment Error");
                exit(1);
        }
        sprintf(CfgFile, "%s%s", CfgEnv, AGSS_CFG);
        if(NULL==(p=fopen(CfgFile, "r"))){
		printf("%s\n", CfgFile);
                AG_MsgLog("AG_ReadCfgInt", "Cannot Open AgAutoSelect.cfg");
                exit(1);
        }
	while(NULL!=fgets(line, 255, p)){
		if((line[0] != '#') && (NULL!=strstr(line, fcs)) && (NULL!=strstr(line, item))){
			sscanf(line, "%*s %*s %d", ret);
			fclose(p);
			return(OK);
		}
	}
        fclose(p);
	return(NG);
}
 

int AG_ReadCfgDbl(char* fcs, char* item, double* ret){
	FILE *p;
	char *CfgEnv, CfgFile[255], line[255];

        CfgEnv=getenv("QDASVGWHOME");
        if(CfgEnv==(char*)NULL){
                AG_MsgLog("AG_ReadCfgDbl", "QDASVGWHOME environment Error");
                exit(1);
        }
        sprintf(CfgFile, "%s%s", CfgEnv, AGSS_CFG);
        if(NULL==(p=fopen(CfgFile, "r"))){
		printf("%s\n", CfgFile);
                AG_MsgLog("AG_ReadCfgDbl", "Cannot Open AgAutoSelect.cfg");
                exit(1);
        }
	while(NULL!=fgets(line, 255, p)){
		if((line[0] != '#') && (NULL!=strstr(line, fcs)) && (NULL!=strstr(line, item))){
			sscanf(line, "%*s %*s %lf", ret);
			fclose(p);
			return(OK);
		}
	}
        fclose(p);
	return(NG);
} 


int AG_ReadCfgVignet(char* fcs, char* item, double Vignet[][200]){
	FILE *p;
	char *CfgEnv, CfgFile[255], line[255], ref_fcs[255], ref_item[255];
	double r100, r50, r0, angle, rvig[16];
	double Nr100, Nr50, Nr0, Nangle, Nrvig[16];
	double Ar100, Ar50, Ar0, Arvig[16], transp;
	int i, j, jj, k, vigflag, n;

        CfgEnv=getenv("QDASVGWHOME");
        if(CfgEnv==(char*)NULL){
                AG_MsgLog("AG_ReadCfgVignet", "QDASVGWHOME environment Error");
                exit(1);
        }
        sprintf(CfgFile, "%s%s", CfgEnv, AGSS_CFG);
        if(NULL==(p=fopen(CfgFile, "r"))){
		printf("%s\n", CfgFile);
                AG_MsgLog("AG_ReadCfgVignet", "Cannot Open AgAutoSelect.cfg");
                exit(1);
        }

	k=0; vigflag=0;
	while(NULL!=fgets(line, 255, p)){
		if(NULL!=strstr(line, "VIGNET TABLE START")) vigflag=1;
		else if(NULL!=strstr(line, "VIGNET TABLE END")) vigflag=0;
/* CS, NS : New Vignetting Map format 2003/12/12 G.K. */
		if((vigflag==1)&&(0!=strncasecmp(fcs, "P_", 2))){
			sscanf(line, "%s %s", ref_fcs, ref_item);
			if((0==strcmp(ref_fcs, fcs))&&(0==strcmp(ref_item, item))){
				k++;
				if(k==1){
					sscanf(line, "%*s %*s %lf %lf %lf %lf %lf %lf %lf %lf %lf %lf %lf %lf %lf %lf %lf %lf %lf", &angle, &rvig[0], &rvig[1], &rvig[2], &rvig[3], &rvig[4], &rvig[5], &rvig[6], &rvig[7], &rvig[8], &rvig[9], &rvig[10], &rvig[11], &rvig[12], &rvig[13], &rvig[14], &rvig[15]);
					if(angle!=0.0){
       	         				AG_MsgLog("AG_ReadCfgVignet", "Vignetting Map Format Error");
       	         				exit(1);
					}
				}else{
					Nangle=angle;
					for(n=0; n<16; n++) Nrvig[n] = rvig[n];
					sscanf(line, "%*s %*s %lf %lf %lf %lf %lf %lf %lf %lf %lf %lf %lf %lf %lf %lf %lf %lf %lf", &angle, &rvig[0], &rvig[1], &rvig[2], &rvig[3], &rvig[4], &rvig[5], &rvig[6], &rvig[7], &rvig[8], &rvig[9], &rvig[10], &rvig[11], &rvig[12], &rvig[13], &rvig[14], &rvig[15]);
					for(i=0; i<=72; i++){
						if(((5.0*(double)i)>=Nangle) && ((5.0*(double)i)<angle)){
							for(n=0; n<16; n++) Arvig[n]=(rvig[n]*(5.0*(double)i-Nangle)+Nrvig[n]*(angle-5.0*(double)i)) / (angle-Nangle);
							for(j=0; j<150; j++){
								jj = (int)(j/10);
								transp=(Arvig[jj]*((jj+1)*10.0-j) + Arvig[jj+1]*(j-jj*10.0))/1000.0;
								if(transp>=0.01) Vignet[i][j]=-2.5*log10(transp);
								else Vignet[i][j]=50.0;
							}
							for(j=150; j<200; j++) Vignet[i][j]=50.0;
						}
					}
				}
			}
/* P_OPT, P_IR : Original Vignetting Map format */
		}else if((vigflag==1)&&(0==strncasecmp(fcs, "P_", 2))){
			sscanf(line, "%s %s", ref_fcs, ref_item);
			if((0==strcmp(ref_fcs, fcs))&&(0==strcmp(ref_item, item))){
				k++;
				if(k==1){
					sscanf(line, "%*s %*s %lf %lf %lf %lf", &angle, &r100, &r50, &r0);
					if(angle!=0.0){
       	         				AG_MsgLog("AG_ReadCfgVignet", "Vignetting Map Format Error");
       	         				exit(1);
					}
				}else{
					Nr100=r100; Nr50=r50; Nr0=r0; Nangle=angle;
					sscanf(line, "%*s %*s %lf %lf %lf %lf", &angle, &r100, &r50, &r0);
					for(i=0; i<=72; i++){
						if(((5.0*(double)i)>=Nangle) && ((5.0*(double)i)<angle)){
							Ar100=(r100*(5.0*(double)i-Nangle)+Nr100*(angle-5.0*(double)i)) / (angle-Nangle);
							Ar50=(r50*(5.0*(double)i-Nangle)+Nr50*(angle-5.0*(double)i)) / (angle-Nangle);
							Ar0=(r0*(5.0*(double)i-Nangle)+Nr0*(angle-5.0*(double)i)) / (angle-Nangle);
							if(Ar100==Ar50) Ar100--;
							if(Ar0==Ar50) Ar0++;
							for(j=0; j<200; j++){
								if(j<=Ar100) Vignet[i][j]=0.0;
								else if(j<=Ar50) Vignet[i][j]=-2.5*log10(((Ar50-(double)j)+0.5*((double)j-Ar100))/(Ar50-Ar100));
								else if(j<Ar0){
									Vignet[i][j]=-2.5*log10(0.5*(Ar0-(double)j)/(Ar0-Ar50));
									if(Vignet[i][j]>50.0) Vignet[i][j]=50.0;
								}
								else Vignet[i][j]=50.0;
							}
						}
					}
				}
			}
		}
	}
	if(angle!=360.0){
                AG_MsgLog("AG_ReadCfgVignet", "Vignetting Map Format Error");
                exit(1);
	}else for(j=0; j<200; j++) Vignet[72][j]=Vignet[0][j];

        fclose(p);
	return(OK);
} 


int AG_ReadPFParam(char* fcs, char* item, struct AG_PFPRM* ret){
	FILE *p;
	char *CfgEnv, CfgFile[255], line[255];

        CfgEnv=getenv("QDASVGWHOME");
        if(CfgEnv==(char*)NULL){
                AG_MsgLog("AG_ReadCfgDbl", "QDASVGWHOME environment Error");
                exit(1);
        }
        sprintf(CfgFile, "%s%s", CfgEnv, AGSS_CFG);
        if(NULL==(p=fopen(CfgFile, "r"))){
		printf("%s\n", CfgFile);
                AG_MsgLog("AG_ReadCfgDbl", "Cannot Open AgAutoSelect.cfg");
                exit(1);
        }
	while(NULL!=fgets(line, 255, p)){
		if((line[0] != '#') && (NULL!=strstr(line, fcs)) && (NULL!=strstr(line, item))){
			sscanf(line, "%*s %*s %*lf %lf %lf %lf %lf", &ret->x0, &ret->x1, &ret->y0, &ret->y1);
			fclose(p);
			return(OK);
		}
	}
        fclose(p);
	return(NG);
} 

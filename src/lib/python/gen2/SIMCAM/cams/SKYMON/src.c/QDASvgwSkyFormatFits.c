/************************************************************
	QDASvgwSkyFormatFits.c

	2001/07/25 by George Kosugi

Usage: QDASvgwSkyFormatFits AZ(deg) IR/Opt Fits(In) Fits(Out)

This program transform the original sky monitor image to the
modified image whose direction is North-up and East-left.

If AZROTATION equal 1, we assume the sky monitor is set up
on the dome/enclosure which co-rotates with telescope AZ.

CALCMODE : FAST:1  SLOW:0 1: FAST : Fast calculation
           0: SLOW : Accurate Calculation

SKY_ROT_IR/OPT : Offset angle of the North direction on the
		 image
SKY_FLIP_IR/OPT : If the rotation direction from north to
		 east is a clockwise, the flag should be
                 set to 1, otherwise -1.
SKY_R_IR/OPT : Radious(pixel) of the sky image (X-Width)
ZENITH_X_IR/OPT : Center of the sky image(pixel)
ZENITH_Y_IR/OPT : Center of the sky image(pixel)
ELLIPSE_IR/OPT  : Elliptisity of the SkyMonitor Image (Vertical/Holizontal)
SKY_EL_LIMIT_IR/OPT : Elevation Lower Limit of the SkyMonitor (degree)
HOLE_R_IR/OPT  : Size of the Primary Mirror Central Hole (degree)

** This program refer the environment variable 'QDASVGWHOME'.
** Configuration file : $QDASVGWHOME/file/QDASvgwSkyEditFmt.tcl 

************************************************************/

#include<stdio.h>
#include<stdlib.h>
#include<math.h>
#include<string.h>
#include"./skyfont.h"

#define DEBUG 1
#define AZROTATION 0
#define CALCMODE 1
#define FONT_HEIGHT 8
#define FONT_WIDTH 6
#define FONT_OFFSET_X 1
#define FONT_OFFSET_Y 10
#define CIRRUS_FONT_OFFSET_X 1
#define CIRRUS_FONT_OFFSET_Y 1
#define DIRECTION_FONT_OFFSET_X 30
#define DIRECTION_FONT_OFFSET_Y 30
#define DIRECTION_FONT_MAGNIFICATION 1
#define SUBARU_FONT_OFFSET_X 130
#define SUBARU_FONT_OFFSET_Y 11
#define SUBARU_FONT_MAGNIFICATION 1
/*#define SUBARU_FONT_OFFSET_X 2
#define SUBARU_FONT_OFFSET_Y 21
#define SUBARU_FONT_MAGNIFICATION 2*/
#define FONT_MAGNIFICATION 1

#define SKY_ROT_IR 0
#define SKY_FLIP_IR 1
#define SKY_R_IR 115
#define SKY_EL_LIMIT_IR 20
#define ZENITH_X_IR 166
#define ZENITH_Y_IR 124
#define HOLE_R_IR 13
#define ELLIPSE_IR 0.916

#define SKY_ROT_OPT 30
#define SKY_FLIP_OPT 1
#define SKY_R_OPT 150
#define SKY_EL_LIMIT_OPT 20
#define ZENITH_X_OPT 200
#define ZENITH_Y_OPT 200
#define HOLE_R_OPT 17
#define ELLIPSE_OPT 1.0

#define SMIN "SAMPLE(MIN)"
#define SMAX "SAMPLE(MAX)"
#define SX1 "SAMPLE(X1)"
#define SX2 "SAMPLE(X2)"
#define SY1 "SAMPLE(Y1)"
#define SY2 "SAMPLE(Y2)"
#define SCX "CENTER(X)"
#define SCY "CENTER(Y)"
#define SCR "CENTER(R)"
#define SFX "SKYFORMATFITS(X)"
#define SFY "SKYFORMATFITS(Y)"
#define FMIN 0.0
#define FMAX 1000.0
#define HEADERBLOCK 36
#define FITSBLOCK 2880

void ReadConfigFile(int*, int*, int*, int*, float*, float*, int*, int*, int*, int*, int*);
int CountFitsHeader(char*, int*, int*);
void ReadFits(char*, int, int, int, char*, float*, int, int, char*, char*, char*, float*, float*);
void FitsTransform_IR(float*, float*, int, int, int, int, int, int, int, float, float);
void FitsTransform_Opt(float*, float*, int, int, int, int, int, int, int, float, float);
void MakeWedge(int, int, int, int, int, int, float, float, float*, int, int);
void MakeUTdate(char*, char*, char*, float, float*, int);
void MakeCirrusCloudCover(float, float, float, float*, int);
void MakeSubaruLogo(float, float*, int, int);
void MakeDirection(float, float*, int, int);
void MakeFont(char, int, int, float, float*, int, int);
void WriteFits(char*, int, int, int, char*, float*);

void readout(float *buf, int dx, int dy) 
{
    float *q, t;
    int i, j;
    
    q = buf;
    printf("READOUT\n");
    for (i = 0; i < dx; ++i)
        for (j = 0; j < dy; j++) 
        {
            t = *q++;
            printf("pix = %8.8f\n", t);
        }
    printf("DONE\n");
}

void byteswap_buf(void *ptr, int len) 
{
    unsigned int a, d, *src;
    unsigned char *dst = (unsigned char *)&d;
    unsigned char *ast = (unsigned char *)&a;
    void *q;

    q = ptr + (sizeof(unsigned int) * len);
/*    printf("start = %x, end = %x\n", ptr, q);*/

    while (ptr < q)
    {
        src = (unsigned int *)ptr;
        a = *src;
    
        dst[0] = ast[3];
        dst[1] = ast[2];
        dst[2] = ast[1];
        dst[3] = ast[0];

        *src = d;
        ptr += sizeof(unsigned int);
    }
/*    printf("end = %x, uint = %d\n", src, sizeof(unsigned int)); */
}

int main(int argc, char**argv){
	FILE *fp_out;
	float az=0.0;
	char *header, date_obs[32], ut[32], hst[32];
	int wedge_x1, wedge_x2, wedge_y1, wedge_y2, fits, dx, dy, headsize, cx, cy, cr, fx, fy;
	float wedge_min, wedge_max, *data_in, *data_out, cirrus, cloud;

	if(argc!=5){
		fputs("QDASvgwSkyFormatFits: Parameter Err", stdout);
		exit(1);
	}
	ReadConfigFile(&wedge_x1, &wedge_y1, &wedge_x2, &wedge_y2, &wedge_min, &wedge_max, &cx, &cy, &cr, &fx, &fy);
	if((wedge_x1>fx)||(wedge_x2>fx)||(wedge_y1>fy)||(wedge_y2+11>fy)||(wedge_x1<1)||(wedge_x2<1)||(wedge_y1<1)||(wedge_y2<1)){
		fputs("QDASvgwSkyFormatFits: Wedge Over Range Err", stdout);
		exit(1);
	}

#if(DEBUG!=0)
	printf("X1=%d  Y1=%d  X2=%d  Y2=%d  Min=%f  Max=%f\n", wedge_x1, wedge_y1, wedge_x2, wedge_y2, wedge_min, wedge_max);
	printf("CX=%d  CY=%d  R=%d  fx=%d  fy=%d\n", cx, cy, cr, fx, fy);
#endif
	fits=CountFitsHeader(argv[3], &dx, &dy);
#if(DEBUG!=0)
	printf("Header=%d  dx=%d  dy=%d\n", fits, dx, dy);
#endif
	if(NULL==(data_in=(float*)malloc(sizeof(float)*dx*dy))){
		fputs("QDASvgwSkyFormatFits: Malloc Err", stdout);
		exit(1);
	}
	if(NULL==(data_out=(float*)malloc(sizeof(float)*fx*fy))){
		fputs("QDASvgwSkyFormatFits: Malloc Err", stdout);
		exit(1);
	}
	headsize=sizeof(char)*80*HEADERBLOCK*(int)((fits-1)/HEADERBLOCK+1);
	if(NULL==(header=(char*)malloc(headsize+1))){
		fputs("QDASvgwSkyFormatFits: Malloc Err", stdout);
		exit(1);
	}
	ReadFits(argv[3], dx, dy, headsize, header, data_in, fx, fy, date_obs, ut, hst, &cirrus, &cloud);
#if(DEBUG!=0)
	printf("Date-Obs=%s  ut=%s\n", date_obs, ut);
	printf("Cirrus=%f  Cloud=%f\n", cirrus, cloud);
#endif
/*        printf("start = %x, end = %x\n", (unsigned int *)data_in, (unsigned int *)data_in +
          (sizeof(unsigned int)*dx*dy)); */
        byteswap_buf((void *)data_in, dx*dy);
        /* readout(data_in, dx, dy); */

#if(AZROTATION!=0)
	sscanf(argv[1], "%f", &az);
#endif
	if(0==strncasecmp(argv[2], "IR", 2)){
		FitsTransform_IR(data_in, data_out, dx, dy, cx, cy, cr, fx, fy, az, (wedge_min+wedge_max)/3.0);
	}else FitsTransform_Opt(data_in, data_out, dx, dy, cx, cy, cr, fx, fy, az, (wedge_min+wedge_max)/3.0);

	MakeWedge(fx, fy, (wedge_x1-1), (wedge_y1-1), (wedge_x2-1), (wedge_y2-1), wedge_min, wedge_max, data_out, fx, fy);
	MakeUTdate(date_obs, ut, hst, wedge_max, data_out, fx);
	MakeCirrusCloudCover(cirrus, cloud, wedge_max, data_out, fx);
	MakeSubaruLogo(wedge_max, data_out, fx, fy);
	MakeDirection(wedge_max, data_out, fx, fy);

        byteswap_buf((void *)data_out, fx*fy);
	WriteFits(argv[4], fx, fy, headsize, header, data_out);
        /* readout(data_out, fx, fy); */

	free(data_in);
	free(data_out);
	free(header);
	exit(0);
}


void ReadConfigFile(int *x1, int*y1, int*x2, int*y2, float*min, float*max, int*cx, int*cy, int*cr, int*fx, int*fy){
	FILE *fp_cfg;
	char *env, config[1024], buff[1024], *p;
	int num=0;

	if(NULL==(env=getenv("QDASVGWHOME"))){
		fputs("QDASvgwSkyFormatFits: Undefined Environment: QDASVGWHOME", stdout);
		exit(1);
	}
	/* sprintf(config, "%s/file/QDASvgwSkyEditFmt.tcl", env); */
	sprintf(config, "%s/QDASvgwSkyEditFmt.tcl", env);
	if(NULL==(fp_cfg=fopen(config, "r"))){
		fputs("QDASvgwSkyFormatFits: Open Config File Err", stdout);
		exit(1);
	}
	while(NULL!=fgets(buff, 1023, fp_cfg)){
		if(NULL!=(p=strstr(buff, SMIN))){
			num++;
			if(NULL!=strstr(buff, "NULL")) *min=FMIN;
			else(sscanf(p, "%*s %f", min));
		}else if(NULL!=(p=strstr(buff, SMAX))){
			num++;
			if(NULL!=strstr(buff, "NULL")) *max=FMAX;
			else(sscanf(p, "%*s %f", max));
		}else if(NULL!=(p=strstr(buff, SX1))){
			num++;
			sscanf(p, "%*s %d", x1);
		}else if(NULL!=(p=strstr(buff, SX2))){
			num++;
			sscanf(p, "%*s %d", x2);
		}else if(NULL!=(p=strstr(buff, SY1))){
			num++;
			sscanf(p, "%*s %d", y1);
		}else if(NULL!=(p=strstr(buff, SY2))){
			num++;
			sscanf(p, "%*s %d", y2);
		}else if(NULL!=(p=strstr(buff, SCX))){
			num++;
			sscanf(p, "%*s %d", cx);
		}else if(NULL!=(p=strstr(buff, SCY))){
			num++;
			sscanf(p, "%*s %d", cy);
		}else if(NULL!=(p=strstr(buff, SCR))){
			num++;
			sscanf(p, "%*s %d", cr);
		}else if(NULL!=(p=strstr(buff, SFX))){
			num++;
			sscanf(p, "%*s %d", fx);
		}else if(NULL!=(p=strstr(buff, SFY))){
			num++;
			sscanf(p, "%*s %d", fy);
		}
	}
	fclose(fp_cfg);
	if(num!=11){
		fputs("QDASvgwSkyFormatFits: Config Parameter Err", stdout);
		exit(1);
	}
	return;
}


int CountFitsHeader(char*filename, int*dx, int*dy){
	FILE *fp_in;
	int num=0, bitpix;
	char buff[128];

	if(NULL==(fp_in=fopen(filename, "r"))){
		fputs("QDASvgwSkyFormatFits: Open FITS File Err", stdout);
		exit(1);
	}
	while(80==fread(buff, 1, 80, fp_in)){
		buff[80]=0;
#if(DEBUG>100)
	printf("FITS: %s\n", buff);
#endif
		num++;
		if(0==strncmp(buff, "NAXIS1", 6)) sscanf(buff, "%*s %*s %d", dx);
		else if(0==strncmp(buff, "NAXIS2", 6)) sscanf(buff, "%*s %*s %d", dy);
		else if(0==strncmp(buff, "BITPIX", 6)) sscanf(buff, "%*s %*s %d", &bitpix);
		else if(0==strncmp(buff, "END", 3)) break;
	}
	fclose(fp_in);
	if(bitpix!=-32){
		fputs("QDASvgwSkyFormatFits: Fits File Pixel Format Err", stdout);
		exit(1);
	}
	return(num);
}

void ReadFits(char*filename, int dx, int dy, int headsize, char*header, float*data_in, int fx, int fy, char*date_obs, char*ut, char*hst, float*cirrus, float*cloud){
	FILE *fp_in;
	char *p, s[16];
        
	if(NULL==(fp_in=fopen(filename, "r"))){
		fputs("QDASvgwSkyFormatFits: Open FITS File Err", stdout);
		exit(1);
	}
	if(headsize!=fread(header, 1, headsize, fp_in)){
		fputs("QDASvgwSkyFormatFits: FITS Header Read Err", stdout);
		exit(1);
	}
	header[headsize]=0;
	if(NULL!=(p=strstr(header, "NAXIS1  ="))){
		sprintf(s, "%6d", fx);
		memcpy(p+24, s, 6);
	}
	if(NULL!=(p=strstr(header, "NAXIS2  ="))){
		sprintf(s, "%6d", fy);
		memcpy(p+24, s, 6);
	}
        
	if((dx*dy)!=fread(data_in, 4, dx*dy, fp_in)){
		fputs("QDASvgwSkyFormatFits: FITS Data Read Err", stdout);
		exit(1);
                }
        
	strcpy(date_obs, "----------");
	if(NULL!=(p=strstr(header, "DATE-OBS="))){
		memcpy(date_obs, p+11, 10);
		date_obs[10]=0;
	}
	strcpy(ut, "--------");
	if(NULL!=(p=strstr(header, "UT      ="))){
		memcpy(ut, p+11, 8);
		ut[8]=0;
	}
	strcpy(hst, "--------");
	if(NULL!=(p=strstr(header, "HST     ="))){
		memcpy(hst, p+11, 8);
		hst[8]=0;
	}

	*cirrus=*cloud=0;
	if(NULL!=(p=strstr(header, "A_CIRRUS="))) sscanf(p+11, "%f", cirrus);
	if(NULL!=(p=strstr(header, "A_CLOUD ="))) sscanf(p+11, "%f", cloud);

	fclose(fp_in);
	return;
}


void FitsTransform_IR(float*data_in, float*data_out, int dx, int dy, int cx, int cy, int cr, int fx, int fy, float az, float hole){
	int i, j, k, l, cr2, r2, hr2;
	float val[5], sinrot, cosrot, x1, y1, scale, scale2;
	float scaley, scale2y;

	cr2=cr*cr*(90.0-SKY_EL_LIMIT_IR)*(90.0-SKY_EL_LIMIT_IR)/90.0/90.0;
	hr2=cr*cr*HOLE_R_IR*HOLE_R_IR/90.0/90.0;
	sinrot=(float)sin(-1.0*(SKY_ROT_IR+az)*3.141592653/180.0);
	cosrot=(float)cos(-1.0*(SKY_ROT_IR+az)*3.141592653/180.0);
	scale=(float)SKY_R_IR*90.0/(90.0-SKY_EL_LIMIT_IR)/(float)cr;
	scaley=(float)SKY_R_IR*90.0/(90.0-SKY_EL_LIMIT_IR)/(float)cr*(float)ELLIPSE_IR;
	scale2=(float)SKY_R_IR*90.0/(90.0-SKY_EL_LIMIT_IR)/(float)cr/2.0;
	scale2y=(float)SKY_R_IR*90.0/(90.0-SKY_EL_LIMIT_IR)/(float)cr/2.0*(float)ELLIPSE_IR;

	for(i=0; i<fy; i++){
		for(j=0; j<fx; j++){
			r2=(cx-j)*(cx-j)+(cy-i)*(cy-i);
			if(r2>=cr2) data_out[i*fx+j]=0.0;
			else if(r2<=hr2) data_out[i*fx+j]=hole;
			else{
				x1=ZENITH_X_IR-(cosrot*(float)(cx-j)*SKY_FLIP_IR*scale+sinrot*(float)(cy-i)*scaley);
				y1=ZENITH_Y_IR-(-1.0*sinrot*(float)(cx-j)*SKY_FLIP_IR*scale+cosrot*(float)(cy-i)*scaley);
				if(((x1-scale2)<0.0)||((x1+scale2)>(float)(dx-1))||((y1-scale2y)<0.0)||((y1+scale2y)>(float)(dy-1))){
					data_out[i*fx+j]=0.0;
				}else{
#if(CALCMODE!=1)
					data_out[i*fx+j]=(data_in[(int)x1+dx*(int)y1]*4.0 + data_in[(int)(x1-scale2)+dx*(int)(y1-scale2y)] \
					+ data_in[(int)(x1+scale2)+dx*(int)(y1-scale2y)] + data_in[(int)(x1+scale2)+dx*(int)(y1+scale2y)] \
					+ data_in[(int)(x1-scale2)+dx*(int)(y1-scale2y)]) / 8.0;
#else
					data_out[i*fx+j]=data_in[(int)x1+dx*(int)y1];
#endif
				}
			}
		}
	}
	return;
}


void FitsTransform_Opt(float*data_in, float*data_out, int dx, int dy, int cx, int cy, int cr, int fx, int fy, float az, float hole){
	int i, j;

	for(i=0; i<fy; i++){
		for(j=0; j<fx; j++){
			if((i>(dy-1))||(j>(dx-1))) data_out[i*fx+j]=0.0;
			else data_out[i*fx+j]=data_in[i*dx+j];
		}
	}
	return;
}


void WriteFits(char*filename, int dx, int dy, int headsize, char*header, float*data_out){
	FILE *fp_out;
	char *p, s[16];
	int i, j;

	if(NULL==(fp_out=fopen(filename, "w"))){
		fputs("QDASvgwSkyFormatFits: Write FITS File Err", stdout);
		exit(1);
	}
	if(headsize!=fwrite(header, 1, headsize, fp_out)){
		fputs("QDASvgwSkyFormatFits: FITS Header Write Err", stdout);
		exit(1);
	}
	if((dx*dy)!=fwrite(data_out, 4, dx*dy, fp_out)){
		fputs("QDASvgwSkyFormatFits: FITS Data Write Err", stdout);
		exit(1);
	}
	i=FITSBLOCK-(dx*dy*4+headsize)%FITSBLOCK;
	for(j=0; j<i; j++) header[j]=0;
	if(i!=fwrite(header, 1, i, fp_out)){
		fputs("QDASvgwSkyFormatFits: FITS Tail Write Err", stdout);
		exit(1);
	}

	fclose(fp_out);
	return;
}


void MakeWedge(int dx, int dy, int x1, int y1, int x2, int y2, float wmin, float wmax, float*data_out, int fx, int fy){
	int i, j;
	float width;
	char buff[128];

	width=(float)(x2-x1-2);
	for(i=y1+1; i<y2; i++){
		for(j=x1+1; j<x2; j++){
			data_out[i*fx+j]=wmin+(wmax-wmin)/width*(float)(j-x1-1);
		}
	}
	for(i=y1; i<=y2+2; i++) data_out[i*fx+x1]=wmax;
	for(i=y1; i<=y2+2; i++) data_out[i*fx+x2]=wmax;
	for(i=y2; i<=y2+2; i++) data_out[i*fx+(x1+x2)/2]=wmax;
	for(j=x1; j<=x2; j++) data_out[y1*fx+j]=wmax;
	for(j=x1; j<=x2; j++) data_out[y2*fx+j]=wmax;
	
	sprintf(buff, "%.0f", wmin);
	for(i=0, j=0; i<strlen(buff); i++, j++) MakeFont(buff[i], x1+j*FONT_WIDTH, y2+4, wmax, data_out, fx, 1);
	sprintf(buff, "%.0f", wmax);
	for(i=0, j=0; i<strlen(buff); i++, j++) MakeFont(buff[i], x2+1+j*FONT_WIDTH-strlen(buff)*6, y2+4, wmax, data_out, fx, 1);
	sprintf(buff, "%.0f", (wmin+wmax)/2.0);
	for(i=0, j=0; i<strlen(buff); i++, j++) MakeFont(buff[i], (x1+x2)/2+j*FONT_WIDTH-strlen(buff)*3, y2+4, wmax, data_out, fx, 1);
	return;
}


void MakeUTdate(char*date_obs, char*ut, char*hst, float val, float*data_out, int fx){
	int i, n;
	char buff[64];

	sprintf(buff, "%10s %8s UT  %8s HST", date_obs, ut, hst);
	for(i=0, n=0; i<strlen(buff); i++, n+=FONT_MAGNIFICATION) MakeFont(buff[i], FONT_OFFSET_X+n*FONT_WIDTH, FONT_OFFSET_Y, val, data_out, fx, FONT_MAGNIFICATION);
	return;
}


void MakeCirrusCloudCover(float cirrus, float cloud, float val, float*data_out, int fx){
	int i, n;
	char buff[64];

	sprintf(buff, "CIRRUS/CLOUD COVERAGE : %.2f / %.2f", cirrus, cloud);
	for(i=0, n=0; i<strlen(buff); i++, n+=FONT_MAGNIFICATION) MakeFont(buff[i], CIRRUS_FONT_OFFSET_X+n*FONT_WIDTH, CIRRUS_FONT_OFFSET_Y, val, data_out, fx, FONT_MAGNIFICATION);

	return;
}


void MakeSubaruLogo(float val, float*data_out, int fx, int fy){
	int i, n;
	char buff[64];

	sprintf(buff, "SUBARU TELESCOPE IR CLOUD MONITOR VER 1.1");
	for(i=0, n=0; i<strlen(buff); i++, n+=SUBARU_FONT_MAGNIFICATION) MakeFont(buff[i], SUBARU_FONT_OFFSET_X+n*FONT_WIDTH, fy-SUBARU_FONT_OFFSET_Y, val, data_out, fx, SUBARU_FONT_MAGNIFICATION);

	return;
}


void MakeDirection(float val, float*data_out, int fx, int fy){
	int i, n;
	char buff[64];

	sprintf(buff, "  u");
	for(i=0, n=-2; i<strlen(buff); i++, n+=SUBARU_FONT_MAGNIFICATION) MakeFont(buff[i], fx-DIRECTION_FONT_OFFSET_X+n*FONT_WIDTH, fy-DIRECTION_FONT_OFFSET_Y+2*FONT_HEIGHT, val, data_out, fx, DIRECTION_FONT_MAGNIFICATION);
	sprintf(buff, "  N");
	for(i=0, n=-2; i<strlen(buff); i++, n+=SUBARU_FONT_MAGNIFICATION) MakeFont(buff[i], fx-DIRECTION_FONT_OFFSET_X+n*FONT_WIDTH, fy-DIRECTION_FONT_OFFSET_Y+FONT_HEIGHT, val, data_out, fx, DIRECTION_FONT_MAGNIFICATION);
	sprintf(buff, "lE Wr");
	for(i=0, n=-2; i<strlen(buff); i++, n+=SUBARU_FONT_MAGNIFICATION) MakeFont(buff[i], fx-DIRECTION_FONT_OFFSET_X+n*FONT_WIDTH, fy-DIRECTION_FONT_OFFSET_Y, val, data_out, fx, DIRECTION_FONT_MAGNIFICATION);
	sprintf(buff, "  S");
	for(i=0, n=-2; i<strlen(buff); i++, n+=SUBARU_FONT_MAGNIFICATION) MakeFont(buff[i], fx-DIRECTION_FONT_OFFSET_X+n*FONT_WIDTH, fy-DIRECTION_FONT_OFFSET_Y-FONT_HEIGHT, val, data_out, fx, DIRECTION_FONT_MAGNIFICATION);
	sprintf(buff, "  d");
	for(i=0, n=-2; i<strlen(buff); i++, n+=SUBARU_FONT_MAGNIFICATION) MakeFont(buff[i], fx-DIRECTION_FONT_OFFSET_X+n*FONT_WIDTH, fy-DIRECTION_FONT_OFFSET_Y-2*FONT_HEIGHT, val, data_out, fx, DIRECTION_FONT_MAGNIFICATION);

	return;
}


void MakeFont(char f, int offset_x, int offset_y, float val, float*data_out, int fx, int mag){
	float *p;
	int i, j, k, l;

	if(f=='0') p=font0;
	else if(f=='1') p=font1;
	else if(f=='2') p=font2;
	else if(f=='3') p=font3;
	else if(f=='4') p=font4;
	else if(f=='5') p=font5;
	else if(f=='6') p=font6;
	else if(f=='7') p=font7;
	else if(f=='8') p=font8;
	else if(f=='9') p=font9;
	else if(f=='A') p=fontA;
	else if(f=='B') p=fontB;
	else if(f=='C') p=fontC;
	else if(f=='D') p=fontD;
	else if(f=='E') p=fontE;
	else if(f=='F') p=fontF;
	else if(f=='G') p=fontG;
	else if(f=='H') p=fontH;
	else if(f=='I') p=fontI;
	else if(f=='L') p=fontL;
	else if(f=='M') p=fontM;
	else if(f=='N') p=fontN;
	else if(f=='O') p=fontO;
	else if(f=='P') p=fontP;
	else if(f=='R') p=fontR;
	else if(f=='S') p=fontS;
	else if(f=='T') p=fontT;
	else if(f=='U') p=fontU;
	else if(f=='V') p=fontV;
	else if(f=='W') p=fontW;
	else if(f==':') p=fontCO;
	else if(f=='-') p=fontHI;
	else if(f=='/') p=fontSL;
	else if(f=='.') p=fontPD;
	else if(f=='u') p=fontAU;
	else if(f=='d') p=fontAD;
	else if(f=='r') p=fontAR;
	else if(f=='l') p=fontAL;
	else p=fontSP;

	for(i=0; i<7; i++){
		for(j=0; j<5; j++){
			for(k=0; k<mag; k++){
				for(l=0; l<mag; l++){
					data_out[offset_x+l+j*mag+(offset_y+k+(7-i)*mag)*fx]=p[i*5+j]*val;
				}
			}
		}
	}
	return;
}


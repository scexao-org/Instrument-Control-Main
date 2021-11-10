#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include<math.h>

#define DEBUG 0 

#define AGSS_CFG	"/file/AgAutoSelect.cfg"

#define	sHeader01	"ASSAM :Autoguiding Star Selection for Automated Method"
#define	sHeader02	"                      By"
#define	sHeader03	"George KOSUGI (Subaru Telescope, Hilo, Hawaii)"
#define	sHeader04	"\n"
#define	sHeaderField01	"name\tRA\tDEC\tmag\tFlag\tB-R\tPreference\tPriority\tDst(min)"
#define	sHeaderField02	"----\t--\t---\t----\t----\t---\t----------\t--------\t--------"
#define	sCentRA 	"FieldCenterRA"
#define	sCentDEC	"FieldCenterDEC"
#define	sRangeRA	"FieldRangeRA"
#define	sRangeDEC	"FieldRangeDEC"
#define	sMinMag 	"MinimumMagnitude"
#define	sMaxMag 	"MaximumMagnitude"
#define	sStarNum	"StarNumber"
#define	sPrefNum	"PreferedNumber"
#define	sInsert 	"name"
#define	sBeginBody	"----"
#define KeyNumber	9

#define	DEGtoRAD	0.017453293
#define	InitPreference	10.0
#define	BrightEnd	1.0
#define	BestFlag	2.0
#define	DiffCatalog	1.5

#define	NG	-1
#define	OK	1
#define	NODATA	99

struct AG_Struct {
	double CentRA;
	double CentDEC;
	double RangeRA;
	double RangeDEC;
	double MinMag;
	double MaxMag;
	int StarNum;
	int PrefNum;
};

struct AG_CmdLine {
	int StarNum;
	double TelRA;
	double TelDEC;
	double RangeFOV;
	double LimitMag;
	double PrbRA;
	double PrbDEC;
	char TelFocus[32];
	char Instrument[32];
	double PrbR;
	double PrbT;
	double PrbX;
	double PrbY;
	double Rotate;
	double GoodMag;
	double Scale;
	char FOV_NAME[128];
};

struct AG_Keyword {
	char Key[20];
	int flag;
};

struct AG_List {
	char name[20];
	double RA;
	double DEC;
	double Mag;
	double BR;
	int Flag;
	double Pref;
	double dx;
	double dy;
	double r;
	double t;
};

struct AG_PFPRM {
	double x0;
	double x1;
	double y0;
	double y1;
};

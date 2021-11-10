#include"AG_StarSelection.h"
#include"prototype.h"


static int AG_Func(struct AG_List* ag1, struct AG_List* ag2){
	if(ag1->Pref > ag2->Pref) return(1);
	if(ag1->Pref < ag2->Pref) return(-1);
	return(0);
}

#! /usr/bin/perl

#######################################################
# *** PC version (byte-swap)
#
# usage: jpg2fits source_dir
#
# This script should be alway running.
# (1) Check  $in_dir/full*-0099.jpg
#    if it not exits; do nothing. if it exists, do followings. 
# (2) Check $work_dir, and if it does not exist, create it
# (3) load $sky_file (for sky and flat).
# (4) make fits-header of $output_file.
# (5) load full*-00??.jpg files and averaging, (flat-fielding,)and subtract sky.
# (6) write $output_file to $work_dir.
# (7) convert $output_file from JPG to FITS format
# (8) mv FITS file to $out_dir.
# (9) return to (1).
#
# This script has no stop condition. Please use kill command to kill it.
# 
#
# Convert from jpg images (240x 352) 
# to 32-bit IEEE-754 floating point format FITS image.
#
# created: Naruhisa Takato
# date: 20010728
# modified: 20010804
# modified: 20011003
# modified: 20011003  correct MDJ (add hour-min-sec)
# modified: 20011003 remove offset adjustment 
# modified: 20011016 no message output
# modified: 20011024 $last_file change from "full*-0049.jpg" to "end*.jpg"
#     (if "end.jpg" not work well. Must be include wild card! : glob )
#     systm "rm",$* => system "rm ".$*
# modified: 20011027 output central 159-175 x 116-132 pixel value stdout
# modified: 20011028 offset correction using central 256 pixel value
# modified: 20020619 $output_dir => /mnt/disk2/IR_CLOUD_MONITOR/TMP/
#                 cp $output_file $soss_output_dir => mv
# modified: 20020904  change image processing 
#			output = @buf - $offset - @sky, where offset is @buf - @sky in the central 16x16 pixel region
#                   ==> output = 3"(@buf/$scaling -@sky)+70, where $scaling = @buf/@sky in the area of 20x20 pixel outside the 2ndry.
# modified: 20020920HST  Suppress output after 16:30UT
#                         Add software version No. in FTIS header.
# modified: 20030215HST  bug fixed : JD calculation
#                             <= form 2003.01.01 JD delay 1 or 2 days
# modified: 20040307UT sky and flat changed.
# modified: 20040313UT Set $scaling to 150 when it become zero.
# modified: 20051203UT add horizontal shift adjustment, make new sky file 
#                           and change scaling method.
# modified: 20051225UT change scaling parameter $DISP_MAGNIFY=5; EXPTIME=3.33; 
# modified: 20060330UT change FITS KEY WORD "A_" to "E_".
# last modified: 20060812UT change $DISP_MAGNIFY=5 to 3.
######################################################
#$VERSION="2-1-1";
$VERSION="20060811aHST";
print "Version = ".$VERSION."\n";

##### file directory settings #####
$in_dir="/data/SKYMON/Incoming/";
$work_dir="/data/SKYMON/Process0/";
$out_dir="/data/SKYMON/Process1/";
#$test_dir="/data/SKYMON/test/";

#$last_file = $in_dir."full*-0049.jpg";
$last_file = $in_dir."end*.jpg";
#$sky_test_file = "testsky.txt";
#$sky_file = "sky20040307.txt";
$sky_file = "sky20051203UT.txt";

##### parameter for fits header and display #####
$XSHIFT = -15; # image shift adjustment 
$DISP_OFFSET = 75;
#$DISP_MAGNIFY = 10;
#$DISP_MAGNIFY = 5;
$DISP_MAGNIFY = 3;
$eps = 180;
$LONGITUDE = -((155*60 + 28)*60 +48.8)/15; # sec #
$NAXIS1=352;
$NAXIS2=240;
#$EXPTIME=1.66; # sec: 50 * 1/30 #
$EXPTIME=3.33; # sec: 50 * 1/30 #

##### temporary file name (fits-file) #####
$tempfile=$in_dir."temp.fits";

##### load sky- (= flat-) files (text file) #####
$i=0;
$Nskyave=0;
open IN,"<".$in_dir.$sky_file or die "*** faile to open $sky_file.\n";
while(<IN>){
	@sky[$i] = $_;
	$x=$i%$NAXIS1;
	$y=int($i/$NAXIS1);
	if($x>=70 and $x<=220 and $y>=50 and $y<=200){
		$skyave += $_;
		$Nskyave++;
	}
	$i=$i+1;
}
$skyave=$skyave/$Nskyave;
for($i=0;$i<$NAXIS1*$NAXIS2;$i++){
	@flat[$i] = @sky[$i] / $skyave;
	if(@flat[$i] < 0.01){
		@flat[$i] = 1;
	}
#	print @sky[$i],"\t";
}
close(IN);

while(1){
    sleep 1; ### ryu 040714 ??? ###
    if(glob($last_file)){
	print "START converting...\n";
	### UT ###
	($sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst)=gmtime;
	$year+=1900;
	$mon+=1;
	$DATEOBS=sprintf("'%04d-%02d-%02d'",$year,$mon,$mday);
	$UT=sprintf("'%02d:%02d:%06.3f'",$hour,$min,$sec);

	$mmon=$mon;
	$y=$year+8000;
	if($mmon<3){
		$y=$y-1;
		$mmon+=12;
	}
	
	$JD = $y*365 + int($y/4) - int($y/100) + int($y/400) - 1200820 + int(($mmon*153+3)/5)-92 + $mday - 1 - 0.5 + ($hour+($min+$sec/60)/60)/24;

#	$JD=int(1461*($year+4800)/4)+int(367*($mon-2)/12)
#	     -int(3*int(($year+4900)/100)/4)+$mday-32075-0.5
#             +($hour+($min+$sec/60)/60)/24;

	$MJD=$JD-2400000.5;
	print "MJD=$MJD\n";

	$UThour=$hour;

	##### check dir for output file #####
	if(not (-e $work_dir)){
	    mkdir $work_dir,0777 or die "*** failure: mkdir $work_dir:$!\n"; 
	}
	$output_file_name=sprintf("SkyMonitorPic%04d%02d%02d%02d%02d%02d.fits",
	                       $year,$mon,$mday,$hour,$min,$sec);
	$output_file= $work_dir.$output_file_name;

	##### make fits header #####
	&make_fits_header;

	##### averaging, flat-fielding and subtract sky_ff #####
	
	open OUT, ">>".$output_file
		or die "*** failed to open $output_file.\n";
	sysseek(OUT, 0, 2);

	##### clear buffer for averaging #####
	for($i=0;$i<$NAXIS1*$NAXIS2;$i++){
		@buf[$i]=0;
		@sbuf[$i]=0;
	}

	##### convert jpg-file to gray-file and sum up #####
	@files = glob($in_dir."full*-*.jpg");
	$Naverage=0;
	foreach (@files){
#		print "Now reading $_\n";
		(system "convert",$_,$tempfile)==0
	           or die "*** Failed to convert jpg to fits:$_"; 
		open IN,"<".$tempfile
			or die "*** failed to open $tempfile.\n";
		sysseek(IN,0,0);
		sysread(IN,$header,2880) or die "*** failed to read header of $_.\n";
		for($i=0;$i<$NAXIS1*$NAXIS2;$i++){
			sysread(IN,$rbuf,1);
			@buf[$i] += unpack("C", $rbuf);
		}
		close(IN);
		(system "rm ".$_)==0
	           or die "*** Failed to delete $_"; 
		$Naverage++;
	}
	if($Naverage==0){$Naverage=1;}

        ##### remove flag file #####
	(system "rm ".$last_file)==0
        	or die "*** Failed to delete $last_file"; 

        #### shift image horizontaly (x-direction) in $XSHIFT pixels ####
	$i=0;
	for($k=0;$k<$NAXIS1*$NAXIS2;$k++){
		$x=$k%$NAXIS1;
		$y=int($k/$NAXIS1);
		if($XSHIFT < 0){
			$Xshift=-$XSHIFT;
			if($x>=$Xshift){
				@sbuf[$i]=@buf[$k];
				$i++;
			}
			if($x==$NAXIS1-1){
				for($h=0;$h<$Xshift;$h++){
					@sbuf[$i]=0;
					$i++;
				}
			}
		}
		if($XSHIFT > 0){
			$Xshift=$XSHIFT;
			if($x==0){
				for($h=0;$h<$Xshift;$h++){
					@sbuf[$i]=0;
					$i++;
				}
			}
			if($x<$NAXIS1-$Xshift){
				@sbuf[$i]=@buf[$k];
				$i++;
			}
		}
	}
        #### scaling ####
	$ref=0.000000000;
	$refsky=0.00;
	for($k=0;$k<$NAXIS1*$NAXIS2;$k++){
		$x=$k%$NAXIS1;
		$y=int($k/$NAXIS1);
		if($x>=35 and $x<=55 and $y>=90 and $y<=110){
			$refsky += @sky[$k];
			$ref += @sbuf[$k]/$Naverage;
#print $k."\t".@sky[$k]."\t".$refsky."\t".$ref."\n";
		}
	}

	$scaling = $ref/$refsky;
	if($scaling < 1e-3){$scaling = 1;}
	printf "%s %s %f %f\n",$DATEOBS,$UT,$JD,$scaling;

	##### scaling, subtract sky and flat fielding #####
	for($k=0;$k<$NAXIS1*$NAXIS2;$k++){
#print @sbuf[$k]."\t";
		@sbuf[$k] = @sbuf[$k]/$Naverage/$scaling;
#print @sbuf[$k]."\t";
		@sbuf[$k] -= @sky[$k];
#print @sbuf[$k]."\t";
		@sbuf[$k] /= @flat[$k];
#print @sbuf[$k]."\t";
		@sbuf[$k] *= $DISP_MAGNIFY;
#print @sbuf[$k]."\t";
		@sbuf[$k] += $DISP_OFFSET;
#print @sbuf[$k]."\n";

		syswrite OUT, pack("f",@sbuf[$k]), 1, 3;
		syswrite OUT, pack("f",@sbuf[$k]), 1, 2;
		syswrite OUT, pack("f",@sbuf[$k]), 1, 1;
		syswrite OUT, pack("f",@sbuf[$k]), 1, 0;
	}

	##### make file size to N * 2880 byte #####
	printf OUT "%1920s","";
	close(OUT);

	if(($UThour>=16 and $min>=30) or $UThour>= 17 or $UThour<4){
	    print "Too early; removing $output_file ...";
	    #system "rm ".$output_file;
	    system "mv", $output_file, $out_dir;
	}else{
	    print "moving $output_file to $out_dir ...";
	    system "mv", $output_file, $out_dir;
	}
	print "END\n";
    }
#   print "$last_file has not yet created. I'm waiting...\n";
}
#########################################################
sub make_fits_header{
	
	### values not defined ###
	$CIRRUS = -1;
	$CLOUD = -2;

	### LST ###
	$Tu = ($JD - 2451545.0)/36525;
	$GMST = 24110.54841 + 8640184.812866*$Tu + 0.093104*$Tu*$Tu; # sec #
	$DAY_RATIO = 1.002737909350795 + $Tu*5.9006e-11 - $Tu*$Tu*5.9e-15;
	$UTsec = (($hour*60 + $min)*60 + $sec)*$DAY_RATIO; # sec #
	$LMST = $GMST + $UTsec + $LONGITUDE; # sec #
	if($LMST < 0){
		$LMST +=24*3600;
	}
	$LST = $LMST - int($LMST/86400)*86400; # sec : wrap 24h#
	$LSTh = int($LST/3600);
	$LSTm = int(($LST - $LSTh*3600)/60);
	$LSTs = $LST - $LSTh*3600 - $LSTm*60;
	$LSTstr=sprintf("'%02d:%02d:%06.3f'",$LSTh,$LSTm,$LSTs);

	### HST ###
	($HSTsec, $HSTmin, $HSThour, $HSTmday, $HSTmon, $HSTyear, $HSTwday, $HSTyday, $isdst)=localtime;
	$HST=sprintf("'%02d:%02d:%06.3f'",$HSThour,$HSTmin,$HSTsec);


	open OUT, ">".$output_file
		or die "*** failed to open $output_file.\n";
	@filelist=($outfile);
	chmod 0666, @filelist;

#	$num_key = 25;
	$num_key = 26;
	@key=("SIMPLE","BITPIX","NAXIS","NAXIS1","NAXIS2","BSCALE","BZERO");
	@value=("T","-32","2","352","240","1.0","0.0");
	@comment=(" "," "," "," "," "," "," ");
	for($i=0; $i<7;$i++){
		printf OUT "%-8s=%+21s / %-47s",@key[$i],@value[$i],@comment[$i];
	}
	printf OUT "%-8s= %-20s / %-47s","BUNIT","'ADU     '"," ";
	printf OUT "%-8s= %20s / %-47s","BLANK","-32767"," ";
	printf OUT "%-8s= %-20s / %-47s","TIMESYS","'UTC     '"," ";
	printf OUT "%-8s= %-20s / %-47s","DATE-OBS",$DATEOBS," ";
	printf OUT "%-8s= %-20s / %-47s","UT",$UT," ";
	printf OUT "%-8s= %20.8f / %-47s","MJD",$MJD," ";
	printf OUT "%-8s= %-20s / %-47s","HST",$HST," ";
	printf OUT "%-8s= %-20s / %-47s","LST",$LSTstr," ";
	printf OUT "%-8s= %20.2f / %-47s","EXPTIME",$EXPTIME,"sec";
	printf OUT "%-8s= %-20s / %-47s","OBSERVAT","'NAOJ    '"," ";
	printf OUT "%-8s= %-20s / %-47s","INSTRUME","'Skymonitor'"," ";
	printf OUT "%-8s= %-20s / %-47s","OBJECT","'Skymonitor'"," ";
	printf OUT "%-8s= %-20s / %-47s","DATA-TYP","'Skymonitor'"," ";
	printf OUT "%-8s= %-20s / %-47s","DETECTOR","'Skymonitor'"," ";
	printf OUT "%-8s= %20.2f / %-47s","GAIN",1.00," ";
	printf OUT "%-8s= %20s / %-47s","EXTEND","F"," ";
#	printf OUT "%-8s= %20.2f / %-47s","A_CIRRUS",$CIRRUS,"Cirrus coverage";
#	printf OUT "%-8s= %20.2f / %-47s","A_CLOUD",$CLOUD,"Cloud coverage";
	printf OUT "%-8s= %20.2f / %-47s","E_CIRRUS",$CIRRUS,"Cirrus coverage";
	printf OUT "%-8s= %20.2f / %-47s","E_CLOUD",$CLOUD,"Cloud coverage";
	printf OUT "%-8s= %20.2f / %-47s","VERSION",$VERSION,"Software version";
	printf OUT "%-80s","END";
	for($i=$num_key+1; $i<36; $i++){
		printf OUT "%80s","";
	}
	close(OUT);
}

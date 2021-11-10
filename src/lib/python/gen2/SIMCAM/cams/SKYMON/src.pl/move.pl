#!/usr/bin/perl

# move result image files and flag file from $result_dir to /skymonif
#
# created by Naruhisa Takato
# date: 20010730
# modified 20011003
# modified 20040817	wait and retry if "mv" command fails

$Nmax = 1024; # maximum number of files to be mv'd 

$result_dir="/home/IR_Cloud_Monitor/result_image/";
$dist_dir="/skymonif/";

$flag_file=$dist_dir."QDASvgwSkyRcvFlag.dat";

while(1){
   sleep 1;   #### ryu 040714 ??? ###
#################
if( -e $flag_file){
#	printf "*** Flag file has not yet deleted. --- Do nothing.\n";
}else{
	chdir $result_dir 
      	or die "*** I can't change dir to $result_dir. --- Do nothing.\n";
	@files=glob("*.fits");
	$i=0;
	foreach (@files){
		$i++;
	}
	if($i>0){
		if($i>=$Nmax){
			print "*** file number exceeds $Nmax.\nOnly $Nmax files mv'd. The other files will be sent next time.\n";
		}
		splice @files, $Nmax;

		foreach (@files){
			$arg1 = $result_dir.$_;
			$arg2 = $dist_dir;
			if ((system "mv",$arg1,$arg2)!=0){
### wait and tray again ###
		        	sleep 2; 
				if ((system "mv",$arg1,$arg2)!=0){
					sleep 1;
					(system "mv",$arg1,$arg2)==0    	
       			       			or die "*** failure to mv $arg1 to $arg2.\n";
				}
			}
		}

		open OUT,">".$flag_file
		     or die "*** I can't create $flag_file. Do nothing.\n";
		foreach (@files){
			printf OUT "%s\n",$_;
		}
		printf OUT "END\n";
		close(OUT);

		@files=glob($dist_dir."*.fits");
		chmod 0666,@files;
		@files=($flag_file);
		chmod 0666,@files;
	}
}
#####################
}

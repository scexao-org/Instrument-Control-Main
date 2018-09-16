#!/bin/sh

for i in $(seq 1 20)
do
/home/scexao/bin/sim_chuck 9000 /home/scexao/Documents/ananya/fitsfile/fits_$i.fits
mdate=$(date +"%Y-%m-%d-%H:%M:%S:%N")
#(sleep 10s; echo " $i File appeared at $mdate" > "/home/scexao/Documents/ananya/fits/astromtest_$mdate.txt") &
( sleep 7s ; cp /home/scexao/Documents/ananya/fitsfile/fits_$i.fits /home/scexao/Documents/ananya/fits/f_$i.fits) &
done



#nohup sleep 10 && cp /home/scexao/Documents/ananya/fitsfile/fits_$i.fits /home/scexao/Documents/ananya/fits/f_$i.fits &
#{ cp /home/scexao/Documents/ananya/fitsfile/fits_$i.fits /home/scexao/Documents/ananya/fits/f_$i.fits && sleep 10; } &



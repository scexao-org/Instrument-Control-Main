#!/bin/sh

echo "Keeping DM flat for 12 hours, press ctrl+c to stop."
for i in $(seq 1 24)
do
dmflat
sleep 30m
done


#!/bin/sh

# This is a wrapper file to runup STSradio. It makes use of the
# hostname command to construct the name of the STSradio configuration
# file such that it reads the appropriate omsa_logger log file.
# usage: STSradio_wrapper.sh <STSradio_executable> <STSradio_config>
# Note that we run STSradio with the -t option so that it positions
# the file pointer at the end of the file. Otherwise, it takes a long
# time to read the whole log file, which can be quite large. 

if [ $# -ge 1 ]; then
    STSradio_exe=$1
else
    echo "Error: STSradio executable file not specified"
    exit 1
fi

if [ $# -ge 2 ]; then
    config_file_base=$2
else
    echo "Error: Configuration file base not specified"
    exit 1
fi

config_file_prefix=`hostname`
config_file_full=${config_file_prefix}_$config_file_base

echo "$0 running $STSradio_exe -t -c $config_file_full"
$STSradio_exe -t -c $config_file_full

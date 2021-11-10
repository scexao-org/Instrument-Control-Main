#!/bin/bash

# telstat font setting
#xset +fp /opt/share/ssd/fonts
#xset fp rehash

export PYHOME=/home/gen2/Git/python
export GEN2HOME=$PYHOME/Gen2
export LIBHOME=/home/gen2/lib64/python
export PYTHONPATH=$PYHOME:$LIBHOME:/home/gen2/Git/python/Gen2/telstat/OSSO_TelStatLib:$PYTHONPATH

#export PATH=$PATH

export GEN2COMMON=/home/gen2/gen2
export CONFHOME=$GEN2COMMON/conf
#export LOGHOME=$GEN2COMMON/logs
export DATAHOME=/data
export ARCHHOME=$GEN2COMMON/arch/64

# for TelStat
export SOSSHOME=$ARCHHOME
export LOGHOME=$HOME
export OSS_SOUND=/home/gen2/gen2/conf/product/file/Sounds

python $@


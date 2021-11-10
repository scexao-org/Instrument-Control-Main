#!/bin/bash

export PATH=/usr/local/bin\:$PATH
export PYTHONPATH=$HOME/Svn/python

./daqsink.py --daqdir=/mdata/fits --keyfile=daq.key --passfile=daq.pass --host=g2stat --loglevel=10 --stderr --log=/app/OBC/log/daqsink.log

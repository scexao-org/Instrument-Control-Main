# AAsourceme.csh -- Bruce Bon -- 2006-01-24
#
# Following will setup an environment that will work for the current directory
# structure, but may not work if things are moved.  PYTHONPATH must point to a
# directory under which may be found the SOSSrpc and status directories.
# OSS_SYSTEM must point to a directory containing StatusAlias.def and Table.def.
setenv PYTHONPATH ../..
setenv OSS_SYSTEM ../status

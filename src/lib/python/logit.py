# scexao logging function
#!/usr/bin/env python


from subprocess import Popen as _subprocessPopen

def logit(system_keyword, status, checkfolder=True):
    """
    This function logs ''status'' at the end of ''/media/data/YYYYMMDD/logging/system_keyword.log'', together with a timestamp
    
    inputs:
      **system_keyword** (string <= 10 char) is refering to the system you are dealing with. It is used to create/update the logging file ''system_keyword.log''
      **status** (string) is whatever you want to log about the system referred by ''system_keyword''
      **checkfolder** (bool) set to True will first check for the date folder in ''/media/data/YYYYMMDD'' and create it if it doesn't exist yet
    returns: nothing

    Important note:
      This logging system cannot log faster than 230Hz when ''checkfolder'' is True, and 280Hz when ''checkfolder'' is False.
      Apostrophe (') will be automatically deleted from ''statuts''
    """
    if checkfolder:
        # max frequency of 230Hz
        dummy = _subprocessPopen("/home/scexao/bin/dolog "+str(system_keyword)+" '"+str(status).replace("'","")+"'", shell=True)
    else:
        # max frequency of 280Hz, will return an error if date-folder doesn't exist
        dummy = _subprocessPopen("/home/scexao/bin/dolog -s "+str(system_keyword)+" '"+str(status).replace("'","")+"'", shell=True)


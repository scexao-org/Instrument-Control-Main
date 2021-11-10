#
# db_config.py -- configuration code for Gen2 database
#
# Eric Jeschke (eric@naoj.org)
#
# ***** NOTE: NOTE: NOTE: NOTE *****
#   DO NOT PUT THIS FILE UNDER VERSION CONTROL
#
import os.path

try:
    dbhome = os.path.join(os.environ['GEN2COMMON'], 'db')

except KeyError:
    raise Exception("Please set your GEN2COMMON variable.")

def config(metadata):
    # Choose the back end we will use
    #metadata.bind = "sqlite:///:memory:"
    metadata.bind = ("sqlite:///%s/g2db.sqlite3" % dbhome)

    # Uncomment this to see SQL statements fly by to the back end
    metadata.bind.echo = True


#END

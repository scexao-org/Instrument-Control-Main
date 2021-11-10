#
# Configuration file for remoteObjects
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Thu Jul  8 11:59:27 HST 2010
#]
#

# Port for manager service to run on
managerServicePort = 7070

# Port for name service to run on
nameServicePort    = 7075

# Beginning of range of ports for remote object services
objectsBasePort    = 8000

# Do you want to default to SSL connections (slower)
# NOTE: currently this should be set to False!
default_secure     = False

# Path of default cert file to use for encrypted servers
# NOTE: careful, if you set this then anyone with access to this file
# will run a server with that cert
default_cert       = None

# If set to True, and no explicit authentication is supplied
# servers and clients will resort to using the service name.
# A good idea to leave True, to prevent accidental masquerading.
use_default_auth   = True

# Timeout value for certain known types of remoteObject calls (e.g. nameSvc)
timeout = 10.0

# Default seconds between pings to the remoteObjectsNameSvc
default_ns_ping_interval = 10.0

# Should remoteObject servers be multithreaded by default?
default_threaded_server = True

# Should we allow Long to pass unhindered?  (long is not a part of the
# XML-RPC standard)
allow_long = True

#END


#
# common.py -- code to interface to the Gen2 database
#
# Eric Jeschke (eric@naoj.org)
#

import os, threading
try:
    # Ubuntu 12.04
    from sqlalchemy.exc import SQLAlchemyError as dbError
except ImportError:
    # Ubuntu 10.04
    from sqlalchemy.exceptions import SQLAlchemyError as dbError

# Import schema.
# NOTE: this imports a number of important variables into the module
# namespace, such as 'session' and all the python classes that correspond
# to the table definitions
from schema import *
import Bunch


class g2dbError(Exception):
    pass


try:
    import db_config

    db_config.config(metadata)

except ImportError, e:
    raise g2dbError("Please set your db configuration module")


setup_all()

# LOCKS
# Module-level locks because database is global to all modules
locks = Bunch.Bunch(frame=threading.RLock(),
                    obsnote=threading.RLock())

# ORM ABSTRACTIONS

#END

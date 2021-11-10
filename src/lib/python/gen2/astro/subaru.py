#
# subaru.py -- Miscellaneous Subaru-specific constants, functions, etc.
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Mon Apr 11 11:31:11 HST 2011
#]
#
"""
This module provides various constants and utility functions for
Subaru specific constants.
"""

SUBARU_LONGITUDE = "-155:28:48.900"
SUBARU_LONGITUDE_DEG = -155.47611111111
SUBARU_LATITUDE  = "+19:49:42.600"
SUBARU_LATITUDE_DEG = 19.8285
SUBARU_ALTITUDE_METERS = 4139

# Maximum and minimum commanded AZ/EL for safe operation
CMD_TEL_MAXAZ = 262.0
CMD_TEL_MINAZ = -262.0
CMD_TEL_MAXEL = 89.0
CMD_TEL_MINEL = 15.0

# Some limits for AG
probe_min_range_cs = -150.0
probe_max_range_cs = 150.0
probe_min_range_ns = -150.0
probe_max_range_ns = 150.0
ccd_center_offset_x = 0.0
ccd_center_offset_y = 0.0
ccd_max_width_y    = 512.0


# END

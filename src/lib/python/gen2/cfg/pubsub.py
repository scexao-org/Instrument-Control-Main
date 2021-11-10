#
# Configuration file for the Gen2 Pub/Sub system (aka "monitor")
#
# Eric Jeschke
#
import Bunch
from cfg.INS import INSdata

channels = Bunch.Bunch()

# -- infrastructure channels --
channels.frames = ['names']

# -- interface channels --

# instrument interfaces
ins_data = INSdata()
channels.ins = []
for obcpnum in ins_data.getNumbers(active=True):
    channels.ins.append('INSint%d' % obcpnum)
# TSC simulator
channels.ins.append('INSint%d' % 89)

channels.stars = ['STARSint']
channels.tsc = ['TCSint0']
channels.guider = ['GuiderInt']

# -- service channels --
channels.frames = ['frames']
channels.bootmgr = ['bootmgr']
channels.sessmgr = ['sessions']
#channels.statint = ['statint']
channels.statint = ['statupd']
channels.status = ['status']
# Might need to break this up into multiples like taskmgr...
channels.sound = ['sound']
channels.error = ['errors']

channels.taskmgr = []
for num in (0, 1, 2, 3, 4, 5):
    channels.taskmgr.append('taskmgr%d' % num)

# information from archiver about completed frames
channels.fits = ['fits']

# -- aggregate channels --
aggregates = Bunch.Bunch()
aggregates.INSint = channels.ins
aggregates.taskmgr = channels.taskmgr
# TODO: set this up on a per-session basis inside the session manager
# i.e. taskmanager subscribes to the session feed, which is ad-hoc feed
# formed from allocation info
aggregates.g2task = ['taskmgr', 'frames', 'INSint', 'TCSint0']

channels.aggregates = aggregates.keys()


def setup(pubsub):

    # Add all the channels
    for name in channels.keys():
        pubsub.add_channels(channels[name])

    # Create aggregations
    for name in aggregates.keys():
        pubsub.aggregate(name, aggregates[name])


# END

# OSSC_screenPrintData.py -- Bruce Bon -- 2008-08-26
#
# This is data to be used by OSSC_screenPrint_sim.
# Which dictionary is used will be selected by an environment variable.
# 
# NOTES:
#   - The 'period' tuple provides a set of periods during which a particular
#       value will be used.  For example, if the n-th value of the 'period'
#       tuple is 5, then the n-th value of each alias tuple will be used
#       for 5 cycles, i.e. 5 calls to OSSC_screenPrint.
#   - Unquoted numeric variables the the value tuples below will be
#       interpolated.  For example, if the n-th value of 'period' is 5,
#       the n-th value of the 'TSCS.EL' tuple is 10 and the (n+1)-th value 
#       is 20, then OSSC_screenPrint will return values for 'TSCS.EL' of
#       10, 12, 14, 16 and 18, before moving to the next (n+1) tuple
#       entries.
#   - If you have numeric values which should NOT be interpolated, then
#       quote them.  OSSC_screenPrint only returns strings anyway, so
#       this will force the n-th value to stay constant for period[n]
#       cycles.  This is particularly appropriate for bit-mapped values.

######################################################################
################   assign needed globals   ###########################
######################################################################

# Following selects from among several "test sets", which I have found
# to be necessary since there are far more than 20 combinations of things
# to test.  For now, selection is by editing this variable, but one could
# implement a GUI or command-line option to do the selection dynamically.
# See end of this file for conditional assignments.
ADC_PF_CS       = 1001      # Test ADC at PF and Cs
ADC_NS_ROT_PF   = 1002      # Test ADC at NS, and rotator at PF
ROT_PF_CS_NS    = 1003      # Test rotator at PF, Cs and some Ns
ROT_NS          = 1004      # Test rotator at Ns (the rest)
ROT_NS          = 1004      # Test rotator at Ns (the rest)
AGSV_THRESHOLDS = 1005      # Test AG and SV camera thresholds in Tracking Pane
LIMITS_ALARMS   = 1006      # Test limits alarms, also for probe slew detection
TIP_TILT_CHOP   = 1007      # Test tip/tilt/chopping suffixes to M2 and warning
LIM_WARN_SUPPRES= 1008      # Test az and rot limit warning suppression
IMGROTMODE      = 1009      # Test TSCV.ImgRotMode
FMOSAG          = 1010      # Test FMOS AG modes
NSIRAO          = 1011      # Test NsIR with AO

SimTestSet = NSIRAO
#SimTestSet = None


aliasDict = \
      { 'dictName':
           ('aliasDict0','aliasDict1','aliasDict2','aliasDict3','aliasDict4',
            'aliasDict5','aliasDict6','aliasDict7','aliasDict8','aliasDict9',
            'aliasDict10','aliasDict11','aliasDict12','aliasDict13','aliasDict14',
            'aliasDict15','aliasDict16','aliasDict17','aliasDict18','aliasDict19'),
        'period':
           (5,5,2,5,3,
            5,5,2,5,3,
            5,5,2,5,3,
            5,5,2,5,3),
        
        'FITS.SBR.MAINOBCP':
           ( 'IRCS', 'AO', 'CIAO', 'OHS', 'FOCAS',
             'HDS', 'COMICS', 'SPCAM', 'SUKA', 'MIRTOS',
             'VTOS', 'CAC', 'IRCS', 'AO', 'CIAO',
             'OHS', 'FOCAS', 'HDS', 'COMICS', 'SPCAM' ),

        'FITS.IRC.PROP_ID':
           ( 'IRCS Proposal 1', 'IRCS Proposal 2', 'IRCS Proposal 3', 
             'IRCS Proposal 4', 'IRCS Proposal 5', 'IRCS Proposal 6', 
             'IRCS Proposal 7', 'IRCS Proposal 8', 'IRCS Proposal 9', 
             'IRCS Proposal 10', 'IRCS Proposal 11', 'IRCS Proposal 12', 
             'IRCS Proposal 13', 'IRCS Proposal 14', 'IRCS Proposal 15',
             'IRCS Proposal 16', 'IRCS Proposal 17', 'IRCS Proposal 18', 
             'IRCS Proposal 19', 'IRCS Proposal 20'),
        'FITS.AOS.PROP_ID':
           ( 'AO Proposal 1', 'AO Proposal 2', 'AO Proposal 3', 
             'AO Proposal 4', 'AO Proposal 5', 'AO Proposal 6', 
             'AO Proposal 7', 'AO Proposal 8', 'AO Proposal 9', 
             'AO Proposal 10', 'AO Proposal 11', 'AO Proposal 12', 
             'AO Proposal 13', 'AO Proposal 14', 'AO Proposal 15',
             'AO Proposal 16', 'AO Proposal 17', 'AO Proposal 18', 
             'AO Proposal 19', 'AO Proposal 20'),
        'FITS.CIA.PROP_ID':
           ( 'CIAO Proposal 1', 'CIAO Proposal 2', 'CIAO Proposal 3', 
             'CIAO Proposal 4', 'CIAO Proposal 5', 'CIAO Proposal 6', 
             'CIAO Proposal 7', 'CIAO Proposal 8', 'CIAO Proposal 9', 
             'CIAO Proposal 10', 'CIAO Proposal 11', 'CIAO Proposal 12', 
             'CIAO Proposal 13', 'CIAO Proposal 14', 'CIAO Proposal 15',
             'CIAO Proposal 16', 'CIAO Proposal 17', 'CIAO Proposal 18', 
             'CIAO Proposal 19', 'CIAO Proposal 20'),
        'FITS.OHS.PROP_ID':
           ( 'OHS Proposal 1', 'OHS Proposal 2', 'OHS Proposal 3', 
             'OHS Proposal 4', 'OHS Proposal 5', 'OHS Proposal 6', 
             'OHS Proposal 7', 'OHS Proposal 8', 'OHS Proposal 9', 
             'OHS Proposal 10', 'OHS Proposal 11', 'OHS Proposal 12', 
             'OHS Proposal 13', 'OHS Proposal 14', 'OHS Proposal 15',
             'OHS Proposal 16', 'OHS Proposal 17', 'OHS Proposal 18', 
             'OHS Proposal 19', 'OHS Proposal 20'),
        'FITS.FCS.PROP_ID':
           ( 'FOCAS Proposal 1', 'FOCAS Proposal 2', 'FOCAS Proposal 3', 
             'FOCAS Proposal 4', 'FOCAS Proposal 5', 'FOCAS Proposal 6', 
             'FOCAS Proposal 7', 'FOCAS Proposal 8', 'FOCAS Proposal 9', 
             'FOCAS Proposal 10', 'FOCAS Proposal 11', 'FOCAS Proposal 12', 
             'FOCAS Proposal 13', 'FOCAS Proposal 14', 'FOCAS Proposal 15',
             'FOCAS Proposal 16', 'FOCAS Proposal 17', 'FOCAS Proposal 18', 
             'FOCAS Proposal 19', 'FOCAS Proposal 20'),
        'FITS.HDS.PROP_ID':
           ( 'HDS Proposal 1', 'HDS Proposal 2', 'HDS Proposal 3', 
             'HDS Proposal 4', 'HDS Proposal 5', 'HDS Proposal 6', 
             'HDS Proposal 7', 'HDS Proposal 8', 'HDS Proposal 9', 
             'HDS Proposal 10', 'HDS Proposal 11', 'HDS Proposal 12', 
             'HDS Proposal 13', 'HDS Proposal 14', 'HDS Proposal 15',
             'HDS Proposal 16', 'HDS Proposal 17', 'HDS Proposal 18', 
             'HDS Proposal 19', 'HDS Proposal 20'),
        'FITS.COM.PROP_ID':
           ( 'COMICS Proposal 1', 'COMICS Proposal 2', 'COMICS Proposal 3', 
             'COMICS Proposal 4', 'COMICS Proposal 5', 'COMICS Proposal 6', 
             'COMICS Proposal 7', 'COMICS Proposal 8', 'COMICS Proposal 9', 
             'COMICS Proposal 10', 'COMICS Proposal 11', 'COMICS Proposal 12', 
             'COMICS Proposal 13', 'COMICS Proposal 14', 'COMICS Proposal 15',
             'COMICS Proposal 16', 'COMICS Proposal 17', 'COMICS Proposal 18', 
             'COMICS Proposal 19', 'COMICS Proposal 20'),
        'FITS.SUP.PROP_ID':
           ( 'SPCAM Proposal 1', 'SPCAM Proposal 2', 'SPCAM Proposal 3', 
             'SPCAM Proposal 4', 'SPCAM Proposal 5', 'SPCAM Proposal 6', 
             'SPCAM Proposal 7', 'SPCAM Proposal 8', 'SPCAM Proposal 9', 
             'SPCAM Proposal 10', 'SPCAM Proposal 11', 'SPCAM Proposal 12', 
             'SPCAM Proposal 13', 'SPCAM Proposal 14', 'SPCAM Proposal 15',
             'SPCAM Proposal 16', 'SPCAM Proposal 17', 'SPCAM Proposal 18', 
             'SPCAM Proposal 19', 'SPCAM Proposal 20'),
        'FITS.SUK.PROP_ID':
           ( 'SUKA Proposal 1', 'SUKA Proposal 2', 'SUKA Proposal 3', 
             'SUKA Proposal 4', 'SUKA Proposal 5', 'SUKA Proposal 6', 
             'SUKA Proposal 7', 'SUKA Proposal 8', 'SUKA Proposal 9', 
             'SUKA Proposal 10', 'SUKA Proposal 11', 'SUKA Proposal 12', 
             'SUKA Proposal 13', 'SUKA Proposal 14', 'SUKA Proposal 15',
             'SUKA Proposal 16', 'SUKA Proposal 17', 'SUKA Proposal 18', 
             'SUKA Proposal 19', 'SUKA Proposal 20'),
        'FITS.MIR.PROP_ID':
           ( 'MIRTOS Proposal 1', 'MIRTOS Proposal 2', 'MIRTOS Proposal 3', 
             'MIRTOS Proposal 4', 'MIRTOS Proposal 5', 'MIRTOS Proposal 6', 
             'MIRTOS Proposal 7', 'MIRTOS Proposal 8', 'MIRTOS Proposal 9', 
             'MIRTOS Proposal 10', 'MIRTOS Proposal 11', 'MIRTOS Proposal 12', 
             'MIRTOS Proposal 13', 'MIRTOS Proposal 14', 'MIRTOS Proposal 15',
             'MIRTOS Proposal 16', 'MIRTOS Proposal 17', 'MIRTOS Proposal 18', 
             'MIRTOS Proposal 19', 'MIRTOS Proposal 20'),
        'FITS.VTO.PROP_ID':
           ( 'VTOS Proposal 1', 'VTOS Proposal 2', 'VTOS Proposal 3', 
             'VTOS Proposal 4', 'VTOS Proposal 5', 'VTOS Proposal 6', 
             'VTOS Proposal 7', 'VTOS Proposal 8', 'VTOS Proposal 9', 
             'VTOS Proposal 10', 'VTOS Proposal 11', 'VTOS Proposal 12', 
             'VTOS Proposal 13', 'VTOS Proposal 14', 'VTOS Proposal 15',
             'VTOS Proposal 16', 'VTOS Proposal 17', 'VTOS Proposal 18', 
             'VTOS Proposal 19', 'VTOS Proposal 20'),
        'FITS.CAC.PROP_ID':
           ( 'CAC Proposal 1', 'CAC Proposal 2', 'CAC Proposal 3', 
             'CAC Proposal 4', 'CAC Proposal 5', 'CAC Proposal 6', 
             'CAC Proposal 7', 'CAC Proposal 8', 'CAC Proposal 9', 
             'CAC Proposal 10', 'CAC Proposal 11', 'CAC Proposal 12', 
             'CAC Proposal 13', 'CAC Proposal 14', 'CAC Proposal 15',
             'CAC Proposal 16', 'CAC Proposal 17', 'CAC Proposal 18', 
             'CAC Proposal 19', 'CAC Proposal 20'),
        'FITS.SKY.PROP_ID':
           ( 'SKY Proposal 1', 'SKY Proposal 2', 'SKY Proposal 3', 
             'SKY Proposal 4', 'SKY Proposal 5', 'SKY Proposal 6', 
             'SKY Proposal 7', 'SKY Proposal 8', 'SKY Proposal 9', 
             'SKY Proposal 10', 'SKY Proposal 11', 'SKY Proposal 12', 
             'SKY Proposal 13', 'SKY Proposal 14', 'SKY Proposal 15',
             'SKY Proposal 16', 'SKY Proposal 17', 'SKY Proposal 18', 
             'SKY Proposal 19', 'SKY Proposal 20'),
        'FITS.PI1.PROP_ID':
           ( 'PI1 Proposal 1', 'PI1 Proposal 2', 'PI1 Proposal 3', 
             'PI1 Proposal 4', 'PI1 Proposal 5', 'PI1 Proposal 6', 
             'PI1 Proposal 7', 'PI1 Proposal 8', 'PI1 Proposal 9', 
             'PI1 Proposal 10', 'PI1 Proposal 11', 'PI1 Proposal 12', 
             'PI1 Proposal 13', 'PI1 Proposal 14', 'PI1 Proposal 15',
             'PI1 Proposal 16', 'PI1 Proposal 17', 'PI1 Proposal 18', 
             'PI1 Proposal 19', 'PI1 Proposal 20'),
        'FITS.K3D.PROP_ID':
           ( 'K3D Proposal 1', 'K3D Proposal 2', 'K3D Proposal 3', 
             'K3D Proposal 4', 'K3D Proposal 5', 'K3D Proposal 6', 
             'K3D Proposal 7', 'K3D Proposal 8', 'K3D Proposal 9', 
             'K3D Proposal 10', 'K3D Proposal 11', 'K3D Proposal 12', 
             'K3D Proposal 13', 'K3D Proposal 14', 'K3D Proposal 15',
             'K3D Proposal 16', 'K3D Proposal 17', 'K3D Proposal 18', 
             'K3D Proposal 19', 'K3D Proposal 20'),
        'FITS.VGW.PROP_ID':
           ( 'VGW Proposal 1', 'VGW Proposal 2', 'VGW Proposal 3', 
             'VGW Proposal 4', 'VGW Proposal 5', 'VGW Proposal 6', 
             'VGW Proposal 7', 'VGW Proposal 8', 'VGW Proposal 9', 
             'VGW Proposal 10', 'VGW Proposal 11', 'VGW Proposal 12', 
             'VGW Proposal 13', 'VGW Proposal 14', 'VGW Proposal 15',
             'VGW Proposal 16', 'VGW Proposal 17', 'VGW Proposal 18', 
             'VGW Proposal 19', 'VGW Proposal 20'),
        'FITS.MCS.PROP_ID':
           ( 'MOIRCS Proposal 1', 'MOIRCS Proposal 2', 'MOIRCS Proposal 3', 
             'MOIRCS Proposal 4', 'MOIRCS Proposal 5', 'MOIRCS Proposal 6', 
             'MOIRCS Proposal 7', 'MOIRCS Proposal 8', 'MOIRCS Proposal 9', 
             'MOIRCS Proposal 10', 'MOIRCS Proposal 11', 'MOIRCS Proposal 12', 
             'MOIRCS Proposal 13', 'MOIRCS Proposal 14', 'MOIRCS Proposal 15',
             'MOIRCS Proposal 16', 'MOIRCS Proposal 17', 'MOIRCS Proposal 18', 
             'MOIRCS Proposal 19', 'MOIRCS Proposal 20'),
        'FITS.FMS.PROP_ID':
           ( 'FMOS Proposal 1', 'FMOS Proposal 2', 'FMOS Proposal 3', 
             'FMOS Proposal 4', 'FMOS Proposal 5', 'FMOS Proposal 6', 
             'FMOS Proposal 7', 'FMOS Proposal 8', 'FMOS Proposal 9', 
             'FMOS Proposal 10', 'FMOS Proposal 11', 'FMOS Proposal 12', 
             'FMOS Proposal 13', 'FMOS Proposal 14', 'FMOS Proposal 15',
             'FMOS Proposal 16', 'FMOS Proposal 17', 'FMOS Proposal 18', 
             'FMOS Proposal 19', 'FMOS Proposal 20'),

        'FITS.IRC.OBJECT':
           ( 'NGC 1234', 'NGC 5678', 'NGC 9012', 'NGC 3456', 'NGC 3789',
             'NGC 2234', 'NGC 2678', 'NGC 2012', 'NGC 2456', 'NGC 2789',
             'NGC 3234', 'NGC 3678', 'NGC 3012', 'NGC 3356', 'NGC 3489',
             'NGC 4234', 'NGC 4678', 'NGC 4012', 'NGC 4456', 'NGC 4789'),
        'FITS.AOS.OBJECT':
           ( 'NGC 1234', 'NGC 5678', 'NGC 9012', 'NGC 3456', 'NGC 3789',
             'NGC 2234', 'NGC 2678', 'NGC 2012', 'NGC 2456', 'NGC 2789',
             'NGC 3234', 'NGC 3678', 'NGC 3012', 'NGC 3356', 'NGC 3489',
             'NGC 4234', 'NGC 4678', 'NGC 4012', 'NGC 4456', 'NGC 4789'),
        'FITS.CIA.OBJECT':
           ( 'NGC 1234', 'NGC 5678', '', 'NGC 3456', 'NGC 3789',
             'NGC 2234', 'NGC 2678', 'NGC 2012', 'NGC 2456', 'NGC 2789',
             'NGC 3234', 'NGC 3678', 'NGC 3012', 'NGC 3356', 'NGC 3489',
             'NGC 4234', 'NGC 4678', 'NGC 4012', 'NGC 4456', 'NGC 4789'),
        'FITS.OHS.OBJECT':
           ( 'NGC 1234', 'NGC 5678', 'NGC 9012', 'NGC 3456', 'NGC 3789',
             'NGC 2234', 'NGC 2678', 'NGC 2012', 'NGC 2456', 'NGC 2789',
             'NGC 3234', 'NGC 3678', 'NGC 3012', 'NGC 3356', 'NGC 3489',
             'NGC 4234', 'NGC 4678', 'NGC 4012', 'NGC 4456', 'NGC 4789'),
        'FITS.FCS.OBJECT':
           ( 'NGC 1234', 'NGC 5678', 'NGC 9012', 'NGC 3456', 'NGC 3789',
             'NGC 2234', 'NGC 2678', 'NGC 2012', 'NGC 2456', 'NGC 2789',
             'NGC 3234', 'NGC 3678', 'NGC 3012', 'NGC 3356', 'NGC 3489',
             'NGC 4234', 'NGC 4678', 'NGC 4012', 'NGC 4456', 'NGC 4789'),
        'FITS.HDS.OBJECT':
           ( 'NGC 1234', 'NGC 5678', 'NGC 9012', 'NGC 3456', 'NGC 3789',
             'NGC 2234', 'NGC 2678', 'NGC 2012', 'NGC 2456', 'NGC 2789',
             'NGC 3234', 'NGC 3678', 'NGC 3012', 'NGC 3356', 'NGC 3489',
             'NGC 4234', 'NGC 4678', 'NGC 4012', 'NGC 4456', 'NGC 4789'),
        'FITS.COM.OBJECT':
           ( 'NGC 1234', 'NGC 5678', 'NGC 9012', 'NGC 3456', 'NGC 3789',
             'NGC 2234', 'NGC 2678', 'NGC 2012', 'NGC 2456', 'NGC 2789',
             'NGC 3234', 'NGC 3678', 'NGC 3012', 'NGC 3356', 'NGC 3489',
             'NGC 4234', 'NGC 4678', 'NGC 4012', 'NGC 4456', 'NGC 4789'),
        'FITS.SUP.OBJECT':
           ( 'NGC 1234', 'NGC 5678', 'NGC 9012', 'NGC 3456', 'NGC 3789',
             'NGC 2234', 'NGC 2678', 'NGC 2012', 'NGC 2456', 'NGC 2789',
             'NGC 3234', 'NGC 3678', 'NGC 3012', 'NGC 3356', 'NGC 3489',
             'NGC 4234', 'NGC 4678', 'NGC 4012', 'NGC 4456', 'NGC 4789'),
        'FITS.SUK.OBJECT':
           ( 'NGC 1234', 'NGC 5678', 'NGC 9012', 'NGC 3456', 'NGC 3789',
             'NGC 2234', 'NGC 2678', 'NGC 2012', 'NGC 2456', 'NGC 2789',
             'NGC 3234', 'NGC 3678', 'NGC 3012', 'NGC 3356', 'NGC 3489',
             'NGC 4234', 'NGC 4678', 'NGC 4012', 'NGC 4456', 'NGC 4789'),
        'FITS.MIR.OBJECT':
           ( 'NGC 1234', 'NGC 5678', 'NGC 9012', 'NGC 3456', 'NGC 3789',
             'NGC 2234', 'NGC 2678', 'NGC 2012', 'NGC 2456', 'NGC 2789',
             'NGC 3234', 'NGC 3678', 'NGC 3012', 'NGC 3356', 'NGC 3489',
             'NGC 4234', 'NGC 4678', 'NGC 4012', 'NGC 4456', 'NGC 4789'),
        'FITS.VTO.OBJECT':
           ( 'NGC 1234', 'NGC 5678', 'NGC 9012', 'NGC 3456', 'NGC 3789',
             'NGC 2234', 'NGC 2678', 'NGC 2012', 'NGC 2456', 'NGC 2789',
             'NGC 3234', 'NGC 3678', 'NGC 3012', 'NGC 3356', 'NGC 3489',
             'NGC 4234', 'NGC 4678', 'NGC 4012', 'NGC 4456', 'NGC 4789'),
        'FITS.CAC.OBJECT':
           ( 'NGC 1234', 'NGC 5678', 'NGC 9012', 'NGC 3456', 'NGC 3789',
             'NGC 2234', 'NGC 2678', 'NGC 2012', 'NGC 2456', 'NGC 2789',
             'NGC 3234', 'NGC 3678', 'NGC 3012', 'NGC 3356', 'NGC 3489',
             'NGC 4234', 'NGC 4678', 'NGC 4012', 'NGC 4456', 'NGC 4789'),
        'FITS.SKY.OBJECT':
           ( 'NGC 1234', 'NGC 5678', 'NGC 9012', 'NGC 3456', 'NGC 3789',
             'NGC 2234', 'NGC 2678', 'NGC 2012', 'NGC 2456', 'NGC 2789',
             'NGC 3234', 'NGC 3678', 'NGC 3012', 'NGC 3356', 'NGC 3489',
             'NGC 4234', 'NGC 4678', 'NGC 4012', 'NGC 4456', 'NGC 4789'),
        'FITS.PI1.OBJECT':
           ( 'NGC 1234', 'NGC 5678', 'NGC 9012', 'NGC 3456', 'NGC 3789',
             'NGC 2234', 'NGC 2678', 'NGC 2012', 'NGC 2456', 'NGC 2789',
             'NGC 3234', 'NGC 3678', 'NGC 3012', 'NGC 3356', 'NGC 3489',
             'NGC 4234', 'NGC 4678', 'NGC 4012', 'NGC 4456', 'NGC 4789'),
        'FITS.K3D.OBJECT':
           ( 'NGC 1234', 'NGC 5678', 'NGC 9012', 'NGC 3456', 'NGC 3789',
             'NGC 2234', 'NGC 2678', 'NGC 2012', 'NGC 2456', 'NGC 2789',
             'NGC 3234', 'NGC 3678', 'NGC 3012', 'NGC 3356', 'NGC 3489',
             'NGC 4234', 'NGC 4678', 'NGC 4012', 'NGC 4456', 'NGC 4789'),
        'FITS.VGW.OBJECT':
           ( 'NGC 1234', 'NGC 5678', 'NGC 9012', 'NGC 3456', 'NGC 3789',
             'NGC 2234', 'NGC 2678', 'NGC 2012', 'NGC 2456', 'NGC 2789',
             'NGC 3234', 'NGC 3678', 'NGC 3012', 'NGC 3356', 'NGC 3489',
             'NGC 4234', 'NGC 4678', 'NGC 4012', 'NGC 4456', 'NGC 4789'),
        'FITS.MCS.OBJECT':
           ( 'NGC 1234', 'NGC 5678', 'NGC 9012', 'NGC 3456', 'NGC 3789',
             'NGC 2234', 'NGC 2678', 'NGC 2012', 'NGC 2456', 'NGC 2789',
             'NGC 3234', 'NGC 3678', 'NGC 3012', 'NGC 3356', 'NGC 3489',
             'NGC 4234', 'NGC 4678', 'NGC 4012', 'NGC 4456', 'NGC 4789'),
        'FITS.FMS.OBJECT':
           ( 'NGC 1234', 'NGC 5678', 'NGC 9012', 'NGC 3456', 'NGC 3789',
             'NGC 2234', 'NGC 2678', 'NGC 2012', 'NGC 2456', 'NGC 2789',
             'NGC 3234', 'NGC 3678', 'NGC 3012', 'NGC 3356', 'NGC 3489',
             'NGC 4234', 'NGC 4678', 'NGC 4012', 'NGC 4456', 'NGC 4789'),

        'STATL.AG1_I_BOTTOM':
           ( '1500', '3750', '9600', '16656', '32768' ,
             '1500', '3750', '9600', '16656', '32768' ,
             '1500', '3750', '9600', '16656', '32768' ,
             '1500', '3750', '9600', '16656', '32768' ),
        'STATL.AG1_I_CEIL':
           ( '4096', '8192', '16535', '32768', '65535' ,
             '4096', '8192', '16535', '32768', '65535' ,
             '4096', '8192', '16535', '32768', '65535' ,
             '4096', '8192', '16535', '32768', '65535' ),
        'STATL.AGRERR':
           (0, 100, 100, 750, 1600,
            0, 500, 600, 950, 1000,
            0, 100, 100, 750, 100,
            0, 100, 100, 750, 100),
        'STATL.AG_R_CMD':
           ( -50, 150, 350, 625, -200 ,
             -50, 150, 350, 625, -200 ,
             -50, 150, 350, 625, -200 ,
             -50, 150, 350, 625, -200 ),
        'STATL.AG_THETA_CMD':
           ( -25, 15, 48, 72, -60 ,
             -25, 15, 48, 72, -60 ,
             -25, 'None', 48, 72, -60 ,
             -25, 15, 48, 72, -60 ),
        'STATL.SVRERR':
           (0, 100, 100, 750, 1600,
            0, 100, 100, 750, 1600,
            0, 100, 100, 750, 1600,
            0, 100, 100, 750, 1600),
        'STATL.SV1_I_BOTTOM':
           ( '1500', '3750', '9600', '16656', '32768' ,
             '1500', '3750', '9600', '16656', '32768' ,
             '1500', '3750', '9600', '16656', '32768' ,
             '1500', '3750', '9600', '16656', '32768' ),
        'STATL.SV1_I_CEIL':
           ( '4096', '8192', '16535', '32768', '65535' ,
             '4096', '8192', '16535', '32768', '65535' ,
             '4096', '8192', '16535', '32768', '65535' ,
             '4096', '8192', '16535', '32768', '65535' ),
        'STATL.TELDRIVE':
           ( 'None', 'xzyc', 'Pointing', 'Tracking', 'Tracking(Non-Sidereal)',
             'Slewing', 'Guiding(AG1)', 'Guiding(AG2)', 
                 'Guiding(SV1)', 'Guiding(SV2)',
             'None', 'xzyc', 'Pointing', 'Tracking', 'Tracking(Non-Sidereal)',
             'Slewing', 'Guiding(AG1)', 'Guiding(AG2)', 
                 'Guiding(SV1)', 'Guiding(SV2)' ),
        'STATL.TELDRIVE_INFO':
           ( 'NORMAL', 'WARNING', 'NORMAL', 'ALARM', 'NORMAL' ,
             'ALARM', 'WARNING', 'WARNING', 'ALARM', 'WARNING' ,
             'NORMAL', 'WARNING', 'NORMAL', 'WARNING', 'NORMAL' ,
             'NORMAL', 'WARNING', 'NORMAL', 'WARNING', 'NORMAL' ),
        'STATL.SV_CALC_MODE':
           ( 'AGBAD', 'AGBAD', 'AGBAD', 'AGBAD', 'AGBAD' ,
             'AGBAD', 'AGBAD', 'AGBAD', 'SLIT',  'BSECT' ,
             'AGBAD', 'AGBAD', 'AGBAD', 'AGBAD', 'AGBAD' ,
             'AGBAD', 'AGBAD', 'AGBAD', 'PK',    'CTR' ),

        'STATS.AZDIF':
           (0.0, 0.1, 0.2, 0.1, 0.0,
            0.0, 0.1, 0.2, 0.1, 0.0,
            0.0, 0.1, 0.2, 0.1, 0.0,
            0.0, 0.1, 0.2, 0.1, 0.0),
        'STATS.ELDIF':
           (0.0, 0.1, 0.2, 0.1, 0.0,
            0.0, 0.1, 0.2, 0.1, 0.0,
            0.0, 0.1, 0.2, 0.1, 0.0,
            0.0, 0.1, 0.2, 0.1, 0.0),
        'STATS.EQUINOX':
           ('2000.0000', '2000.0000', '2000.0000', '2000.0000', '2000.0000',
            '1998.0000', '1998.0000', '1998.0000', '1998.0000', '1998.0000',
            '1970.0000', '1970.0000', '1970.0000', '1970.0000', '1970.0000',
            'None', 'None', 'None', 'None', 'None'),
        'STATS.ROTDIF':
           ( 0.00, 18.00, 5.00, 4.00, 3.00,
             2.00, 1.00, 1.00, 1.00, 1.00,
             40.00, 30.00, 20.00, 10.00, 1.00,
             1.00, 1.00, 1.00, 1.00, 1.00 ),
        'STATS.ROTDIF_PF':
           ( 0.00, 12.00, 5.00, 4.00, 3.00,
             2.00, 1.00, 1.00, 1.00, 1.00,
             40.00, 30.00, 20.00, 10.00, 1.00,
             1.00, 1.00, 1.00, 1.00, 1.00 ),

        'TSCL.AG1Intensity':
           ( 10, 0, 600, 0, 1100 ,
             0, 1100, 0, 0, 10 ,
             5000, 0, 10, 100, 100 ,
             5000, 0, 10, 100, 100 ),
        'TSCL.AGPF_X':
           ( 50, 0, 10, 100, 70 ,
             50, 0, 10, 100, 70 ,
             50, 0, 10, 100, 75 ,
             50, 0, 10, 100, 80 ),
        'TSCL.AGPF_X_CMD':
           ( 51, 0, 10, 110, 71 ,
             52, 0, 11, 120, 72 ,
             53, 0, 12, 130, 76 ,
             54, 0, 13, 140, 81 ),
        'TSCL.AGPF_Y':
           ( 19, 0, 10, 17, 70 ,
             19, 0, 10, 17, 70 ,
             19, 0, 10, 17, 75 ,
             19, 0, 10, 17, 80 ),
        'TSCL.AGPF_Y_CMD':
           ( 11, 0, 10, 11, 71 ,
             12, 0, 11, 12, 72 ,
             13, 0, 12, 13, 76 ,
             14, 0, 13, 14, 81 ),
        'TSCL.AG1dX':
           ( 400, 250, 125, -125, -50 ,
             75, 125, 325, -325, -25 ,
             75, 125, 325, -325, -25 ,
             75, 125, 325, -325, -25 ),
        'TSCL.AG1dY':
           ( 75, 125, 325, -325, -25 ,
             400, 250, 125, -125, -50 ,
             75, 125, 325, -325, -25 ,
             75, 125, 325, -325, -25 ),
        'TSCL.CAL_HAL1_AMP':
           (0, 1.2345, 0, 0, 0,
            0, 1.2345, 0, 0, 0,
            0, 1.2345, 0, 0, 0,
            0, 1.2345, 0, 0, 0),
        'TSCL.CAL_HAL2_AMP':
           ('0', '0', '0', '0', '-9.9999',
            '0', '0', '0', '0', '-9.9999',
            '0', '0', '0', '0', '-9.9999',
            '0', '0', '0', '0', '-9.9999'),
        'TSCL.CAL_HCT1_AMP':
           (56.321, 0, 0, 0, 0,
            56.321, 0, 0, 0, 0,
            56.321, 0, 0, 0, 0,
            56.321, 0, 0, 0, 0),
        'TSCL.CAL_HCT2_AMP':
           (0, 0, 0, 1.234, 0,
            0, 0, 0, 1.234, 0,
            0, 0, 0, 1.234, 0,
            0, 0, 0, 1.234, 0),
        'TSCL.CAL_POS':
           (20.56, -10.45, 0.0, 999.999, -999.999,
            20.56, -10.45, 0.0, 999.999, -999.999, 
            20.56, -10.45, 0.0, 999.999, -999.999, 
            20.56, -10.45, 0.0, 999.999, -999.999 ),
        'TSCL.HUMI_I':
           (0.56,25.56,50.56,75.56,45.65,
            0.56,25.56,50.56,75.56,45.65,
            0.56,25.56,50.56,75.56,45.65,
            0.56,25.56,50.56,75.56,45.65),
        'TSCL.HUMI_O':
           (45.65,75.56,50.56,25.56,5.56,
            45.65,75.56,50.56,25.56,5.56,
            45.65,75.56,50.56,25.56,5.56,
            45.65,75.56,50.56,25.56,5.56),
        'TSCL.INSROTPA_PF':
           ( -250.0, 70.1, 100.2, 250.3, -300.4,
             250.0, -70.1, -100.2, -250.3, 300.4,
             -150.0, 10.1, 10.2, 60.3, 30.4,
             150.0, 170.1, 16.2, 250.3, 400.4),
        'TSCL.InsRotPA':
           ( -250.0, 70.1, 100.2, 250.3, -300.4,
             250.0, -70.1, -100.2, -250.3, 300.4,
             -150.0, 10.1, 10.2, 60.3, 30.4,
             150.0, 170.1, 16.2, 250.3, 400.4),
        'TSCL.ImgRotPA':
           ( -250.0, 70.1, 100.2, 250.3, -300.4,
             250.0, -70.1, -100.2, -250.3, 300.4,
             -150.0, 10.1, 10.2, 60.3, 30.4,
             150.0, 170.1, 16.2, 250.3, 400.4),
        'TSCL.LIMIT_FLAG':
           ( '0x01', '0x04', '0x02', '0x08', '0x03',
             '0x05', '0x02', '0x06', '0x0a', '0x04',
             '0x08', '0x0b', '0x0c', '0x0d', '0x0e',
             '0x02', '0x04', '0x01', '0x0f', '0x01'),
        'TSCL.LIMIT_EL_LOW':
           ( '031.1', '005.1', '410.1', '129.1', '001.0',
             '005.1', '000.1', '622.1', '029.1', '003.1',
             '135.1', '120.1', '805.1', '018.1', '002.1',
             '731.1', '201.1', '001.0', '911.1', '008.1'),
        'TSCL.LIMIT_EL_HIGH':
           ( '041.1', '005.1', '110.1', '119.1', '001.1',
             '006.1', '000.0',  '20.1', '019.1', '003.1',
             '145.1', '140.1', '805.1', '018.1', '002.1',
             '721.1', '201.1', '201.1', '  1.1', '008.1'),
        'TSCL.LIMIT_AZ':
           ( '720.1', '000.1', '659.1', '029.1', '002.1',
             '030.1', 'None', '  10.1', '129.1', '001.1',
             '131.1', '040.1', ' 10.1', '014.1', '002.1',
             '031.1', '001.1', '233.1', '  9.1', '011.1'),
        'TSCL.LIMIT_ROT':
           ( '032.1', '000.2', '359.1', '028.1', '001.1',
             '030.1', '001.1', '415.1', '009.1', '001.1',
             '001.1', '240.1', ' 10.1', '015.1', '008.1',
             '231.1', '101.1', '233.1', '919.1', '009.1'),
        'TSCL.SV1DX':
           ( 0.5, 0.25, 0.125, -0.125, -0.5 ,
             0.5, 0.25, 0.125, -0.125, -0.5 ,
             0.5, 0.25, 0.125, -0.125, -0.5 ,
             0.5, 0.25, 0.125, -0.125, -0.5 ),
        'TSCL.SV1DY':
           ( 0.5, -0.5, -0.25, -0.1, 0.2 ,
             0.5, -0.5, -0.25, -0.1, 0.2 ,
             0.5, -0.5, -0.25, -0.1, 0.2 ,
             0.5, -0.5, -0.25, -0.1, 0.2 ),
        'TSCL.SV1Intensity':
           ( 5000, 10, 0, 0, 100 ,
             5000, 10, 0, 10, 100 ,
             10, 0, 0, 0, 0 ,
             10, 10, 10, 10, 10 ),
        'TSCL.TEMP_I':
           (25.56,7.56,-8.56,-15.56,5.56,
            25.56,7.56,-8.56,-15.56,5.56,
            25.56,7.56,-8.56,-15.56,5.56,
            25.56,7.56,-8.56,-15.56,5.56),
        'TSCL.TEMP_O':
           (-29.6,8.56,27.56,2.56,-11.56,
            -29.6,8.56,27.56,2.56,-11.56,
            -29.6,8.56,27.56,2.56,-11.56,
            -29.6,8.56,27.56,2.56,-11.56),
        'TSCL.TSFPOS':
           (3.008, 3.008, 5.008, 5.008, 16.008,
            3.008, 3.008, 3.008, 3.008, 3.008, 
            16.008, 16.008, 10.0, 15.0, 20.0,
            20.0, 20.0, 10.0, 15.0, 20.0),
        'TSCL.TSRPOS':
           (1.507, 1.507, 1.507, 1.507, 1.507, 
            1.507, 1.507, 9.997, 9.997, 10.007,
            10.007, 10.007, 5.0, 10.0, 20.0,
            20.0, 20.0, 5.0, 10.0, 20.0),
        'TSCL.WINDSPOS':
           (4.0, 6.1, 7.2,  8.1, 14.7,
            14.9, 5.1, 6.2, 14.1, 14.9,
            2.0, 5.1, 6.2,  8.1, 14.9,
            2.0, 5.1, 6.2, 14.1, 14.9),
        'TSCL.WINDSCMD':
           (2.0, 5.1, 6.2,  8.1, 14.9,
            14.9, 7.1, 9.2, 14.1, 14.9,
            2.0, 5.1, 6.2,  8.1, 14.9,
            2.0, 5.1, 6.2, 14.1, 14.9),
        'TSCL.WINDS_I':
           (0.0,5.0,10.00,15.56,19.3,
            0.0,5.0,10.00,15.56,19.3,
            0.0,5.0,10.00,15.56,19.3,
            0.0,5.0,10.00,15.56,19.3),
        'TSCL.WINDS_O':
           (19.3,15.56,10.56,5.56,1.56,
            19.3,15.56,10.56,5.56,1.56,
            19.3,15.56,10.56,5.56,1.56,
            19.3,15.56,10.56,5.56,1.56),
        'TSCL.Z':
           (-93.0, 6.1, 17.2, 80.1, -20.0,
            -93.0, 6.1, 17.2, 80.1, -20.0,
            -93.0, 6.1, 17.2, 80.1, -20.0,
            -93.0, 6.1, 17.2, 80.1, -20.0),

        'TSCS.ALPHA':
           ('0000000000','0100000000','0500000000','0700000000','1100000000',
            '1700000000','3400000000','3900000000','2300000000','2500000000',
            '1800000000','1759000000','1758000000','0743000000','0722000000',
            '1800000000','1759000000','1758000000','0743000000','0722000000'),
        'TSCS.ALPHA_C':
           ('1802300000','1902300000','1802300000','1002300000','0902300000',
            '1802300000','1902300000','1802300000','1002300000','0902300000',
            '1802300000','1902300000','1802300000','1002300000','0902300000',
            '1802300000','1902300000','1802300000','1002300000','0902300000'),
        'TSCS.AZ':
           (-245.0, -265.0, -269.0, -269.6, -272.0,
            -245.0, 'None',  -10.1,   65.1,  160.5,
             245.0,  265.0,  269.0,  269.5,  160.0,
              65.1, -245.0, -269.0, -269.6, -270.0),
        'TSCS.AZ_CMD':
           (-250.0, -269.0, -269.6, -272.0, -252.0,
             -85.0,  -45.0, 'None',   75.1,  169.5,
             255.0,  269.0,  269.9,  269.0,  150.0,
              65.1, -245.0, -269.0, -269.6, -270.0),
        'TSCS.DELTA':
           ('8060000000','8050000000','8040000000',' 060000000',' 040000000',
            '8060000000','8050000000','8040000000',' 060000000',' 040000000',
            '8060000000','8050000000','8040000000',' 060000000',' 040000000',
            '8060000000','8050000000','8040000000',' 060000000',' 040000000'),
        'TSCS.DELTA_C':
           ('8062500000','8042500000','8032500000',' 062500000',' 064500000',
            '8062500000','8042500000','8032500000',' 062500000',' 064500000',
            '8062500000','8042500000','8032500000',' 062500000',' 064500000',
            '8062500000','8042500000','8032500000',' 062500000',' 064500000'),
        'TSCS.EL':
           (90.0,90.0,90.0,90.0,90.0,
            90.0,90.0,90.0,90.0,90.0,
            70.980,48.980,20.980, 4.980,90.0,
            60.980,38.980,10.980,10.980,80.980),
        'TSCS.EL_CMD':
           (90.0,90.0,90.0,90.0,90.0,
            70.980,48.980,20.980, 4.980,90.0,
            60.980,38.980,10.980,10.980,80.980,
            70.980,48.980,20.980, 5.980,90.0),
        # INSROTPOS_PF ADC_NS_ROT_PF and most others:
        'TSCS.INSROTPOS_PF':
           (32.794,74.293,96.293,-3.293,-30.293,
            32.794,30.794,15.794,-26.794,22.794,
            32.794,30.794,15.794,-26.794,22.794,
            32.794,30.794,'None',-26.794,22.794),
        'TSCS.INSROTCMD_PF':
           (133.293,96.293,96.293,-3.293,-30.293,
            133.293,96.293,74.293,-3.293,-30.293,
            133.293,96.293,74.293,-3.293,-30.293,
            133.293,96.293,74.293,'None',-30.293),
        'TSCS.INSROTPOS':
           (32.794,30.794,15.794,-26.794,22.794,
            32.794,'None',30.794,-3.293,-30.293,
            32.794,30.794,30.794,-3.293,-30.293,
            32.794,30.794,30.794,-3.293, 22.794),
        'TSCS.INSROTCMD':
           (133.293,96.293,74.293,-3.293,-30.293,
            133.293,96.293,'None',-3.293,-30.293,
            133.293,74.293,96.293,-3.293,-30.293,
            133.293,74.293,74.293,-3.293,-30.293),
        'TSCS.ImgRotPos':
           (32.794,30.794,15.794,-26.794,22.794,
            32.794,'None',30.794,-3.293,-30.293,
            32.794,30.794,30.794,-3.293,-30.293,
            32.794,30.794,30.794,-3.293, 22.794),
        'TSCS.IMGROTCMD':
           (133.293,96.293,74.293,-3.293,-30.293,
            133.293,96.293,'None',-3.293,-30.293,
            133.293,74.293,96.293,-3.293,-30.293,
            133.293,74.293,74.293,-3.293,-30.293),

        'TSCV.ADCInOut':
           ('0x10', '0x08', '0x08', '0x10', '0x08',
            '0x10', '0x08', '0x08', '0x08', '0x03',
            '0x10', '0x80', '0x80', '0x10', '0x80',
            '0x10', '0x80', '0x80', '0x10', '0x80'),
        'TSCV.ADCONOFF_PF':
           ('0x01', '0x01', '0x00', '0x02', '0x02',
            '0x01', '0x02', '0x01', '0x01', '0x02',
            '0x01', '0x02', '0x01', '0x01', '0x02',
            '0x01', '0x02', '0x01', '0x01', '0x02'), 
        'TSCV.ADCMODE_PF':
           ('0x40', '0x80', '0x40', '0x40', '0x80',
            '0x40', '0x80', '0x80', '0x40', '0x80',
            '0x04', '0x80', '0x80', '0x04', '0x80',
            '0x40', '0x80', '0x80', '0x40', '0x80'), 
        'TSCV.ADCOnOff':
           ('0x0f', '0x02', '0x01', '0x01', '0x02',
            'None', '0x02', '0x01', '0x01', '0x01',
            '0x01', '0x0f', '0x01', '0x01', 'None',
            '0x02', '0x01', '0x01', '0x01', '0x01'), 
        'TSCV.ADCMode':
           ('0x04', '0x08', '0x08', '0x04', '0x08',
            '0x04', '0x08', 'None', '0x40', '0x80',
            '0xff', '0x08', '0x08', '0x04', '0x08',
            '0x04', '0x08', '0x08', '0x04', '0x08'), 


        'TSCV.AGExpTime':
           ( '1000', '5000', '6000', '10000', '30000' ,
             '1000', '5000', '6000', '10000', '30000' ,
             '1000', '5000', '60000', '600000', '300000' ,
             '1000', '5000', '60000', '600000', '300000' ),
        'TSCV.AGR':
           ( -200, -50, 150, 350, 625 ,
             -200, -50, 150, 350, 625 ,
             -200, -50, 150, 350, 625 ,
             -200, -50, 150, 350, 625 ),
        'TSCV.AGTheta':
           ( -60, -25, 15, 48, 72 ,
             -60, -25, 15, 48, 72 ,
             -60, -25, 15, 'None', 72 ,
             -60, -25, 15, 48, 72 ),
        'TSCV.CAL_HCT_LAMP1':
           ('0x55', '0xaa', '0xaa', '0xaa', '0xaa',
            '0xaa', '0x9a', '0xa6', '0xaa', '0xaa',
            '0xaa', '0xaa', '0xaa', '0xaa', '0xaa',
            '0xaa', '0xff', '0xaa', '0xaa', '0xaa'),
        'TSCV.CAL_HCT_LAMP2':
           ('0x0a', '0x05', '0x0a', '0x0a', '0x0a',
            '0x0a', '0x0a', '0x0a', '0x09', '0x0a',
            '0x0a', '0x0a', '0x0a', '0x0a', '0x0a',
            '0x0a', '0x0a', '0x0a', '0x03', '0x0a'),
        'TSCV.CAL_HAL_LAMP1':
           ('0x2a', '0x2a', '0x15', '0x2a', '0x2a',
            '0x2a', '0x2a', '0x1a', '0x2a', '0x1a',
            '0x29', '0x2a', '0x2a', '0x2a', '0x2a',
            '0x2a', '0x2a', '0x2a', '0x2a', '0x00'),
        'TSCV.CAL_HAL_LAMP2':
           ('0x2a', '0x2a', '0x2a', '0x15', '0x2a',
            '0x2a', '0x2a', '0x2a', '0x26', '0x1a',
            '0x2a', '0x26', '0x2a', '0x2a', '0x29',
            '0x2a', '0x2a', '0x2a', '0x2a', '0x2a'),
        'TSCV.CAL_RGL_LAMP1':
           ('0x22', '0x22', '0x22', '0x22', '0x11',
            '0x22', '0x22', '0x22', '0x22', '0x22',
            '0x22', '0x22', '0x12', '0x12', '0x22',
            '0x22', '0x22', '0x22', '0x22', '0x22'),
        'TSCV.CAL_RGL_LAMP2':
           ('0x22', '0x22', '0x22', '0x22', '0x22',
            '0x11', '0x22', '0x22', '0x22', '0x22',
            '0x22', '0x21', '0x12', '0x21', '0x00',
            '0x22', '0x22', '0x22', '0x22', '0x22'),
        'TSCV.CellCover':
           ('0x04', 'None', '0x00', '0x01', '0x01',
            '0x01', '0x31', '0x42', '0x03', '0x06',
            '0x00', '0x04', '0x04', '0x00', '0x01',
            '0x01', '0x01', '0x00', '0x04', '0x02'), 
        'TSCV.DomeFF_1B':
           ('0x04','0x08','0x04','0x04','0x04',
            '0x04','0x08','0x04','0x04','0x04',
            '0x04','0x08','0x04','0x04','0x04',
            '0x0a','0x00','0x04','0x0c','0x04'),
        'TSCV.DomeFF_2B':
           ('0x20','0x10','0x10','0x20','0x20',
            '0x20','0x10','0x10','0x20','0x0f',
            '0x20','0x00','0x10','0x30','0x20',
            '0x20','0x20','0x10','0x20','0x20'),
        'TSCV.DomeFF_3B':
           ('0x02','0x02','0x02','0x01','0x02',
            '0x02','0x02','0x03','0x01','0x02',
            '0x02','0x02','0x02','0x01','0x02',
            '0x02','0x02','0x02','0x01','0x02'),
        'TSCV.DomeFF_4B':
           ('0x08','0x08','0x08','0x08','0x0a',
            '0x00','0x08','0x08','0x08','0x00',
            '0x08','0x08','0x08','0x08','0x0f',
            '0x08','0x08','0x08','0x08','0x04'),
        'TSCV.DomeFF_A':
           ('0x01','0x03','0x02','0x00','0x02',
            '0x01','0x02','0x02','0x02','0x02',
            '0x01','0x02','0x02','0x02','0x02',
            '0x01','0x02','0x02','0x02','0x02'),
        'TSCV.DomeShutter':
           ('0x50', '0x50', '0x50', '0x50', '0x50',
            '0x50', '0x50', '0x50', '0x30', '0x30',
            '0x10', '0x10', '0x40', '0x30', '0x50',
            '0x10', '0x10', '0x40', '0x30', '0x50'), 

       'TSCV.FOCUSINFO':
          ('None', '00000100', '00000200', '00000400', '00000800',
           '0010', '00001000', '00002000', '00004000', '00008000',
           '0020', '00000001', '00000002', '00000004', '00000008',
           '0040', '00000010', '00000020', '00000040', '00000080'),
       'TSCV.FOCUSINFO2':
          ('None', '00', '00', '00', '00',
           '00',   '00', '00', '00', '00',
           '00',   '00', '00', '00', '00',
           '00',   '00', '00', '00', '00'),
        'TSCV.FOCUSALARM':
           ('None', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00',
            '0x10', '0x10', '0x08', '0x08', '0x18'),

        'TSCV.INSROTROTATION_PF':
           ('0x10', '0x20', '0x30', '0x10', '0x10', 
            '0x20', '0x30', '0x00', '0x10', '0x20', 
            '0x30', '0x00', '0x10', '0x20', '0x30', 
            '0x00', '0x10', '0x20', '0x30', '0x02'),

        # INSROTMODE_PF ADC_PF_CS, ADC_NS_ROT_PF, ROT_PF_CS_NS, ROT_NS:
        'TSCV.INSROTMODE_PF':
           ('0x20', '0x10', '0x40', '0x10', '0x10', 
            '0x20', '0x30', '0x00', '0x10', '0x20', 
            '0x30', '0x00', '0x10', '0x20', '0x30', 
            '0x00', 'None', '0x20', '0x30', '0x00'),

        # InsRotRotation ADC_PF_CS, ADC_NS_ROT_PF, ROT_PF_CS_NS, ROT_NS:
        'TSCV.InsRotRotation':
           ('0x01', '0x02', '0x03', '0x00', '0x01',  
            '0x02', '0x03', '0x00', '0x02', '0x01', 
            '0x01', '0x01', '0x04', '0x02', '0x03', 
            '0x00', '0x01', '0x02', '0x03', '0x00'),

        # InsRotMode ADC_PF_CS, ADC_NS_ROT_PF, ROT_PF_CS_NS, ROT_NS:
        'TSCV.InsRotMode':
           ('0x01', '0x02', '0x03', '0x00', '0x01', 
            '0x02', '0x03', '0x00', '0x01', '0x02', 
            '0x01', '0x40', '0x01', 'None', '0x01', 
            '0x01', '0x01', '0x04', '0x03', '0x00'),

        # ImgRotRotation ADC_PF_CS, ADC_NS_ROT_PF, ROT_PF_CS_NS, ROT_NS:
        'TSCV.ImgRotRotation':
           ('0x01', '0x01', '0x01', '0x01', '0x01', 
            '0x01', '0x01', '0x01', '0x01', '0x02', 
            '0x01', '0x01', '0x01', '0x01', '0x01', 
            '0x01', '0x01', '0x01', '0x03', '0x02'),

        # ImgRotMode ADC_PF_CS, ADC_NS_ROT_PF, ROT_PF_CS_NS, ROT_NS:
        'TSCV.ImgRotMode':
           ('0x02', '0x02', '0x01', '0x40', '0x40', 
            '0x01', '0x40', '0x01', '0x01', '0x01', 
            '0x02', '0x01', '0x02', '0x01', '0x02', 
            '0x01', 'None', '0x01', '0x01', '0x01'),

        # ImgRotType ADC_PF_CS, ADC_NS_ROT_PF, ROT_PF_CS_NS, ROT_NS:
        'TSCV.ImgRotType':
           ('0x12', '0x0C', '0x12', '0x0c', '0x04',
            '0x04', '0x04', '0x0f', 'None', '0x04',
            'None', '0x0f', '0x10', '0x04', '0x14',
            '0x12', '0x0C', '0x12', '0x12', '0x0C'), 

        'TSCV.M1Cover':
           ('0x1111111111111111111111', 'None',
            '0x1111111111111111111111', '0x1111111111111111111111',
            '0x1111111111111111111111', '0x1111111111111111111111',
            '0x1111111111111111111111', '0x4444444444444444444444',
            '0x8888888888888888888888', '0x3333333333333333333333',
            '0xffffffffffffffffffffff', '0x1111111111111111111111',
            '0x4444444444444444444444', '0x8888888888888888888888',
            '0x3333333333333333333333', '0xffffffffffffffffffffff',
            '0x1111111111111111111111', '0x4444444444444444444444',
            '0x8888888888888888888888', '0x3333333333333333333333'), 
        'TSCV.M1CoverOnway':
           ('0x00', '0x00', '0x00', '0x00', 'None',
            '0x00', '0x00', '0x00', '0x02', '0x02',
            '0x00', '0xFF', '0xf0', '0x0f', '0x44',
            '0x00', '0xFF', '0xf0', '0x0f', '0x44'),
        'TSCV.M2Drive':
           ('0x01', '0x02', '0x04', '0x08', '0x10',
            '0xff', '0xf2', '0x0f', '0xf0', '0xf0f0f010',
            '0x01', '0x02', '0x04', '0x08', '0x10',
            '0x01', '0x02', '0x04', '0x08', '0x10'), 
        'TSCV.PROBE_LINK':
           ( '0x00', '0x00', '0x00', '0x01', '0x01',
             '0x01', '0x01', '0x00', '0x00', '0x00',
             '0x00', '0x00', '0x00', '0x01', '0x01',
             '0x01', '0x01', '0x00', '0x00', '0x00'),
        'TSCV.RotatorType':
           ('0x08','0x08','0x08','0x08',
            '0x10','0x10','0x10','0x10',
            '0x01','0x01','0x01','0x01',
            '0x02','0x02','0x02','0x02',
            '0x04','0x04','0x04','0x04'),
        'TSCV.SVExpTime':
           ( '60000', '50000', '10000', '6000', '3000' ,
             '60000', '50000', '10000', '6000', '3000' ,
             '600000', '5000', '1000', '60000', '300000' ,
             '600000', '5000', '1000', '60000', '300000' ),
        'TSCV.TopScreen':
           ('0x08', '0x04', '0x10', '0x00', '0x04',
            '0x08', '0x04', '0x08', '0x00', '0x04',
            '0x08', '0x04', '0x08', '0x10', '0x04',
            '0x08', '0x04', '0x08', '0x10', '0x04'), 
        'TSCV.TT_Mode':
           ('0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00'), 
        'TSCV.TT_Drive':
           ('0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00'), 
        'TSCV.TT_DataAvail':
           ('0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00'), 
        'TSCV.TT_ChopStat':
           ('0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00'), 
        'TSCV.WINDSDRV':
           ('0x08', '0x00', '0x08', '0x04', '0x04',
            '0x04', '0x04', '0x04', '0x04', '0x0C',
            '0x08', '0x04', '0x00', '0x04', '0x08',
            '0x0F', '0x0F', '0x0F', '0x04', '0x08'), 
        'TSCV.WindScreen':
           ('0x01', '0x01', '0x01', '0x02', '0x01',
            '0x01', '0x02', '0x01', '0x01', '0x02',
            '0x01', '0x02', '0x01', '0x01', '0x02',
            '0x01', '0x02', '0x01', '0x01', '0x02'), 


        'VGWD.FWHM.AG':
           ( 1.78, 1.33, 0.76, 0.45, 0.33,
             1.78, 1.33, 0.76, 0.45, 0.33,
             1.78, 1.33, 0.76, 0.45, 0.33,
             1.78, 1.33, 0.76, 0.45, 0.33),
        'VGWD.FWHM.SV':
           ( 1.78, 1.33, 0.76, 0.45, 0.33,
             1.78, 1.33, 0.76, 0.45, 0.33,
             1.78, 1.33, 0.76, 0.45, 0.33,
             1.78, 1.33, 0.76, 0.45, 0.33),

        'test.addition':
           ('testVal1','testVal1','testVal1','testVal1','testVal1',
            'testVal1','testVal1','testVal1','testVal1','testVal1',
            'testVal1','testVal1','testVal1','testVal1','testVal1',
            'testVal1','testVal1','testVal1','testVal1','testVal1')
        
      }

# Changes for specific test sets
if  SimTestSet == ADC_PF_CS:
    aliasDict['TSCV.ADCInOut'] =    \
           ('0x10', '0x08', '0x08', '0x10', '0x08',
            '0x10', '0x08', '0x08', '0x08', '0x03',
            'None', '0x10', '0x08', '0x10', '0x08',
            '0x08', '0x08', '0x08', '0x08', '0x08')
    aliasDict['TSCV.ADCONOFF_PF'] =    \
           ('0x01', '0x02', 'None', '0x02', '0x01',
            '0x01', '0x01', '0x01', '0x0f', '0x0f',
            '0x01', '0x02', '0x01', '0x01', 'None',
            '0x02', '0x01', '0x01', '0x01', '0x01')
    aliasDict['TSCV.ADCMODE_PF'] =    \
           ('0x40', '0x80', '0x40', '0x40', 'None',
            '0x40', '0x80', '0xff', '0x40', '0x80',
            '0x04', '0x80', '0x80', '0x04', '0x80',
            '0x40', 'None', '0x40', '0x80', '0xff')
    aliasDict['TSCV.ADCOnOff'] =    \
           ('0x01', '0x02', '0x01', '0x01', '0x02',
            '0x01', '0x02', '0x01', '0x04', '0x02',
            '0x01', '0x02', '0x01', '0x01', 'None',
            '0x02', '0x01', '0x01', '0x01', '0x01')
    aliasDict['TSCV.ADCMode'] =    \
           ('0x04', '0x08', '0x08', '0x04', '0x08',
            '0x04', '0x08', '0x08', '0x04', '0x08',
            '0x04', '0x08', '0x08', '0x04', '0x08',
            '0x04', 'None', '0x04', '0x08', '0xff')
    aliasDict['TSCV.FOCUSINFO'] =    \
           ('None',     'ffffff00', '01000000', '01000000', '01000000',
            '01000000', '01000000', '01000000', '01000000', '00000080',
            '04000000', '08000000', '04000000', '04000000', '08000000', 
            '08000000', '08000000', '08000000', '08000000', '08000000')
    aliasDict['TSCV.FOCUSALARM'] =    \
           ('0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00')
    aliasDict['TSCV.INSROTROTATION_PF'] =    \
           ('0x10', '0x20', '0x30', '0x10', '0x10', 
            '0x20', '0x30', '0x00', '0x10', '0x20', 
            '0x30', '0x00', '0x10', '0x20', '0x30', 
            '0x00', '0x10', '0x20', '0x30', '0x02')

elif  SimTestSet == ADC_NS_ROT_PF:
    aliasDict['TSCV.ADCInOut'] =    \
           ('0x08', 'None', '0x10', '0x08', '0x10',
            '0x08', '0x08', '0x08', '0x08', '0x08',
            '0x08', '0x08', '0x08', '0x08', '0x08',
            '0x08', '0x08', '0x08', '0x08', '0x08') 
    aliasDict['TSCV.ADCONOFF_PF'] =    \
           ('0x0f', '0x01', '0x00', '0x02', '0x02',
            'None', '0x02', '0x01', '0x01', '0x01',
            '0x01', '0x0f', '0x01', '0x01', '0x01',
            '0x01', '0x01', '0x01', '0x01', '0x01')
    aliasDict['TSCV.ADCMODE_PF'] =    \
           ('0x40', '0x80', '0x40', '0x40', '0x80',
            '0x40', '0x80', 'None', '0x40', '0x80',
            '0xff', '0x80', '0x80', '0x04', '0x80',
            '0x40', '0x80', '0x80', '0x40', '0x80')
    aliasDict['TSCV.ADCOnOff'] =    \
           ('0x0f', '0x02', '0x01', '0x01', '0x02',
            'None', '0x02', '0x01', '0x01', '0x01',
            '0x01', '0x0f', '0x01', '0x01', 'None',
            '0x02', '0x01', '0x01', '0x01', '0x01')
    aliasDict['TSCV.ADCMode'] =    \
           ('0x04', '0x08', '0x08', '0x04', '0x08',
            '0x04', '0x08', 'None', '0x04', '0x08',
            '0xff', '0x08', '0x08', '0x04', '0x08',
            '0x04', '0x08', '0x08', '0x04', '0x08')
    aliasDict['TSCV.FOCUSINFO'] =    \
           ('08000000', '10000000', '20000000', '40000000', '00010000',
            '80000000', '00020000', '00200000', '00800000', '00000200',
            '00004000', '00000001', 'None',     '00000020', '01000000', 
            '01000000', '01000000', '02000000', '01000000', '02000000')
    aliasDict['TSCV.FOCUSALARM'] =    \
           ('0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x40',
            '0x80', '0x00', '0x00', '0x00', '0x00')
    aliasDict['TSCV.INSROTROTATION_PF'] =    \
           ('0x10', '0x20', '0x30', '0x10', '0x10', 
            '0x20', '0x30', '0x00', '0x10', '0x20', 
            '0x30', '0x00', '0x10', '0x20', '0x30', 
            '0x00', '0x10', '0x20', '0x30', '0x02')

elif  SimTestSet == ROT_PF_CS_NS:
    aliasDict['TSCV.FOCUSINFO'] =    \
           ('01000000', '02000000', '01000000', '02000000', '04000000',
            '04000000', '04000000', '08000000', '00001000', '04000000',
            '08000000', '00001000', '04000000', '08000000', '10000000', 
            '10000000', '00040000', '40000000', '40000000', '40000000')
    aliasDict['TSCV.FOCUSALARM'] =    \
           ('0x00', '0x00', '0x00', '0x00', '0x40',
            '0x80', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x40',
            '0x80', '0x00', '0x00', '0x00', '0x00')
    aliasDict['TSCV.INSROTROTATION_PF'] =    \
           ('0x01', '0x01', '0x01', '0x04', '0x04', 
            '0x20', '0x10', '0x30', '0x02', '0x01', 
            '0x01', '0x01', '0x04', '0x20', '0x30', 
            '0x00', '0x10', '0x20', '0x30', '0x00')
    aliasDict['TSCS.ImgRotPos'] =    \
           (32.794,30.794,15.794,-26.794,22.794,
            32.794,'None',30.794,-3.293,-30.293,
            32.794,30.794,30.794,-3.293,-30.293,
            32.794,30.794,30.794,'None', 22.794)
    aliasDict['TSCS.IMGROTCMD'] =    \
           ( 32.788,96.293,74.293,-3.293,-30.293,
            133.293,96.293,'None',-3.293,-30.293,
            133.293,74.293,96.293,-3.293,-30.293,
            133.293,74.293,20.293,-30.293,'None')

elif  SimTestSet == ROT_NS:
    aliasDict['TSCV.FOCUSINFO'] =    \
           ('10000000', '40000000', '80000000', '00010000', '00020000',
            '00080000', '00400000', '00800000', '00000100', '00000200',
            '00000800', '00008000', '00000001', '00000002', '00000004', 
            '00000010', '00000010', '00000010', '00000010', '00000010')
    aliasDict['TSCV.FOCUSALARM'] =    \
           ('0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00')
    aliasDict['TSCV.INSROTROTATION_PF'] =    \
           ('0x01', '0x01', '0x01', '0x04', '0x04', 
            '0x20', '0x10', '0x30', '0x02', '0x01', 
            '0x01', '0x01', '0x04', '0x20', '0x30', 
            '0x00', '0x10', '0x20', '0x30', '0x00')
    aliasDict['TSCS.ImgRotPos'] =    \
           (32.794,30.794,15.794,-26.794,-30.284,
            32.794,30.794,30.794,-3.293,-30.293,
            32.794,30.794,30.794,-3.293,-30.293,
            32.794,30.794,30.794,-3.293,-30.293)
    aliasDict['TSCS.IMGROTCMD'] =    \
           ( 32.788,96.293,74.293,-26.80,-30.293,
            32.794,30.794,30.794,-3.293,-30.293,
            32.794,30.794,30.794,-3.293,-30.293,
            32.794,30.794,30.794,-3.293,-30.493)

elif  SimTestSet == AGSV_THRESHOLDS:
    aliasDict['TSCL.AG1Intensity'] =    \
           ( 10, 0, 0, 0, 0 ,
             '10', '10', '20', '10', '10' ,     # quotes defeat interpolation
             '5000', '125', '10', '100', '100' ,
             5000, 0, 10, 100, 100 )
    aliasDict['STATL.AGRERR'] =    \
           (0, 100, 100, 750, 1600,
            '0', '300', '250', '950', '1000',
            '0', '750', '100', '750', '100',
            0, 100, 100, 750, 100)
    aliasDict['TSCL.SV1Intensity'] =    \
           ( 5000, 10, 0, 0, 100 ,
             '5000', '10', '0', '10', '10' ,
             '10', '0', '0', '0', '0' ,
             10, 10, 10, 10, 10 )
    aliasDict['STATL.SVRERR'] =    \
           (0, 100, 100, 750, 1600,
            '0', '100', '100', '200',  '150',
            '0', '100', '100', '750', '1600',
            0, 100, 100, 750, 1600)
    aliasDict['STATL.TELDRIVE'] =   \
           ( 'None', 'xzyc', 'Pointing', 'Tracking', 'Tracking(Non-Sidereal)',
             'Slewing', 'Guiding(AG1)', 'Guiding(AG2)', 
                                               'Guiding(SV1)', 'Guiding(SV2)',
             'Guiding(AG1)', 'Guiding(AG2)', 'Guiding(SV1)', 
                                               'Guiding(SV2)', 'Guiding(SV2)',
             'Slewing', 'Guiding(AG1)', 'Guiding(AG2)', 
                 'Guiding(SV1)', 'Guiding(SV2)' )

elif  SimTestSet == LIMITS_ALARMS:
    aliasDict['TSCV.FOCUSINFO'] =    \
           ('None', '01000000', '01000000', '01000000', '01000000',
            '04000000', '04000000', '04000000', '04000000', '04000000',
            '01000000', '01000000', '01000000', '01000000', '01000000', 
            '04000000', '04000000', '04000000', '04000000', '04000000')
#           None,  PfOpt, PfOpt, PfOpt, PfOpt,
#           CsOpt, CsOpt, CsOpt, CsOpt, CsOpt, 
#           PfOpt, PfOpt, PfOpt, PfOpt, PfOpt,
#           CsOpt, CsOpt, CsOpt, CsOpt, CsOpt, 
    aliasDict['TSCS.AZ'] =    \
           (-245.0, -265.00, 'None', -269.6, -272.0,
            -245.0, 'None',  -10.1,   65.1,  160.5,
             245.0,  265.0,  269.0,  269.5,  160.0,
              65.1, -245.0, -269.0, -269.6, -270.0)
    aliasDict['TSCS.AZ_CMD'] =    \
           (-250.0, -265.01, -269.6, -272.0, -252.0,
             -85.0,  -45.0, 'None',   75.1,  169.5,
             255.0,  269.0,  269.9,  269.0,  150.0,
              65.1, -245.0, -269.0, -269.6, -270.0)
    aliasDict['TSCS.INSROTPOS_PF'] =    \
           (32.794,74.293,96.293,-3.293,-30.293,
            32.794,30.794,15.794,-26.794,22.794,
            32.794,30.794,15.794,-26.794,22.794,
            32.794,30.794,'None',-26.794,22.794)
    aliasDict['TSCS.INSROTCMD_PF'] =    \
           (133.293,96.293,96.293,-3.293,'None',
            133.293,96.293,74.293,-3.293,'None',
            133.293,96.293,74.293,-3.293,-30.293,
            133.293,96.293,74.293,'None',-30.293)
    # Following used for PfOpt
    aliasDict['TSCL.AGPF_X'] =    \
           ( 50, 0, 10, 100, 70 ,
             50, 0, 10, 100, 70 ,
             50, 1,  8,  97, 76.9,
             50, 0, 10, 100, 80 )
    aliasDict['TSCL.AGPF_X_CMD'] =    \
           ( 50, 0, 11, 102, 68.1,
             50, 0, 10, 100, 70 ,
             50, 0, 10, 100, 75 ,
             50, 0, 10, 100, 80 )
    aliasDict['TSCL.AGPF_Y'] =    \
           ( 19, 0, 10, 17, 19 ,
             19, 0, 10, 17, 70 ,
             19, 1, 11.1, 15.9, 15 ,
             19, 0, 10, 17, 80 )
    aliasDict['TSCL.AGPF_Y_CMD'] =    \
           ( 19, 0, 10, 17, 19 ,
             19, 0, 10, 17, 70 ,
             19, 0, 10, 17, 15 ,
             19, 0, 10, 17, 80 )
    # Following used for CsOpt
    aliasDict['TSCV.AGTheta'] =    \
           ( -60, 'None', 15, 48, 72 ,
             -60, -25, 15, 48, 72 ,
             -60, -25, 15, 'None', 72 ,
             -60, -25, 15, 48, 72 )
    aliasDict['STATL.AG_THETA_CMD'] =    \
           ( -60, 'None', 15, 48, 72 ,
             -60, -25.5, 16, 46, 72 ,
             -60, -25, 15, 'None', 72 ,
             -60, -25, 15, 48, 72 )
    aliasDict['TSCV.AGR'] =    \
           ( -200, -50, 150, 350, 625 ,
             -200, -50, 150, 350, 625 ,
             -200, -50, 150, 350, 625 ,
             -200, -49.1, 148.9, 351.5, 625.9 )
    aliasDict['STATL.AG_R_CMD'] =    \
           ( -200, -50, 150, 350, 625 ,
             -200, -50, 150, 350, 625 ,
             -200, -50, 150, 350, 625 ,
             -200, -50, 150, 350, 625 )

elif  SimTestSet == TIP_TILT_CHOP:
    aliasDict['TSCV.FOCUSINFO'] =    \
           ('00001000', '00001000', '00001000', '00001000', '00001000',
            '00000008', '00000008', '00000008', '00000008', '00000008',
            '00000008', '00000008', '00000008', '00000008', '00000008',
            '00001000', '00001000', '00001000', '00001000', '00001000')
#           CsIR/IR, CsIR/IR, CsIR/IR, CsIR/IR, CsIR/IR,
#           NsIR/IR, NsIR/IR, NsIR/IR, NsIR/IR, NsIR/IR, 
#           NsIR/IR, NsIR/IR, NsIR/IR, NsIR/IR, NsIR/IR,
#           CsIR/IR, CsIR/IR, CsIR/IR, CsIR/IR, CsIR/IR 
    aliasDict['TSCV.TT_Mode'] =    \
           ('0x00', '0x00', '0x02', '0x02', '0x04',
            '0x05', '0x02', '0x02', '0x02', '0x02',
            '0x01', '0x01', '0x01', '0x01', '0x01',
            '0x01', '0x01', '0x01', '0x01', '0x01')
    aliasDict['TSCV.TT_Drive'] =    \
           ('0x00', '0x00', '0x05', '0x05', '0x05',
            '0x05', '0x05', '0x01', '0x04', '0x02',
            'None', '0x05', '0x05', '0x05', '0x05',
            '0x05', '0x05', '0x01', '0x04', '0x02')
    aliasDict['TSCV.TT_DataAvail'] =    \
           ('0x00', '0x00', '0x00', '0x01', '0x01',
            '0x01', '0x00', '0x01', '0x01', '0x01',
            '0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00')
    aliasDict['TSCV.TT_ChopStat'] =    \
           ('0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00',
            '0x02', '0x01', '0x04', '0x05', '0x07',
            '0x01', '0x02', '0x05', '0x05', '0x05')

elif  SimTestSet == LIM_WARN_SUPPRES:
    #   NsIR/IR
    aliasDict['TSCV.FOCUSINFO'] =    \
           ('00000008', '00000008', '00000008', '00000008', '00000008',
            '00000008', '00000008', '00000008', '00000008', '00000008',
            '00000008', '00000008', '00000008', '00000008', '00000008',
            '00000008', '00000008', '00000008', '00000008', '00000008')

    aliasDict['TSCL.LIMIT_AZ'] =    \
           ( ' 40.0', ' 40.0', ' 40.0', ' 40.0', ' 40.0',
             ' 32.0', ' 10.0', ' 10.0', ' 10.0', ' 10.0',
             ' 40.0', ' 40.0', ' 40.0', ' 40.0', ' 40.0',
             ' 32.0', ' 10.0', ' 10.0', ' 10.0', ' 10.0')
    aliasDict['TSCL.LIMIT_ROT'] =   \
           ( ' 32.0', ' 10.0', ' 10.0', ' 10.0', ' 10.0',
             ' 40.0', ' 40.0', ' 40.0', ' 40.0', ' 40.0',
             ' 32.0', ' 10.0', ' 10.0', ' 10.0', ' 10.0',
             ' 40.0', ' 40.0', ' 10.0', ' 40.0', ' 40.0')
    aliasDict['TSCL.LIMIT_FLAG'] =  \
           ( '0x0C', '0x0C', '0x0C', '0x0C', '0x0C',
             '0x0C', '0x0C', '0x0C', '0x0C', '0x0C',
             '0x0C', '0x0C', '0x0C', '0x0C', '0x0C',
             '0x0C', '0x0C', '0x1C', '0x0C', '0x0C')
    aliasDict['TSCV.PROBE_LINK'] =  \
           ( '0x00', '0x00', '0x00', '0x00', '0x00',
             '0x00', '0x00', '0x00', '0x00', '0x00',
             '0x00', '0x00', '0x00', '0x00', '0x00',
             '0x00', '0x00', '0x00', '0x00', '0x00')    # always Rotator

    #   limits are +/- 260 for warnings,  +/- 269.5 for alarms
    aliasDict['TSCS.AZ'] =    \
           (-245.0, -265.0, -269.0, -269.6, -269.9,
            -250.0, -250.0, -250.0, -250.0, -250.0,
              30.0,   30.0,   30.0,   30.0,   30.0,
              30.0,   30.0,   30.0,   30.0,   30.0)
    aliasDict['TSCS.AZ_CMD'] =    \
           (-250.0, -250.0, -250.0, -250.0, -250.0,
            -245.0, -265.0, -269.0, -269.6, -269.9,
              30.0,   30.0,   30.0,   30.0,   30.0,
              30.0,   30.0,   30.0,   30.0,   30.0)

    #   limits are +/- 175 for warnings,  +/- 179.5 for alarms (Ns)
    aliasDict['TSCS.ImgRotPos'] =    \
           (  30.0,   30.0,   30.0,   30.0,   30.0, 
              30.0,   30.0,   30.0,   30.0,   30.0, 
             150.0,  176.0,  179.0,  179.6,  179.9,
             140.0,  140.0,  140.0,  140.0,  140.0)
    aliasDict['TSCS.IMGROTCMD'] =    \
           (  30.0,   30.0,   30.0,   30.0,   30.0, 
              30.0,   30.0,   30.0,   30.0,   30.0, 
             140.0,  140.0,  140.0,  140.0,  140.0,
             150.0,  176.0,  179.0,  179.6,  179.9)

elif  SimTestSet == IMGROTMODE:
    aliasDict['TSCV.FOCUSINFO'] =    \
           ('40000000', '80000000', '00000008', '00010000', '00020000',
            '00400000', '00800000', '00000008', '00000100', '00000200',
            '00008000', '00000001', '00000008', '00000002', '00000004',
            '00080000', '00000800', '00000008', '00000010', '00000010')
    # no alarms
    aliasDict['TSCV.FOCUSALARM'] =   \
           ('0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00')


    # ImgRotMode:
    aliasDict['TSCV.ImgRotRotation'] =  \
           ('0x01', '0x01', '0x01', '0x01', '0x01', 
            '0x01', '0x01', '0x01', '0x01', '0x01', 
            '0x01', '0x01', '0x01', '0x01', '0x01', 
            '0x01', '0x01', '0x01', '0x01', '0x01')
    aliasDict['TSCV.ImgRotMode'] =   \
           ('0x40', '0x01', '0x01', '0x02', '0x40', 
            '0x01', '0x02', '0x01', '0x01', '0x40', 
            '0x02', '0x40', '0x01', '0x01', '0x02', 
            '0x40', '0x02', '0x01', '0x01', '0x02')
    aliasDict['TSCV.ImgRotType'] =   \
           ('0x12', '0x10', '0x12', '0x0c', '0x0c',
            '0x12', '0x10', '0x0f', '0x04', '0x04',
            '0x0c', '0x04', '0x10', '0x12', '0x10',
            '0x12', '0x0C', '0x12', '0x12', '0x0C')
    aliasDict['TSCS.ImgRotPos'] =   \
           (32.794,30.794,15.794,-26.794,22.794,
            32.794,32.794,30.794,-3.293,-30.293,
            32.794,30.794,30.794,-3.293,-30.293,
            32.794,30.794,30.794,-3.293, 22.794)
    aliasDict['TSCS.IMGROTCMD'] =   \
           (32.794,30.794,15.794,-26.794,22.794,
            32.794,32.794,30.794,-3.293,-30.293,
            32.794,30.794,30.794,-3.293,-30.293,
            32.794,30.794,30.794,-3.293, 22.794)

elif  SimTestSet == FMOSAG:
    aliasDict['TSCV.FOCUSINFO'] =    \
           ('40000000', '02000000', '02000000', '02000000', '02000000',
            '02000000', '02000000', '02000000', '02000000', '02000000',
            '02000000', '02000000', '02000000', '02000000', '02000000',
            '02000000', '02000000', '02000000', '02000000', '00000010')
    # no alarms
    aliasDict['TSCV.FOCUSALARM'] =   \
           ('0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00',
            '0x00', '0x00', '0x00', '0x00', '0x00')

elif  SimTestSet == NSIRAO:
    aliasDict['TSCV.FOCUSINFO'] =    \
          ('None', '00000008', '00000010', '00000800', '00080000',
           '0000', '00000000', '00000000', '00000000', '00000000',
           '0000', '00000000', '00000000', '00000000', '00000000',
           '0000', '00000000', '00000000', '00000000', '00000000')
    aliasDict['TSCV.FOCUSINFO2'] =    \
          ('None', '00', '00', '00', '00',
           '02',   '02', '02', '02', '02',
           '04',   '04', '04', '04', '04',
           '01',   '01', '01', '01', '01')
    aliasDict['TSCV.ADCInOut'] =    \
           ('0x08', 'None', '0x10', '0x08', '0x10',
            '0x08', '0x08', '0x08', '0x08', '0x08',
            '0x08', '0x08', '0x08', '0x08', '0x08',
            '0x08', '0x08', '0x08', '0x08', '0x08') 
    aliasDict['TSCV.ADCOnOff'] =    \
           ('0x0f', '0x02', '0x01', '0x01', '0x02',
            'None', '0x02', '0x01', '0x01', '0x01',
            '0x01', '0x0f', '0x01', '0x01', 'None',
            '0x02', '0x01', '0x01', '0x01', '0x01')
    aliasDict['TSCV.ADCMode'] =    \
           ('0x04', '0x08', '0x08', '0x04', '0x08',
            '0x04', '0x08', 'None', '0x04', '0x08',
            '0xff', '0x08', '0x08', '0x04', '0x08',
            '0x04', '0x08', '0x08', '0x04', '0x08')
    aliasDict['TSCS.ImgRotPos'] =    \
           (32.794,30.794,15.794,-26.794,-30.284,
            32.794,30.794,30.794,-3.293,-30.293,
            32.794,30.794,30.794,-3.293,-30.293,
            32.794,30.794,30.794,-3.293,-30.293)
    aliasDict['TSCS.IMGROTCMD'] =   \
           (32.794,30.794,15.794,-26.794,22.794,
            32.794,32.794,30.794,-3.293,-30.293,
            32.794,30.794,30.794,-3.293,-30.293,
            32.794,30.794,30.794,-3.293, 22.794)
    aliasDict['TSCV.ImgRotMode'] =   \
           ('0x40', '0x01', '0x01', '0x02', '0x40', 
            '0x01', '0x02', '0x01', '0x01', '0x40', 
            '0x02', '0x40', '0x01', '0x01', '0x02', 
            '0x40', '0x02', '0x01', '0x01', '0x02')




NumDictionaries = len( aliasDict['dictName'] )


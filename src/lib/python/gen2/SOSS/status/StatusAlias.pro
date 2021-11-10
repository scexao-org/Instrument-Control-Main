#
# Don't change "StatusAlias.def" file.
# change file is "StatusAlias.def" file.
#
# Change sequence :
#  step 1 : cd $OSS_SYSTEM
#  step 2 : vi StatusAlias.pro (edit prototype file)
#           vi StatusTSCV.sh (edit TSCV offset define file)
#  step 3 : makedef.sh
#  step 4 : install.sh file
#
# StatusAlias.defファイルは手で変更してはならない。
# StatusAlias.proファイルを変更する。
#
# 変更するときはStatusAlias.proを変更してmake -f StatusAlias.mkを実行。
#
#
# exsample
#
#    # for OSSO_ObsAllocInfo Screen
#    DISPAREA1,CON_SCH(1680:$AAA:R)
#    DISPAREA2,CON_SCH($BBB:128:R)
#    DISPAREA3,CON_SCH(1936:128:$CCC)
#    DISPAREA4,CON_SCH($AAA+80:128:R)
#    
#    # define
#    #---+----1----+----2----+----3----+----4----+----5----+----6
#    @AAA                          111
#    @BBB                          2222
#    @CCC                          33333
#
#    ※ 変数定義の値は必ず３１桁目に定義しなければいけません！
#


# 以下のコメントは参考資料です
# 1997.06.28 観測画面ST用 Higaside.s
# エイリアス名,ステータス位置定義
# エイリアス名
#       最大３０バイト。英数文字、ドット、アンダーバーからなる。
# ステータス位置定義 = テーブルコード(n:m:T:M)
#       テーブルコード
#               テーブル定義ファイル($OSS_SYSTEM/Table.def)に記述された
#               ステータステーブルのテーブルコード
#       ｎ
#               ステータス項目の開始位置をテーブルの先頭からのバイト位置を
#               十進数で示す。0から(テーブルサイズ-1)を指定可能とする。
#       ｍ
#               ステータス項目のデータバイト長を十進数で示す。
#               １から（テーブルサイズ-ｎ) を指定可能とする。
#               ただしＴが"Ｌ"または"Ｓ"の場合、"１"及び"２"が指定可能であり、
#               その他の場合４バイト長とみなされる。
#       Ｔ
#               ステータス項目の評価型を示す。
#               以下の値を指定可能とする。
#               C:文字列 "%s"
#                       0x20未満または0x7f超過のデータを含む場合エラー
#               I:整数 "%d"
#                       atoiの結果が0の場合のみ数字又は' '以外を含むとエラー
#               U:符号なし整数 "%d"
#                       strtoulの結果が0の場合のみ数字又は' '以外を含むとエラー
#               F:浮動小数点 "%f"
#                       atofの結果が0の場合のみ数字,' '又は'.'以外を含むとエラー
#                       (Fは前後空白の削除をするがL,Sではしない)
#               B:ビット列 "%02x"×ｍ
#               D:ＢＣＤ "+999.999999"
#               (以下新規追加分)
#               R:ローデータ
#                       データをそのまま返す
#               L:符号なしバイナリ "%f"
#               S:符号ありバイナリ "%f"
#       Ｍ
#               Ｔが"Ｂ"または"Ｄ"の場合、ステータス項目に対するマスク値を
#               先頭に"Ｈ"をつけた十六進数にて示す。
#               マスクデータ長がステータス項目長(ｍ)より短い場合、
#               マスク値の終端に不足バイト長分"ff"が付加される。
#               Ｔが"Ｌ"または"Ｓ"の場合、ステータス項目に対する乗数を
#               先頭に"Ｗ"をつけた十進数にて示す。
#               乗数を省略または０を指定した場合、乗数は１となる。
#               マスク値または乗数は省略可能。
#
# (English Translation)
# Comment the following reference
# ST screen for observation Higaside.s # 1997.06.28
# Alias name, status defined position
# Name aliases
# Up to 30 bytes. Alphanumeric characters, dots, underscores bar.
# Define status = code table position (n: m: T: M)
# Code table
# Table definition files ($ OSS_SYSTEM / Table.def) has been described in
# Status code table in Table
# N
# Bytes from the top of the table position to the start of entry status
# 10 shown in decimal. 0 (-1 table size) to be specified.
# M
# Indicates the length in bytes in decimal data entry status.
# 1 (Table size-n) to be specified.
# The T is "L" or "S" if, "a" and "2" can be specified,
# 4 will be considered if the other word.
# T
# Indicates the type of item review status.
# You can specify the following values.
# C: string "% s"
# 0x20 Error 0x7f or less, including excess data
# I: integer "% d"
# Atoi results only if the number of 0 or '' an error, including non -
# U: unsigned integer "% d"
# Strtoul results only if the number of 0 or '' an error, including non -
# F: floating point "% f"
# Atof results only if the number of 0, '' or '.' Error and the other containing
# (F will be empty after the removal of the L, S does not)
# B: bit-string "% 02x" m
# D: BCD "+999.999999"
# (New Additions)
# R: raw data
# Returns data as
# L: unsigned binary "% f"
# S: binary code with "% f"
# M
# T a "B" or "D", the mask values for item status
# The first "H" shown at 60 with a decimal.
# Item # status data length mask length (m) is shorter than,
# Minutes missing at the end of the word mask value "ff" are appended.
# T is "L" or "S", the multiplier for the status item
# The first "W" shown at 10 with a decimal.
# Or 0 if you omit to specify the multiplier, the multiplier is 1.
# Multiplier value or mask is optional.
#

#---+----1----+----2----+----3----+----4----+----5----+----6
# Offset Define for CON_SCH (change 01.02.25)
@CON_SCH_DISP                 40*(76)

# for OSSO_MonSys Screen
STATLOG,CON_LOG(1160:40960:R) # status receive status(40byte x 100record)


# for OSSO_AdmIns & OSSO_MonTel Screen
INSFOCUS,OSSO_IC(128:424:R) # OBE setting position information
INSFOCUS.PRIME,OSSO_IC(128+46:20:R) # FOCUS POSITION PRIME
INSFOCUS.CASS,OSSO_IC(128+67:20:R) # FOCUS POSITION CASS
INSFOCUS.NASOPT,OSSO_IC(128+88:20:R) # FOCUS POSITION NASOPT
INSFOCUS.NASIR,OSSO_IC(128+109:20:R) # FOCUS POSITION NASIR
INSFOCUS.COUDE,OSSO_IC(128+130:20:R) # FOCUS POSITION COUDE

# for OSSO_AdmMode Screen
TSCL.MODE,TSCV($TSCV00A1+8:1:B:H07) # TSC MODE 01:OBSPRI 02:TSCPRI 04:TSCONLY

# for OSSS_InterfaceOBS and OSSO_ACmdList Screen
CON_SCH_UID_1,CON_SCH($CON_SCH_DISP+128*0+8:5:R) ## alloc uid 1
CON_SCH_UID_2,CON_SCH($CON_SCH_DISP+128*1+8:5:R) # alloc uid 2
CON_SCH_UID_3,CON_SCH($CON_SCH_DISP+128*2+8:5:R) # alloc uid 3
CON_SCH_UID_4,CON_SCH($CON_SCH_DISP+128*3+8:5:R) # alloc uid 4
CON_SCH_UID_5,CON_SCH($CON_SCH_DISP+128*4+8:5:R) # alloc uid 5
CON_SCH_UID_6,CON_SCH($CON_SCH_DISP+128*5+8:5:R) # alloc uid 6
CON_SCH_HOST_1,CON_SCH($CON_SCH_DISP+128*0+23:8:R) ## alloc host 1
CON_SCH_HOST_2,CON_SCH($CON_SCH_DISP+128*1+23:8:R) # alloc host 2
CON_SCH_HOST_3,CON_SCH($CON_SCH_DISP+128*2+23:8:R) # alloc host 3
CON_SCH_HOST_4,CON_SCH($CON_SCH_DISP+128*3+23:8:R) # alloc host 4
CON_SCH_HOST_5,CON_SCH($CON_SCH_DISP+128*4+23:8:R) # alloc host 5
CON_SCH_HOST_6,CON_SCH($CON_SCH_DISP+128*5+23:8:R) # alloc host 6
CON_SCH_PID_1,CON_SCH($CON_SCH_DISP+128*0+31:8:R) ## alloc pid 1
CON_SCH_PID_2,CON_SCH($CON_SCH_DISP+128*1+31:8:R) # alloc pid 2
CON_SCH_PID_3,CON_SCH($CON_SCH_DISP+128*2+31:8:R) # alloc pid 3
CON_SCH_PID_4,CON_SCH($CON_SCH_DISP+128*3+31:8:R) # alloc pid 4
CON_SCH_PID_5,CON_SCH($CON_SCH_DISP+128*4+31:8:R) # alloc pid 5
CON_SCH_PID_6,CON_SCH($CON_SCH_DISP+128*5+31:8:R) # alloc pid 6
CON_SCH_MODE_1,CON_SCH($CON_SCH_DISP+128*0+39:3:R) ## alloc mode 1
CON_SCH_MODE_2,CON_SCH($CON_SCH_DISP+128*1+39:3:R) # alloc mode 2
CON_SCH_MODE_3,CON_SCH($CON_SCH_DISP+128*2+39:3:R) # alloc mode 3
CON_SCH_MODE_4,CON_SCH($CON_SCH_DISP+128*3+39:3:R) # alloc mode 4
CON_SCH_MODE_5,CON_SCH($CON_SCH_DISP+128*4+39:3:R) # alloc mode 5
CON_SCH_MODE_6,CON_SCH($CON_SCH_DISP+128*5+39:3:R) # alloc mode 6
CON_SCH_OBCP_1,CON_SCH($CON_SCH_DISP+128*0+43:80:R) ## alloc obcp 1
CON_SCH_OBCP_2,CON_SCH($CON_SCH_DISP+128*1+43:80:R) # alloc obcp 2
CON_SCH_OBCP_3,CON_SCH($CON_SCH_DISP+128*2+43:80:R) # alloc obcp 3
CON_SCH_OBCP_4,CON_SCH($CON_SCH_DISP+128*3+43:80:R) # alloc obcp 4
CON_SCH_OBCP_5,CON_SCH($CON_SCH_DISP+128*4+43:80:R) # alloc obcp 5
CON_SCH_OBCP_6,CON_SCH($CON_SCH_DISP+128*5+43:80:R) # alloc obcp 6
CON_SCH_BUSY_1,CON_SCH($CON_SCH_DISP+128*0+123:1:R) ## alloc busy 1
CON_SCH_BUSY_2,CON_SCH($CON_SCH_DISP+128*1+123:1:R) # alloc busy 2
CON_SCH_BUSY_3,CON_SCH($CON_SCH_DISP+128*2+123:1:R) # alloc busy 3
CON_SCH_BUSY_4,CON_SCH($CON_SCH_DISP+128*3+123:1:R) # alloc busy 4
CON_SCH_BUSY_5,CON_SCH($CON_SCH_DISP+128*4+123:1:R) # alloc busy 5
CON_SCH_BUSY_6,CON_SCH($CON_SCH_DISP+128*5+123:1:R) # alloc busy 6
#Dipatcher version(add shiraishi 2003.05.23)
CON_SCH_VER_0,CON_SCH(118:1:R:) #intdispatcher version
CON_SCH_VER_1,CON_SCH(158:1:R:) #dispatcher1 version
CON_SCH_VER_2,CON_SCH(198:1:R:) #dispatcher2 version
CON_SCH_VER_3,CON_SCH(238:1:R:) #dispatcher3 version
CON_SCH_VER_4,CON_SCH(278:1:R:) #dispatcher4 version
CON_SCH_VER_5,CON_SCH(318:1:R:) #dispatcher5 version
CON_SCH_VER_6,CON_SCH(358:1:R:) #dispatcher6 version


# for OSSO_ObsAllocInfo Screen
DISPAREA1,CON_SCH($CON_SCH_DISP+128*0:128:R) ## alloc info 1
DISPAREA2,CON_SCH($CON_SCH_DISP+128*1:128:R) # alloc info 2
DISPAREA3,CON_SCH($CON_SCH_DISP+128*2:128:R) # alloc info 3
DISPAREA4,CON_SCH($CON_SCH_DISP+128*3:128:R) # alloc info 4
DISPAREA5,CON_SCH($CON_SCH_DISP+128*4:128:R) # alloc info 5
DISPAREA6,CON_SCH($CON_SCH_DISP+128*5:128:R) # alloc info 6

# for OSSO_MonEnv Screen
TSCL.WINDD,TSCL($TSCL_WMON+1:6:D) # Wind Direction (deg)
TSCL.WINDS_O,TSCL($TSCL_WMON+7:6:D) # Wind Speed Outside (m/s) # change summit 98.03.19
TSCL.WINDS_I,TSCL($TSCL_DOME_TEMP+115:6:D) # Wind Speed Dome (m/s) # change summit 98.03.19
TSCL.TEMP_O,TSCL($TSCL_WMON+25:6:D) # Temperature Outside (C) # change summit 98.03.19
TSCL.TEMP_I,TSCL($TSCL_DOME_TEMP+361:6:D) # Temperature Dome (C)
TSCL.HUMI_O,TSCL($TSCL_WMON+31:6:D) # Humidity Outside (%) # change summit 98.03.19
TSCL.HUMI_I,TSCL($TSCL_DOME_TEMP+97:6:D) # T.B.D. # Humidity Dome (%)
TSCL.ATOM,TSCL($TSCL_WMON+43:4:L:0.1) # Air Pressure (hPa) # change summit 98.03.19
TSCL.RAIN,TSCL($TSCL_WMON+37:6:D) # Rain Gauge (mm/h)
TSCL.SEEN,TSCL($TSCL_AG+33:4:L:0.00001) # Seeing (arcsec) # same AG1StarSize # change siwai 000317
TSCL.THRU,TSCL(6550:6:D) # T.B.D. # Sky Transparency (%)
TSCV.OIL,TSCV($TSCV00B3+41:1:B:H0C) # oil condition # change kawai 99.06.22 : 2 high,3 low 0C
TSCV.WATER,TSCV($TSCV00B3+41:1:B:H30) # warter condition # change kawai 99.06.22 : 4 high,5 low 30

# for OSSO_MonTel Top Screen 
TSCS.ALPHA,TSCS($TSCS_TSC+1:5:B) # RA(hhmmssssss) # change summit 98.03.19
TSCS.ALPHA_C,TSCS($TSCS_TSC+106:5:B) # RA(command) # change kosugi 99.07.08 # change wata 02.0305
TSCS.DELTA,TSCS($TSCS_TSC+7:5:B) # DEC(80ddmmssss) (8:-,0=+)
TSCS.DELTA_C,TSCS($TSCS_TSC+112:5:B) # DEC(command) # change kosugi 99.07.08 # change wata 02.0305
TSCS.AZ,TSCS($TSCS_TSC+50:6:D) # AZ(deg)
TSCS.EL,TSCS($TSCS_TSC+56:6:D) # EL(deg)
TSCS.EQUINOX,TSCS($TSCS_TSC+12:6:D:H0000FFFFFFFF) # equinox(year) # change kusu 98.03.19 #change kosugi 99.10.04 old=EQN
TSCV.TelDrive,TSCV($TSCV00A1+17:2:B:HF03C) # TelDrive (rkackley change 2012.05.23)
OBSS.AutoGuideOn,OBSS(128+40* 9+38:1:C) # AutoGuideOn(obs) : TSC 0
TSCV.AutoGuideOn,TSCV($TSCV00B1+9:1:B:H07) # AutoGuideOn(tsc)
TSCV.AutoGuideOff,TSCV($TSCV00A1+17:1:B:H40) # AutoGuideOff(tsc)
TSCV.WindScreen,TSCV($TSCV00A1+13:1:B:H03) # WindScreen
TSCV.DomeFF_A,TSCV($TSCV0061+5:1:B:H03) # DomeFF Lamp 1-A〜4-A On,Off (2001.05.03 ooto)
TSCV.DomeFF_1B,TSCV($TSCV0061+5:1:B:H0C) # DomeFF Lamp 1-B On,Off (2001.05.03 ooto)
TSCV.DomeFF_2B,TSCV($TSCV0061+5:1:B:H30) # DomeFF Lamp 2-B On,Off (2001.05.03 ooto)
TSCV.DomeFF_3B,TSCV($TSCV0061+6:1:B:H03) # DomeFF Lamp 3-B On,Off (2001.05.03 ooto)
TSCV.DomeFF_4B,TSCV($TSCV0061+6:1:B:H0C) # DomeFF Lamp 4-B On,Off (2001.05.03 ooto)
TSCV.TopScreen,TSCV($TSCV00A1+13:1:B:H3C) # TopScreen
TSCV.DomeShutter,TSCV($TSCV0030+4:1:B:H50) # DomeShutter
TSCV.DomeLight,TSCV($TSCV0030+58:2:B:HFF10) # DomeLight
TSCV.M1Cover,TSCV($TSCV0024+4:11:B:H5555555555555555555555) # M1Cover
TSCV.M1CoverOnway,TSCV($TSCV0024+15:1:B:H07) # M1CoverOnway
TSCV.CellCover,TSCV($TSCV0024+21:1:B:H05) # CellCover
TSCV.M3Cover,TSCV($TSCV0024+20:1:B:H05) # M3Cover
TSCV.M2Drive,TSCV($TSCV00A1+4:1:B:H1F) # M2Drive (99.03.09 chg Mr.sasaki) (will delete 2004.12.24)
TSCV.M2TipTilt,TSCV($TSCV0028+2:1:B:H07) # M2 TipTilt (chg kawai 99.10.25)
TSCL.Fq,TSCL($TSCL_TTCU+1:6:D) # M2 Frequency(Hz) (chg kawai 99.10.25)
TSCL.Amp,TSCL($TSCL_TTCU+7:6:D) # M2 Amplifier(arcsec) (chg kawai 99.10.25)
TSCL.Z,TSCV($TSCV00B2+836:6:D) # M2 Z (1999.02.24 chg Mr.kosugi)
TSCV.Z,TSCV($TSCV00B2+836:6:D) # same as TSCL.Z (add ukawa 2005.02.01)
TSCL.TX,TSCL($TSCL_SMCU+19:6:D) # M2 TX
TSCL.TY,TSCL($TSCL_SMCU+25:6:D) # M2 TY
TSCV.M3Drive,TSCV($TSCV0025+1:1:B:H0F) # M3Drive
TSCV.Focus,TSCV($TSCV00A1+3:1:B:H1F) # Focus (will delete 2004.12.24)
TSCV.Z_PIR,TSCV($TSCV00B2+949:6:D) # PIR FAM(z) Offset Position (add ukawa 2005.02.01)
TSCV.UV_Z,TSCV($TSCV0040+795:6:D) # M2 Z offset for UV parameter.

# for OSSO_MonTel AG Screen 
TSCV.AGredB1,TSCV($TSCV00B1+2:1:B:H64) # AG button color(red) (99.03.09 chg Mr.sasaki)
TSCV.AGredB2,TSCV($TSCV00B1+9:1:B:H80) # AG button color(red)
TSCV.AGredB3,TSCV($TSCV0006+78:1:B:HC7) # AG button color(red)
TSCV.AGredB4,TSCV($TSCV0006+81:1:B:H3F) # AG button color(red) (99.03.09 chg Mr.sasaki)
TSCV.AGredB5,TSCV($TSCV0006+86:1:B:H0F) # AG button color(red) (99.03.09 chg Mr.sasaki)
TSCV.AGredB6,TSCV($TSCV0006+87:1:B:H0F) # AG button color(red) (99.03.09 chg Mr.sasaki)
TSCV.AGredB7,TSCV($TSCV0006+88:1:B:H0F) # AG button color(red) (99.03.09 chg Mr.sasaki)
TSCV.AGredB8,TSCV($TSCV0006+89:1:B:H0F) # AG button color(red) (99.03.09 chg Mr.sasaki)
TSCV.AGredB9,TSCV($TSCV0006+90:1:B:H0F) # AG button color(red) (99.03.09 chg Mr.sasaki)
TSCV.AGredBa,TSCV($TSCV0006+2:1:B:H08) # AG button color(red) (99.03.09 chg Mr.sasaki)
TSCV.AGredBb,TSCV($TSCV003B+64:1:B:H3F) # AG button color(red) for PIR (add ukawa 2005.02.01)
TSCV.AGredBc,TSCV($TSCV003B+70:1:B:H07) # AG button color(red) for PIR (add ukawa 2005.02.01)
TSCV.AGType,TSCV($TSCV00B1+9:1:B:H07) # AGType
TSCL.AG1dX,TSCL($TSCL_AG+9:4:S:0.01) # AG1dX (mas)
TSCL.AG1dY,TSCL($TSCL_AG+13:4:S:0.01) # AG1dY (mas)
TSCL.AG1Intensity,TSCL($TSCL_AG+17:2:L) # AG1Intensity
TSCL.AG1StarSize,TSCL($TSCL_AG+33:4:L:0.00001) # AG1StarSize (arcsec) # change siwai 000317
TSCL.AG2dX,TSCL($TSCL_AG+19:4:S:0.01) # AG2dX (mas)
TSCL.AG2dY,TSCL($TSCL_AG+23:4:S:0.01) # AG2dY (mas)
TSCL.AG2Intensity,TSCL($TSCL_AG+27:2:L) # AG2Intensity
TSCL.AG2StarSize,TSCL($TSCL_AG+37:4:L:0.00001) # AG2StarSize (arcsec) # change siwai 000317
TSCL.OBEdX,TSCL($TSCL_OBE+1:4:S:0.01) # OBEdX (mas)
TSCL.OBEdY,TSCL($TSCL_OBE+5:4:S:0.01) # OBEdY (mas)
TSCL.OBEIntensity,TSCL($TSCL_OBE+9:2:L) # OBEIntensity
TSCL.OBEStarSize,TSCL($TSCL_OBE+23:4:L:0.00001) # OBEStarSize (arcsec) # change siwai 000329
TSCV.AGTracking,TSCV($TSCV00A1+17:1:B:H20) # AGTracking
TSCV.AGCCalc,TSCV($TSCV0006+19:1:B:H14) # AGCCalc # change ukawa 2005.02.17
TSCV.AGImage,TSCV($TSCV0006+19:1:B:HC0) # AGImage
TSCV.AGShutter,TSCV($TSCV0006+19:1:B:H03) # AGShutter
TSCV.AGExpTime,TSCV($TSCV0006+5:4:L) # AGExpTime
TSCV.AGBinning,TSCV($TSCV0006+77:1:B:HFF) # AGBinning
TSCV.AGImgRegX1,TSCV($TSCV0006+22:2:L) # AGImgRegX1
TSCV.AGImgRegY1,TSCV($TSCV0006+24:2:L) # AGImgRegY1 # change summit 98.03.19
TSCV.AGImgRegX2,TSCV($TSCV0006+26:2:L) # AGImgRegX2 # change summit 98.03.19
TSCV.AGImgRegY2,TSCV($TSCV0006+28:2:L) # AGImgRegY2
TSCV.AGCCalcRegX11,TSCV($TSCV0006+30:2:L) # AGCCalcRegX11
TSCV.AGCCalcRegY11,TSCV($TSCV0006+32:2:L) # AGCCalcRegY11
TSCV.AGCCalcRegX21,TSCV($TSCV0006+34:2:L) # AGCCalcRegX21
TSCV.AGCCalcRegY21,TSCV($TSCV0006+36:2:L) # AGCCalcRegY21
TSCV.AGCCalcRegX12,TSCV($TSCV0006+38:2:L) # AGCCalcRegX12
TSCV.AGCCalcRegY12,TSCV($TSCV0006+40:2:L) # AGCCalcRegY12
TSCV.AGCCalcRegX22,TSCV($TSCV0006+42:2:L) # AGCCalcRegX22
TSCV.AGCCalcRegY22,TSCV($TSCV0006+44:2:L) # AGCCalcRegY22
TSCV.AGCCalcMode,TSCV($TSCV0006+20:1:B:H07) # AGCCalcMode
TSCV.AGCalibSky,TSCV($TSCV0006+66:1:B:H03) # AGCalibSky
TSCV.AGCalibDark,TSCV($TSCV0006+71:1:B:H03) # AGCalibDark
TSCV.AGCalibFlat,TSCV($TSCV0006+76:1:B:H03) # AGCalibFlat
TSCV.AGPos,TSCL(0:0:D) # AGPos # T.B.D.
TSCV.AGr,TSCL($TSCL_FPCI+1:6:D) # AGr
TSCV.AGR,TSCL($TSCL_FPCI+1:6:D) # AGr(command)
TSCV.AGTheta,TSCL($TSCL_FPCI+7:6:D) # AGTheta
TSCV.AGTHETA,TSCL($TSCL_FPCI+7:6:D) # AGTheta(command)
TSCV.AGMode,TSCV($TSCV00B1+7:1:B:H03) # AGMode
TSCL.AGPIRStarSize,TSCL($TSCL_OBCP+33:4:L:0.00001) # AG for SH Image Size(arcsec) (add ukawa 2005.02.01)
TSCL.AGPIRIntensity,TSCL($TSCL_OBCP+37:2:L) # AG for SH Star Position Intensity (add ukawa 2005.02.01)
TSCL.AGFMOSStarSize,TSCL($TSCL_OBCP+63:4:L:0.00001) # Fibre AG Image Size(arcsec) (add ukawa 2005.02.01)
TSCL.AGFMOSIntensity,TSCL($TSCL_OBCP+67:2:L) # Fibre AG Intensity (add ukawa 2005.02.01)

# for OSSO_MonTel InsRot Screen 
TSCV.RotatorType,TSCV($TSCV0004+5:1:B:H1F) # RotatorType
TSCV.InsRotredB1,TSCV($TSCV0004+9:1:B:H0F) # InsRot button color(red)
TSCV.InsRotredB2,TSCV($TSCV0004+14:1:B:H09) # InsRot button color(red)
TSCV.InsRotredB3,TSCV($TSCV0004+15:1:B:H01) # InsRot button color(red)
TSCV.InsRotredB4,TSCV($TSCV0004+16:1:B:H0F) # InsRot button color(red)
TSCV.InsRotredB5,TSCV($TSCV0004+6:1:B:H03) # InsRot button color(red)
TSCV.InsRotredB6,TSCV($TSCV0004+7:1:B:H22) # InsRot button color(red)
TSCV.InsRotredB7,TSCV($TSCV0004+8:1:B:H0F) # InsRot button color(red)
TSCV.InsRotRotation,TSCV($TSCV0004+4:1:B:H03) # InsRotRotation
TSCV.INSROTROTATION,TSCV($TSCV0004+4:1:B:H03) # InsRotRotation (add kusu 99.10.21)
TSCV.InsRotMode,TSCV($TSCV00B1+6:1:B:H03) # InsRotMode
TSCS.InsRotPos,TSCS($TSCS_FRAD+1:6:D) # InsRotPos
TSCS.INSROTPOS,TSCS($TSCS_FRAD+1:6:D) # InsRotPos(real)
TSCS.INSROTCMD,TSCS($TSCS_FRAD+7:6:D) # InsRotPos(command)
TSCL.InsRotSpeed,TSCL($TSCL_FRAD+13:6:D) # InsRotSpeed
TSCL.InsRotPA,TSCL($TSCL_MLP1+99:6:D) # InsRotPA
TSCL.INSROTPA,TSCL($TSCL_MLP1+99:6:D) # InsRotPA
TSCL.ZPOS,TSCL($TSCL_SMCU+13:6:D) # ZPOS (1999.02.24 add Mr.kosugi 99.06.29 kusu mask cut)
TSCL.ZCMD,TSCL($TSCL_SMCU+79:6:D) # ZCMD (1999.02.24 add Mr.kosugi 99.06.29 kusu mask cut)
TSCV.INSROTROTATION_PF,TSCV($TSCV0036+4:1:B:H03) # InsRotRotation_PF
TSCV.INSROTMODE_PF,TSCV($TSCV00B1+7:1:B:H30) # InsRotMode_PF
TSCS.INSROTPOS_PF,TSCS($TSCS_FRADPF+1:6:D) # InsRotPos_PF(real)
TSCS.INSROTCMD_PF,TSCS($TSCS_FRADPF+7:6:D) # InsRotPos(command)
TSCL.INSROTSPEED_PF,TSCL($TSCL_FRCU+13:6:D) # InsRotSpeed
TSCL.INSROTPA_PF,TSCL($TSCL_MLP1+111:6:D) # InsRotPA(command)

# for OSSO_MonTel ImgRot Screen 

#TSCV.ImgRotredB1,TSCV($TSCV0004+2:16:B:H0F0F000000000000000000001301FFFF) # ImgRot button color(red)
TSCV.ImgRotredB1,TSCV($TSCV0004+2:1:B:H0F) # ImgRot button color(red)
TSCV.ImgRotredB2,TSCV($TSCV0004+3:1:B:H0F) # ImgRot button color(red)
TSCV.ImgRotredB3,TSCV($TSCV0004+14:1:B:H16) # ImgRot button color(red) (99.03.09 chg Mr.sasaki)
TSCV.ImgRotredB4,TSCV($TSCV0004+15:1:B:H01) # ImgRot button color(red)
TSCV.ImgRotredB5,TSCV($TSCV0004+17:1:B:H0F) # ImgRot button color(red)
TSCV.ImgRotredB6,TSCV($TSCV0004+18:1:B:H0F) # ImgRot button color(red)
TSCV.ImgRotredB7,TSCV($TSCV0004+6:1:B:H1C) # ImgRot button color(red)
TSCV.ImgRotredB8,TSCV($TSCV0004+7:1:B:H22) # ImgRot button color(red)
TSCV.ImgRotredB9,TSCV($TSCV0004+8:1:B:H0F) # ImgRot button color(red)
TSCV.ImgRotRotation,TSCV($TSCV0004+4:1:B:H03) # ImgRotRotation
TSCV.IMGROTROTATION,TSCV($TSCV0004+4:1:B:H03) # ImgRotRotation (add kusu 99.10.21)
TSCV.ImgRotMode,TSCV($TSCV00B1+6:1:B:H43) # ImgRotMode
TSCV.ImgRotType,TSCV($TSCV0004+12:1:B:H1E) # ImgRotType
TSCV.ImgRotType_NS_IR,TSCV($TSCV0004+12:1:B:H18) # ImgRotType for NS_IR (add iwai 00.02.28)
TSCS.ImgRotPos,TSCS($TSCS_FRAD+1:6:D) # ImgRotPos
TSCS.IMGROTCMD,TSCS($TSCS_FRAD+7:6:D) # InsRotPos(command) (99.07.15 add kosugi)
TSCL.ImgRotSpeed,TSCL($TSCL_FRAD+13:6:D) # ImgRotSpeed
TSCL.ImgRotPA,TSCL($TSCL_MLP1+99:6:D) # ImgRotPA

# for OSSO_MonTel ADC Screen 
TSCV.ADCType,TSCV($TSCV0004+26:1:B:H0F) # ADCType
TSCV.ADCredB1,TSCV($TSCV0004+23:1:B:H0F) # ADC button color(red)
TSCV.ADCredB2,TSCV($TSCV0004+24:1:B:H01) # ADC button color(red)
TSCV.ADCredB3,TSCV($TSCV0004+27:1:B:H0F) # ADC button color(red)
TSCV.ADCredB4,TSCV($TSCV0004+33:1:B:H07) # ADC button color(red)
TSCV.ADCredB5,TSCV($TSCV0004+34:1:B:H01) # ADC button color(red)
TSCV.ADCredB6,TSCV($TSCV00B1+2:1:B:H18) # ADC button color(red)
TSCV.ADCredB7,TSCV($TSCV0004+28:1:B:H22) # ADC button color(red) (99.03.09 chg Mr.sasaki)
TSCV.ADCredB8,TSCV($TSCV0004+29:1:B:H07) # ADC button color(red) (99.03.09 chg Mr.sasaki)
TSCV.ADCredB9,TSCV($TSCV0004+31:1:B:H4F) # ADC button color(red) (99.03.09 chg Mr.sasaki)
TSCV.ADCInOut,TSCV($TSCV0004+30:1:B:H18) # ADCInOut
TSCV.ADCOnOff,TSCV($TSCV0004+25:1:B:H03) # ADCOnOff
TSCV.ADCMode,TSCV($TSCV00A1+10:1:B:H0C) # ADCMode
TSCL.ADCPos,TSCL($TSCL_FRAD+37:6:D) # ADCPos
TSCL.ADCSpeed,TSCL($TSCL_FRAD+49:6:D) # ADCSpeed
TSCV.ADCWaveLen,TSCV($TSCV00A1+60:6:D:H000FFFF00000) # ADCWaveLen
TSCV.ADCONOFF_PF,TSCV($TSCV0036+25:1:B:H03) # ADCOnOff_PF
TSCV.ADCMODE_PF,TSCV($TSCV00A1+10:1:B:HC0) # ADCMode_PF
TSCL.ADCPOS_PF,TSCL($TSCL_FRCU+37:6:D) # ADCPos_PF
TSCL.ADCCMD_PF,TSCL($TSCL_FRCU+43:6:D) # ADCCmd_PF (add kawai 99.08.23)
TSCL.ADCSPEED_PF,TSCL($TSCL_FRCU+49:6:D) # ADCSpeed_PF

# for OSSO_MonTel SV Screen 
TSCV.SVredB1,TSCV($TSCV0007+4:1:B:H33) # SV button color(red)
TSCV.SVredB2,TSCV($TSCV00B1+3:1:B:H04) # SV button color(red)
TSCV.SVredB3,TSCV($TSCV0007+25:1:B:H0F) # SV button color(red)
TSCV.SVredB4,TSCV($TSCV0007+27:1:B:HC7) # SV button color(red)
TSCV.SVImage,TSCV($TSCV0007+5:1:B:HC0) # SVImage
TSCV.SVShutter,TSCV($TSCV0007+26:1:B:H03) # SVShutter
TSCV.SVExpTime,TSCV($TSCV0007+8:4:L) # SVExpTime
TSCV.SVBinning,TSCV($TSCV0007+22:1:B:HFF) # SVBinning
TSCV.SVFilter,TSCV($TSCV0007+23:1:B) # SVFilter
TSCV.SVImgRegX1,TSCV($TSCV0007+14:2:L) # SVImgRegX1
TSCV.SVImgRegY1,TSCV($TSCV0007+16:2:L) # SVImgRegY1
TSCV.SVImgRegX2,TSCV($TSCV0007+18:2:L) # SVImgRegX2
TSCV.SVImgRegY2,TSCV($TSCV0007+20:2:L) # SVImgRegY2
VGW.SVCalibSky,VGWD(244:8:C) # SVCalibSky
VGW.SVCalibDark,VGWD(244:8:C) # SVCalibDark
VGW.SVCalibFlat,VGWD(244:8:C) # SVCalibFlat
TSCL.SVPos,TSCL($TSCL_SV+1:4:S:0.001) # SVPos

# for OSSO_MonTel SH Screen 
TSCV.SHredB1,TSCV($TSCV0009+51:1:B:H0F) # SH button color
TSCV.SHredB2,TSCV($TSCV0009+52:1:B:H07) # SH button color
TSCV.SHredB3,TSCV($TSCV0009+53:1:B:H07) # SH button color
TSCV.SHredB4,TSCV($TSCV0009+54:1:B:H07) # SH button color
TSCV.SHredB5,TSCV($TSCV0009+55:1:B:H07) # SH button color
TSCV.SHredB6,TSCV($TSCV0009+56:1:B:H07) # SH button color
TSCV.SHredB7,TSCV($TSCV0009+50:1:B:HC7) # SH button color
TSCV.SHredB8,TSCV($TSCV00B1+2:1:B:H60) # SH button color (99.03.09 chg Mr.sasaki)
TSCV.SHTest,TSCV($TSCV0009+15:1:B:H03) # SHTest
TSCV.SHMode,TSCV($TSCV00B1+7:1:B:H03) # SHMode
TSCV.SHr,TSCL($TSCL_FPCI+1:6:D) # same AGr (99.07.08 chg kosugi)
TSCV.SHR,TSCL($TSCL_FPCI+1:6:D) # same AGr (99.07.08 chg kosugi)
TSCV.SHTheta,TSCL($TSCL_FPCI+7:6:D) # same AGTheta (99.07.08 chg kosugi)
TSCV.SHTHETA,TSCL($TSCL_FPCI+7:6:D) # same AGTheta (99.07.08 chg kosugi)

# for OSSO_MonTel CalSource Screen 
TSCV.CALredB1,TSCV($TSCV000E+46:1:B:HFF) # Cal button color(red)
TSCV.CALredB2,TSCV($TSCV000E+52:1:B:HFF) # Cal button color(red)
TSCV.CALredB3,TSCV($TSCV000E+53:1:B:HE7) # Cal button color(red) (99.03.09 chg Mr.sasaki)
TSCV.CALredB4,TSCV($TSCV000E+45:1:B:H83) # Cal button color(red) (99.03.09 chg Mr.sasaki)
TSCV.CALredB5,TSCV($TSCV000E+48:1:B:H16) # Cal button color(red)
TSCV.CALredB6,TSCV($TSCV000E+49:1:B:H07) # Cal button color(red)
TSCV.CALredB7,TSCV($TSCV000E+50:1:B:H02) # Cal button color(red)
TSCV.CALredB8,TSCV($TSCV000E+54:1:B:H1F) # Cal button color(red)

# for OSSO_TelStat Tip/Tilt/Chopping status
TSCV.TT_Mode,TSCV($TSCV0028+2:1:B:H87)       # Tip-Tilt Mode Chop/TT/Pos/Maint (add bon 2005.08.17)
TSCV.TT_Drive,TSCV($TSCV0028+4:1:B:H07)      # Tip-Tilt Drive On/Off/On Rdy    (add bon 2005.08.17)
TSCV.TT_DataAvail,TSCV($TSCV0028+12:1:B:H01) # Tip-Tilt Data Available         (add bon 2005.08.17)
TSCV.TT_TTStart,TSCV($TSCV0028+12:1:B:H01)   # Tip-Tilt Start                  (add bon 2005.09.15)
TSCV.TT_ChopStat,TSCV($TSCV0028+28:1:B:H07)  # Tip-Tilt Chopping Status        (add bon 2005.08.17)
TSCL.TT_Chop_Offset_Ang,TSCL($TSCL_MLP1+117:6:D) # Chopping Position Offset Angle

# for OSSL_StatS,L process
#     一部 OSSO_MonTel と重複するため同一ステータスは定義しない
TSCS.PMRA,TSCS($TSCS_TSC+19:6:D) # PMRA
TSCS.PMDEC,TSCS($TSCS_TSC+25:6:D) # PMDEC
TSCS.E,TSCS($TSCS_TSC+37:1:B:H03) # E
TSCS.ANAB,TSCS($TSCS_TSC+31:6:D) # ANAB
TSCV.OBJNAME,TSCV($TSCV00A1+40:20:C) # OBJECT NAME
TSCV.OBJKIND,TSCV($TSCV00A1+706:32:C) # OBJECT KIND
TSCL.AZ_SPEED,TSCL($TSCL_MTDR+25:6:D) # AZ_SPEED
TSCL.EL_SPEED,TSCL($TSCL_MTDR+31:6:D) # EL_SPEED
TSCS.DDMODE,TSCS(0:0:C) # T.B.D. # DomeDriveMode
TSCS.DDPOS,TSCS($TSCS_DRDR+1:6:D) # DomeDrivePosition
TSCL.WSPOS,TSCL($TSCL_THRM+1:6:D) # WindScreenPosition
TSCV.P_SEL,TSCV($TSCV0030+13:1:B:HF0) # P Select
TSCL.TSFPOS,TSCL($TSCL_THRM+7:6:D) # TopScreenFrontPosition
TSCL.TSRPOS,TSCL($TSCL_THRM+13:6:D) # TopScreenRearPosition
TSCV.AG_DT_OBJ,TSCV(0:1:B) # T.B.D. # AG DataType OBJ
TSCV.AG_DT_SKY,TSCV($TSCV0006+66:1:B:H04) # AG DataType SKY
TSCV.AG_DT_FLAT,TSCV($TSCV0006+76:1:B:H04) # AG DataType FLAT
TSCV.AG_DT_DARK,TSCV($TSCV0006+71:1:B:H04) # AG DataType DARK
TSCV.AG_EXP_OBJ,TSCV($TSCV0006+5:4:L) # AG EXP OBJ
TSCV.AG_EXP_SKY,TSCV($TSCV0006+62:4:L) # AG EXP SKY
TSCV.AG_EXP_FLAT,TSCV($TSCV0006+67:4:L) # AG EXP FLAT
TSCV.AG_EXP_DARK,TSCV($TSCV0006+72:4:L) # AG EXP DARK
TSCV.AG_CAL_LOOP,TSCV($TSCV0006+9:2:L) # AG CAL LOOP
TSCV.AG1_I_SEIL,TSCV($TSCV0006+13:2:L) # AG1 Intensity CEIL
TSCV.AG1_I_CEIL,TSCV($TSCV0006+13:2:L) # AG1 Intensity CEIL (add ukawa 2003.11.24)
TSCV.AG1_I_BOTTOM,TSCV($TSCV0006+11:2:L) # AG1 Intensity BOTTOM
TSCV.AG2_I_SEIL,TSCV($TSCV0006+17:2:L) # AG1 Intensity CEIL
TSCV.AG2_I_CEIL,TSCV($TSCV0006+17:2:L) # AG1 Intensity CEIL (add ukawa 2003.11.24)
TSCV.AG2_I_BOTTOM,TSCV($TSCV0006+15:2:L) # AG1 Intensity BOTTOM
TSCV.SV_CAL_LOOP,TSCV(0:1:L) # SV CAL LOOP # T.B.D.
TSCS.ROTCMD,TSCS($TSCS_FRAD+7:6:D) # Insrot,ImgRot deg (cmd) (99.03.10 kosugi)
TSCS.ROTPOS,TSCS($TSCS_FRAD+1:6:D) # Insrot,ImgRot deg (pos) (99.03.10 kosugi)
TSCL.TOPS_F_CMD,TSCL($TSCL_TSC+115:6:D) # TOPS_F_CMD (cmd) (99.03.10 kosugi)
TSCL.TOPS_F_POS,TSCL($TSCL_THRM+7:6:D) # TOPS_F_POS (pos) (99.03.10 kosugi)
TSCL.TOPS_R_CMD,TSCL($TSCL_TSC+121:6:D) # TOPS_R_CMD (cmd) (99.03.10 kosugi)
TSCL.TOPS_R_POS,TSCL($TSCL_THRM+13:6:D) # TOPS_R_POS (pos) (99.03.10 kosugi)
TSCL.WINDSCMD,TSCL($TSCL_TSC+127:6:D) # WINDSCMD (cmd) (99.03.10 kosugi)
TSCL.WINDSPOS,TSCL($TSCL_THRM+1:6:D) # WINDSPOS (pos) (99.03.10 kosugi)
TSCL.ADCCMD,TSCL($TSCL_FRAD+43:6:D) # ADCCMD (cmd) (99.03.10 kosugi)
TSCL.ADCPOS,TSCL($TSCL_FRAD+37:6:D) # ADCPOS (pos) (99.03.10 kosugi)
TSCL.TT_POS,TSCL($TSCL_TTCU+13:6:D) # TipTilt Position (deg) (chg kawai 99.10.25)
TSCV.TT_OFFSETMODE,TSCV($TSCV0028+3:1:B:H07) # TipTilt OffsetMode (chg kawai 99.10.25)
TSCV.TT_ZEROBIAS,TSCV($TSCV0028+19:6:D) # TipTilt ZeroBias (arcsec) (chg kawai 99.10.25)
TSCS.TT_TX,TSCS($TSCS_TTCU+1:6:D) # TipTilt TX real arcsec (add kawai 99.10.25)
TSCS.TT_TY,TSCS($TSCS_TTCU+7:6:D) # TipTilt TY real arcsec (add kawai 99.10.25)
TSCS.TT_Z,TSCS($TSCS_TTCU+49:6:D) # TipTilt Z real mm (add kawai 99.10.25)
TSCV.TT_PATTERN,TSCV($TSCV0028+27:1:B:H07) # TipTilt Pattern (add kawai 99.10.25)
TSCV.TT_SIGNAL,TSCV($TSCV0028+29:1:B:H03) # TipTilt Signal (add kawai 99.10.25)
TSCL.CAL_POS,TSCL($TSCL_CAL+1:6:D) # Cal_Pos mm (add kawai 99.10.25)
TSCV.CAL_FILTER_A,TSCV($TSCV000E+33:1:B:H0F) # Cal_Filter_A 1,2,3,4 (add kawai 99.10.25)
TSCV.CAL_FILTER_B,TSCV($TSCV000E+34:1:B:H0F) # Cal_Filter_B 1,2,3,4 (add kawai 99.10.25)
TSCV.CAL_FILTER_C,TSCV($TSCV000E+35:1:B:H0F) # Cal_Filter_C 1,2,3,4 (add kawai 99.10.25)
TSCV.CAL_FILTER_D,TSCV($TSCV000E+36:1:B:H0F) # Cal_Filter_D 1,2,3,4 (add kawai 99.10.25)
TSCL.CAL_HCT1_AMP,TSCL($TSCL_CAL+13:6:D) # Cal_HCT1_AMP mA (add kawai 99.10.25)
TSCL.CAL_HCT2_AMP,TSCL($TSCL_CAL+25:6:D) # Cal_HCT2_AMP mA (add kawai 99.10.25)
TSCL.CAL_HAL1_AMP,TSCL($TSCL_CAL+37:6:D) # Cal_HAL1_AMP A (add kawai 99.10.25)
TSCL.CAL_HAL2_AMP,TSCL($TSCL_CAL+49:6:D) # Cal_HAL2_AMP A (add kawai 99.10.25)
TSCV.CAL_FOCUS,TSCV($TSCV000E+25:1:B:H1F) # Cal_FOCUS (add ooto 00.08.08)
TSCV.CAL_DRIVE,TSCV($TSCV000E+31:1:B:H0F) # Cal_DRIVE (add koura 00.06.22)
TSCV.CAL_HCT_LAMP,TSCV($TSCV000E+32:1:B:H07) # Cal_HCT_LAMP (add koura 00.06.22)
TSCV.CAL_HCT_LAMP1,TSCV($TSCV000E+37:1:B:HFF) # Cal_HCT_LAMP1 (add koura 00.06.22)
TSCV.CAL_HCT_LAMP2,TSCV($TSCV000E+38:1:B:H0F) # Cal_HCT_LAMP2 (add koura 00.06.22)
TSCV.CAL_HAL_LAMP1,TSCV($TSCV000E+39:1:B:H3F) # Cal_HAL_LAMP1 (add koura 00.06.22)
TSCV.CAL_HAL_LAMP2,TSCV($TSCV000E+40:1:B:H3F) # Cal_HAL_LAMP2 (add koura 00.06.22)
TSCV.CAL_RGL_LAMP1,TSCV($TSCV000E+41:1:B:H33) # Cal_RGL_LAMP1 (add koura 00.06.22, add oooto 00.08.08)
TSCV.CAL_RGL_LAMP2,TSCV($TSCV000E+42:1:B:H33) # Cal_RGL_LAMP2 (add koura 00.06.22, add oooto 00.08.08)
TSCV.CAL_SHUTTER,TSCV($TSCV000E+43:1:B:H3F) # Cal_SHUTTER (add koura 00.06.22)
TSCL.AG_R,TSCL($TSCL_FPCI+1:6:D) # AG_R (chg kusu 99.07.27)
TSCL.AG_R_CMD,TSCL($TSCL_FPCI+13:6:D) # AG_R(command) (add koura 00.11.13)
TSCL.AG_THETA,TSCL($TSCL_FPCI+7:6:D) # AG_THETA (chg kusu 99.07.27)
TSCL.AG_THETA_CMD,TSCL($TSCL_FPCI+19:6:D) # AG_THETA(command) (add koura 00.11.13)
TSCL.AGPF_X,TSCL($TSCL_ASCU+1:6:D) # AGPF_X (chg kusu 99.07.27)
TSCL.AGPF_Y,TSCL($TSCL_ASCU+7:6:D) # AGPF_Y (chg kusu 99.07.27)
TSCL.AGPF_Z,TSCL($TSCL_ASCU+13:6:D) # AGPF_Z (chg kusu 99.07.27)
TSCV.ADCPF_TELESCOPE,TSCV($TSCV00A1+10:1:B:HC0) # ADCPF_TELESCOPE (chg kusu 99.07.27)
TSCL.ADCPF_SPEED,TSCL($TSCL_FRAD+49:6:D) # ADCPF_SPEED (chg kusu 99.07.27)
TSCL.ADCPF_POS,TSCL($TSCL_FRAD+37:6:D) # ADCPF_POS (chg kusu 99.07.27)
TSCV.IROTPF_TELESCOPE,TSCV($TSCV00B1+7:1:B:H30) # IROTPF_TELESCOPE (chg kusu 99.07.27)
TSCL.IROTPF_SPEED,TSCL($TSCL_FRAD+13:6:D) # IROTPF_SPEED (chg kusu 99.07.27)
TSCS.IROTPF_POS,TSCS($TSCS_FRAD+1:6:D) # IROTPF_POS (chg kusu 99.07.27)
TSCV.PF_OFF_X,TSCV($TSCV00B2+824:6:D) # PFU OFFSET X(mm) (add ooto 00.07.11)
TSCV.PF_OFF_Y,TSCV($TSCV00B2+830:6:D) # PFU OFFSET Y(mm) (add ooto 00.07.11)
TSCV.PF_OFF_Z,TSCV($TSCV00B2+836:6:D) # PFU OFFSET Z(mm) (add ooto 00.07.11)
TSCV.PF_OFF_TX,TSCV($TSCV00B2+842:6:D) # PFU OFFSET TX(arcmin) (add ooto 00.07.11)
TSCV.PF_OFF_TY,TSCV($TSCV00B2+848:6:D) # PFU OFFSET TY(arcmin) (add ooto 00.07.11)
TSCV.PF_OFF_TZ,TSCV($TSCV00B2+884:6:D) # PFU OFFSET TZ(arcmin) (add ooto 00.07.11)
TSCS.RA_OFFSET,TSCS($TSCS_TSC+86:6:B) # OFFSET RA(arcsec) (add ooto 01.08.14)
TSCS.DEC_OFFSET,TSCS($TSCS_TSC+92:5:B) # OFFSET DEC(arcsec) (add ooto 01.08.14)
TSCL.AGPF_X_CMD,TSCL($TSCL_ASCU+19:6:D) # AGPF_X(command) (add ooto 01.08.14)
TSCL.AGPF_Y_CMD,TSCL($TSCL_ASCU+25:6:D) # AGPF_X(command) (add ooto 01.08.14)
TSCV.WINDSDRV,TSCV($TSCV0030+7:1:B:H0C) # Wind Screen Drive (add ooto 01.08.14)
TSCS.AZDIF,TSCS($TSCS_MTDR+25:6:D) # Az diff (add ooto 01.09.27)
TSCS.ELDIF,TSCS($TSCS_MTDR+31:6:D) # El diff (add ooto 01.09.27)
TSCV.AG_OVERLOAD,TSCV($TSCV0006+78:1:B:H08) # AG Over load (add ukawa 2004.09.03)
TSCV.SV_OVERLOAD,TSCV($TSCV0007+27:1:B:H08) # SV Over load (add ukawa 2004.09.03)
TSCV.AG_AUTO_I_CUT,TSCV($TSCV0006+79:1:B:HC0) # AG Auto Intensity cut (add ukawa 2004.09.03)
TSCV.SV_AUTO_I_CUT,TSCV($TSCV0007+28:1:B:HC0) # SV Auto Intensity cut (add ukawa 2004.09.03)
TSCV.TRACKING,TSCV($TSCV00A1+15:1:B:H3C) # Tracking (add ukawa 2004.09.03)
TSCV.FOCUSINFO,TSCV($TSCV00A1+1552:4:B:HFFFFFF1F) # Focus (add ukawa 2004.12.24)
TSCV.FOCUSALARM,TSCV($TSCV00A1+1555:1:B:HC0) # Focus Alarm (add ukawa 2004.12.24)
TSCV.FOCUSINFO2,TSCV($TSCV00A1+1557:1:B:H0F) # AO/HSC Focus (rkackley 2012.05.22)
TSCL.AGPIRdX,TSCL($TSCL_OBCP+9:4:S:0.01) # AG for SH Error dX(marcsec) (add ukawa 2005.02.01)
TSCL.AGPIRdY,TSCL($TSCL_OBCP+13:4:S:0.01) # AG for SH Error dY(marcsec) (add ukawa 2005.02.01)
TSCL.AGFMOSdAZ,TSCL($TSCL_OBCP+55:4:S:0.001) # Fibre AG Error dAz(arcsec) (add ukawa 2005.02.01)
TSCL.AGFMOSdEL,TSCL($TSCL_OBCP+59:4:S:0.001) # Fibre AG Error dEl(arcsec) (add ukawa 2005.02.01)
TSCL.AGPIR_X,TSCL($TSCL_OBCP+69:6:D) # AG/SH REAL POSN for PIR(mm) (add ukawa 2005.02.01)
TSCL.AGPIR_X_CMD,TSCL($TSCL_OBCP+75:6:D) # AG/SH REAL POSN CMD for PIR(mm) (add ukawa 2005.02.01)
TSCL.ZPOS_PIR,TSCL($TSCL_OBCP+85:6:D) # FAM REAL POSN for PIR (add ukawa 2005.02.01)
TSCV.AGPIRCCalc,TSCV($TSCV003B+1:1:B:H04) # AG for SH Detect Star (add ukawa 2005.02.01)
TSCV.AGPIRImage,TSCV($TSCV003B+1:1:B:H03) # AG for SH Exposure (add ukawa 2005.02.01)
TSCV.AGPIR_I_BOTTOM,TSCV($TSCV003B+6:2:L) # AG for SH Lower Limit (add ukawa 2005.02.01)
TSCV.AGPIR_I_CEIL,TSCV($TSCV003B+8:2:L) # AG for SH Upper Limit (add ukawa 2005.02.01)
TSCV.AGPIRExpTime,TSCV($TSCV003B+2:4:L) # AG for SH Exposure Time(ms) (add ukawa 2005.02.01)
TSCV.AGPIRImgRegX1,TSCV($TSCV003B+10:2:L) # AG for SH Video Area X(pixel) (add ukawa 2005.02.01)
TSCV.AGPIRImgRegY1,TSCV($TSCV003B+12:2:L) # AG for SH Video Area Y(pixel) (add ukawa 2005.02.01)
TSCV.AGPIRImgRegX2,TSCV($TSCV003B+14:2:L) # AG for SH Video Area Width X(pixel) (add ukawa 2005.02.01)
TSCV.AGPIRImgRegY2,TSCV($TSCV003B+16:2:L) # AG for SH Video Area Width Y(pixel) (add ukawa 2005.02.01)
TSCV.AGPIRCCalcRegX1,TSCV($TSCV003B+18:2:L) # AG for SH Star Position DET Area X(pixel) (add ukawa 2005.02.01)
TSCV.AGPIRCCalcRegY1,TSCV($TSCV003B+20:2:L) # AG for SH Star Position DET Area Y(pixel) (add ukawa 2005.02.01)
TSCV.AGPIRCCalcRegX2,TSCV($TSCV003B+22:2:L) # AG for SH Star Position DET Area Width X(pixel) (add ukawa 2005.02.01)
TSCV.AGPIRCCalcRegY2,TSCV($TSCV003B+24:2:L) # AG for SH Star Position DET Area Width Y(pixel) (add ukawa 2005.02.01)
TSCV.AGPIRBinning,TSCV($TSCV003B+34:1:B:HFF) # AG for SH Binning Pattern (add ukawa 2005.02.01)
TSCV.AGFMOSCCalc,TSCV($TSCV003B+39:1:B:H04) # Fibre AG Detect Star (add ukawa 2005.02.01)
TSCV.AGFMOSImage,TSCV($TSCV003B+39:1:B:H03) # Fibre AG Exposure (add ukawa 2005.02.01)
TSCV.AGFMOSExpTime,TSCV($TSCV003B+40:4:L) # Fibre AG Exposure Time(ms) (add ukawa 2005.02.01)
TSCV.PIRShutter,TSCV($TSCV003B+50:1:B:H03) # PIR ENTRANCE SHUTTER (add ukawa 2005.02.01)
TSCV.AGAutoGuideReady,TSCV($TSCV00B1+8:1:B:H03) # AG Guide Ready (add ukawa 2005.02.01)
TSCV.M2_TIPTILT,TSCV($TSCV00B1+9:1:B:H18) # Tip-Tilt Auto Guide (add ukawa 2005.02.01)
TSCV.SVAutoGuideReady,TSCV($TSCV00B1+146:1:B:H03) # SV Auto Guide Ready (add ukawa 2005.02.01)
TSCV.PIRAutoGuideReady,TSCV($TSCV00B1+146:1:B:H0C) # PIR Auto Guide Ready (add ukawa 2005.02.01)
TSCV.PIRAutoGuideOn,TSCV($TSCV00B1+147:1:B:H0C) # PIR Auto Guide (add ukawa 2005.02.01)
TSCV.SVAutoGuideOn,TSCV($TSCV00B1+147:1:B:H03) # SV Auto Guide (add ukawa 2005.02.01)
TSCL.AGPIRDX,TSCL($TSCL_OBCP+9:4:S:0.01) # AG for SH Error dX(marcsec) (add ukawa 2005.02.01)
TSCL.AGPIRDY,TSCL($TSCL_OBCP+13:4:S:0.01) # AG for SH Error dY(marcsec) (add ukawa 2005.02.01)

# POpt Rotator Limits
TSCV.P_RotLim,TSCV($TSCV0036+2:1:B:H0F) # P Rotator 1st and 2nd Limits

# Prime Focus AG/SH Limits and DPA Faults
TSCV.P_AG_SH_XY_1stLim,TSCV($TSCV0037+19:1:B:HF0) # P AG/SH X and Y 1st Limits
TSCV.P_AG_SH_Z_1stLim,TSCV($TSCV0037+20:1:B:H03) # P AG/SH Z 1st Limits
TSCV.P_AG_SH_2ndLim,TSCV($TSCV0037+20:1:B:HFC) # P AG/SH 2nd Limits
TSCV.P_AG_SH_DPA_Fault,TSCV($TSCV0037+8:1:B:H07) # P AG/SH DPA Fault
TSCV.P_AG_SH_DPA2_Fault,TSCV($TSCV0037+21:1:B:H01) # P AG/SH DPA2 Fault
TSCV.P_AG_SH_DPA3_Fault,TSCV($TSCV0037+21:1:B:H02) # P AG/SH DPA3 Fault

# HSCSCAG Table aliases
TSCV.HSC.Shutter,TSCV($TSCV003D+1:1:B:H03) # HSC Shutter Open/Close
TSCV.HSC.ShutterAlarm,TSCV($TSCV003D+2:1:B:H01) # HSC Shutter Alarm
TSCV.HSC.Filter,TSCV($TSCV003D+3:1:B) # HSC Filter Selected
TSCV.HSC.SCAG.ExpTime,TSCV($TSCV003D+28:4:L) # HSC AG for SC Exposure Time
TSCV.HSC.SCAG.ImgRegX1,TSCV($TSCV003D+44:2:L) # HSC AG for SC Area X CCD
TSCV.HSC.SCAG.ImgRegY1,TSCV($TSCV003D+46:2:L) # HSC AG for SC Area Y CCD
TSCV.HSC.SCAG.ImgRegX2,TSCV($TSCV003D+48:2:L) # HSC AG for SC Area Width X CCD
TSCV.HSC.SCAG.ImgRegY2,TSCV($TSCV003D+50:2:L) # HSC AG for SC Area Width Y CCD
TSCV.HSC.SCAG.Image,TSCV($TSCV003D+26:1:B:H03) # HSC AG for SC Exposure On/Off
TSCV.HSC.SCAG.CCalcRegX1,TSCV($TSCV003D+52:2:L) # HSC AG for SC Star DET Area X
TSCV.HSC.SCAG.CCalcRegY1,TSCV($TSCV003D+54:2:L) # HSC AG for SC Star DET Area Y
TSCV.HSC.SCAG.CCalcRegX2,TSCV($TSCV003D+56:2:L) # HSC AG for SC Star DET Area Width X
TSCV.HSC.SCAG.CCalcRegY2,TSCV($TSCV003D+58:2:L) # HSC AG for SC Star DET Area Width Y
TSCV.HSC.SCAG.CCalc,TSCV($TSCV003D+26:1:B:H04) # HSC AG for SC Star Detect Start
TSCL.HSC.SCAG.DX,TSCL($TSCL_HSCSCAG+1:4:S:0.01) # HSC AG for SC Star Posn Error X
TSCL.HSC.SCAG.DY,TSCL($TSCL_HSCSCAG+5:4:S:0.01) # HSC AG for SC Star Posn Error Y
TSCL.HSC.SCAG.dAZ,TSCL($TSCL_HSCSCAG+9:6:D) # HSC AG for SC Star Posn Error AZ
TSCL.HSC.SCAG.dEL,TSCL($TSCL_HSCSCAG+15:6:D) # HSC AG for SC Star Posn Error EL
TSCL.HSC.SCAG.Intensity,TSCL($TSCL_HSCSCAG+33:2:L) # HSC AG for SC Star Posn Intensity
TSCL.HSC.SCAG.StarSize,TSCL($TSCL_HSCSCAG+29:4:L:0.00001) # HSC AG for SC  Image Size
TSCV.HSC.SCAG.AutoGuideReady,TSCV($TSCV003D+27:1:B:H01) # HSC AG for SC Guide Ready
TSCV.HSC.SCAG.CamIFAlarm,TSCV($TSCV003D+60:1:B:H01) # HSC AG for SC Camera I/F Alarm
TSCV.HSC.SCAG.MLP1IFAlarm,TSCV($TSCV003D+61:1:B:H01) # MLP1-HSCSCAG I/F Alarms
TSCV.HSC.SCAG.IFAlarms,TSCV($TSCV003D+67:1:B:H07) # HSCSCAG-VGW/TWS1/TWS2 I/F Alarms

# HSCSHAG Table aliases
TSCV.HSC.SHAG.ExpTime,TSCV($TSCV003E+30:4:L) # HSC AG for SH Exposure Time
TSCV.HSC.SHAG.ImgRegX1,TSCV($TSCV003E+46:2:L) # HSC AG for SH Video Area X CCD
TSCV.HSC.SHAG.ImgRegY1,TSCV($TSCV003E+48:2:L) # HSC AG for SH Video Area Y CCD
TSCV.HSC.SHAG.ImgRegX2,TSCV($TSCV003E+50:2:L) # HSC AG for SH Video Area Width X CCD
TSCV.HSC.SHAG.ImgRegY2,TSCV($TSCV003E+52:2:L) # HSC AG for SH Video Area Width Y CCD
TSCV.HSC.SHAG.Image,TSCV($TSCV003E+28:1:B:H03) # HSC AG for SH Exposure On/Off
TSCV.HSC.SHAG.CCalcRegX1,TSCV($TSCV003E+54:2:L) # HSC AG for SH Star DET Area X
TSCV.HSC.SHAG.CCalcRegY1,TSCV($TSCV003E+56:2:L) # HSC AG for SH Star DET Area Y
TSCV.HSC.SHAG.CCalcRegX2,TSCV($TSCV003E+58:2:L) # HSC AG for SH Star DET Area Width X
TSCV.HSC.SHAG.CCalcRegY2,TSCV($TSCV003E+60:2:L) # HSC AG for SH Star DET Area Width Y
TSCV.HSC.SHAG.CCalc,TSCV($TSCV003E+28:1:B:H04) # HSC AG for SH Star Detect Start
TSCL.HSC.SHAG.DX,TSCL($TSCL_HSCSHAG+1:4:S:0.01) # HSC AG for SH Star Posn Error X
TSCL.HSC.SHAG.DY,TSCL($TSCL_HSCSHAG+5:4:S:0.01) # HSC AG for SH Star Posn Error Y
TSCL.HSC.SHAG.dAZ,TSCL($TSCL_HSCSHAG+9:6:D) # HSC AG for SH Star Posn Error AZ
TSCL.HSC.SHAG.dEL,TSCL($TSCL_HSCSHAG+15:6:D) # HSC AG for SH Star Posn Error EL
TSCL.HSC.SHAG.Intensity,TSCL($TSCL_HSCSHAG+33:2:L) # HSC AG for SH Star Posn Intensity
TSCL.HSC.SHAG.StarSize,TSCL($TSCL_HSCSHAG+29:4:L:0.00001) # HSC AG for SH  Image Size
TSCV.HSC.SHAG.AutoGuideReady,TSCV($TSCV003E+29:1:B:H01) # HSC AG for SH Guide Ready
TSCV.HSC.SHAG.CamIFAlarm,TSCV($TSCV003E+64:1:B:H01) # HSC AG for SH Camera I/F Alarm
TSCV.HSC.SHAG.MLP1IFAlarm,TSCV($TSCV003E+65:1:B:H01) # MLP1-HSCSHAG I/F Alarms
TSCV.HSC.SHAG.IFAlarms,TSCV($TSCV003E+71:1:B:H07) # HSCSHAG-VGW/TWS1/TWS2 I/F Alarms
TSCV.HSC.SHAG.I_BOTTOM,TSCV($TSCV003E+72:2:L) # HSC AG for SH CCD Lower Limit
TSCV.HSC.SHAG.I_CEIL,TSCV($TSCV003E+74:2:L) # HSC AG for SH CCD Upper Limit

# HSCSH Table aliases
TSCV.HSC.SH.ExpTime,TSCV($TSCV003F+30:4:L) # HSC SH Exposure Time
TSCV.HSC.SH.Image,TSCV($TSCV003F+28:1:B:H03) # HSC SH Exposure On/Off
TSCV.HSC.SH.Test,TSCV($TSCV003F+28:1:B:H0C) # HSC SH Test On/Off
TSCV.HSC.SH.CCalc,TSCV($TSCV003F+29:1:B:H01) # HSCSH REF Position Detected Start
TSCV.HSC.SH.CamIFAlarm,TSCV($TSCV003F+36:1:B:H01) # HSC SH Camera I/F Alarm
TSCV.HSC.SH.MLP2IFAlarm,TSCV($TSCV003F+37:1:B:H01) # MLP2-HSCSH I/F Alarms
TSCV.HSC.SH.IFAlarms,TSCV($TSCV003F+43:1:B:H07) # HSCSH-VGW/TWS1/TWS2 I/F Alarms
TSCV.HSC.SH.I_BOTTOM,TSCV($TSCV003F+44:2:L) # HSCSH CCD Lower Limit
TSCV.HSC.SH.I_CEIL,TSCV($TSCV003F+46:2:L) # HSCSH CCD Upper Limit
TSCV.HSC.SH.CAL_LOOP,TSCV($TSCV003F+48:2:L) # HSCSH Exposure Count
TSCV.HSC.SH.CalibDark,TSCV($TSCV003F+52:1:B:H03) # HSCSH Dark Data Used/Not Used
TSCV.HSC.SH.DT_DARK,TSCV($TSCV003F+52:1:B:H04) # HSCSH Dark Data Get Start
TSCV.HSC.SH.EXP_DARK,TSCV($TSCV003F+53:4:L) # HSCSH Dark Data Exposure Time

# HSC aliases from MLP1MON document
TSCV.HSC.SCAG.MLP1Fault,TSCV($TSCV00B1+106:1:B:H01) # HSCSCAG - MLP1 Fault
TSCV.HSC.SHAG.MLP1Fault,TSCV($TSCV00B1+106:1:B:H02) # HSCSHAG - MLP1 Fault

# HSC FEU alias
TSCV.HSC.FiltExchRdy,TSCV($TSCV00A1+1512:1:B:H0F) # HSC Filter Exchange Ready (Both IR and Opt)

# statmon env
TSCL.M1_TEMP,TSCL($TSCL_TSC+13:6:D) # m1 temperature.  
TSCL.TOPRING_WINDS_F,TSCL($TSCL_TLSCP_TEMP+187:6:D) # top-ring front wind speed
TSCL.TOPRING_WINDS_R,TSCL($TSCL_TLSCP_TEMP+181:6:D) # top-ring rear wind speed.

# Wind speeds at center section (i.e., elevation axis) of telescope
# F => Front, R => Rear
TSCL.CSCT_WINDS_F.X,TSCL($TSCL_TLSCP_TEMP+205:6:D) # Center section wind speed: CSCT(F) WVEL(X) Data
TSCL.CSCT_WINDS_F.Y,TSCL($TSCL_TLSCP_TEMP+211:6:D) # Center section wind speed: CSCT(F) WVEL(Y) Data
TSCL.CSCT_WINDS_F.Z,TSCL($TSCL_TLSCP_TEMP+217:6:D) # Center section wind speed: CSCT(F) WVEL(Z) Data
TSCL.CSCT_WINDS_R.X,TSCL($TSCL_TLSCP_TEMP+223:6:D) # Center section wind speed: CSCT(R) WVEL(X) Data
TSCL.CSCT_WINDS_R.Y,TSCL($TSCL_TLSCP_TEMP+229:6:D) # Center section wind speed: CSCT(R) WVEL(Y) Data
TSCL.CSCT_WINDS_R.Z,TSCL($TSCL_TLSCP_TEMP+235:6:D) # Center section wind speed: CSCT(R) WVEL(Z) Data

#TSCL.M1_TEMP_P,TSCL($TSCL_TSC+31:6:D) # m1 temp periphery . note:testing 
#TSCL.DEW_TELESCOPE,TSCL($TSCL_TSC+43:6:D) # telescope dew point. note:testing 
#TSCL.DEW_M1,TSCL($TSCL_TSC+43:61:D) # m1 dew point. note:testing

# STATS table alias
STATS.RA,STATS(32*01:32:C) # RA(hhmmss.sss)
STATS.DEC,STATS(32*02:32:C) # DEC(+ddmmss.ss)
STATS.EQUINOX,STATS(32*03:32:C) # equinox(yyyy.yyyy) #change kosugi 99.10.04 old=EQNX
STATS.PMRA,STATS(32*04:32:C) # PMRA(arcsec/year)
STATS.PMDEC,STATS(32*05:32:C) # PMDEC(arcsec/year)
STATS.E,STATS(32*06:32:C) # E(ON,OFF)
STATS.ANAB,STATS(32*07:32:C) # ANBA arcsec
STATS.AZ,STATS(32*08:32:C) # AZ(deg)
STATS.EL,STATS(32*09:32:C) # EL(deg)
STATS.DOMEDRIVE_MODE,STATS(32*10:32:C) # T.B.D. # DomeDriveMode(TSC,OBS)
STATS.DOMEDRIVE_POS,STATS(32*11:32:C) # DomeDrivePosition(deg)
STATS.IROT_POS,STATS(32*12:32:C) # (Ins/Img)Rot position(deg)
STATS.ROTDIF,STATS(32*13:32:C) # ROTDIF abs(ROTCMD-ROTPOS) (99.03.10 kosugi)
STATS.IROTPF_POS,STATS(32*14:32:C) # IROTPF_POS (chg kusu 99.07.27)
STATS.ROTDIF_PF,STATS(32*15:32:C) # ROTDIF_PF abs(ROTCMD_PF-ROTPOS_PF) (add kawai 99.08.23)
STATS.AZDIF,STATS(32*16:32:C) # AZDIF abs(AZDIF) (add ooto 01.08.14) (change ooto 01.09.27)
STATS.ELDIF,STATS(32*17:32:C) # ELDIF abs(ELDIF) (add ooto 01.08.14) (change ooto 01.09.27)

# STATL table alias
STATL.OBJNAME,STATL(32*01:32:C) # object name(ascii max 20byte)
STATL.OBJKIND,STATL(32*02:32:C) # object kind(ascii max 32byte)
STATL.AZ_SPEED,STATL(32*03:32:C) # AZ speed(deg/sec)
STATL.EL_SPEED,STATL(32*04:32:C) # EL speed(deg/sec)
STATL.TSC_F_SELECT,STATL(32*05:32:C) # TSC FocusSelect(P_OPT,P_IR,CS,NS_OPT,NS_IR) TSCV.M2Drive:01,02=CS_OPT,CS_IR
STATL.Z,STATL(32*06:32:C) # Z(mm)
STATL.M1COVER_POS,STATL(32*07:32:C) # M1 cover position(OPEN,CLOSE,ON_WAY)
STATL.CELLCOVER_POS,STATL(32*08:32:C) # Cell cover position(OPEN,CLOSE,ON_WAY)
STATL.DOMESHUTTER_POS,STATL(32*09:32:C) # Dome shutter position(OPEN,CLOSE,ON_WAY)
STATL.WINDSCREEN_POS,STATL(32*10:32:C) # Wind screen position(m)
STATL.P_SELECT,STATL(32*11:32:C) # Position select(FRONT,REAR)
STATL.TOPSCREEN_FPOS,STATL(32*12:32:C) # TopScreenFrontPosition(m)
STATL.TOPSCREEN_RPOS,STATL(32*13:32:C) # TopScreenRearPosition(m)
STATL.SVPROVE_POS,STATL(32*14:32:C) # SVProvePosition(mm)
STATL.AG_SHUTTER,STATL(32*15:32:C) # AG shutter(OPEN,CLOSE)
STATL.D_TYPE,STATL(32*16:32:C) # AG DataType(OBJ,DARK,SKY,FLAT)
STATL.AG_EXPOSURE_OBJ,STATL(32*17:32:C) # AG EXP OBJ(ms)
STATL.AG_EXPOSURE_SKY,STATL(32*18:32:C) # AG EXP SKY(ms)
STATL.AG_EXPOSURE_DARK,STATL(32*19:32:C) # AG EXP DARK(ms)
STATL.AG_EXPOSURE_FLAT,STATL(32*20:32:C) # AG EXP FLAT(ms)
STATL.AG_BINNING,STATL(32*21:32:C) # AG BINNING(11,22,44,88)
STATL.CAL_DARK,STATL(32*22:32:C) # AG CAL DARK(ON,OFF)
STATL.CAL_SKY,STATL(32*23:32:C) # AG CAL SKY(ON,OFF)
STATL.CAL_FLAT,STATL(32*24:32:C) # AG CAL FLAT(ON,OFF)
STATL.AG_X1,STATL(32*25:32:C) # AG X1(pixel)
STATL.AG_Y1,STATL(32*26:32:C) # AG Y1(pixel)
STATL.AG_X2,STATL(32*27:32:C) # AG X2(pixel)
STATL.AG_Y2,STATL(32*28:32:C) # AG Y2(pixel)
STATL.AG_CAL_LOOP,STATL(32*29:32:C) # AG CAL LOOP(number)
STATL.CALC_MODE,STATL(32*30:32:C) # AG CALC MODE(CTR,BSECT,PK)
STATL.AG1_X1,STATL(32*31:32:C) # AG1 X1(pixel)
STATL.AG1_Y1,STATL(32*32:32:C) # AG1 Y1(pixel)
STATL.AG1_X2,STATL(32*33:32:C) # AG1 X2(pixel)
STATL.AG1_Y2,STATL(32*34:32:C) # AG1 Y2(pixel)
STATL.AG2_X1,STATL(32*35:32:C) # AG2 X1(pixel)
STATL.AG2_Y1,STATL(32*36:32:C) # AG2 Y1(pixel)
STATL.AG2_X2,STATL(32*37:32:C) # AG2 X2(pixel)
STATL.AG2_Y2,STATL(32*38:32:C) # AG2 Y2(pixel)
STATL.CALC_REGION,STATL(32*39:32:C) # CALC REGION(1,2)
STATL.AG1_I_SEIL,STATL(32*40:32:C) # AG1 Intensity CEIL(number)
STATL.AG2_I_SEIL,STATL(32*41:32:C) # AG2 Intensity CEIL(number)
STATL.AG1_I_BOTTOM,STATL(32*42:32:C) # AG1 Intensity BOTTOM(number)
STATL.AG2_I_BOTTOM,STATL(32*43:32:C) # AG2 Intensity BOTTOM(number)
STATL.SV_SHUTTER,STATL(32*44:32:C) # SV shutter(OPEN,CLOSE)
STATL.FILTER,STATL(32*45:32:C) # FILTER(NOP,0,1,2,3)
STATL.SV_EXPOSURE,STATL(32*46:32:C) # SV EXPOSURE(ms)
STATL.SV_BINNING,STATL(32*47:32:C) # SV BINNING(11,22,44,88)
STATL.SV_X1,STATL(32*48:32:C) # SV X1(pixel)
STATL.SV_Y1,STATL(32*49:32:C) # SV X2(pixel)
STATL.SV_X2,STATL(32*50:32:C) # SV Y1(pixel)
STATL.SV_Y2,STATL(32*51:32:C) # SV Y2(pixel)
STATL.SV_CAL_LOOP,STATL(32*52:32:C) # SV CAL LOOP(number)
STATL.ADC_F_SELECT,STATL(32*53:32:C) # ADC FocusSelect(P_OPT,P_IR,CS,NS_OPT)
STATL.ADC_TELESCOPE,STATL(32*54:32:C) # ADC telescope(LINK,FREE)
STATL.ADC_MODE,STATL(32*55:32:C) # ADC MODE(IN,OUT)
STATL.ADC_SPEED,STATL(32*56:32:C) # ADC SPEED(deg/sec)
STATL.ADC_POS,STATL(32*57:32:C) # ADC position(deg)
STATL.WAVELEN,STATL(32*58:32:C) # WaveLength(micro m)
STATL.IROT_TELESCOPE,STATL(32*59:32:C) # (Ins/Img)Rot telescope(LINK,FREE)
STATL.IROT_SPEED,STATL(32*60:32:C) # (Ins/Img)Rot speed(deg/sec)
STATL.IROT_POS,STATL(32*61:32:C) # (Ins/Img)Rot position(deg)
STATL.IROT_TYPE,STATL(32*62:32:C) # (Ins/Img)Rot type(BLUE,RED,NONE)
STATL.LAMP,STATL(32*63:32:C) # lamp(ON,OFF)
STATL.ZDIF,STATL(32*64:32:C) # ZDIF abs(ZCMD-ZPOS) (99.03.10 kosugi)
STATL.TOPS_F_DIF,STATL(32*65:32:C) # TOPS_F_DIF abs(TOPS_F_CMD-TOPS_F_POS) (99.03.10 kosugi)
STATL.TOPS_R_DIF,STATL(32*66:32:C) # TOPS_R_DIF abs(TOPS_R_CMD-TOPS_R_POS) (99.03.10 kosugi)
STATL.WINDSDIF,STATL(32*67:32:C) # WINDSDIF abs(WINDSCMD-WINDSPOS) (m) (99.03.10 kosugi)
STATL.ADCDIF,STATL(32*68:32:C) # ADCDIF abs(ADCCMD-ADCPOS) (99.03.10 kosugi)
STATL.TT_MODE,STATL(32*69:32:C) # TipTilt MODE (1999.06.15 kusu)
STATL.TT_FQ,STATL(32*70:32:C) # TipTilt FQ (1999.06.15 kusu)
STATL.TT_AMP,STATL(32*71:32:C) # TipTilt AMP (1999.06.15 kusu)
STATL.TT_POS,STATL(32*72:32:C) # TipTilt POSITION (1999.06.15 kusu)
STATL.TT_OFFSETMODE,STATL(32*73:32:C) # TipTilt OFFSET_MODE (1999.06.15 kusu)
STATL.TT_ZEROBIAS,STATL(32*74:32:C) # TipTilt ZERO_BIAS (1999.06.15 kusu)
STATL.AG_R,STATL(32*75:32:C) # AG_R (chg kusu 99.07.27)
STATL.AG_R_CMD,STATL(32*76:32:C) # AG_R_CMD (add koura 00.11.13)
STATL.AG_R_DIF,STATL(32*77:32:C) # AG_R_DIF abs(AG_R_CMD-AG_R) (add koura 00.11.13)
STATL.AG_THETA,STATL(32*78:32:C) # AG_THETA (chg kusu 99.07.27)
STATL.AG_THETA_CMD,STATL(32*79:32:C) # AG_THETA_CMD (add koura 00.11.13)
STATL.AG_THETA_DIF,STATL(32*80:32:C) # AG_THETA_DIF abs(AG_THETA_CMD-AG_THETA) (add koura 00.11.13)
STATL.AGPF_X,STATL(32*81:32:C) # AGPF_X (chg kusu 99.07.27)
STATL.AGPF_Y,STATL(32*82:32:C) # AGPF_y (chg kusu 99.07.27)
STATL.AGPF_Z,STATL(32*83:32:C) # AGPF_Z (chg kusu 99.07.27)
STATL.ADCPF_TELESCOPE,STATL(32*84:32:C) # ADCPF_TELESCOPE (chg kusu 99.07.27)
STATL.ADCPF_SPEED,STATL(32*85:32:C) # ADCPF_SPEED (chg kusu 99.07.27)
STATL.ADCPF_POS,STATL(32*86:32:C) # ADCPF_POS (chg kusu 99.07.27)
STATL.IROTPF_TELESCOPE,STATL(32*87:32:C) # IROTPF_TELESCOPE (chg kusu 99.07.27)
STATL.IROTPF_SPEED,STATL(32*88:32:C) # IROTPF_SPEED (chg kusu 99.07.27)
STATL.ADCDIF_PF,STATL(32*89:32:C) # ADCDIF_PF abs(ADCCMD_PF-ADCPOS_PF) (add kawai 99.08.23)
STATL.TT_PATTERN,STATL(32*90:32:C) # TipTilt PATTERN 1,2,3 (add kawai 99.10.25)
STATL.TT_SIGNAL,STATL(32*91:32:C) # TipTilt SIGNAL int,ext (add kawai 99.10.25)
STATL.TT_TX,STATL(32*92:32:C) # TipTilt TX arcsec (add kawai 99.10.25)
STATL.TT_TY,STATL(32*93:32:C) # TipTilt TY arcsec (add kawai 99.10.25)
STATL.TT_Z,STATL(32*94:32:C) # TipTilt Z mm (add kawai 99.10.25)
STATL.CAL_POS,STATL(32*95:32:C) # Cal_Pos mm (add kawai 99.10.25)
STATL.CAL_FILTER_A,STATL(32*96:32:C) # Cal_Filter_A 1,2,3,4 (add kawai 99.10.25)
STATL.CAL_FILTER_B,STATL(32*97:32:C) # Cal_Filter_B 1,2,3,4 (add kawai 99.10.25)
STATL.CAL_FILTER_C,STATL(32*98:32:C) # Cal_Filter_C 1,2,3,4 (add kawai 99.10.25)
STATL.CAL_FILTER_D,STATL(32*99:32:C) # Cal_Filter_D 1,2,3,4 (add kawai 99.10.25)
STATL.CAL_HCT1_AMP,STATL(32*100:32:C) # Cal_HCT1_AMP A (<-mA) (add kawai 99.10.25)
STATL.CAL_HCT2_AMP,STATL(32*101:32:C) # Cal_HCT2_AMP A (<-mA) (add kawai 99.10.25)
STATL.CAL_HAL1_AMP,STATL(32*102:32:C) # Cal_HAL1_AMP A (add kawai 99.10.25)
STATL.CAL_HAL2_AMP,STATL(32*103:32:C) # Cal_HAL2_AMP A (add kawai 99.10.25)
STATL.CAL_DRIVE,STATL(32*104:32:C) # Cal_DRIVE (add koura 00.06.22)
STATL.CAL_HCT_LAMP,STATL(32*105:32:C) # Cal_HCT_LAMP (add koura 00.06.22)
STATL.CAL_HCT_LAMP1,STATL(32*106:32:C) # Cal_HCT_LAMP1 (add koura 00.06.22)
STATL.CAL_HCT_LAMP2,STATL(32*107:32:C) # Cal_HCT_LAMP2 (add koura 00.06.22)
STATL.CAL_HAL_LAMP1,STATL(32*108:32:C) # Cal_HAL_LAMP1 (add koura 00.06.22)
STATL.CAL_HAL_LAMP2,STATL(32*109:32:C) # Cal_HAL_LAMP2 (add koura 00.06.22)
STATL.CAL_RGL_LAMP1,STATL(32*110:32:C) # Cal_RGL_LAMP1 (add koura 00.06.22)
STATL.CAL_RGL_LAMP2,STATL(32*111:32:C) # Cal_RGL_LAMP2 (add koura 00.06.22)
STATL.CAL_SHUTTER,STATL(32*112:32:C) # Cal_SHUTTER (add koura 00.06.22)
STATL.M2_TYPE,STATL(32*113:32:C) # M2_TYPE (add ooto 01.08.01)
STATL.RA_OFFSET,STATL(32*114:32:C) # RA_OFFSET (arcsec) (add ooto 01.08.14)
STATL.DEC_OFFSET,STATL(32*115:32:C) # DEC_OFFSET (arcsec) (add ooto 01.08.14)
STATL.AGRERR,STATL(32*116:32:C) # AG Error (add ooto 01.08.14)
STATL.LIMIT_AZ,STATL(32*117:32:C) # AZ limit (minute) (add ooto 01.08.14)
STATL.LIMIT_EL,STATL(32*118:32:C) # EL limit (minute) (add ooto 01.08.14)
STATL.LIMIT_ROT,STATL(32*119:32:C) # ROT limit (minute) (add ooto 01.08.14)
STATL.AGXDIF,STATL(32*120:32:C) # fabs(X - X_CMD) (add ooto 01.08.14)
STATL.AGYDIF,STATL(32*121:32:C) # fabs(Y - Y_CMD) (add ooto 01.08.14)
STATL.AGRSEC,STATL(32*122:32:C) # AG_R (arcsec) (add ooto 01.08.14)
STATL.AGXSEC,STATL(32*123:32:C) # AG_X (arcsec) (add ooto 01.08.14)
STATL.AGYSEC,STATL(32*124:32:C) # AG_Y (arcsec) (add ooto 01.08.14)
STATL.SV_CALC_MODE,STATL(32*125:32:C) # SV CALC MODE(CTR,BSECT,PK) (add nwata 03.06.30)
STATL.SV1_X1,STATL(32*126:32:C) # SV1 X1(pixel) (add nwata 03.06.30)
STATL.SV1_Y1,STATL(32*127:32:C) # SV1 Y1(pixel) (add nwata 03.06.30)
STATL.SV1_X2,STATL(32*128:32:C) # SV1 X2(pixel) (add nwata 03.06.30)
STATL.SV1_Y2,STATL(32*129:32:C) # SV1 Y2(pixel) (add nwata 03.06.30)
STATL.SV2_X1,STATL(32*130:32:C) # SV2 X1(pixel) (add nwata 03.06.30)
STATL.SV2_Y1,STATL(32*131:32:C) # SV2 Y1(pixel) (add nwata 03.06.30)
STATL.SV2_X2,STATL(32*132:32:C) # SV2 X2(pixel) (add nwata 03.06.30)
STATL.SV2_Y2,STATL(32*133:32:C) # SV2 Y2(pixel) (add nwata 03.06.30)
STATL.SV_CALC_REGION,STATL(32*134:32:C) # SV CALC REGION(1,2) (add nwata 03.06.30)
STATL.SV1_I_SEIL,STATL(32*135:32:C) # SV1 Intensity CEIL(number) (add nwata 03.06.30)
STATL.SV2_I_SEIL,STATL(32*136:32:C) # SV2 Intensity CEIL(number) (add nwata 03.06.30)
STATL.SV1_I_BOTTOM,STATL(32*137:32:C) # SV1 Intensity BOTTOM(number) (add nwata 03.06.30)
STATL.SV2_I_BOTTOM,STATL(32*138:32:C) # SV2 Intensity BOTTOM(number) (add nwata 03.06.30)
STATL.SVRERR,STATL(32*139:32:C) # SV Error (add ukawa 03.07.23)
STATL.SH_SHUTTER,STATL(32*140:32:C) # SH shutter(OPEN,CLOSE) (add ukawa 03.11.24)
STATL.SH_EXPOSURE,STATL(32*141:32:C) # SH EXPOSURE(ms) (add ukawa 03.11.24)
STATL.SH_BINNING,STATL(32*142:32:C) # SH BINNING(11,22) (add ukawa 03.11.24)
STATL.SH_CAL_DARK,STATL(32*143:32:C) # SH CAL DARK(ON,OFF) (add ukawa 03.11.24)
STATL.SH_CAL_SKY,STATL(32*144:32:C) # SH CAL SKY(ON,OFF) (add ukawa 03.11.24)
STATL.SH_CAL_LOOP,STATL(32*145:32:C) # SH CAL LOOP(number) (add ukawa 03.11.24)
STATL.SH_I_CEIL,STATL(32*146:32:C) # SH Intensity CEIL(number) (add ukawa 03.11.24)
STATL.SH_I_BOTTOM,STATL(32*147:32:C) # SH Intensity BOTTOM(number) (add ukawa 03.11.24)
STATL.AG1_I_CEIL,STATL(32*148:32:C) # AG1 Intensity CEIL(number) (add ukawa 2003.11.24)
STATL.AG2_I_CEIL,STATL(32*149:32:C) # AG2 Intensity CEIL(number) (add ukawa 2003.11.24)
STATL.SV1_I_CEIL,STATL(32*150:32:C) # SV1 Intensity CEIL(number) (add ukawa 03.11.24)
STATL.SV2_I_CEIL,STATL(32*151:32:C) # SV2 Intensity CEIL(number) (add ukawa 03.11.24)
STATL.ZERNIKE_RMS,STATL(32*152:32:C) # ZERNIKE DATA RMS(number) (add ukawa 2004.02.25)
STATL.ZERNIKE_RMS_WOA20,STATL(32*153:32:C) # ZERNIKE DATA RMS(without A20)(number) (add ukawa 2004.02.25)
STATL.AG_OVERLOAD,STATL(32*154:32:C) # AG Over load(ON,OFF) (add ukawa 2004.09.03)
STATL.SV_OVERLOAD,STATL(32*155:32:C) # SV Over load(ON,OFF) (add ukawa 2004.09.03)
STATL.AG_AUTO_I_CUT,STATL(32*156:32:C) # AG Auto Intensity cut(ON,OFF) (add ukawa 2004.09.03)
STATL.SV_AUTO_I_CUT,STATL(32*157:32:C) # SV Auto Intensity cut(ON,OFF) (add ukawa 2004.09.03)
STATL.TRACKING,STATL(32*158:32:C) # Tracking(SIDEREAL,NON_SIDEREAL,NON_SIDEREAL_ERR) (add ukawa 2004.09.03)
STATL.TELDRIVE,STATL(32*159:32:C) # Telescope Drive(Guiding(AG),Guiding(SV),Slewing,Tracking,Tracking(Non-Sidereal)) (add ukawa 2004.09.03)
STATL.TELDRIVE_INFO,STATL(32*160:32:C) # Telescope Drive Alarm(NORMAL,WARNING,ALARM) (add ukawa 2004.09.03)
STATL.FOCUSINFO,STATL(32*161:32:C) # Telescope Focus(POpt Selected,PIR Selected....) (add ukawa 2004.12.24)
STATL.CAL_FILTER_A_NUM,STATL(32*162:32:C) # Cal_Filter_A 1,2,3,4 (add ukawa 2005.05.26)
STATL.CAL_FILTER_B_NUM,STATL(32*163:32:C) # Cal_Filter_B 1,2,3,4 (add ukawa 2005.05.26)
STATL.CAL_FILTER_C_NUM,STATL(32*164:32:C) # Cal_Filter_C 1,2,3,4 (add ukawa 2005.05.26)
STATL.CAL_FILTER_D_NUM,STATL(32*165:32:C) # Cal_Filter_D 1,2,3,4 (add ukawa 2005.05.26)
STATL.Z_PIR,STATL(32*166:32:C) # FAM REAL POSN for PIR(number) (add ukawa 2005.02.01)
STATL.AGPIR_X,STATL(32*167:32:C) # AG/SH REAL POSN for PIR(mm) (add ukawa 2005.02.01)
STATL.PIR_SHUTTER,STATL(32*168:32:C) # PIR ENTRANCE SHUTTER(OPEN,CLOSE) (add ukawa 2005.02.01)
STATL.AGPIR_EXPOSURE,STATL(32*169:32:C) # AG for SH Exposure Time(ms) (add ukawa 2005.02.01)
STATL.AGPIR_BINNING,STATL(32*170:32:C) # AG for SH Binning Pattern(11) (add ukawa 2005.02.01)
STATL.AGPIR_X1,STATL(32*171:32:C) # AG for SH Video Area X(pixel) (add ukawa 2005.02.01)
STATL.AGPIR_Y1,STATL(32*172:32:C) # AG for SH Video Area Y(pixel) (add ukawa 2005.02.01)
STATL.AGPIR_X2,STATL(32*173:32:C) # AG for SH Video Area Width X(pixel) (add ukawa 2005.02.01)
STATL.AGPIR_Y2,STATL(32*174:32:C) # AG for SH Video Area Width Y(pixel) (add ukawa 2005.02.01)
STATL.AGPIR_CALC_X1,STATL(32*175:32:C) # AG for SH Star Position DET Area X(pixel) (add ukawa 2005.02.01)
STATL.AGPIR_CALC_Y1,STATL(32*176:32:C) # AG for SH Star Position DET Area Y(pixel) (add ukawa 2005.02.01)
STATL.AGPIR_CALC_X2,STATL(32*177:32:C) # AG for SH Star Position DET Area Width X(pixel) (add ukawa 2005.02.01)
STATL.AGPIR_CALC_Y2,STATL(32*178:32:C) # AG for SH Star Position DET Area Width Y(pixel) (add ukawa 2005.02.01)
STATL.AGPIR_I_CEIL,STATL(32*179:32:C) # AG for SH Upper Limit(number) (add ukawa 2005.02.01)
STATL.AGPIR_I_BOTTOM,STATL(32*180:32:C) # AG for SH Lower Limit(number) (add ukawa 2005.02.01)
STATL.PIR_CALC_REGION,STATL(32*181:32:C) # PIR Calc Region(PIR,FMOS) (add ukawa 2005.02.01)
STATL.CALC_REGION_INFO,STATL(32*182:32:C) # Calc Region information(AG1,AG2,SV1,.......)(add ukawa 2005.02.01)
STATL.M2_TIPTILT,STATL(32*183:32:C) # Tip-tilt Auto Guide(AG,AO_OBE) (add ukawa 2005.02.01)
STATL.WINDSDIF_SIGN,STATL(32*184:32:C) # WINDSDIF (WINDSCMD-WINDSPOS) (m) (add bon 05.09.16)

# STATOBS table alias 
STATOBS.NEWORIGIN_X1,STATOBS(64*01:64:C) # AG_GETOFFSET calc data
STATOBS.NEWORIGIN_Y1,STATOBS(64*02:64:C) # AG_GETOFFSET calc data
STATOBS.NEWCENTROID_X1,STATOBS(64*03:64:C) # AG_GETOFFSET calc data
STATOBS.NEWCENTROID_Y1,STATOBS(64*04:64:C) # AG_GETOFFSET calc data
STATOBS.NEWCENTROID_X2,STATOBS(64*05:64:C) # AG_GETOFFSET calc data
STATOBS.NEWCENTROID_Y2,STATOBS(64*06:64:C) # AG_GETOFFSET calc data
STATOBS.NEWREADOUT_X1,STATOBS(64*07:64:C) # AG_GETOFFSET calc data
STATOBS.NEWREADOUT_Y1,STATOBS(64*08:64:C) # AG_GETOFFSET calc data
STATOBS.NEWREADOUT_X2,STATOBS(64*09:64:C) # AG_GETOFFSET calc data
STATOBS.NEWREADOUT_Y2,STATOBS(64*10:64:C) # AG_GETOFFSET calc data
STATOBS.RASECOUT,STATOBS(64*11:64:C) # CALCSECRADEC calc data
STATOBS.DECSECOUT,STATOBS(64*12:64:C) # CALCSECRADEC calc data
STATOBS.RARELOUT,STATOBS(64*13:64:C) # CALCSECRADEC calc data
STATOBS.DECRELOUT,STATOBS(64*14:64:C) # CALCSECRADEC calc data
STATOBS.SIN,STATOBS(64*15:64:C) # CALC calc data
STATOBS.COS,STATOBS(64*16:64:C) # CALC calc data
STATOBS.TAN,STATOBS(64*17:64:C) # CALC calc data
STATOBS.ASIN,STATOBS(64*18:64:C) # CALC calc data
STATOBS.ACOS,STATOBS(64*19:64:C) # CALC calc data
STATOBS.ATAN,STATOBS(64*20:64:C) # CALC calc data
STATOBS.ATAN2,STATOBS(64*21:64:C) # CALC calc data
STATOBS.LOG10,STATOBS(64*22:64:C) # CALC calc data
STATOBS.POW,STATOBS(64*23:64:C) # CALC calc data
STATOBS.SQRT,STATOBS(64*24:64:C) # CALC calc data
STATOBS.RACALCOUT,STATOBS(64*25:64:C) # CALCRADEC calc data
STATOBS.DECCALCOUT,STATOBS(64*26:64:C) # CALCRADEC calc data

# CALC_PROBE
STATOBS.AG_R,STATOBS(64*27:64:C) # CALC_PROBE data
STATOBS.AG_THETA,STATOBS(64*28:64:C) # CALC_PROBE data
STATOBS.AGPF_X,STATOBS(64*29:64:C) # CALC_PROBE data
STATOBS.AGPF_Y,STATOBS(64*30:64:C) # CALC_PROBE data

# for CALC_AD (add ooto 2001.07.13) (chg kusu 2002.01.21)
STATOBS.CALC_AD.RASEC,STATOBS(64*31:64:C) # CALC_AD RASEC (arcsec)
STATOBS.CALC_AD.DECSEC,STATOBS(64*32:64:C) # CALC_AD DECSEC (arcsec)
STATOBS.CALC_AD.ELSEC,STATOBS(64*33:64:C) # CALC_AD ELSEC (arcsec)

#
# for OSST_checkOBCP (add ooto 2001.12.05)
# Attention !! This is STATOBS Table!!
FITS.IRC.STATUS,STATOBS(64*1015:64:C) # for OBCP STATUS CHECK
FITS.AOS.STATUS,STATOBS(64*1016:64:C) # for OBCP STATUS CHECK
FITS.CIA.STATUS,STATOBS(64*1017:64:C) # for OBCP STATUS CHECK
FITS.OHS.STATUS,STATOBS(64*1018:64:C) # for OBCP STATUS CHECK
FITS.FCS.STATUS,STATOBS(64*1019:64:C) # for OBCP STATUS CHECK
FITS.HDS.STATUS,STATOBS(64*1020:64:C) # for OBCP STATUS CHECK
FITS.COM.STATUS,STATOBS(64*1021:64:C) # for OBCP STATUS CHECK
FITS.SUP.STATUS,STATOBS(64*1022:64:C) # for OBCP STATUS CHECK
FITS.SUK.STATUS,STATOBS(64*1023:64:C) # for OBCP STATUS CHECK
FITS.MIR.STATUS,STATOBS(64*1024:64:C) # for OBCP STATUS CHECK
FITS.VTO.STATUS,STATOBS(64*1025:64:C) # for OBCP STATUS CHECK
FITS.CAC.STATUS,STATOBS(64*1026:64:C) # for OBCP STATUS CHECK
FITS.SKY.STATUS,STATOBS(64*1027:64:C) # for OBCP STATUS CHECK
FITS.PI1.STATUS,STATOBS(64*1028:64:C) # for OBCP STATUS CHECK
FITS.K3D.STATUS,STATOBS(64*1029:64:C) # for OBCP STATUS CHECK
FITS.O16.STATUS,STATOBS(64*1030:64:C) # for OBCP STATUS CHECK
FITS.MCS.STATUS,STATOBS(64*1031:64:C) # for OBCP STATUS CHECK
FITS.FMS.STATUS,STATOBS(64*1032:64:C) # for OBCP STATUS CHECK
FITS.FLD.STATUS,STATOBS(64*1033:64:C) # for OBCP STATUS CHECK
FITS.AON.STATUS,STATOBS(64*1034:64:C) # for OBCP STATUS CHECK
FITS.HIC.STATUS,STATOBS(64*1035:64:C) # for OBCP STATUS CHECK
FITS.WAV.STATUS,STATOBS(64*1036:64:C) # for OBCP STATUS CHECK
FITS.LGS.STATUS,STATOBS(64*1037:64:C) # for OBCP STATUS CHECK
FITS.O24.STATUS,STATOBS(64*1038:64:C) # for OBCP STATUS CHECK
FITS.O25.STATUS,STATOBS(64*1039:64:C) # for OBCP STATUS CHECK
FITS.O26.STATUS,STATOBS(64*1040:64:C) # for OBCP STATUS CHECK
FITS.O27.STATUS,STATOBS(64*1041:64:C) # for OBCP STATUS CHECK
FITS.O28.STATUS,STATOBS(64*1042:64:C) # for OBCP STATUS CHECK
FITS.O29.STATUS,STATOBS(64*1043:64:C) # for OBCP STATUS CHECK
FITS.O30.STATUS,STATOBS(64*1044:64:C) # for OBCP STATUS CHECK
FITS.O31.STATUS,STATOBS(64*1045:64:C) # for OBCP STATUS CHECK
FITS.O32.STATUS,STATOBS(64*1046:64:C) # for OBCP STATUS CHECK

#
# for OSST_change_propid (add ooto 2001.12.12)
STATOBS.PROP.NEW_PROP,STATOBS(64*1047:64:C) # new proposal ID
STATOBS.PROP.OLD_PROP,STATOBS(64*1048:64:C) # old proposal ID
STATOBS.PROP.NEW_OBSERVER,STATOBS(64*1049:64:C) # new observer
STATOBS.PROP.OLD_OBSERVER,STATOBS(64*1050:64:C) # old observer

# for OSST_Calc_ProbeOffset (add watanabe 2002.03.26)
STATOBS.PROBERASEC,STATOBS(64*1051:64:C) # Calc_ProbeOffset RASEC (arcsec)
STATOBS.PROBEDECSEC,STATOBS(64*1052:64:C) # Calc_ProbeOffset DECSEC (arcsec)

##############################################
# OBSINFO & TIMER  <OBCP1-32,CMN>
#(add shiraishi 2003.05.22)
##############################################
#IRC
STATOBS.IRC.OBSINFO1,STATOBS(64*1053:64:C:)
STATOBS.IRC.OBSINFO2,STATOBS(64*1054:64:C:)
STATOBS.IRC.OBSINFO3,STATOBS(64*1055:64:C:)
STATOBS.IRC.OBSINFO4,STATOBS(64*1056:64:C:)
STATOBS.IRC.OBSINFO5,STATOBS(64*1057:64:C:)
STATOBS.IRC.TIMER_SEC,STATOBS(64*1058:64:C:)
STATOBS.IRC.TIMER_TIME,STATOBS(64*1059:64:C:)
#AOS
STATOBS.AOS.OBSINFO1,STATOBS(64*1060:64:C:)
STATOBS.AOS.OBSINFO2,STATOBS(64*1061:64:C:)
STATOBS.AOS.OBSINFO3,STATOBS(64*1062:64:C:)
STATOBS.AOS.OBSINFO4,STATOBS(64*1063:64:C:)
STATOBS.AOS.OBSINFO5,STATOBS(64*1064:64:C:)
STATOBS.AOS.TIMER_SEC,STATOBS(64*1065:64:C:)
STATOBS.AOS.TIMER_TIME,STATOBS(64*1066:64:C:)
#CIA
STATOBS.CIA.OBSINFO1,STATOBS(64*1067:64:C:)
STATOBS.CIA.OBSINFO2,STATOBS(64*1068:64:C:)
STATOBS.CIA.OBSINFO3,STATOBS(64*1069:64:C:)
STATOBS.CIA.OBSINFO4,STATOBS(64*1070:64:C:)
STATOBS.CIA.OBSINFO5,STATOBS(64*1071:64:C:)
STATOBS.CIA.TIMER_SEC,STATOBS(64*1072:64:C:)
STATOBS.CIA.TIMER_TIME,STATOBS(64*1073:64:C:)
#OHS
STATOBS.OHS.OBSINFO1,STATOBS(64*1074:64:C:)
STATOBS.OHS.OBSINFO2,STATOBS(64*1075:64:C:)
STATOBS.OHS.OBSINFO3,STATOBS(64*1076:64:C:)
STATOBS.OHS.OBSINFO4,STATOBS(64*1077:64:C:)
STATOBS.OHS.OBSINFO5,STATOBS(64*1078:64:C:)
STATOBS.OHS.TIMER_SEC,STATOBS(64*1079:64:C:)
STATOBS.OHS.TIMER_TIME,STATOBS(64*1080:64:C:)
#FCS
STATOBS.FCS.OBSINFO1,STATOBS(64*1081:64:C:)
STATOBS.FCS.OBSINFO2,STATOBS(64*1082:64:C:)
STATOBS.FCS.OBSINFO3,STATOBS(64*1083:64:C:)
STATOBS.FCS.OBSINFO4,STATOBS(64*1084:64:C:)
STATOBS.FCS.OBSINFO5,STATOBS(64*1085:64:C:)
STATOBS.FCS.TIMER_SEC,STATOBS(64*1086:64:C:)
STATOBS.FCS.TIMER_TIME,STATOBS(64*1087:64:C:)
#HDS
STATOBS.HDS.OBSINFO1,STATOBS(64*1088:64:C:)
STATOBS.HDS.OBSINFO2,STATOBS(64*1089:64:C:)
STATOBS.HDS.OBSINFO3,STATOBS(64*1090:64:C:)
STATOBS.HDS.OBSINFO4,STATOBS(64*1091:64:C:)
STATOBS.HDS.OBSINFO5,STATOBS(64*1092:64:C:)
STATOBS.HDS.TIMER_SEC,STATOBS(64*1093:64:C:)
STATOBS.HDS.TIMER_TIME,STATOBS(64*1094:64:C:)
#COM
STATOBS.COM.OBSINFO1,STATOBS(64*1095:64:C:)
STATOBS.COM.OBSINFO2,STATOBS(64*1096:64:C:)
STATOBS.COM.OBSINFO3,STATOBS(64*1097:64:C:)
STATOBS.COM.OBSINFO4,STATOBS(64*1098:64:C:)
STATOBS.COM.OBSINFO5,STATOBS(64*1099:64:C:)
STATOBS.COM.TIMER_SEC,STATOBS(64*1100:64:C:)
STATOBS.COM.TIMER_TIME,STATOBS(64*1101:64:C:)
#SUP
STATOBS.SUP.OBSINFO1,STATOBS(64*1102:64:C:)
STATOBS.SUP.OBSINFO2,STATOBS(64*1103:64:C:)
STATOBS.SUP.OBSINFO3,STATOBS(64*1104:64:C:)
STATOBS.SUP.OBSINFO4,STATOBS(64*1105:64:C:)
STATOBS.SUP.OBSINFO5,STATOBS(64*1106:64:C:)
STATOBS.SUP.TIMER_SEC,STATOBS(64*1107:64:C:)
STATOBS.SUP.TIMER_TIME,STATOBS(64*1108:64:C:)
#SUK
STATOBS.SUK.OBSINFO1,STATOBS(64*1109:64:C:)
STATOBS.SUK.OBSINFO2,STATOBS(64*1110:64:C:)
STATOBS.SUK.OBSINFO3,STATOBS(64*1111:64:C:)
STATOBS.SUK.OBSINFO4,STATOBS(64*1112:64:C:)
STATOBS.SUK.OBSINFO5,STATOBS(64*1113:64:C:)
STATOBS.SUK.TIMER_SEC,STATOBS(64*1114:64:C:)
STATOBS.SUK.TIMER_TIME,STATOBS(64*1115:64:C:)
#MIR
STATOBS.MIR.OBSINFO1,STATOBS(64*1116:64:C:)
STATOBS.MIR.OBSINFO2,STATOBS(64*1117:64:C:)
STATOBS.MIR.OBSINFO3,STATOBS(64*1118:64:C:)
STATOBS.MIR.OBSINFO4,STATOBS(64*1119:64:C:)
STATOBS.MIR.OBSINFO5,STATOBS(64*1120:64:C:)
STATOBS.MIR.TIMER_SEC,STATOBS(64*1121:64:C:)
STATOBS.MIR.TIMER_TIME,STATOBS(64*1122:64:C:)
#VTO
STATOBS.VTO.OBSINFO1,STATOBS(64*1123:64:C:)
STATOBS.VTO.OBSINFO2,STATOBS(64*1124:64:C:)
STATOBS.VTO.OBSINFO3,STATOBS(64*1125:64:C:)
STATOBS.VTO.OBSINFO4,STATOBS(64*1126:64:C:)
STATOBS.VTO.OBSINFO5,STATOBS(64*1127:64:C:)
STATOBS.VTO.TIMER_SEC,STATOBS(64*1128:64:C:)
STATOBS.VTO.TIMER_TIME,STATOBS(64*1129:64:C:)
#CAC
STATOBS.CAC.OBSINFO1,STATOBS(64*1130:64:C:)
STATOBS.CAC.OBSINFO2,STATOBS(64*1131:64:C:)
STATOBS.CAC.OBSINFO3,STATOBS(64*1132:64:C:)
STATOBS.CAC.OBSINFO4,STATOBS(64*1134:64:C:)
STATOBS.CAC.OBSINFO5,STATOBS(64*1135:64:C:)
STATOBS.CAC.TIMER_SEC,STATOBS(64*1136:64:C:)
STATOBS.CAC.TIMER_TIME,STATOBS(64*1137:64:C:)
#SKY
STATOBS.SKY.OBSINFO1,STATOBS(64*1138:64:C:)
STATOBS.SKY.OBSINFO2,STATOBS(64*1139:64:C:)
STATOBS.SKY.OBSINFO3,STATOBS(64*1140:64:C:)
STATOBS.SKY.OBSINFO4,STATOBS(64*1141:64:C:)
STATOBS.SKY.OBSINFO5,STATOBS(64*1142:64:C:)
STATOBS.SKY.TIMER_SEC,STATOBS(64*1143:64:C:)
STATOBS.SKY.TIMER_TIME,STATOBS(64*1144:64:C:)
#PI1
STATOBS.PI1.OBSINFO1,STATOBS(64*1145:64:C:)
STATOBS.PI1.OBSINFO2,STATOBS(64*1146:64:C:)
STATOBS.PI1.OBSINFO3,STATOBS(64*1147:64:C:)
STATOBS.PI1.OBSINFO4,STATOBS(64*1148:64:C:)
STATOBS.PI1.OBSINFO5,STATOBS(64*1149:64:C:)
STATOBS.PI1.TIMER_SEC,STATOBS(64*1150:64:C:)
STATOBS.PI1.TIMER_TIME,STATOBS(64*1151:64:C:)
#K3D
STATOBS.K3D.OBSINFO1,STATOBS(64*1152:64:C:)
STATOBS.K3D.OBSINFO2,STATOBS(64*1153:64:C:)
STATOBS.K3D.OBSINFO3,STATOBS(64*1154:64:C:)
STATOBS.K3D.OBSINFO4,STATOBS(64*1155:64:C:)
STATOBS.K3D.OBSINFO5,STATOBS(64*1156:64:C:)
STATOBS.K3D.TIMER_SEC,STATOBS(64*1157:64:C:)
STATOBS.K3D.TIMER_TIME,STATOBS(64*1158:64:C:)
#O16
STATOBS.O16.OBSINFO1,STATOBS(64*1159:64:C:)
STATOBS.O16.OBSINFO2,STATOBS(64*1160:64:C:)
STATOBS.O16.OBSINFO3,STATOBS(64*1161:64:C:)
STATOBS.O16.OBSINFO4,STATOBS(64*1162:64:C:)
STATOBS.O16.OBSINFO5,STATOBS(64*1163:64:C:)
STATOBS.O16.TIMER_SEC,STATOBS(64*1164:64:C:)
STATOBS.O16.TIMER_TIME,STATOBS(64*1165:64:C:)
#MCS
STATOBS.MCS.OBSINFO1,STATOBS(64*1166:64:C:)
STATOBS.MCS.OBSINFO2,STATOBS(64*1167:64:C:)
STATOBS.MCS.OBSINFO3,STATOBS(64*1168:64:C:)
STATOBS.MCS.OBSINFO4,STATOBS(64*1169:64:C:)
STATOBS.MCS.OBSINFO5,STATOBS(64*1170:64:C:)
STATOBS.MCS.TIMER_SEC,STATOBS(64*1171:64:C:)
STATOBS.MCS.TIMER_TIME,STATOBS(64*1172:64:C:)
#FMS
STATOBS.FMS.OBSINFO1,STATOBS(64*1173:64:C:)
STATOBS.FMS.OBSINFO2,STATOBS(64*1174:64:C:)
STATOBS.FMS.OBSINFO3,STATOBS(64*1175:64:C:)
STATOBS.FMS.OBSINFO4,STATOBS(64*1176:64:C:)
STATOBS.FMS.OBSINFO5,STATOBS(64*1177:64:C:)
STATOBS.FMS.TIMER_SEC,STATOBS(64*1178:64:C:)
STATOBS.FMS.TIMER_TIME,STATOBS(64*1179:64:C:)
#FLD
STATOBS.FLD.OBSINFO1,STATOBS(64*1180:64:C:)
STATOBS.FLD.OBSINFO2,STATOBS(64*1181:64:C:)
STATOBS.FLD.OBSINFO3,STATOBS(64*1182:64:C:)
STATOBS.FLD.OBSINFO4,STATOBS(64*1183:64:C:)
STATOBS.FLD.OBSINFO5,STATOBS(64*1184:64:C:)
STATOBS.FLD.TIMER_SEC,STATOBS(64*1185:64:C:)
STATOBS.FLD.TIMER_TIME,STATOBS(64*1186:64:C:)
#AON
STATOBS.AON.OBSINFO1,STATOBS(64*1187:64:C:)
STATOBS.AON.OBSINFO2,STATOBS(64*1188:64:C:)
STATOBS.AON.OBSINFO3,STATOBS(64*1189:64:C:)
STATOBS.AON.OBSINFO4,STATOBS(64*1190:64:C:)
STATOBS.AON.OBSINFO5,STATOBS(64*1191:64:C:)
STATOBS.AON.TIMER_SEC,STATOBS(64*1192:64:C:)
STATOBS.AON.TIMER_TIME,STATOBS(64*1193:64:C:)
#HIC
STATOBS.HIC.OBSINFO1,STATOBS(64*1194:64:C:)
STATOBS.HIC.OBSINFO2,STATOBS(64*1195:64:C:)
STATOBS.HIC.OBSINFO3,STATOBS(64*1196:64:C:)
STATOBS.HIC.OBSINFO4,STATOBS(64*1197:64:C:)
STATOBS.HIC.OBSINFO5,STATOBS(64*1198:64:C:)
STATOBS.HIC.TIMER_SEC,STATOBS(64*1199:64:C:)
STATOBS.HIC.TIMER_TIME,STATOBS(64*1200:64:C:)
#WAV
STATOBS.WAV.OBSINFO1,STATOBS(64*1201:64:C:)
STATOBS.WAV.OBSINFO2,STATOBS(64*1202:64:C:)
STATOBS.WAV.OBSINFO3,STATOBS(64*1203:64:C:)
STATOBS.WAV.OBSINFO4,STATOBS(64*1204:64:C:)
STATOBS.WAV.OBSINFO5,STATOBS(64*1205:64:C:)
STATOBS.WAV.TIMER_SEC,STATOBS(64*1206:64:C:)
STATOBS.WAV.TIMER_TIME,STATOBS(64*1207:64:C:)
#LGS
STATOBS.LGS.OBSINFO1,STATOBS(64*1208:64:C:)
STATOBS.LGS.OBSINFO2,STATOBS(64*1209:64:C:)
STATOBS.LGS.OBSINFO3,STATOBS(64*1210:64:C:)
STATOBS.LGS.OBSINFO4,STATOBS(64*1211:64:C:)
STATOBS.LGS.OBSINFO5,STATOBS(64*1212:64:C:)
STATOBS.LGS.TIMER_SEC,STATOBS(64*1213:64:C:)
STATOBS.LGS.TIMER_TIME,STATOBS(64*1214:64:C:)
#O24

STATOBS.O24.OBSINFO1,STATOBS(64*1215:64:C:)
STATOBS.O24.OBSINFO2,STATOBS(64*1216:64:C:)
STATOBS.O24.OBSINFO3,STATOBS(64*1217:64:C:)
STATOBS.O24.OBSINFO4,STATOBS(64*1218:64:C:)
STATOBS.O24.OBSINFO5,STATOBS(64*1219:64:C:)
STATOBS.O24.TIMER_SEC,STATOBS(64*1220:64:C:)
STATOBS.O24.TIMER_TIME,STATOBS(64*1221:64:C:)
#O25
STATOBS.O25.OBSINFO1,STATOBS(64*1222:64:C:)
STATOBS.O25.OBSINFO2,STATOBS(64*1223:64:C:)
STATOBS.O25.OBSINFO3,STATOBS(64*1224:64:C:)
STATOBS.O25.OBSINFO4,STATOBS(64*1225:64:C:)
STATOBS.O25.OBSINFO5,STATOBS(64*1226:64:C:)
STATOBS.O25.TIMER_SEC,STATOBS(64*1227:64:C:)
STATOBS.O25.TIMER_TIME,STATOBS(64*1228:64:C:)
#O26
STATOBS.O26.OBSINFO1,STATOBS(64*1229:64:C:)
STATOBS.O26.OBSINFO2,STATOBS(64*1230:64:C:)
STATOBS.O26.OBSINFO3,STATOBS(64*1231:64:C:)
STATOBS.O26.OBSINFO4,STATOBS(64*1232:64:C:)
STATOBS.O26.OBSINFO5,STATOBS(64*1233:64:C:)
STATOBS.O26.TIMER_SEC,STATOBS(64*1234:64:C:)
STATOBS.O26.TIMER_TIME,STATOBS(64*1235:64:C:)
#O27
STATOBS.O27.OBSINFO1,STATOBS(64*1236:64:C:)
STATOBS.O27.OBSINFO2,STATOBS(64*1237:64:C:)
STATOBS.O27.OBSINFO3,STATOBS(64*1238:64:C:)
STATOBS.O27.OBSINFO4,STATOBS(64*1239:64:C:)
STATOBS.O27.OBSINFO5,STATOBS(64*1240:64:C:)
STATOBS.O27.TIMER_SEC,STATOBS(64*1241:64:C:)
STATOBS.O27.TIMER_TIME,STATOBS(64*1242:64:C:)
#O28
STATOBS.O28.OBSINFO1,STATOBS(64*1243:64:C:)
STATOBS.O28.OBSINFO2,STATOBS(64*1244:64:C:)
STATOBS.O28.OBSINFO3,STATOBS(64*1245:64:C:)
STATOBS.O28.OBSINFO4,STATOBS(64*1246:64:C:)
STATOBS.O28.OBSINFO5,STATOBS(64*1247:64:C:)
STATOBS.O28.TIMER_SEC,STATOBS(64*1248:64:C:)
STATOBS.O28.TIMER_TIME,STATOBS(64*1249:64:C:)
#O29
STATOBS.O29.OBSINFO1,STATOBS(64*1250:64:C:)
STATOBS.O29.OBSINFO2,STATOBS(64*1251:64:C:)
STATOBS.O29.OBSINFO3,STATOBS(64*1252:64:C:)
STATOBS.O29.OBSINFO4,STATOBS(64*1253:64:C:)
STATOBS.O29.OBSINFO5,STATOBS(64*1254:64:C:)
STATOBS.O29.TIMER_SEC,STATOBS(64*1255:64:C:)
STATOBS.O29.TIMER_TIME,STATOBS(64*1256:64:C:)
#O30
STATOBS.O30.OBSINFO1,STATOBS(64*1257:64:C:)
STATOBS.O30.OBSINFO2,STATOBS(64*1258:64:C:)
STATOBS.O30.OBSINFO3,STATOBS(64*1259:64:C:)
STATOBS.O30.OBSINFO4,STATOBS(64*1260:64:C:)
STATOBS.O30.OBSINFO5,STATOBS(64*1261:64:C:)
STATOBS.O30.TIMER_SEC,STATOBS(64*1262:64:C:)
STATOBS.O30.TIMER_TIME,STATOBS(64*1263:64:C:)
#O31
STATOBS.O31.OBSINFO1,STATOBS(64*1264:64:C:)
STATOBS.O31.OBSINFO2,STATOBS(64*1265:64:C:)
STATOBS.O31.OBSINFO3,STATOBS(64*1266:64:C:)
STATOBS.O31.OBSINFO4,STATOBS(64*1267:64:C:)
STATOBS.O31.OBSINFO5,STATOBS(64*1268:64:C:)
STATOBS.O31.TIMER_SEC,STATOBS(64*1269:64:C:)
STATOBS.O31.TIMER_TIME,STATOBS(64*1270:64:C:)
#O32
STATOBS.O32.OBSINFO1,STATOBS(64*1271:64:C:)
STATOBS.O32.OBSINFO2,STATOBS(64*1272:64:C:)
STATOBS.O32.OBSINFO3,STATOBS(64*1273:64:C:)
STATOBS.O32.OBSINFO4,STATOBS(64*1274:64:C:)
STATOBS.O32.OBSINFO5,STATOBS(64*1275:64:C:)
STATOBS.O32.TIMER_SEC,STATOBS(64*1276:64:C:)
STATOBS.O32.TIMER_TIME,STATOBS(64*1277:64:C:)
#CMN
STATOBS.CMN.OBSINFO1,STATOBS(64*1278:64:C:)
STATOBS.CMN.OBSINFO2,STATOBS(64*1279:64:C:)
STATOBS.CMN.OBSINFO3,STATOBS(64*1280:64:C:)
STATOBS.CMN.OBSINFO4,STATOBS(64*1281:64:C:)
STATOBS.CMN.OBSINFO5,STATOBS(64*1282:64:C:)
STATOBS.CMN.TIMER_SEC,STATOBS(64*1283:64:C:)
STATOBS.CMN.TIMER_TIME,STATOBS(64*1284:64:C:)

###############################
# 34 - 90 rezerve
###############################
# cleate : /soss/SRC/product/OSSS/OSSS_InterfaceOBS.d/alias.sh
# change kusu 2002.01.21
###############################
# IRC
STATOBS.IRC.C1,STATOBS(64*91:64:C) # MEMORY data (IRC)
STATOBS.IRC.C2,STATOBS(64*92:64:C) # MEMORY data (IRC)
STATOBS.IRC.C3,STATOBS(64*93:64:C) # MEMORY data (IRC)
STATOBS.IRC.C4,STATOBS(64*94:64:C) # MEMORY data (IRC)
STATOBS.IRC.C5,STATOBS(64*95:64:C) # MEMORY data (IRC)
STATOBS.IRC.C6,STATOBS(64*96:64:C) # MEMORY data (IRC)
STATOBS.IRC.C7,STATOBS(64*97:64:C) # MEMORY data (IRC)
STATOBS.IRC.C8,STATOBS(64*98:64:C) # MEMORY data (IRC)
STATOBS.IRC.C9,STATOBS(64*99:64:C) # MEMORY data (IRC)
STATOBS.IRC.N1,STATOBS(64*100:64:C) # MEMORY data (IRC)
STATOBS.IRC.N2,STATOBS(64*101:64:C) # MEMORY data (IRC)
STATOBS.IRC.N3,STATOBS(64*102:64:C) # MEMORY data (IRC)
STATOBS.IRC.N4,STATOBS(64*103:64:C) # MEMORY data (IRC)
STATOBS.IRC.N5,STATOBS(64*104:64:C) # MEMORY data (IRC)
STATOBS.IRC.N6,STATOBS(64*105:64:C) # MEMORY data (IRC)
STATOBS.IRC.N7,STATOBS(64*106:64:C) # MEMORY data (IRC)
STATOBS.IRC.N8,STATOBS(64*107:64:C) # MEMORY data (IRC)
STATOBS.IRC.N9,STATOBS(64*108:64:C) # MEMORY data (IRC)
STATOBS.IRC.CONFIRMATION,STATOBS(64*109:64:C) # CONFIRMATION IRC
STATOBS.IRC.UI1,STATOBS(64*110:64:C) # USERINPUT IRC
STATOBS.IRC.UI2,STATOBS(64*111:64:C) # USERINPUT IRC
STATOBS.IRC.UI3,STATOBS(64*112:64:C) # USERINPUT IRC
STATOBS.IRC.UI4,STATOBS(64*113:64:C) # USERINPUT IRC
STATOBS.IRC.UI5,STATOBS(64*114:64:C) # USERINPUT IRC
STATOBS.IRC.UI6,STATOBS(64*115:64:C) # USERINPUT IRC
STATOBS.IRC.UI7,STATOBS(64*116:64:C) # USERINPUT IRC
STATOBS.IRC.UI8,STATOBS(64*117:64:C) # USERINPUT IRC
STATOBS.IRC.UI9,STATOBS(64*118:64:C) # USERINPUT IRC

# AOS
STATOBS.AOS.C1,STATOBS(64*119:64:C) # MEMORY data (AOS)
STATOBS.AOS.C2,STATOBS(64*120:64:C) # MEMORY data (AOS)
STATOBS.AOS.C3,STATOBS(64*121:64:C) # MEMORY data (AOS)
STATOBS.AOS.C4,STATOBS(64*122:64:C) # MEMORY data (AOS)
STATOBS.AOS.C5,STATOBS(64*123:64:C) # MEMORY data (AOS)
STATOBS.AOS.C6,STATOBS(64*124:64:C) # MEMORY data (AOS)
STATOBS.AOS.C7,STATOBS(64*125:64:C) # MEMORY data (AOS)
STATOBS.AOS.C8,STATOBS(64*126:64:C) # MEMORY data (AOS)
STATOBS.AOS.C9,STATOBS(64*127:64:C) # MEMORY data (AOS)
STATOBS.AOS.N1,STATOBS(64*128:64:C) # MEMORY data (AOS)
STATOBS.AOS.N2,STATOBS(64*129:64:C) # MEMORY data (AOS)
STATOBS.AOS.N3,STATOBS(64*130:64:C) # MEMORY data (AOS)
STATOBS.AOS.N4,STATOBS(64*131:64:C) # MEMORY data (AOS)
STATOBS.AOS.N5,STATOBS(64*132:64:C) # MEMORY data (AOS)
STATOBS.AOS.N6,STATOBS(64*133:64:C) # MEMORY data (AOS)
STATOBS.AOS.N7,STATOBS(64*134:64:C) # MEMORY data (AOS)
STATOBS.AOS.N8,STATOBS(64*135:64:C) # MEMORY data (AOS)
STATOBS.AOS.N9,STATOBS(64*136:64:C) # MEMORY data (AOS)
STATOBS.AOS.CONFIRMATION,STATOBS(64*137:64:C) # CONFIRMATION AOS
STATOBS.AOS.UI1,STATOBS(64*138:64:C) # USERINPUT AOS
STATOBS.AOS.UI2,STATOBS(64*139:64:C) # USERINPUT AOS
STATOBS.AOS.UI3,STATOBS(64*140:64:C) # USERINPUT AOS
STATOBS.AOS.UI4,STATOBS(64*141:64:C) # USERINPUT AOS
STATOBS.AOS.UI5,STATOBS(64*142:64:C) # USERINPUT AOS
STATOBS.AOS.UI6,STATOBS(64*143:64:C) # USERINPUT AOS
STATOBS.AOS.UI7,STATOBS(64*144:64:C) # USERINPUT AOS
STATOBS.AOS.UI8,STATOBS(64*145:64:C) # USERINPUT AOS
STATOBS.AOS.UI9,STATOBS(64*146:64:C) # USERINPUT AOS

# CIA
STATOBS.CIA.C1,STATOBS(64*147:64:C) # MEMORY data (CIA)
STATOBS.CIA.C2,STATOBS(64*148:64:C) # MEMORY data (CIA)
STATOBS.CIA.C3,STATOBS(64*149:64:C) # MEMORY data (CIA)
STATOBS.CIA.C4,STATOBS(64*150:64:C) # MEMORY data (CIA)
STATOBS.CIA.C5,STATOBS(64*151:64:C) # MEMORY data (CIA)
STATOBS.CIA.C6,STATOBS(64*152:64:C) # MEMORY data (CIA)
STATOBS.CIA.C7,STATOBS(64*153:64:C) # MEMORY data (CIA)
STATOBS.CIA.C8,STATOBS(64*154:64:C) # MEMORY data (CIA)
STATOBS.CIA.C9,STATOBS(64*155:64:C) # MEMORY data (CIA)
STATOBS.CIA.N1,STATOBS(64*156:64:C) # MEMORY data (CIA)
STATOBS.CIA.N2,STATOBS(64*157:64:C) # MEMORY data (CIA)
STATOBS.CIA.N3,STATOBS(64*158:64:C) # MEMORY data (CIA)
STATOBS.CIA.N4,STATOBS(64*159:64:C) # MEMORY data (CIA)
STATOBS.CIA.N5,STATOBS(64*160:64:C) # MEMORY data (CIA)
STATOBS.CIA.N6,STATOBS(64*161:64:C) # MEMORY data (CIA)
STATOBS.CIA.N7,STATOBS(64*162:64:C) # MEMORY data (CIA)
STATOBS.CIA.N8,STATOBS(64*163:64:C) # MEMORY data (CIA)
STATOBS.CIA.N9,STATOBS(64*164:64:C) # MEMORY data (CIA)
STATOBS.CIA.CONFIRMATION,STATOBS(64*165:64:C) # CONFIRMATION CIA
STATOBS.CIA.UI1,STATOBS(64*166:64:C) # USERINPUT CIA
STATOBS.CIA.UI2,STATOBS(64*167:64:C) # USERINPUT CIA
STATOBS.CIA.UI3,STATOBS(64*168:64:C) # USERINPUT CIA
STATOBS.CIA.UI4,STATOBS(64*169:64:C) # USERINPUT CIA
STATOBS.CIA.UI5,STATOBS(64*170:64:C) # USERINPUT CIA
STATOBS.CIA.UI6,STATOBS(64*171:64:C) # USERINPUT CIA
STATOBS.CIA.UI7,STATOBS(64*172:64:C) # USERINPUT CIA
STATOBS.CIA.UI8,STATOBS(64*173:64:C) # USERINPUT CIA
STATOBS.CIA.UI9,STATOBS(64*174:64:C) # USERINPUT CIA

# OHS
STATOBS.OHS.C1,STATOBS(64*175:64:C) # MEMORY data (OHS)
STATOBS.OHS.C2,STATOBS(64*176:64:C) # MEMORY data (OHS)
STATOBS.OHS.C3,STATOBS(64*177:64:C) # MEMORY data (OHS)
STATOBS.OHS.C4,STATOBS(64*178:64:C) # MEMORY data (OHS)
STATOBS.OHS.C5,STATOBS(64*179:64:C) # MEMORY data (OHS)
STATOBS.OHS.C6,STATOBS(64*180:64:C) # MEMORY data (OHS)
STATOBS.OHS.C7,STATOBS(64*181:64:C) # MEMORY data (OHS)
STATOBS.OHS.C8,STATOBS(64*182:64:C) # MEMORY data (OHS)
STATOBS.OHS.C9,STATOBS(64*183:64:C) # MEMORY data (OHS)
STATOBS.OHS.N1,STATOBS(64*184:64:C) # MEMORY data (OHS)
STATOBS.OHS.N2,STATOBS(64*185:64:C) # MEMORY data (OHS)
STATOBS.OHS.N3,STATOBS(64*186:64:C) # MEMORY data (OHS)
STATOBS.OHS.N4,STATOBS(64*187:64:C) # MEMORY data (OHS)
STATOBS.OHS.N5,STATOBS(64*188:64:C) # MEMORY data (OHS)
STATOBS.OHS.N6,STATOBS(64*189:64:C) # MEMORY data (OHS)
STATOBS.OHS.N7,STATOBS(64*190:64:C) # MEMORY data (OHS)
STATOBS.OHS.N8,STATOBS(64*191:64:C) # MEMORY data (OHS)
STATOBS.OHS.N9,STATOBS(64*192:64:C) # MEMORY data (OHS)
STATOBS.OHS.CONFIRMATION,STATOBS(64*193:64:C) # CONFIRMATION OHS
STATOBS.OHS.UI1,STATOBS(64*194:64:C) # USERINPUT OHS
STATOBS.OHS.UI2,STATOBS(64*195:64:C) # USERINPUT OHS
STATOBS.OHS.UI3,STATOBS(64*196:64:C) # USERINPUT OHS
STATOBS.OHS.UI4,STATOBS(64*197:64:C) # USERINPUT OHS
STATOBS.OHS.UI5,STATOBS(64*198:64:C) # USERINPUT OHS
STATOBS.OHS.UI6,STATOBS(64*199:64:C) # USERINPUT OHS
STATOBS.OHS.UI7,STATOBS(64*200:64:C) # USERINPUT OHS
STATOBS.OHS.UI8,STATOBS(64*201:64:C) # USERINPUT OHS
STATOBS.OHS.UI9,STATOBS(64*202:64:C) # USERINPUT OHS

# FCS
STATOBS.FCS.C1,STATOBS(64*203:64:C) # MEMORY data (FCS)
STATOBS.FCS.C2,STATOBS(64*204:64:C) # MEMORY data (FCS)
STATOBS.FCS.C3,STATOBS(64*205:64:C) # MEMORY data (FCS)
STATOBS.FCS.C4,STATOBS(64*206:64:C) # MEMORY data (FCS)
STATOBS.FCS.C5,STATOBS(64*207:64:C) # MEMORY data (FCS)
STATOBS.FCS.C6,STATOBS(64*208:64:C) # MEMORY data (FCS)
STATOBS.FCS.C7,STATOBS(64*209:64:C) # MEMORY data (FCS)
STATOBS.FCS.C8,STATOBS(64*210:64:C) # MEMORY data (FCS)
STATOBS.FCS.C9,STATOBS(64*211:64:C) # MEMORY data (FCS)
STATOBS.FCS.N1,STATOBS(64*212:64:C) # MEMORY data (FCS)
STATOBS.FCS.N2,STATOBS(64*213:64:C) # MEMORY data (FCS)
STATOBS.FCS.N3,STATOBS(64*214:64:C) # MEMORY data (FCS)
STATOBS.FCS.N4,STATOBS(64*215:64:C) # MEMORY data (FCS)
STATOBS.FCS.N5,STATOBS(64*216:64:C) # MEMORY data (FCS)
STATOBS.FCS.N6,STATOBS(64*217:64:C) # MEMORY data (FCS)
STATOBS.FCS.N7,STATOBS(64*218:64:C) # MEMORY data (FCS)
STATOBS.FCS.N8,STATOBS(64*219:64:C) # MEMORY data (FCS)
STATOBS.FCS.N9,STATOBS(64*220:64:C) # MEMORY data (FCS)
STATOBS.FCS.CONFIRMATION,STATOBS(64*221:64:C) # CONFIRMATION FCS
STATOBS.FCS.UI1,STATOBS(64*222:64:C) # USERINPUT FCS
STATOBS.FCS.UI2,STATOBS(64*223:64:C) # USERINPUT FCS
STATOBS.FCS.UI3,STATOBS(64*224:64:C) # USERINPUT FCS
STATOBS.FCS.UI4,STATOBS(64*225:64:C) # USERINPUT FCS
STATOBS.FCS.UI5,STATOBS(64*226:64:C) # USERINPUT FCS
STATOBS.FCS.UI6,STATOBS(64*227:64:C) # USERINPUT FCS
STATOBS.FCS.UI7,STATOBS(64*228:64:C) # USERINPUT FCS
STATOBS.FCS.UI8,STATOBS(64*229:64:C) # USERINPUT FCS
STATOBS.FCS.UI9,STATOBS(64*230:64:C) # USERINPUT FCS

# HDS
STATOBS.HDS.C1,STATOBS(64*231:64:C) # MEMORY data (HDS)
STATOBS.HDS.C2,STATOBS(64*232:64:C) # MEMORY data (HDS)
STATOBS.HDS.C3,STATOBS(64*233:64:C) # MEMORY data (HDS)
STATOBS.HDS.C4,STATOBS(64*234:64:C) # MEMORY data (HDS)
STATOBS.HDS.C5,STATOBS(64*235:64:C) # MEMORY data (HDS)
STATOBS.HDS.C6,STATOBS(64*236:64:C) # MEMORY data (HDS)
STATOBS.HDS.C7,STATOBS(64*237:64:C) # MEMORY data (HDS)
STATOBS.HDS.C8,STATOBS(64*238:64:C) # MEMORY data (HDS)
STATOBS.HDS.C9,STATOBS(64*239:64:C) # MEMORY data (HDS)
STATOBS.HDS.N1,STATOBS(64*240:64:C) # MEMORY data (HDS)
STATOBS.HDS.N2,STATOBS(64*241:64:C) # MEMORY data (HDS)
STATOBS.HDS.N3,STATOBS(64*242:64:C) # MEMORY data (HDS)
STATOBS.HDS.N4,STATOBS(64*243:64:C) # MEMORY data (HDS)
STATOBS.HDS.N5,STATOBS(64*244:64:C) # MEMORY data (HDS)
STATOBS.HDS.N6,STATOBS(64*245:64:C) # MEMORY data (HDS)
STATOBS.HDS.N7,STATOBS(64*246:64:C) # MEMORY data (HDS)
STATOBS.HDS.N8,STATOBS(64*247:64:C) # MEMORY data (HDS)
STATOBS.HDS.N9,STATOBS(64*248:64:C) # MEMORY data (HDS)
STATOBS.HDS.CONFIRMATION,STATOBS(64*249:64:C) # CONFIRMATION HDS
STATOBS.HDS.UI1,STATOBS(64*250:64:C) # USERINPUT HDS
STATOBS.HDS.UI2,STATOBS(64*251:64:C) # USERINPUT HDS
STATOBS.HDS.UI3,STATOBS(64*252:64:C) # USERINPUT HDS
STATOBS.HDS.UI4,STATOBS(64*253:64:C) # USERINPUT HDS
STATOBS.HDS.UI5,STATOBS(64*254:64:C) # USERINPUT HDS
STATOBS.HDS.UI6,STATOBS(64*255:64:C) # USERINPUT HDS
STATOBS.HDS.UI7,STATOBS(64*256:64:C) # USERINPUT HDS
STATOBS.HDS.UI8,STATOBS(64*257:64:C) # USERINPUT HDS
STATOBS.HDS.UI9,STATOBS(64*258:64:C) # USERINPUT HDS

# COM
STATOBS.COM.C1,STATOBS(64*259:64:C) # MEMORY data (COM)
STATOBS.COM.C2,STATOBS(64*260:64:C) # MEMORY data (COM)
STATOBS.COM.C3,STATOBS(64*261:64:C) # MEMORY data (COM)
STATOBS.COM.C4,STATOBS(64*262:64:C) # MEMORY data (COM)
STATOBS.COM.C5,STATOBS(64*263:64:C) # MEMORY data (COM)
STATOBS.COM.C6,STATOBS(64*264:64:C) # MEMORY data (COM)
STATOBS.COM.C7,STATOBS(64*265:64:C) # MEMORY data (COM)
STATOBS.COM.C8,STATOBS(64*266:64:C) # MEMORY data (COM)
STATOBS.COM.C9,STATOBS(64*267:64:C) # MEMORY data (COM)
STATOBS.COM.N1,STATOBS(64*268:64:C) # MEMORY data (COM)
STATOBS.COM.N2,STATOBS(64*269:64:C) # MEMORY data (COM)
STATOBS.COM.N3,STATOBS(64*270:64:C) # MEMORY data (COM)
STATOBS.COM.N4,STATOBS(64*271:64:C) # MEMORY data (COM)
STATOBS.COM.N5,STATOBS(64*272:64:C) # MEMORY data (COM)
STATOBS.COM.N6,STATOBS(64*273:64:C) # MEMORY data (COM)
STATOBS.COM.N7,STATOBS(64*274:64:C) # MEMORY data (COM)
STATOBS.COM.N8,STATOBS(64*275:64:C) # MEMORY data (COM)
STATOBS.COM.N9,STATOBS(64*276:64:C) # MEMORY data (COM)
STATOBS.COM.CONFIRMATION,STATOBS(64*277:64:C) # CONFIRMATION COM
STATOBS.COM.UI1,STATOBS(64*278:64:C) # USERINPUT COM
STATOBS.COM.UI2,STATOBS(64*279:64:C) # USERINPUT COM
STATOBS.COM.UI3,STATOBS(64*280:64:C) # USERINPUT COM
STATOBS.COM.UI4,STATOBS(64*281:64:C) # USERINPUT COM
STATOBS.COM.UI5,STATOBS(64*282:64:C) # USERINPUT COM
STATOBS.COM.UI6,STATOBS(64*283:64:C) # USERINPUT COM
STATOBS.COM.UI7,STATOBS(64*284:64:C) # USERINPUT COM
STATOBS.COM.UI8,STATOBS(64*285:64:C) # USERINPUT COM
STATOBS.COM.UI9,STATOBS(64*286:64:C) # USERINPUT COM

# SUP
STATOBS.SUP.C1,STATOBS(64*287:64:C) # MEMORY data (SUP)
STATOBS.SUP.C2,STATOBS(64*288:64:C) # MEMORY data (SUP)
STATOBS.SUP.C3,STATOBS(64*289:64:C) # MEMORY data (SUP)
STATOBS.SUP.C4,STATOBS(64*290:64:C) # MEMORY data (SUP)
STATOBS.SUP.C5,STATOBS(64*291:64:C) # MEMORY data (SUP)
STATOBS.SUP.C6,STATOBS(64*292:64:C) # MEMORY data (SUP)
STATOBS.SUP.C7,STATOBS(64*293:64:C) # MEMORY data (SUP)
STATOBS.SUP.C8,STATOBS(64*294:64:C) # MEMORY data (SUP)
STATOBS.SUP.C9,STATOBS(64*295:64:C) # MEMORY data (SUP)
STATOBS.SUP.N1,STATOBS(64*296:64:C) # MEMORY data (SUP)
STATOBS.SUP.N2,STATOBS(64*297:64:C) # MEMORY data (SUP)
STATOBS.SUP.N3,STATOBS(64*298:64:C) # MEMORY data (SUP)
STATOBS.SUP.N4,STATOBS(64*299:64:C) # MEMORY data (SUP)
STATOBS.SUP.N5,STATOBS(64*300:64:C) # MEMORY data (SUP)
STATOBS.SUP.N6,STATOBS(64*301:64:C) # MEMORY data (SUP)
STATOBS.SUP.N7,STATOBS(64*302:64:C) # MEMORY data (SUP)
STATOBS.SUP.N8,STATOBS(64*303:64:C) # MEMORY data (SUP)
STATOBS.SUP.N9,STATOBS(64*304:64:C) # MEMORY data (SUP)
STATOBS.SUP.CONFIRMATION,STATOBS(64*305:64:C) # CONFIRMATION SUP
STATOBS.SUP.UI1,STATOBS(64*306:64:C) # USERINPUT SUP
STATOBS.SUP.UI2,STATOBS(64*307:64:C) # USERINPUT SUP
STATOBS.SUP.UI3,STATOBS(64*308:64:C) # USERINPUT SUP
STATOBS.SUP.UI4,STATOBS(64*309:64:C) # USERINPUT SUP
STATOBS.SUP.UI5,STATOBS(64*310:64:C) # USERINPUT SUP
STATOBS.SUP.UI6,STATOBS(64*311:64:C) # USERINPUT SUP
STATOBS.SUP.UI7,STATOBS(64*312:64:C) # USERINPUT SUP
STATOBS.SUP.UI8,STATOBS(64*313:64:C) # USERINPUT SUP
STATOBS.SUP.UI9,STATOBS(64*314:64:C) # USERINPUT SUP

# SUK
STATOBS.SUK.C1,STATOBS(64*315:64:C) # MEMORY data (SUK)
STATOBS.SUK.C2,STATOBS(64*316:64:C) # MEMORY data (SUK)
STATOBS.SUK.C3,STATOBS(64*317:64:C) # MEMORY data (SUK)
STATOBS.SUK.C4,STATOBS(64*318:64:C) # MEMORY data (SUK)
STATOBS.SUK.C5,STATOBS(64*319:64:C) # MEMORY data (SUK)
STATOBS.SUK.C6,STATOBS(64*320:64:C) # MEMORY data (SUK)
STATOBS.SUK.C7,STATOBS(64*321:64:C) # MEMORY data (SUK)
STATOBS.SUK.C8,STATOBS(64*322:64:C) # MEMORY data (SUK)
STATOBS.SUK.C9,STATOBS(64*323:64:C) # MEMORY data (SUK)
STATOBS.SUK.N1,STATOBS(64*324:64:C) # MEMORY data (SUK)
STATOBS.SUK.N2,STATOBS(64*325:64:C) # MEMORY data (SUK)
STATOBS.SUK.N3,STATOBS(64*326:64:C) # MEMORY data (SUK)
STATOBS.SUK.N4,STATOBS(64*327:64:C) # MEMORY data (SUK)
STATOBS.SUK.N5,STATOBS(64*328:64:C) # MEMORY data (SUK)
STATOBS.SUK.N6,STATOBS(64*329:64:C) # MEMORY data (SUK)
STATOBS.SUK.N7,STATOBS(64*330:64:C) # MEMORY data (SUK)
STATOBS.SUK.N8,STATOBS(64*331:64:C) # MEMORY data (SUK)
STATOBS.SUK.N9,STATOBS(64*332:64:C) # MEMORY data (SUK)
STATOBS.SUK.CONFIRMATION,STATOBS(64*333:64:C) # CONFIRMATION SUK
STATOBS.SUK.UI1,STATOBS(64*334:64:C) # USERINPUT SUK
STATOBS.SUK.UI2,STATOBS(64*335:64:C) # USERINPUT SUK
STATOBS.SUK.UI3,STATOBS(64*336:64:C) # USERINPUT SUK
STATOBS.SUK.UI4,STATOBS(64*337:64:C) # USERINPUT SUK
STATOBS.SUK.UI5,STATOBS(64*338:64:C) # USERINPUT SUK
STATOBS.SUK.UI6,STATOBS(64*339:64:C) # USERINPUT SUK
STATOBS.SUK.UI7,STATOBS(64*340:64:C) # USERINPUT SUK
STATOBS.SUK.UI8,STATOBS(64*341:64:C) # USERINPUT SUK
STATOBS.SUK.UI9,STATOBS(64*342:64:C) # USERINPUT SUK

# MIR
STATOBS.MIR.C1,STATOBS(64*343:64:C) # MEMORY data (MIR)
STATOBS.MIR.C2,STATOBS(64*344:64:C) # MEMORY data (MIR)
STATOBS.MIR.C3,STATOBS(64*345:64:C) # MEMORY data (MIR)
STATOBS.MIR.C4,STATOBS(64*346:64:C) # MEMORY data (MIR)
STATOBS.MIR.C5,STATOBS(64*347:64:C) # MEMORY data (MIR)
STATOBS.MIR.C6,STATOBS(64*348:64:C) # MEMORY data (MIR)
STATOBS.MIR.C7,STATOBS(64*349:64:C) # MEMORY data (MIR)
STATOBS.MIR.C8,STATOBS(64*350:64:C) # MEMORY data (MIR)
STATOBS.MIR.C9,STATOBS(64*351:64:C) # MEMORY data (MIR)
STATOBS.MIR.N1,STATOBS(64*352:64:C) # MEMORY data (MIR)
STATOBS.MIR.N2,STATOBS(64*353:64:C) # MEMORY data (MIR)
STATOBS.MIR.N3,STATOBS(64*354:64:C) # MEMORY data (MIR)
STATOBS.MIR.N4,STATOBS(64*355:64:C) # MEMORY data (MIR)
STATOBS.MIR.N5,STATOBS(64*356:64:C) # MEMORY data (MIR)
STATOBS.MIR.N6,STATOBS(64*357:64:C) # MEMORY data (MIR)
STATOBS.MIR.N7,STATOBS(64*358:64:C) # MEMORY data (MIR)
STATOBS.MIR.N8,STATOBS(64*359:64:C) # MEMORY data (MIR)
STATOBS.MIR.N9,STATOBS(64*360:64:C) # MEMORY data (MIR)
STATOBS.MIR.CONFIRMATION,STATOBS(64*361:64:C) # CONFIRMATION MIR
STATOBS.MIR.UI1,STATOBS(64*362:64:C) # USERINPUT MIR
STATOBS.MIR.UI2,STATOBS(64*363:64:C) # USERINPUT MIR
STATOBS.MIR.UI3,STATOBS(64*364:64:C) # USERINPUT MIR
STATOBS.MIR.UI4,STATOBS(64*365:64:C) # USERINPUT MIR
STATOBS.MIR.UI5,STATOBS(64*366:64:C) # USERINPUT MIR
STATOBS.MIR.UI6,STATOBS(64*367:64:C) # USERINPUT MIR
STATOBS.MIR.UI7,STATOBS(64*368:64:C) # USERINPUT MIR
STATOBS.MIR.UI8,STATOBS(64*369:64:C) # USERINPUT MIR
STATOBS.MIR.UI9,STATOBS(64*370:64:C) # USERINPUT MIR

# VTO
STATOBS.VTO.C1,STATOBS(64*371:64:C) # MEMORY data (VTO)
STATOBS.VTO.C2,STATOBS(64*372:64:C) # MEMORY data (VTO)
STATOBS.VTO.C3,STATOBS(64*373:64:C) # MEMORY data (VTO)
STATOBS.VTO.C4,STATOBS(64*374:64:C) # MEMORY data (VTO)
STATOBS.VTO.C5,STATOBS(64*375:64:C) # MEMORY data (VTO)
STATOBS.VTO.C6,STATOBS(64*376:64:C) # MEMORY data (VTO)
STATOBS.VTO.C7,STATOBS(64*377:64:C) # MEMORY data (VTO)
STATOBS.VTO.C8,STATOBS(64*378:64:C) # MEMORY data (VTO)
STATOBS.VTO.C9,STATOBS(64*379:64:C) # MEMORY data (VTO)
STATOBS.VTO.N1,STATOBS(64*380:64:C) # MEMORY data (VTO)
STATOBS.VTO.N2,STATOBS(64*381:64:C) # MEMORY data (VTO)
STATOBS.VTO.N3,STATOBS(64*382:64:C) # MEMORY data (VTO)
STATOBS.VTO.N4,STATOBS(64*383:64:C) # MEMORY data (VTO)
STATOBS.VTO.N5,STATOBS(64*384:64:C) # MEMORY data (VTO)
STATOBS.VTO.N6,STATOBS(64*385:64:C) # MEMORY data (VTO)
STATOBS.VTO.N7,STATOBS(64*386:64:C) # MEMORY data (VTO)
STATOBS.VTO.N8,STATOBS(64*387:64:C) # MEMORY data (VTO)
STATOBS.VTO.N9,STATOBS(64*388:64:C) # MEMORY data (VTO)
STATOBS.VTO.CONFIRMATION,STATOBS(64*389:64:C) # CONFIRMATION VTO
STATOBS.VTO.UI1,STATOBS(64*390:64:C) # USERINPUT VTO
STATOBS.VTO.UI2,STATOBS(64*391:64:C) # USERINPUT VTO
STATOBS.VTO.UI3,STATOBS(64*392:64:C) # USERINPUT VTO
STATOBS.VTO.UI4,STATOBS(64*393:64:C) # USERINPUT VTO
STATOBS.VTO.UI5,STATOBS(64*394:64:C) # USERINPUT VTO
STATOBS.VTO.UI6,STATOBS(64*395:64:C) # USERINPUT VTO
STATOBS.VTO.UI7,STATOBS(64*396:64:C) # USERINPUT VTO
STATOBS.VTO.UI8,STATOBS(64*397:64:C) # USERINPUT VTO
STATOBS.VTO.UI9,STATOBS(64*398:64:C) # USERINPUT VTO

# CAC
STATOBS.CAC.C1,STATOBS(64*399:64:C) # MEMORY data (CAC)
STATOBS.CAC.C2,STATOBS(64*400:64:C) # MEMORY data (CAC)
STATOBS.CAC.C3,STATOBS(64*401:64:C) # MEMORY data (CAC)
STATOBS.CAC.C4,STATOBS(64*402:64:C) # MEMORY data (CAC)
STATOBS.CAC.C5,STATOBS(64*403:64:C) # MEMORY data (CAC)
STATOBS.CAC.C6,STATOBS(64*404:64:C) # MEMORY data (CAC)
STATOBS.CAC.C7,STATOBS(64*405:64:C) # MEMORY data (CAC)
STATOBS.CAC.C8,STATOBS(64*406:64:C) # MEMORY data (CAC)
STATOBS.CAC.C9,STATOBS(64*407:64:C) # MEMORY data (CAC)
STATOBS.CAC.N1,STATOBS(64*408:64:C) # MEMORY data (CAC)
STATOBS.CAC.N2,STATOBS(64*409:64:C) # MEMORY data (CAC)
STATOBS.CAC.N3,STATOBS(64*410:64:C) # MEMORY data (CAC)
STATOBS.CAC.N4,STATOBS(64*411:64:C) # MEMORY data (CAC)
STATOBS.CAC.N5,STATOBS(64*412:64:C) # MEMORY data (CAC)
STATOBS.CAC.N6,STATOBS(64*413:64:C) # MEMORY data (CAC)
STATOBS.CAC.N7,STATOBS(64*414:64:C) # MEMORY data (CAC)
STATOBS.CAC.N8,STATOBS(64*415:64:C) # MEMORY data (CAC)
STATOBS.CAC.N9,STATOBS(64*416:64:C) # MEMORY data (CAC)
STATOBS.CAC.CONFIRMATION,STATOBS(64*417:64:C) # CONFIRMATION CAC
STATOBS.CAC.UI1,STATOBS(64*418:64:C) # USERINPUT CAC
STATOBS.CAC.UI2,STATOBS(64*419:64:C) # USERINPUT CAC
STATOBS.CAC.UI3,STATOBS(64*420:64:C) # USERINPUT CAC
STATOBS.CAC.UI4,STATOBS(64*421:64:C) # USERINPUT CAC
STATOBS.CAC.UI5,STATOBS(64*422:64:C) # USERINPUT CAC
STATOBS.CAC.UI6,STATOBS(64*423:64:C) # USERINPUT CAC
STATOBS.CAC.UI7,STATOBS(64*424:64:C) # USERINPUT CAC
STATOBS.CAC.UI8,STATOBS(64*425:64:C) # USERINPUT CAC
STATOBS.CAC.UI9,STATOBS(64*426:64:C) # USERINPUT CAC

# SKY
STATOBS.SKY.C1,STATOBS(64*427:64:C) # MEMORY data (SKY)
STATOBS.SKY.C2,STATOBS(64*428:64:C) # MEMORY data (SKY)
STATOBS.SKY.C3,STATOBS(64*429:64:C) # MEMORY data (SKY)
STATOBS.SKY.C4,STATOBS(64*430:64:C) # MEMORY data (SKY)
STATOBS.SKY.C5,STATOBS(64*431:64:C) # MEMORY data (SKY)
STATOBS.SKY.C6,STATOBS(64*432:64:C) # MEMORY data (SKY)
STATOBS.SKY.C7,STATOBS(64*433:64:C) # MEMORY data (SKY)
STATOBS.SKY.C8,STATOBS(64*434:64:C) # MEMORY data (SKY)
STATOBS.SKY.C9,STATOBS(64*435:64:C) # MEMORY data (SKY)
STATOBS.SKY.N1,STATOBS(64*436:64:C) # MEMORY data (SKY)
STATOBS.SKY.N2,STATOBS(64*437:64:C) # MEMORY data (SKY)
STATOBS.SKY.N3,STATOBS(64*438:64:C) # MEMORY data (SKY)
STATOBS.SKY.N4,STATOBS(64*439:64:C) # MEMORY data (SKY)
STATOBS.SKY.N5,STATOBS(64*440:64:C) # MEMORY data (SKY)
STATOBS.SKY.N6,STATOBS(64*441:64:C) # MEMORY data (SKY)
STATOBS.SKY.N7,STATOBS(64*442:64:C) # MEMORY data (SKY)
STATOBS.SKY.N8,STATOBS(64*443:64:C) # MEMORY data (SKY)
STATOBS.SKY.N9,STATOBS(64*444:64:C) # MEMORY data (SKY)
STATOBS.SKY.CONFIRMATION,STATOBS(64*445:64:C) # CONFIRMATION SKY
STATOBS.SKY.UI1,STATOBS(64*446:64:C) # USERINPUT SKY
STATOBS.SKY.UI2,STATOBS(64*447:64:C) # USERINPUT SKY
STATOBS.SKY.UI3,STATOBS(64*448:64:C) # USERINPUT SKY
STATOBS.SKY.UI4,STATOBS(64*449:64:C) # USERINPUT SKY
STATOBS.SKY.UI5,STATOBS(64*450:64:C) # USERINPUT SKY
STATOBS.SKY.UI6,STATOBS(64*451:64:C) # USERINPUT SKY
STATOBS.SKY.UI7,STATOBS(64*452:64:C) # USERINPUT SKY
STATOBS.SKY.UI8,STATOBS(64*453:64:C) # USERINPUT SKY
STATOBS.SKY.UI9,STATOBS(64*454:64:C) # USERINPUT SKY

# PI1
STATOBS.PI1.C1,STATOBS(64*455:64:C) # MEMORY data (PI1)
STATOBS.PI1.C2,STATOBS(64*456:64:C) # MEMORY data (PI1)
STATOBS.PI1.C3,STATOBS(64*457:64:C) # MEMORY data (PI1)
STATOBS.PI1.C4,STATOBS(64*458:64:C) # MEMORY data (PI1)
STATOBS.PI1.C5,STATOBS(64*459:64:C) # MEMORY data (PI1)
STATOBS.PI1.C6,STATOBS(64*460:64:C) # MEMORY data (PI1)
STATOBS.PI1.C7,STATOBS(64*461:64:C) # MEMORY data (PI1)
STATOBS.PI1.C8,STATOBS(64*462:64:C) # MEMORY data (PI1)
STATOBS.PI1.C9,STATOBS(64*463:64:C) # MEMORY data (PI1)
STATOBS.PI1.N1,STATOBS(64*464:64:C) # MEMORY data (PI1)
STATOBS.PI1.N2,STATOBS(64*465:64:C) # MEMORY data (PI1)
STATOBS.PI1.N3,STATOBS(64*466:64:C) # MEMORY data (PI1)
STATOBS.PI1.N4,STATOBS(64*467:64:C) # MEMORY data (PI1)
STATOBS.PI1.N5,STATOBS(64*468:64:C) # MEMORY data (PI1)
STATOBS.PI1.N6,STATOBS(64*469:64:C) # MEMORY data (PI1)
STATOBS.PI1.N7,STATOBS(64*470:64:C) # MEMORY data (PI1)
STATOBS.PI1.N8,STATOBS(64*471:64:C) # MEMORY data (PI1)
STATOBS.PI1.N9,STATOBS(64*472:64:C) # MEMORY data (PI1)
STATOBS.PI1.CONFIRMATION,STATOBS(64*473:64:C) # CONFIRMATION PI1
STATOBS.PI1.UI1,STATOBS(64*474:64:C) # USERINPUT PI1
STATOBS.PI1.UI2,STATOBS(64*475:64:C) # USERINPUT PI1
STATOBS.PI1.UI3,STATOBS(64*476:64:C) # USERINPUT PI1
STATOBS.PI1.UI4,STATOBS(64*477:64:C) # USERINPUT PI1
STATOBS.PI1.UI5,STATOBS(64*478:64:C) # USERINPUT PI1
STATOBS.PI1.UI6,STATOBS(64*479:64:C) # USERINPUT PI1
STATOBS.PI1.UI7,STATOBS(64*480:64:C) # USERINPUT PI1
STATOBS.PI1.UI8,STATOBS(64*481:64:C) # USERINPUT PI1
STATOBS.PI1.UI9,STATOBS(64*482:64:C) # USERINPUT PI1

# K3D
STATOBS.K3D.C1,STATOBS(64*483:64:C) # MEMORY data (K3D)
STATOBS.K3D.C2,STATOBS(64*484:64:C) # MEMORY data (K3D)
STATOBS.K3D.C3,STATOBS(64*485:64:C) # MEMORY data (K3D)
STATOBS.K3D.C4,STATOBS(64*486:64:C) # MEMORY data (K3D)
STATOBS.K3D.C5,STATOBS(64*487:64:C) # MEMORY data (K3D)
STATOBS.K3D.C6,STATOBS(64*488:64:C) # MEMORY data (K3D)
STATOBS.K3D.C7,STATOBS(64*489:64:C) # MEMORY data (K3D)
STATOBS.K3D.C8,STATOBS(64*490:64:C) # MEMORY data (K3D)
STATOBS.K3D.C9,STATOBS(64*491:64:C) # MEMORY data (K3D)
STATOBS.K3D.N1,STATOBS(64*492:64:C) # MEMORY data (K3D)
STATOBS.K3D.N2,STATOBS(64*493:64:C) # MEMORY data (K3D)
STATOBS.K3D.N3,STATOBS(64*494:64:C) # MEMORY data (K3D)
STATOBS.K3D.N4,STATOBS(64*495:64:C) # MEMORY data (K3D)
STATOBS.K3D.N5,STATOBS(64*496:64:C) # MEMORY data (K3D)
STATOBS.K3D.N6,STATOBS(64*497:64:C) # MEMORY data (K3D)
STATOBS.K3D.N7,STATOBS(64*498:64:C) # MEMORY data (K3D)
STATOBS.K3D.N8,STATOBS(64*499:64:C) # MEMORY data (K3D)
STATOBS.K3D.N9,STATOBS(64*500:64:C) # MEMORY data (K3D)
STATOBS.K3D.CONFIRMATION,STATOBS(64*501:64:C) # CONFIRMATION K3D
STATOBS.K3D.UI1,STATOBS(64*502:64:C) # USERINPUT K3D
STATOBS.K3D.UI2,STATOBS(64*503:64:C) # USERINPUT K3D
STATOBS.K3D.UI3,STATOBS(64*504:64:C) # USERINPUT K3D
STATOBS.K3D.UI4,STATOBS(64*505:64:C) # USERINPUT K3D
STATOBS.K3D.UI5,STATOBS(64*506:64:C) # USERINPUT K3D
STATOBS.K3D.UI6,STATOBS(64*507:64:C) # USERINPUT K3D
STATOBS.K3D.UI7,STATOBS(64*508:64:C) # USERINPUT K3D
STATOBS.K3D.UI8,STATOBS(64*509:64:C) # USERINPUT K3D
STATOBS.K3D.UI9,STATOBS(64*510:64:C) # USERINPUT K3D

# O16
STATOBS.O16.C1,STATOBS(64*511:64:C) # MEMORY data (O16)
STATOBS.O16.C2,STATOBS(64*512:64:C) # MEMORY data (O16)
STATOBS.O16.C3,STATOBS(64*513:64:C) # MEMORY data (O16)
STATOBS.O16.C4,STATOBS(64*514:64:C) # MEMORY data (O16)
STATOBS.O16.C5,STATOBS(64*515:64:C) # MEMORY data (O16)
STATOBS.O16.C6,STATOBS(64*516:64:C) # MEMORY data (O16)
STATOBS.O16.C7,STATOBS(64*517:64:C) # MEMORY data (O16)
STATOBS.O16.C8,STATOBS(64*518:64:C) # MEMORY data (O16)
STATOBS.O16.C9,STATOBS(64*519:64:C) # MEMORY data (O16)
STATOBS.O16.N1,STATOBS(64*520:64:C) # MEMORY data (O16)
STATOBS.O16.N2,STATOBS(64*521:64:C) # MEMORY data (O16)
STATOBS.O16.N3,STATOBS(64*522:64:C) # MEMORY data (O16)
STATOBS.O16.N4,STATOBS(64*523:64:C) # MEMORY data (O16)
STATOBS.O16.N5,STATOBS(64*524:64:C) # MEMORY data (O16)
STATOBS.O16.N6,STATOBS(64*525:64:C) # MEMORY data (O16)
STATOBS.O16.N7,STATOBS(64*526:64:C) # MEMORY data (O16)
STATOBS.O16.N8,STATOBS(64*527:64:C) # MEMORY data (O16)
STATOBS.O16.N9,STATOBS(64*528:64:C) # MEMORY data (O16)
STATOBS.O16.CONFIRMATION,STATOBS(64*529:64:C) # CONFIRMATION O16
STATOBS.O16.UI1,STATOBS(64*530:64:C) # USERINPUT O16
STATOBS.O16.UI2,STATOBS(64*531:64:C) # USERINPUT O16
STATOBS.O16.UI3,STATOBS(64*532:64:C) # USERINPUT O16
STATOBS.O16.UI4,STATOBS(64*533:64:C) # USERINPUT O16
STATOBS.O16.UI5,STATOBS(64*534:64:C) # USERINPUT O16
STATOBS.O16.UI6,STATOBS(64*535:64:C) # USERINPUT O16
STATOBS.O16.UI7,STATOBS(64*536:64:C) # USERINPUT O16
STATOBS.O16.UI8,STATOBS(64*537:64:C) # USERINPUT O16
STATOBS.O16.UI9,STATOBS(64*538:64:C) # USERINPUT O16

# MCS
STATOBS.MCS.C1,STATOBS(64*539:64:C) # MEMORY data (MCS)
STATOBS.MCS.C2,STATOBS(64*540:64:C) # MEMORY data (MCS)
STATOBS.MCS.C3,STATOBS(64*541:64:C) # MEMORY data (MCS)
STATOBS.MCS.C4,STATOBS(64*542:64:C) # MEMORY data (MCS)
STATOBS.MCS.C5,STATOBS(64*543:64:C) # MEMORY data (MCS)
STATOBS.MCS.C6,STATOBS(64*544:64:C) # MEMORY data (MCS)
STATOBS.MCS.C7,STATOBS(64*545:64:C) # MEMORY data (MCS)
STATOBS.MCS.C8,STATOBS(64*546:64:C) # MEMORY data (MCS)
STATOBS.MCS.C9,STATOBS(64*547:64:C) # MEMORY data (MCS)
STATOBS.MCS.N1,STATOBS(64*548:64:C) # MEMORY data (MCS)
STATOBS.MCS.N2,STATOBS(64*549:64:C) # MEMORY data (MCS)
STATOBS.MCS.N3,STATOBS(64*550:64:C) # MEMORY data (MCS)
STATOBS.MCS.N4,STATOBS(64*551:64:C) # MEMORY data (MCS)
STATOBS.MCS.N5,STATOBS(64*552:64:C) # MEMORY data (MCS)
STATOBS.MCS.N6,STATOBS(64*553:64:C) # MEMORY data (MCS)
STATOBS.MCS.N7,STATOBS(64*554:64:C) # MEMORY data (MCS)
STATOBS.MCS.N8,STATOBS(64*555:64:C) # MEMORY data (MCS)
STATOBS.MCS.N9,STATOBS(64*556:64:C) # MEMORY data (MCS)
STATOBS.MCS.CONFIRMATION,STATOBS(64*557:64:C) # CONFIRMATION MCS
STATOBS.MCS.UI1,STATOBS(64*558:64:C) # USERINPUT MCS
STATOBS.MCS.UI2,STATOBS(64*559:64:C) # USERINPUT MCS
STATOBS.MCS.UI3,STATOBS(64*560:64:C) # USERINPUT MCS
STATOBS.MCS.UI4,STATOBS(64*561:64:C) # USERINPUT MCS
STATOBS.MCS.UI5,STATOBS(64*562:64:C) # USERINPUT MCS
STATOBS.MCS.UI6,STATOBS(64*563:64:C) # USERINPUT MCS
STATOBS.MCS.UI7,STATOBS(64*564:64:C) # USERINPUT MCS
STATOBS.MCS.UI8,STATOBS(64*565:64:C) # USERINPUT MCS
STATOBS.MCS.UI9,STATOBS(64*566:64:C) # USERINPUT MCS

# FMS
STATOBS.FMS.C1,STATOBS(64*567:64:C) # MEMORY data (FMS)
STATOBS.FMS.C2,STATOBS(64*568:64:C) # MEMORY data (FMS)
STATOBS.FMS.C3,STATOBS(64*569:64:C) # MEMORY data (FMS)
STATOBS.FMS.C4,STATOBS(64*570:64:C) # MEMORY data (FMS)
STATOBS.FMS.C5,STATOBS(64*571:64:C) # MEMORY data (FMS)
STATOBS.FMS.C6,STATOBS(64*572:64:C) # MEMORY data (FMS)
STATOBS.FMS.C7,STATOBS(64*573:64:C) # MEMORY data (FMS)
STATOBS.FMS.C8,STATOBS(64*574:64:C) # MEMORY data (FMS)
STATOBS.FMS.C9,STATOBS(64*575:64:C) # MEMORY data (FMS)
STATOBS.FMS.N1,STATOBS(64*576:64:C) # MEMORY data (FMS)
STATOBS.FMS.N2,STATOBS(64*577:64:C) # MEMORY data (FMS)
STATOBS.FMS.N3,STATOBS(64*578:64:C) # MEMORY data (FMS)
STATOBS.FMS.N4,STATOBS(64*579:64:C) # MEMORY data (FMS)
STATOBS.FMS.N5,STATOBS(64*580:64:C) # MEMORY data (FMS)
STATOBS.FMS.N6,STATOBS(64*581:64:C) # MEMORY data (FMS)
STATOBS.FMS.N7,STATOBS(64*582:64:C) # MEMORY data (FMS)
STATOBS.FMS.N8,STATOBS(64*583:64:C) # MEMORY data (FMS)
STATOBS.FMS.N9,STATOBS(64*584:64:C) # MEMORY data (FMS)
STATOBS.FMS.CONFIRMATION,STATOBS(64*585:64:C) # CONFIRMATION FMS
STATOBS.FMS.UI1,STATOBS(64*586:64:C) # USERINPUT FMS
STATOBS.FMS.UI2,STATOBS(64*587:64:C) # USERINPUT FMS
STATOBS.FMS.UI3,STATOBS(64*588:64:C) # USERINPUT FMS
STATOBS.FMS.UI4,STATOBS(64*589:64:C) # USERINPUT FMS
STATOBS.FMS.UI5,STATOBS(64*590:64:C) # USERINPUT FMS
STATOBS.FMS.UI6,STATOBS(64*591:64:C) # USERINPUT FMS
STATOBS.FMS.UI7,STATOBS(64*592:64:C) # USERINPUT FMS
STATOBS.FMS.UI8,STATOBS(64*593:64:C) # USERINPUT FMS
STATOBS.FMS.UI9,STATOBS(64*594:64:C) # USERINPUT FMS

# FLD
STATOBS.FLD.C1,STATOBS(64*595:64:C) # MEMORY data (FLD)
STATOBS.FLD.C2,STATOBS(64*596:64:C) # MEMORY data (FLD)
STATOBS.FLD.C3,STATOBS(64*597:64:C) # MEMORY data (FLD)
STATOBS.FLD.C4,STATOBS(64*598:64:C) # MEMORY data (FLD)
STATOBS.FLD.C5,STATOBS(64*599:64:C) # MEMORY data (FLD)
STATOBS.FLD.C6,STATOBS(64*600:64:C) # MEMORY data (FLD)
STATOBS.FLD.C7,STATOBS(64*601:64:C) # MEMORY data (FLD)
STATOBS.FLD.C8,STATOBS(64*602:64:C) # MEMORY data (FLD)
STATOBS.FLD.C9,STATOBS(64*603:64:C) # MEMORY data (FLD)
STATOBS.FLD.N1,STATOBS(64*604:64:C) # MEMORY data (FLD)
STATOBS.FLD.N2,STATOBS(64*605:64:C) # MEMORY data (FLD)
STATOBS.FLD.N3,STATOBS(64*606:64:C) # MEMORY data (FLD)
STATOBS.FLD.N4,STATOBS(64*607:64:C) # MEMORY data (FLD)
STATOBS.FLD.N5,STATOBS(64*608:64:C) # MEMORY data (FLD)
STATOBS.FLD.N6,STATOBS(64*609:64:C) # MEMORY data (FLD)
STATOBS.FLD.N7,STATOBS(64*610:64:C) # MEMORY data (FLD)
STATOBS.FLD.N8,STATOBS(64*611:64:C) # MEMORY data (FLD)
STATOBS.FLD.N9,STATOBS(64*612:64:C) # MEMORY data (FLD)
STATOBS.FLD.CONFIRMATION,STATOBS(64*613:64:C) # CONFIRMATION FLD
STATOBS.FLD.UI1,STATOBS(64*614:64:C) # USERINPUT FLD
STATOBS.FLD.UI2,STATOBS(64*615:64:C) # USERINPUT FLD
STATOBS.FLD.UI3,STATOBS(64*616:64:C) # USERINPUT FLD
STATOBS.FLD.UI4,STATOBS(64*617:64:C) # USERINPUT FLD
STATOBS.FLD.UI5,STATOBS(64*618:64:C) # USERINPUT FLD
STATOBS.FLD.UI6,STATOBS(64*619:64:C) # USERINPUT FLD
STATOBS.FLD.UI7,STATOBS(64*620:64:C) # USERINPUT FLD
STATOBS.FLD.UI8,STATOBS(64*621:64:C) # USERINPUT FLD
STATOBS.FLD.UI9,STATOBS(64*622:64:C) # USERINPUT FLD

# AON
STATOBS.AON.C1,STATOBS(64*623:64:C) # MEMORY data (AON)
STATOBS.AON.C2,STATOBS(64*624:64:C) # MEMORY data (AON)
STATOBS.AON.C3,STATOBS(64*625:64:C) # MEMORY data (AON)
STATOBS.AON.C4,STATOBS(64*626:64:C) # MEMORY data (AON)
STATOBS.AON.C5,STATOBS(64*627:64:C) # MEMORY data (AON)
STATOBS.AON.C6,STATOBS(64*628:64:C) # MEMORY data (AON)
STATOBS.AON.C7,STATOBS(64*629:64:C) # MEMORY data (AON)
STATOBS.AON.C8,STATOBS(64*630:64:C) # MEMORY data (AON)
STATOBS.AON.C9,STATOBS(64*631:64:C) # MEMORY data (AON)
STATOBS.AON.N1,STATOBS(64*632:64:C) # MEMORY data (AON)
STATOBS.AON.N2,STATOBS(64*633:64:C) # MEMORY data (AON)
STATOBS.AON.N3,STATOBS(64*634:64:C) # MEMORY data (AON)
STATOBS.AON.N4,STATOBS(64*635:64:C) # MEMORY data (AON)
STATOBS.AON.N5,STATOBS(64*636:64:C) # MEMORY data (AON)
STATOBS.AON.N6,STATOBS(64*637:64:C) # MEMORY data (AON)
STATOBS.AON.N7,STATOBS(64*638:64:C) # MEMORY data (AON)
STATOBS.AON.N8,STATOBS(64*639:64:C) # MEMORY data (AON)
STATOBS.AON.N9,STATOBS(64*640:64:C) # MEMORY data (AON)
STATOBS.AON.CONFIRMATION,STATOBS(64*641:64:C) # CONFIRMATION AON
STATOBS.AON.UI1,STATOBS(64*642:64:C) # USERINPUT AON
STATOBS.AON.UI2,STATOBS(64*643:64:C) # USERINPUT AON
STATOBS.AON.UI3,STATOBS(64*644:64:C) # USERINPUT AON
STATOBS.AON.UI4,STATOBS(64*645:64:C) # USERINPUT AON
STATOBS.AON.UI5,STATOBS(64*646:64:C) # USERINPUT AON
STATOBS.AON.UI6,STATOBS(64*647:64:C) # USERINPUT AON
STATOBS.AON.UI7,STATOBS(64*648:64:C) # USERINPUT AON
STATOBS.AON.UI8,STATOBS(64*649:64:C) # USERINPUT AON
STATOBS.AON.UI9,STATOBS(64*650:64:C) # USERINPUT AON

# HIC
STATOBS.HIC.C1,STATOBS(64*651:64:C) # MEMORY data (HIC)
STATOBS.HIC.C2,STATOBS(64*652:64:C) # MEMORY data (HIC)
STATOBS.HIC.C3,STATOBS(64*653:64:C) # MEMORY data (HIC)
STATOBS.HIC.C4,STATOBS(64*654:64:C) # MEMORY data (HIC)
STATOBS.HIC.C5,STATOBS(64*655:64:C) # MEMORY data (HIC)
STATOBS.HIC.C6,STATOBS(64*656:64:C) # MEMORY data (HIC)
STATOBS.HIC.C7,STATOBS(64*657:64:C) # MEMORY data (HIC)
STATOBS.HIC.C8,STATOBS(64*658:64:C) # MEMORY data (HIC)
STATOBS.HIC.C9,STATOBS(64*659:64:C) # MEMORY data (HIC)
STATOBS.HIC.N1,STATOBS(64*660:64:C) # MEMORY data (HIC)
STATOBS.HIC.N2,STATOBS(64*661:64:C) # MEMORY data (HIC)
STATOBS.HIC.N3,STATOBS(64*662:64:C) # MEMORY data (HIC)
STATOBS.HIC.N4,STATOBS(64*663:64:C) # MEMORY data (HIC)
STATOBS.HIC.N5,STATOBS(64*664:64:C) # MEMORY data (HIC)
STATOBS.HIC.N6,STATOBS(64*665:64:C) # MEMORY data (HIC)
STATOBS.HIC.N7,STATOBS(64*666:64:C) # MEMORY data (HIC)
STATOBS.HIC.N8,STATOBS(64*667:64:C) # MEMORY data (HIC)
STATOBS.HIC.N9,STATOBS(64*668:64:C) # MEMORY data (HIC)
STATOBS.HIC.CONFIRMATION,STATOBS(64*669:64:C) # CONFIRMATION HIC
STATOBS.HIC.UI1,STATOBS(64*670:64:C) # USERINPUT HIC
STATOBS.HIC.UI2,STATOBS(64*671:64:C) # USERINPUT HIC
STATOBS.HIC.UI3,STATOBS(64*672:64:C) # USERINPUT HIC
STATOBS.HIC.UI4,STATOBS(64*673:64:C) # USERINPUT HIC
STATOBS.HIC.UI5,STATOBS(64*674:64:C) # USERINPUT HIC
STATOBS.HIC.UI6,STATOBS(64*675:64:C) # USERINPUT HIC
STATOBS.HIC.UI7,STATOBS(64*676:64:C) # USERINPUT HIC
STATOBS.HIC.UI8,STATOBS(64*677:64:C) # USERINPUT HIC
STATOBS.HIC.UI9,STATOBS(64*678:64:C) # USERINPUT HIC

# WAV
STATOBS.WAV.C1,STATOBS(64*679:64:C) # MEMORY data (WAV)
STATOBS.WAV.C2,STATOBS(64*680:64:C) # MEMORY data (WAV)
STATOBS.WAV.C3,STATOBS(64*681:64:C) # MEMORY data (WAV)
STATOBS.WAV.C4,STATOBS(64*682:64:C) # MEMORY data (WAV)
STATOBS.WAV.C5,STATOBS(64*683:64:C) # MEMORY data (WAV)
STATOBS.WAV.C6,STATOBS(64*684:64:C) # MEMORY data (WAV)
STATOBS.WAV.C7,STATOBS(64*685:64:C) # MEMORY data (WAV)
STATOBS.WAV.C8,STATOBS(64*686:64:C) # MEMORY data (WAV)
STATOBS.WAV.C9,STATOBS(64*687:64:C) # MEMORY data (WAV)
STATOBS.WAV.N1,STATOBS(64*688:64:C) # MEMORY data (WAV)
STATOBS.WAV.N2,STATOBS(64*689:64:C) # MEMORY data (WAV)
STATOBS.WAV.N3,STATOBS(64*690:64:C) # MEMORY data (WAV)
STATOBS.WAV.N4,STATOBS(64*691:64:C) # MEMORY data (WAV)
STATOBS.WAV.N5,STATOBS(64*692:64:C) # MEMORY data (WAV)
STATOBS.WAV.N6,STATOBS(64*693:64:C) # MEMORY data (WAV)
STATOBS.WAV.N7,STATOBS(64*694:64:C) # MEMORY data (WAV)
STATOBS.WAV.N8,STATOBS(64*695:64:C) # MEMORY data (WAV)
STATOBS.WAV.N9,STATOBS(64*696:64:C) # MEMORY data (WAV)
STATOBS.WAV.CONFIRMATION,STATOBS(64*697:64:C) # CONFIRMATION WAV
STATOBS.WAV.UI1,STATOBS(64*698:64:C) # USERINPUT WAV
STATOBS.WAV.UI2,STATOBS(64*699:64:C) # USERINPUT WAV
STATOBS.WAV.UI3,STATOBS(64*700:64:C) # USERINPUT WAV
STATOBS.WAV.UI4,STATOBS(64*701:64:C) # USERINPUT WAV
STATOBS.WAV.UI5,STATOBS(64*702:64:C) # USERINPUT WAV
STATOBS.WAV.UI6,STATOBS(64*703:64:C) # USERINPUT WAV
STATOBS.WAV.UI7,STATOBS(64*704:64:C) # USERINPUT WAV
STATOBS.WAV.UI8,STATOBS(64*705:64:C) # USERINPUT WAV
STATOBS.WAV.UI9,STATOBS(64*706:64:C) # USERINPUT WAV

# LGS
STATOBS.LGS.C1,STATOBS(64*707:64:C) # MEMORY data (LGS)
STATOBS.LGS.C2,STATOBS(64*708:64:C) # MEMORY data (LGS)
STATOBS.LGS.C3,STATOBS(64*709:64:C) # MEMORY data (LGS)
STATOBS.LGS.C4,STATOBS(64*710:64:C) # MEMORY data (LGS)
STATOBS.LGS.C5,STATOBS(64*711:64:C) # MEMORY data (LGS)
STATOBS.LGS.C6,STATOBS(64*712:64:C) # MEMORY data (LGS)
STATOBS.LGS.C7,STATOBS(64*713:64:C) # MEMORY data (LGS)
STATOBS.LGS.C8,STATOBS(64*714:64:C) # MEMORY data (LGS)
STATOBS.LGS.C9,STATOBS(64*715:64:C) # MEMORY data (LGS)
STATOBS.LGS.N1,STATOBS(64*716:64:C) # MEMORY data (LGS)
STATOBS.LGS.N2,STATOBS(64*717:64:C) # MEMORY data (LGS)
STATOBS.LGS.N3,STATOBS(64*718:64:C) # MEMORY data (LGS)
STATOBS.LGS.N4,STATOBS(64*719:64:C) # MEMORY data (LGS)
STATOBS.LGS.N5,STATOBS(64*720:64:C) # MEMORY data (LGS)
STATOBS.LGS.N6,STATOBS(64*721:64:C) # MEMORY data (LGS)
STATOBS.LGS.N7,STATOBS(64*722:64:C) # MEMORY data (LGS)
STATOBS.LGS.N8,STATOBS(64*723:64:C) # MEMORY data (LGS)
STATOBS.LGS.N9,STATOBS(64*724:64:C) # MEMORY data (LGS)
STATOBS.LGS.CONFIRMATION,STATOBS(64*725:64:C) # CONFIRMATION LGS
STATOBS.LGS.UI1,STATOBS(64*726:64:C) # USERINPUT LGS
STATOBS.LGS.UI2,STATOBS(64*727:64:C) # USERINPUT LGS
STATOBS.LGS.UI3,STATOBS(64*728:64:C) # USERINPUT LGS
STATOBS.LGS.UI4,STATOBS(64*729:64:C) # USERINPUT LGS
STATOBS.LGS.UI5,STATOBS(64*730:64:C) # USERINPUT LGS
STATOBS.LGS.UI6,STATOBS(64*731:64:C) # USERINPUT LGS
STATOBS.LGS.UI7,STATOBS(64*732:64:C) # USERINPUT LGS
STATOBS.LGS.UI8,STATOBS(64*733:64:C) # USERINPUT LGS
STATOBS.LGS.UI9,STATOBS(64*734:64:C) # USERINPUT LGS

# O24
STATOBS.O24.C1,STATOBS(64*735:64:C) # MEMORY data (O24)
STATOBS.O24.C2,STATOBS(64*736:64:C) # MEMORY data (O24)
STATOBS.O24.C3,STATOBS(64*737:64:C) # MEMORY data (O24)
STATOBS.O24.C4,STATOBS(64*738:64:C) # MEMORY data (O24)
STATOBS.O24.C5,STATOBS(64*739:64:C) # MEMORY data (O24)
STATOBS.O24.C6,STATOBS(64*740:64:C) # MEMORY data (O24)
STATOBS.O24.C7,STATOBS(64*741:64:C) # MEMORY data (O24)
STATOBS.O24.C8,STATOBS(64*742:64:C) # MEMORY data (O24)
STATOBS.O24.C9,STATOBS(64*743:64:C) # MEMORY data (O24)
STATOBS.O24.N1,STATOBS(64*744:64:C) # MEMORY data (O24)
STATOBS.O24.N2,STATOBS(64*745:64:C) # MEMORY data (O24)
STATOBS.O24.N3,STATOBS(64*746:64:C) # MEMORY data (O24)
STATOBS.O24.N4,STATOBS(64*747:64:C) # MEMORY data (O24)
STATOBS.O24.N5,STATOBS(64*748:64:C) # MEMORY data (O24)
STATOBS.O24.N6,STATOBS(64*749:64:C) # MEMORY data (O24)
STATOBS.O24.N7,STATOBS(64*750:64:C) # MEMORY data (O24)
STATOBS.O24.N8,STATOBS(64*751:64:C) # MEMORY data (O24)
STATOBS.O24.N9,STATOBS(64*752:64:C) # MEMORY data (O24)
STATOBS.O24.CONFIRMATION,STATOBS(64*753:64:C) # CONFIRMATION O24
STATOBS.O24.UI1,STATOBS(64*754:64:C) # USERINPUT O24
STATOBS.O24.UI2,STATOBS(64*755:64:C) # USERINPUT O24
STATOBS.O24.UI3,STATOBS(64*756:64:C) # USERINPUT O24
STATOBS.O24.UI4,STATOBS(64*757:64:C) # USERINPUT O24
STATOBS.O24.UI5,STATOBS(64*758:64:C) # USERINPUT O24
STATOBS.O24.UI6,STATOBS(64*759:64:C) # USERINPUT O24
STATOBS.O24.UI7,STATOBS(64*760:64:C) # USERINPUT O24
STATOBS.O24.UI8,STATOBS(64*761:64:C) # USERINPUT O24
STATOBS.O24.UI9,STATOBS(64*762:64:C) # USERINPUT O24

# O25
STATOBS.O25.C1,STATOBS(64*763:64:C) # MEMORY data (O25)
STATOBS.O25.C2,STATOBS(64*764:64:C) # MEMORY data (O25)
STATOBS.O25.C3,STATOBS(64*765:64:C) # MEMORY data (O25)
STATOBS.O25.C4,STATOBS(64*766:64:C) # MEMORY data (O25)
STATOBS.O25.C5,STATOBS(64*767:64:C) # MEMORY data (O25)
STATOBS.O25.C6,STATOBS(64*768:64:C) # MEMORY data (O25)
STATOBS.O25.C7,STATOBS(64*769:64:C) # MEMORY data (O25)
STATOBS.O25.C8,STATOBS(64*770:64:C) # MEMORY data (O25)
STATOBS.O25.C9,STATOBS(64*771:64:C) # MEMORY data (O25)
STATOBS.O25.N1,STATOBS(64*772:64:C) # MEMORY data (O25)
STATOBS.O25.N2,STATOBS(64*773:64:C) # MEMORY data (O25)
STATOBS.O25.N3,STATOBS(64*774:64:C) # MEMORY data (O25)
STATOBS.O25.N4,STATOBS(64*775:64:C) # MEMORY data (O25)
STATOBS.O25.N5,STATOBS(64*776:64:C) # MEMORY data (O25)
STATOBS.O25.N6,STATOBS(64*777:64:C) # MEMORY data (O25)
STATOBS.O25.N7,STATOBS(64*778:64:C) # MEMORY data (O25)
STATOBS.O25.N8,STATOBS(64*779:64:C) # MEMORY data (O25)
STATOBS.O25.N9,STATOBS(64*780:64:C) # MEMORY data (O25)
STATOBS.O25.CONFIRMATION,STATOBS(64*781:64:C) # CONFIRMATION O25
STATOBS.O25.UI1,STATOBS(64*782:64:C) # USERINPUT O25
STATOBS.O25.UI2,STATOBS(64*783:64:C) # USERINPUT O25
STATOBS.O25.UI3,STATOBS(64*784:64:C) # USERINPUT O25
STATOBS.O25.UI4,STATOBS(64*785:64:C) # USERINPUT O25
STATOBS.O25.UI5,STATOBS(64*786:64:C) # USERINPUT O25
STATOBS.O25.UI6,STATOBS(64*787:64:C) # USERINPUT O25
STATOBS.O25.UI7,STATOBS(64*788:64:C) # USERINPUT O25
STATOBS.O25.UI8,STATOBS(64*789:64:C) # USERINPUT O25
STATOBS.O25.UI9,STATOBS(64*790:64:C) # USERINPUT O25

# O26
STATOBS.O26.C1,STATOBS(64*791:64:C) # MEMORY data (O26)
STATOBS.O26.C2,STATOBS(64*792:64:C) # MEMORY data (O26)
STATOBS.O26.C3,STATOBS(64*793:64:C) # MEMORY data (O26)
STATOBS.O26.C4,STATOBS(64*794:64:C) # MEMORY data (O26)
STATOBS.O26.C5,STATOBS(64*795:64:C) # MEMORY data (O26)
STATOBS.O26.C6,STATOBS(64*796:64:C) # MEMORY data (O26)
STATOBS.O26.C7,STATOBS(64*797:64:C) # MEMORY data (O26)
STATOBS.O26.C8,STATOBS(64*798:64:C) # MEMORY data (O26)
STATOBS.O26.C9,STATOBS(64*799:64:C) # MEMORY data (O26)
STATOBS.O26.N1,STATOBS(64*800:64:C) # MEMORY data (O26)
STATOBS.O26.N2,STATOBS(64*801:64:C) # MEMORY data (O26)
STATOBS.O26.N3,STATOBS(64*802:64:C) # MEMORY data (O26)
STATOBS.O26.N4,STATOBS(64*803:64:C) # MEMORY data (O26)
STATOBS.O26.N5,STATOBS(64*804:64:C) # MEMORY data (O26)
STATOBS.O26.N6,STATOBS(64*805:64:C) # MEMORY data (O26)
STATOBS.O26.N7,STATOBS(64*806:64:C) # MEMORY data (O26)
STATOBS.O26.N8,STATOBS(64*807:64:C) # MEMORY data (O26)
STATOBS.O26.N9,STATOBS(64*808:64:C) # MEMORY data (O26)
STATOBS.O26.CONFIRMATION,STATOBS(64*809:64:C) # CONFIRMATION O26
STATOBS.O26.UI1,STATOBS(64*810:64:C) # USERINPUT O26
STATOBS.O26.UI2,STATOBS(64*811:64:C) # USERINPUT O26
STATOBS.O26.UI3,STATOBS(64*812:64:C) # USERINPUT O26
STATOBS.O26.UI4,STATOBS(64*813:64:C) # USERINPUT O26
STATOBS.O26.UI5,STATOBS(64*814:64:C) # USERINPUT O26
STATOBS.O26.UI6,STATOBS(64*815:64:C) # USERINPUT O26
STATOBS.O26.UI7,STATOBS(64*816:64:C) # USERINPUT O26
STATOBS.O26.UI8,STATOBS(64*817:64:C) # USERINPUT O26
STATOBS.O26.UI9,STATOBS(64*818:64:C) # USERINPUT O26

# O27
STATOBS.O27.C1,STATOBS(64*819:64:C) # MEMORY data (O27)
STATOBS.O27.C2,STATOBS(64*820:64:C) # MEMORY data (O27)
STATOBS.O27.C3,STATOBS(64*821:64:C) # MEMORY data (O27)
STATOBS.O27.C4,STATOBS(64*822:64:C) # MEMORY data (O27)
STATOBS.O27.C5,STATOBS(64*823:64:C) # MEMORY data (O27)
STATOBS.O27.C6,STATOBS(64*824:64:C) # MEMORY data (O27)
STATOBS.O27.C7,STATOBS(64*825:64:C) # MEMORY data (O27)
STATOBS.O27.C8,STATOBS(64*826:64:C) # MEMORY data (O27)
STATOBS.O27.C9,STATOBS(64*827:64:C) # MEMORY data (O27)
STATOBS.O27.N1,STATOBS(64*828:64:C) # MEMORY data (O27)
STATOBS.O27.N2,STATOBS(64*829:64:C) # MEMORY data (O27)
STATOBS.O27.N3,STATOBS(64*830:64:C) # MEMORY data (O27)
STATOBS.O27.N4,STATOBS(64*831:64:C) # MEMORY data (O27)
STATOBS.O27.N5,STATOBS(64*832:64:C) # MEMORY data (O27)
STATOBS.O27.N6,STATOBS(64*833:64:C) # MEMORY data (O27)
STATOBS.O27.N7,STATOBS(64*834:64:C) # MEMORY data (O27)
STATOBS.O27.N8,STATOBS(64*835:64:C) # MEMORY data (O27)
STATOBS.O27.N9,STATOBS(64*836:64:C) # MEMORY data (O27)
STATOBS.O27.CONFIRMATION,STATOBS(64*837:64:C) # CONFIRMATION O27
STATOBS.O27.UI1,STATOBS(64*838:64:C) # USERINPUT O27
STATOBS.O27.UI2,STATOBS(64*839:64:C) # USERINPUT O27
STATOBS.O27.UI3,STATOBS(64*840:64:C) # USERINPUT O27
STATOBS.O27.UI4,STATOBS(64*841:64:C) # USERINPUT O27
STATOBS.O27.UI5,STATOBS(64*842:64:C) # USERINPUT O27
STATOBS.O27.UI6,STATOBS(64*843:64:C) # USERINPUT O27
STATOBS.O27.UI7,STATOBS(64*844:64:C) # USERINPUT O27
STATOBS.O27.UI8,STATOBS(64*845:64:C) # USERINPUT O27
STATOBS.O27.UI9,STATOBS(64*846:64:C) # USERINPUT O27

# O28
STATOBS.O28.C1,STATOBS(64*847:64:C) # MEMORY data (O28)
STATOBS.O28.C2,STATOBS(64*848:64:C) # MEMORY data (O28)
STATOBS.O28.C3,STATOBS(64*849:64:C) # MEMORY data (O28)
STATOBS.O28.C4,STATOBS(64*850:64:C) # MEMORY data (O28)
STATOBS.O28.C5,STATOBS(64*851:64:C) # MEMORY data (O28)
STATOBS.O28.C6,STATOBS(64*852:64:C) # MEMORY data (O28)
STATOBS.O28.C7,STATOBS(64*853:64:C) # MEMORY data (O28)
STATOBS.O28.C8,STATOBS(64*854:64:C) # MEMORY data (O28)
STATOBS.O28.C9,STATOBS(64*855:64:C) # MEMORY data (O28)
STATOBS.O28.N1,STATOBS(64*856:64:C) # MEMORY data (O28)
STATOBS.O28.N2,STATOBS(64*857:64:C) # MEMORY data (O28)
STATOBS.O28.N3,STATOBS(64*858:64:C) # MEMORY data (O28)
STATOBS.O28.N4,STATOBS(64*859:64:C) # MEMORY data (O28)
STATOBS.O28.N5,STATOBS(64*860:64:C) # MEMORY data (O28)
STATOBS.O28.N6,STATOBS(64*861:64:C) # MEMORY data (O28)
STATOBS.O28.N7,STATOBS(64*862:64:C) # MEMORY data (O28)
STATOBS.O28.N8,STATOBS(64*863:64:C) # MEMORY data (O28)
STATOBS.O28.N9,STATOBS(64*864:64:C) # MEMORY data (O28)
STATOBS.O28.CONFIRMATION,STATOBS(64*865:64:C) # CONFIRMATION O28
STATOBS.O28.UI1,STATOBS(64*866:64:C) # USERINPUT O28
STATOBS.O28.UI2,STATOBS(64*867:64:C) # USERINPUT O28
STATOBS.O28.UI3,STATOBS(64*868:64:C) # USERINPUT O28
STATOBS.O28.UI4,STATOBS(64*869:64:C) # USERINPUT O28
STATOBS.O28.UI5,STATOBS(64*870:64:C) # USERINPUT O28
STATOBS.O28.UI6,STATOBS(64*871:64:C) # USERINPUT O28
STATOBS.O28.UI7,STATOBS(64*872:64:C) # USERINPUT O28
STATOBS.O28.UI8,STATOBS(64*873:64:C) # USERINPUT O28
STATOBS.O28.UI9,STATOBS(64*874:64:C) # USERINPUT O28

# O29
STATOBS.O29.C1,STATOBS(64*875:64:C) # MEMORY data (O29)
STATOBS.O29.C2,STATOBS(64*876:64:C) # MEMORY data (O29)
STATOBS.O29.C3,STATOBS(64*877:64:C) # MEMORY data (O29)
STATOBS.O29.C4,STATOBS(64*878:64:C) # MEMORY data (O29)
STATOBS.O29.C5,STATOBS(64*879:64:C) # MEMORY data (O29)
STATOBS.O29.C6,STATOBS(64*880:64:C) # MEMORY data (O29)
STATOBS.O29.C7,STATOBS(64*881:64:C) # MEMORY data (O29)
STATOBS.O29.C8,STATOBS(64*882:64:C) # MEMORY data (O29)
STATOBS.O29.C9,STATOBS(64*883:64:C) # MEMORY data (O29)
STATOBS.O29.N1,STATOBS(64*884:64:C) # MEMORY data (O29)
STATOBS.O29.N2,STATOBS(64*885:64:C) # MEMORY data (O29)
STATOBS.O29.N3,STATOBS(64*886:64:C) # MEMORY data (O29)
STATOBS.O29.N4,STATOBS(64*887:64:C) # MEMORY data (O29)
STATOBS.O29.N5,STATOBS(64*888:64:C) # MEMORY data (O29)
STATOBS.O29.N6,STATOBS(64*889:64:C) # MEMORY data (O29)
STATOBS.O29.N7,STATOBS(64*890:64:C) # MEMORY data (O29)
STATOBS.O29.N8,STATOBS(64*891:64:C) # MEMORY data (O29)
STATOBS.O29.N9,STATOBS(64*892:64:C) # MEMORY data (O29)
STATOBS.O29.CONFIRMATION,STATOBS(64*893:64:C) # CONFIRMATION O29
STATOBS.O29.UI1,STATOBS(64*894:64:C) # USERINPUT O29
STATOBS.O29.UI2,STATOBS(64*895:64:C) # USERINPUT O29
STATOBS.O29.UI3,STATOBS(64*896:64:C) # USERINPUT O29
STATOBS.O29.UI4,STATOBS(64*897:64:C) # USERINPUT O29
STATOBS.O29.UI5,STATOBS(64*898:64:C) # USERINPUT O29
STATOBS.O29.UI6,STATOBS(64*899:64:C) # USERINPUT O29
STATOBS.O29.UI7,STATOBS(64*900:64:C) # USERINPUT O29
STATOBS.O29.UI8,STATOBS(64*901:64:C) # USERINPUT O29
STATOBS.O29.UI9,STATOBS(64*902:64:C) # USERINPUT O29

# O30
STATOBS.O30.C1,STATOBS(64*903:64:C) # MEMORY data (O30)
STATOBS.O30.C2,STATOBS(64*904:64:C) # MEMORY data (O30)
STATOBS.O30.C3,STATOBS(64*905:64:C) # MEMORY data (O30)
STATOBS.O30.C4,STATOBS(64*906:64:C) # MEMORY data (O30)
STATOBS.O30.C5,STATOBS(64*907:64:C) # MEMORY data (O30)
STATOBS.O30.C6,STATOBS(64*908:64:C) # MEMORY data (O30)
STATOBS.O30.C7,STATOBS(64*909:64:C) # MEMORY data (O30)
STATOBS.O30.C8,STATOBS(64*910:64:C) # MEMORY data (O30)
STATOBS.O30.C9,STATOBS(64*911:64:C) # MEMORY data (O30)
STATOBS.O30.N1,STATOBS(64*912:64:C) # MEMORY data (O30)
STATOBS.O30.N2,STATOBS(64*913:64:C) # MEMORY data (O30)
STATOBS.O30.N3,STATOBS(64*914:64:C) # MEMORY data (O30)
STATOBS.O30.N4,STATOBS(64*915:64:C) # MEMORY data (O30)
STATOBS.O30.N5,STATOBS(64*916:64:C) # MEMORY data (O30)
STATOBS.O30.N6,STATOBS(64*917:64:C) # MEMORY data (O30)
STATOBS.O30.N7,STATOBS(64*918:64:C) # MEMORY data (O30)
STATOBS.O30.N8,STATOBS(64*919:64:C) # MEMORY data (O30)
STATOBS.O30.N9,STATOBS(64*920:64:C) # MEMORY data (O30)
STATOBS.O30.CONFIRMATION,STATOBS(64*921:64:C) # CONFIRMATION O30
STATOBS.O30.UI1,STATOBS(64*922:64:C) # USERINPUT O30
STATOBS.O30.UI2,STATOBS(64*923:64:C) # USERINPUT O30
STATOBS.O30.UI3,STATOBS(64*924:64:C) # USERINPUT O30
STATOBS.O30.UI4,STATOBS(64*925:64:C) # USERINPUT O30
STATOBS.O30.UI5,STATOBS(64*926:64:C) # USERINPUT O30
STATOBS.O30.UI6,STATOBS(64*927:64:C) # USERINPUT O30
STATOBS.O30.UI7,STATOBS(64*928:64:C) # USERINPUT O30
STATOBS.O30.UI8,STATOBS(64*929:64:C) # USERINPUT O30
STATOBS.O30.UI9,STATOBS(64*930:64:C) # USERINPUT O30

# O31
STATOBS.O31.C1,STATOBS(64*931:64:C) # MEMORY data (O31)
STATOBS.O31.C2,STATOBS(64*932:64:C) # MEMORY data (O31)
STATOBS.O31.C3,STATOBS(64*933:64:C) # MEMORY data (O31)
STATOBS.O31.C4,STATOBS(64*934:64:C) # MEMORY data (O31)
STATOBS.O31.C5,STATOBS(64*935:64:C) # MEMORY data (O31)
STATOBS.O31.C6,STATOBS(64*936:64:C) # MEMORY data (O31)
STATOBS.O31.C7,STATOBS(64*937:64:C) # MEMORY data (O31)
STATOBS.O31.C8,STATOBS(64*938:64:C) # MEMORY data (O31)
STATOBS.O31.C9,STATOBS(64*939:64:C) # MEMORY data (O31)
STATOBS.O31.N1,STATOBS(64*940:64:C) # MEMORY data (O31)
STATOBS.O31.N2,STATOBS(64*941:64:C) # MEMORY data (O31)
STATOBS.O31.N3,STATOBS(64*942:64:C) # MEMORY data (O31)
STATOBS.O31.N4,STATOBS(64*943:64:C) # MEMORY data (O31)
STATOBS.O31.N5,STATOBS(64*944:64:C) # MEMORY data (O31)
STATOBS.O31.N6,STATOBS(64*945:64:C) # MEMORY data (O31)
STATOBS.O31.N7,STATOBS(64*946:64:C) # MEMORY data (O31)
STATOBS.O31.N8,STATOBS(64*947:64:C) # MEMORY data (O31)
STATOBS.O31.N9,STATOBS(64*948:64:C) # MEMORY data (O31)
STATOBS.O31.CONFIRMATION,STATOBS(64*949:64:C) # CONFIRMATION O31
STATOBS.O31.UI1,STATOBS(64*950:64:C) # USERINPUT O31
STATOBS.O31.UI2,STATOBS(64*951:64:C) # USERINPUT O31
STATOBS.O31.UI3,STATOBS(64*952:64:C) # USERINPUT O31
STATOBS.O31.UI4,STATOBS(64*953:64:C) # USERINPUT O31
STATOBS.O31.UI5,STATOBS(64*954:64:C) # USERINPUT O31
STATOBS.O31.UI6,STATOBS(64*955:64:C) # USERINPUT O31
STATOBS.O31.UI7,STATOBS(64*956:64:C) # USERINPUT O31
STATOBS.O31.UI8,STATOBS(64*957:64:C) # USERINPUT O31
STATOBS.O31.UI9,STATOBS(64*958:64:C) # USERINPUT O31

# O32
STATOBS.O32.C1,STATOBS(64*959:64:C) # MEMORY data (O32)
STATOBS.O32.C2,STATOBS(64*960:64:C) # MEMORY data (O32)
STATOBS.O32.C3,STATOBS(64*961:64:C) # MEMORY data (O32)
STATOBS.O32.C4,STATOBS(64*962:64:C) # MEMORY data (O32)
STATOBS.O32.C5,STATOBS(64*963:64:C) # MEMORY data (O32)
STATOBS.O32.C6,STATOBS(64*964:64:C) # MEMORY data (O32)
STATOBS.O32.C7,STATOBS(64*965:64:C) # MEMORY data (O32)
STATOBS.O32.C8,STATOBS(64*966:64:C) # MEMORY data (O32)
STATOBS.O32.C9,STATOBS(64*967:64:C) # MEMORY data (O32)
STATOBS.O32.N1,STATOBS(64*968:64:C) # MEMORY data (O32)
STATOBS.O32.N2,STATOBS(64*969:64:C) # MEMORY data (O32)
STATOBS.O32.N3,STATOBS(64*970:64:C) # MEMORY data (O32)
STATOBS.O32.N4,STATOBS(64*971:64:C) # MEMORY data (O32)
STATOBS.O32.N5,STATOBS(64*972:64:C) # MEMORY data (O32)
STATOBS.O32.N6,STATOBS(64*973:64:C) # MEMORY data (O32)
STATOBS.O32.N7,STATOBS(64*974:64:C) # MEMORY data (O32)
STATOBS.O32.N8,STATOBS(64*975:64:C) # MEMORY data (O32)
STATOBS.O32.N9,STATOBS(64*976:64:C) # MEMORY data (O32)
STATOBS.O32.CONFIRMATION,STATOBS(64*977:64:C) # CONFIRMATION O32
STATOBS.O32.UI1,STATOBS(64*978:64:C) # USERINPUT O32
STATOBS.O32.UI2,STATOBS(64*979:64:C) # USERINPUT O32
STATOBS.O32.UI3,STATOBS(64*980:64:C) # USERINPUT O32
STATOBS.O32.UI4,STATOBS(64*981:64:C) # USERINPUT O32
STATOBS.O32.UI5,STATOBS(64*982:64:C) # USERINPUT O32
STATOBS.O32.UI6,STATOBS(64*983:64:C) # USERINPUT O32
STATOBS.O32.UI7,STATOBS(64*984:64:C) # USERINPUT O32
STATOBS.O32.UI8,STATOBS(64*985:64:C) # USERINPUT O32
STATOBS.O32.UI9,STATOBS(64*986:64:C) # USERINPUT O32

# CMN
STATOBS.CMN.C1,STATOBS(64*987:64:C) # MEMORY data (CMN)
STATOBS.CMN.C2,STATOBS(64*988:64:C) # MEMORY data (CMN)
STATOBS.CMN.C3,STATOBS(64*989:64:C) # MEMORY data (CMN)
STATOBS.CMN.C4,STATOBS(64*990:64:C) # MEMORY data (CMN)
STATOBS.CMN.C5,STATOBS(64*991:64:C) # MEMORY data (CMN)
STATOBS.CMN.C6,STATOBS(64*992:64:C) # MEMORY data (CMN)
STATOBS.CMN.C7,STATOBS(64*993:64:C) # MEMORY data (CMN)
STATOBS.CMN.C8,STATOBS(64*994:64:C) # MEMORY data (CMN)
STATOBS.CMN.C9,STATOBS(64*995:64:C) # MEMORY data (CMN)
STATOBS.CMN.N1,STATOBS(64*996:64:C) # MEMORY data (CMN)
STATOBS.CMN.N2,STATOBS(64*997:64:C) # MEMORY data (CMN)
STATOBS.CMN.N3,STATOBS(64*998:64:C) # MEMORY data (CMN)
STATOBS.CMN.N4,STATOBS(64*999:64:C) # MEMORY data (CMN)
STATOBS.CMN.N5,STATOBS(64*1000:64:C) # MEMORY data (CMN)
STATOBS.CMN.N6,STATOBS(64*1001:64:C) # MEMORY data (CMN)
STATOBS.CMN.N7,STATOBS(64*1002:64:C) # MEMORY data (CMN)
STATOBS.CMN.N8,STATOBS(64*1003:64:C) # MEMORY data (CMN)
STATOBS.CMN.N9,STATOBS(64*1004:64:C) # MEMORY data (CMN)
STATOBS.CMN.CONFIRMATION,STATOBS(64*1005:64:C) # CONFIRMATION CMN
STATOBS.CMN.UI1,STATOBS(64*1006:64:C) # USERINPUT CMN
STATOBS.CMN.UI2,STATOBS(64*1007:64:C) # USERINPUT CMN
STATOBS.CMN.UI3,STATOBS(64*1008:64:C) # USERINPUT CMN
STATOBS.CMN.UI4,STATOBS(64*1009:64:C) # USERINPUT CMN
STATOBS.CMN.UI5,STATOBS(64*1010:64:C) # USERINPUT CMN
STATOBS.CMN.UI6,STATOBS(64*1011:64:C) # USERINPUT CMN
STATOBS.CMN.UI7,STATOBS(64*1012:64:C) # USERINPUT CMN
STATOBS.CMN.UI8,STATOBS(64*1013:64:C) # USERINPUT CMN
STATOBS.CMN.UI9,STATOBS(64*1014:64:C) # USERINPUT CMN

# for SV_GETOFFSET,SV_CENTROID,SV_ORIGIN,SV_TRACKING COMMAND 2003.06.16
STATOBS.NEWORIGIN_SV_X1,STATOBS(64*1285:64:C) # SV_GETOFFSET calc data
STATOBS.NEWORIGIN_SV_Y1,STATOBS(64*1286:64:C) # SV_GETOFFSET calc data
STATOBS.NEWCENTROID_SV_X1,STATOBS(64*1287:64:C) # SV_GETOFFSET calc data
STATOBS.NEWCENTROID_SV_Y1,STATOBS(64*1288:64:C) # SV_GETOFFSET calc data
STATOBS.NEWCENTROID_SV_X2,STATOBS(64*1289:64:C) # SV_GETOFFSET calc data
STATOBS.NEWCENTROID_SV_Y2,STATOBS(64*1290:64:C) # SV_GETOFFSET calc data
STATOBS.NEWREADOUT_SV_X1,STATOBS(64*1291:64:C) # SV_GETOFFSET calc data
STATOBS.NEWREADOUT_SV_Y1,STATOBS(64*1292:64:C) # SV_GETOFFSET calc data
STATOBS.NEWREADOUT_SV_X2,STATOBS(64*1293:64:C) # SV_GETOFFSET calc data
STATOBS.NEWREADOUT_SV_Y2,STATOBS(64*1294:64:C) # SV_GETOFFSET calc data
TSCV.SVCCalcRegX11,TSCV($TSCV0007+66:2:L) # SVCCalcRegX11
TSCV.SVCCalcRegY11,TSCV($TSCV0007+68:2:L) # SVCCalcRegY11
TSCV.SVCCalcRegX21,TSCV($TSCV0007+70:2:L) # SVCCalcRegX21
TSCV.SVCCalcRegY21,TSCV($TSCV0007+72:2:L) # SVCCalcRegY21
TSCV.SVCCalcRegX12,TSCV($TSCV0007+74:2:L) # SVCCalcRegX12
TSCV.SVCCalcRegY12,TSCV($TSCV0007+76:2:L) # SVCCalcRegY12
TSCV.SVCCalcRegX22,TSCV($TSCV0007+78:2:L) # SVCCalcRegX22
TSCV.SVCCalcRegY22,TSCV($TSCV0007+80:2:L) # SVCCalcRegY22
TSCV.SV1_I_SEIL,TSCV($TSCV0007+57:2:L)    # SV1 Intensity CEIL
TSCV.SV1_I_CEIL,TSCV($TSCV0007+57:2:L)    # SV1 Intensity CEIL (add ukawa 2003.11.24)
TSCV.SV1_I_BOTTOM,TSCV($TSCV0007+55:2:L)  # SV1 Intensity BOTTOM
TSCV.SV2_I_SEIL,TSCV($TSCV0007+61:2:L)    # SV2 Intensity CEIL
TSCV.SV2_I_CEIL,TSCV($TSCV0007+61:2:L)    # SV2 Intensity CEIL (add ukawa 2003.11.24)
TSCV.SV2_I_BOTTOM,TSCV($TSCV0007+59:2:L)  # SV2 Intensity BOTTOM
SV.SV1CX,TSCV($TSCV0007+82:4:S:0.01) # SV1 original position X
SV.SV1CY,TSCV($TSCV0007+86:4:S:0.01) # SV2 original position X
SV.SV2CX,TSCV($TSCV0007+90:4:S:0.01) # SV1 original position Y
SV.SV2CY,TSCV($TSCV0007+94:4:S:0.01) # SV2 original position Y
TSCV.SVCCalc,TSCV($TSCV0007+63:1:B:H14) # SVCCalc # change ukawa 2005.02.17
TSCV.SVCCalcMode,TSCV($TSCV0007+64:1:B:H0F) # SVCCalcMode

TSCV.SV_SLITPARAM_X,TSCV($TSCV0007+122:4:L:0.01) # Commanded SV slit center X.
TSCV.SV_SLITPARAM_Y,TSCV($TSCV0007+126:4:L:0.01) # Commanded SV slit center Y.
TSCV.SV_SLITPARAM_THETA,TSCV($TSCV0007+130:4:S:0.01) # Commanded SV slit angle.
TSCV.SV_SLITPARAM_WIDTH,TSCV($TSCV0007+134:4:L:0.01) # Commanded SV slit width.
TSCV.SV_SLITPARAM_STARSIZE,TSCV($TSCV0007+138:4:L:0.01) # Commanded SV slit guiding star size.

# for SV_CHANGE_EXPTIME,SV_CHANGE_SKYLVL COMMAND 2003.07.23
TSCL.SV1DX,TSCL($TSCL_SV+21:4:S:0.01)   # SV STAR1 ERROR X
TSCL.SV1DY,TSCL($TSCL_SV+25:4:S:0.01)   # SV STAR1 ERROR Y
TSCL.SV2DX,TSCL($TSCL_SV+31:4:S:0.01)   # SV STAR2 ERROR X
TSCL.SV2DY,TSCL($TSCL_SV+35:4:S:0.01)   # SV STAR2 ERROR Y
SV.SV1DX,TSCL($TSCL_SV+21:4:S:0.01)     # SV STAR1 ERROR X
SV.SV1DY,TSCL($TSCL_SV+25:4:S:0.01)     # SV STAR1 ERROR Y
SV.SV2DX,TSCL($TSCL_SV+31:4:S:0.01)     # SV STAR2 ERROR X
SV.SV2DY,TSCL($TSCL_SV+35:4:S:0.01)     # SV STAR2 ERROR Y
TSCL.SV1Intensity,TSCL($TSCL_SV+29:2:L) # SV STAR1 INTENSITY
TSCL.SV2Intensity,TSCL($TSCL_SV+39:2:L) # SV STAR2 INTENSITY

# for SH_PARTS,SH,SH_CHANGE_EXPTIME 2003.11.24
TSCV.SHShutter,TSCV($TSCV0009+15:1:B:H30) # SHShutter
TSCV.SHBinning,TSCV($TSCV0009+29:1:B:HFF) # SHBinning
TSCV.SHExpTime,TSCV($TSCV0009+3:4:L) # SHExpTime
TSCV.SHCalibSky,TSCV($TSCV0009+13:1:B:H03) # SHCalibSky
TSCV.SHCalibDark,TSCV($TSCV0009+14:1:B:H03) # SHCalibDark
TSCV.SH_CAL_LOOP,TSCV($TSCV0009+7:2:L) # SH CAL LOOP
TSCV.SH_I_CEIL,TSCV($TSCV0009+11:2:L) # SH Intensity CEIL
TSCV.SH_I_BOTTOM,TSCV($TSCV0009+9:2:L) # SH Intensity BOTTOM
TSCV.ZERNIKE_RMS,TSCV($TSCV00B2+890:8:R) # ZERNIKE DATA RMS (ukawa 2004.01.12 -> 2004.02.25 changed)
TSCV.ZERNIKE_RMS_WOA20,TSCV($TSCV0040+933:8:R) # ZERNIKE DATA RMS(without A20) (ukawa 2004.01.12 -> 2004.02.25 changed)

# for OSSL_Special
E_AGE_R,TSCL(6550:4:S:0.01) # T.B.D. # AG different real(arcsec)
E_AGE_A,TSCL(6550:4:S:0.01) # T.B.D. # AG different average(arcsec)
E_SEEING,TSCL($TSCL_AG+33:4:L:0.00001) # T.B.D. # Seeing (arcsec) (chg iwai 00.03.17) # same AG1StarSize
E_WINDS,TSCL($TSCL_DOME_TEMP+115:6:D) # T.B.D. # Wind Speed Dome (m/s) (chg kusu 99.08.23)
E_HUMID,TSCL($TSCL_DOME_TEMP+97:6:D) # T.B.D. # Humidity Dome (%) (chg kusu 99.08.23)
E_TEMP,TSCL($TSCL_DOME_TEMP+361:6:D) # T.B.D. # Temperature Dome (C) (chg kusu 99.08.23)
S_AG_E,TSCL(6550:4:S:0.01) # T.B.D. # AG different ave & sigma
S_ETEMP,TSCL($TSCL_DOME_TEMP+361:6:D) # T.B.D. # Temperature Dome (C) ave (chg kusu 99.08.23)
S_EHUMID,TSCL($TSCL_DOME_TEMP+97:6:D) # T.B.D. # Humidity Dome (%) ave (chg kusu 99.08.23)
S_EWINDS,TSCL($TSCL_DOME_TEMP+115:6:D) # T.B.D. # Wind Speed Dome (m/s) ave (chg kusu 99.08.23)
S_EWINDD,TSCL($TSCL_WMON+1:6:D) # T.B.D. # Wind Direction Outside (deg) ave (chg kusu 99.08.23)
S_EATOM,TSCL($TSCL_WMON+43:4:L:0.1) # T.B.D. # Air Pressure (hPa) ave (chg kusu 99.08.23)
S_ETRANS,TSCL(6550:6:D) # T.B.D. # Sky Transparency (%) ave (chg kusu 99.08.23)
S_ESEEIN,TSCL($TSCL_AG+33:4:L:0.00001) # T.B.D. # Seeing (arcsec) ave (chg kusu 00.03.17) # same AG1StarSize

# for STS
TSCL.TEMP_NS_VENT_A,TSCL($TSCL_DOME_TEMP+403:6:D) # Temperature Ns Vent A (C) # added 2007-11-08 BB
TSCL.TEMP_NS_VENT_B,TSCL($TSCL_DOME_TEMP+409:6:D) # Temperature Ns Vent B (C) # added 2007-11-08 BB

# SV process
VGW.QDAS.TEL.DATE,VGWD(11:18:C:) # T.B.D. # SV process VGW status date(YYYYMMDDhhmmss.sss)
VGW.QDAS.TEL.ALFA,STSC1S(32:10:C:) # T.B.D. # SV process VGW status RA (hhmmss.sss)
VGW.QDAS.TEL.DELTA,STSC1S(48:9:C:) # T.B.D. # SV process VGW status DEC (ddmmss.ss)

# VGWD
VGWD.DISP.AG,VGWD(205:10:I) # V-LAN DATA DISPLAY AG (zzzzzzzzz9)
VGWD.DISP.SV,VGWD(253:10:I) # V-LAN DATA DISPLAY SV (zzzzzzzzz9)
VGWD.DISP.SH,VGWD(301:10:I) # V-LAN DATA DISPLAY SH (zzzzzzzzz9)
VGWD.FWHM.FLG.AG,VGWD(384:4:C) # AG StarSize Flag (ON or OFF)
VGWD.FWHM.AG,VGWD(389:10:F) # AG StarSize (arcsec)
VGWD.FWHM.TIME.AG,VGWD(400:18:C) # Get AG StarSize Time (YYYYMMDDhhmmss.sss)
VGWD.SVCCALC,VGWD(419:4:C) # SV Centroid Calc status (ON or OFF)
VGWD.FWHM.FLG.SV,VGWD(424:4:C) # SV StarSize Flag (ON or OFF)   add 2003.08.13
VGWD.FWHM.SV,VGWD(429:10:F) # SV StarSize (arcsec)   add 2003.08.13
VGWD.FWHM.TIME.SV,VGWD(440:18:C) # Get SV StarSize Time (YYYYMMDDhhmmss.sss)   add 2003.08.13

# QDAS VGW
VGWQ.AGP.REL.RA,VGWQ(175:11:C) # AG Probe REL RA (+/-hhmmss.sss)
VGWQ.AGP.REL.DEC,VGWQ(187:10:C) # AG Probe REL DEC (+/-ddmmss.ss)
VGWQ.AGP.EQUINOX,VGWQ(198:6:F) # AG Probe Equinox (9999.9) # chg kosugi 99.10.04
VGWQ.AGP.ABS.RA,VGWQ(205:10:C) # AG Probe ABS RA (hhmmss.sss)
VGWQ.AGP.ABS.DEC,VGWQ(216:10:C) # AG Probe ABS DEC (+/-ddmmss.ss)
VGWQ.AGP.MAG,VGWQ(227:4:F) # AG Probe MAG (99.9) # chg watanabe 01.12.18
VGWQ.AGP.OBJECT,VGWQ(232:30:C) # AG Probe OBJECT (XX999999+999999) # chg watanabe 01.12.18
VGWQ.SVP.REL.RA,VGWQ(303:11:C) # SV Probe REL RA (+/-hhmmss.sss)
VGWQ.SVP.REL.DEC,VGWQ(315:10:C) # SV Probe REL DEC (+/-ddmmss.ss)
VGWQ.SVP.EQUINOX,VGWQ(326:6:F) # SV Probe Equinox (9999.9) # chg kosugi 99.10.04
VGWQ.SVP.ABS.RA,VGWQ(333:10:C) # SV Probe ABS RA (hhmmss.sss)
VGWQ.SVP.ABS.DEC,VGWQ(344:10:C) # SV Probe ABS DEC (+/-ddmmss.ss)
VGWQ.SVP.ABS.MM,VGWQ(355:6:F) # SV Probe ABS mm (+/-z9.99)
VGWQ.SVTM.REL.RA,VGWQ(431:11:C) # SV Telemove REL RA (+/-hhmmss.sss)
VGWQ.SVTM.REL.DEC,VGWQ(443:10:C) # SV Telemove REL DEC (+/-hhmmss.ss)
VGWQ.SVTM.EQUINOX,VGWQ(454:6:F) # SV Telemove Equinox (9999.9) # chg kosugi 99.10.04
VGWQ.SVTM.TGT.RA,VGWQ(461:10:C) # SV Telemove Target(Object) RA (hhmmss.sss)
VGWQ.SVTM.TGT.DEC,VGWQ(472:10:C) # SV Telemove Target(Object) DEC (+/-hhmmss.ss)
VGWQ.SVTM.TGT.EQUINOX,VGWQ(454:6:F) # SV Telemove Target(Object) Equinox (9999.9)
VGWQ.SVTM.TGT.X,VGWQ(483:5:F) # SV Telemove Target(Object) X (999.9)
VGWQ.SVTM.TGT.Y,VGWQ(489:5:F) # SV Telemove Target(Object) Y (999.9)
VGWQ.SVTM.DST.RA,VGWQ(495:10:C) # SV Telemove Destination(Slit) RA (hhmmss.sss)
VGWQ.SVTM.DST.DEC,VGWQ(506:10:C) # SV Telemove Destination(Slit) DEC (+/-hhmmss.ss)
VGWQ.SVTM.DST.EQUINOX,VGWQ(454:6:F) # SV Telemove Destination(Slit) Equinox (9999.9)
VGWQ.SVTM.DST.X,VGWQ(517:5:F) # SV Telemove Destination(Slit) X (999.9)
VGWQ.SVTM.DST.Y,VGWQ(523:5:F) # SV Telemove Destination(Slit) Y (999.9)
VGWQ.AGE.X1,VGWQ(559+00:4:I) # AG Exposure Area X1 (zzz9)
VGWQ.AGE.Y1,VGWQ(559+05:4:I) # AG Exposure Area Y1 (zzz9)
VGWQ.AGE.X2,VGWQ(559+10:4:I) # AG Exposure Area X2 (zzz9)
VGWQ.AGE.Y2,VGWQ(559+15:4:I) # AG Exposure Area Y2 (zzz9)
VGWQ.AGE.EXPTIME,VGWQ(579+00:8:I) # AG Exposure Time (zzzzzzz9)
VGWQ.AGE.FWHM,VGWQ(588:10:F) # AG Exposure FWHM (999999.999)
VGWQ.AGE.BRIGHT,VGWQ(599:10:F) # AG Exposure Brightness (99999999.9)
VGWQ.AGE.SKYLVL,VGWQ(610:10:F) # AG Exposure SkyLevel (99999999.9)
VGWQ.AGE.OBJX,VGWQ(621:6:F) # AG Exposure Object X (999.99)
VGWQ.AGE.OBJY,VGWQ(628:6:F) # AG Exposure Object Y (999.99)
VGWQ.AGG1.X1,VGWQ(687+00:4:I) # AG Guide Area1 X1 (zzz9)
VGWQ.AGG1.Y1,VGWQ(687+05:4:I) # AG Guide Area1 Y1 (zzz9)
VGWQ.AGG1.X2,VGWQ(687+10:4:I) # AG Guide Area1 X2 (zzz9)
VGWQ.AGG1.Y2,VGWQ(687+15:4:I) # AG Guide Area1 Y2 (zzz9)
VGWQ.AGG2.X1,VGWQ(707+00:4:I) # AG Guide Area2 X1 (zzz9)
VGWQ.AGG2.Y1,VGWQ(707+05:4:I) # AG Guide Area2 Y1 (zzz9)
VGWQ.AGG2.X2,VGWQ(707+10:4:I) # AG Guide Area2 X2 (zzz9)
VGWQ.AGG2.Y2,VGWQ(707+15:4:I) # AG Guide Area2 Y2 (zzz9)
VGWQ.AGG.FWHM,VGWQ(727:10:F) # AG Guide FWHM (999999.999)
VGWQ.AGG.BRIGHT,VGWQ(738:10:F) # AG Guide Brightness (99999999.9)
VGWQ.AGG.SKYLVL,VGWQ(749:10:F) # AG Guide SkyLevel (99999999.9)
VGWQ.AGG.OBJX,VGWQ(760:6:F) # AG Guide Object X (999.99)
VGWQ.AGG.OBJY,VGWQ(767:6:F) # AG Guide Object Y (999.99)
VGWQ.SVG.X1,VGWQ(815+00:4:I) # SV Guide Area X1 (zzz9)
VGWQ.SVG.Y1,VGWQ(815+05:4:I) # SV Guide Area Y1 (zzz9)
VGWQ.SVG.X2,VGWQ(815+10:4:I) # SV Guide Area X2 (zzz9)
VGWQ.SVG.Y2,VGWQ(815+15:4:I) # SV Guide Area Y2 (zzz9)
VGWQ.SVG.FWHM,VGWQ(835:10:F) # SV Guide FWHM (999999.999)
VGWQ.SVG.BRIGHT,VGWQ(846:10:F) # SV Guide Brightness (99999999.9)
VGWQ.SVG.SKYLVL,VGWQ(857:10:F) # SV Guide SkyLevel (99999999.9)
VGWQ.SVG.OBJX,VGWQ(868:6:F) # SV Guide Object X (999.99)
VGWQ.SVG.OBJY,VGWQ(875:6:F) # SV Guide Object Y (999.99)
VGWQ.SVE.X1,VGWQ(943+00:4:I) # SV Exposure Area X1 (zzz9)
VGWQ.SVE.Y1,VGWQ(943+05:4:I) # SV Exposure Area Y1 (zzz9)
VGWQ.SVE.X2,VGWQ(943+10:4:I) # SV Exposure Area X2 (zzz9)
VGWQ.SVE.Y2,VGWQ(943+15:4:I) # SV Exposure Area Y2 (zzz9)
VGWQ.SVE.EXPTIME,VGWQ(963+00:8:I) # SV Exposure Time (zzzzzzz9)
VGWQ.SVE.FWHM,VGWQ(972:10:F) # SV Exposure FWHM (999999.999)
VGWQ.SVE.BRIGHT,VGWQ(983:10:F) # SV Exposure Brightness (99999999.9)
VGWQ.SVE.SKYLVL,VGWQ(994:10:F) # SV Exposure SkyLevel (99999999.9)
VGWQ.SVE.OBJX,VGWQ(1005:6:F) # SV Exposure Object X (999.99)
VGWQ.SVE.OBJY,VGWQ(1012:6:F) # SV Exposure Object Y (999.99)
VGWQ.SVGSR.DATE,VGWQ(1042:18:C) # SV Guide Signal Report Date (YYYYMMDDhhmmss.sss)
VGWQ.SVGSR.RESULT,VGWQ(1061:2:C) # SV Guide Signal Report Result ("OK"/"NG")
VGWQ.SVGSR.REL.RA,VGWQ(1071:11:C) # SV Guide Signal Report REL RA (+/-hhmmss.sss)
VGWQ.SVGSR.REL.DEC,VGWQ(1083:10:C) # SV Guide Signal Report REL DEC (+/-hhmmss.ss)
VGWQ.SHG.ABS.RA,VGWQ(1199:10:C) # SH Guide ABS RA (hhmmss.sss)
VGWQ.SHG.ABS.DEC,VGWQ(1210:10:C) # SH Guide ABS DEC (+/-hhmmss.ss)
VGWQ.SHG.EQUINOX,VGWQ(1221:6:F) # SH Guide Equinox (9999.9) # chg kosugi 99.10.04
VGWQ.SHG.EXPTIME_AG,VGWQ(1228:8:I) # SH Guide AG Exposure Time (zzzzzzz9)
VGWQ.SHG.EXPTIME_SH,VGWQ(1237:8:I) # SH Guide SH Exposure Time (zzzzzzz9)

# OSSO_MonSys (scheduler)
OBSS.RUN0,OBSS(128+40* 0+28:1:C) # "R" subsystem
OBSS.PEXE,OBSS(128+40* 1+25:1:C) # "R" executer
OBSS.PDS0,OBSS(128+40* 2+25:1:C) # "R" int dispatcher
OBSS.PDS1,OBSS(128+40* 3+25:1:C) # "R" dispatcher 1
OBSS.PDS2,OBSS(128+40* 4+25:1:C) # "R" dispatcher 2
OBSS.PDS3,OBSS(128+40* 5+25:1:C) # "R" dispatcher 3
OBSS.PDS4,OBSS(128+40* 6+25:1:C) # "R" dispatcher 4
OBSS.PDS5,OBSS(128+40* 7+25:1:C) # "R" dispatcher 5
OBSS.PDS6,OBSS(128+40* 8+25:1:C) # "R" dispatcher 6
OBSS.PIT0,OBSS(128+40* 9+25:1:C) # "R" if TSC 0
OBSS.PIT1,OBSS(128+40*10+25:1:C) # "R" if TSC 1
OBSS.PIT2,OBSS(128+40*11+25:1:C) # "R" if TSC 2
OBSS.PIT3,OBSS(128+40*12+25:1:C) # "R" if TSC 3
OBSS.PIT4,OBSS(128+40*13+25:1:C) # "R" if TSC 4
OBSS.PIT5,OBSS(128+40*14+25:1:C) # "R" if TSC 5
OBSS.PCT0,OBSS(128+40*15+25:1:C) # "R" ctrl obs 0
OBSS.PCT1,OBSS(128+40*16+25:1:C) # "R" ctrl obs 1
OBSS.PCT2,OBSS(128+40*17+25:1:C) # "R" ctrl obs 2
OBSS.PCT3,OBSS(128+40*18+25:1:C) # "R" ctrl obs 3
OBSS.PCT4,OBSS(128+40*19+25:1:C) # "R" ctrl obs 4
OBSS.PCT5,OBSS(128+40*20+25:1:C) # "R" ctrl obs 5
OBSS.PIOS,OBSS(128+40*21+25:1:C) # "R" if obs
OBSS.PISW,OBSS(128+40*22+25:1:C) # "R" if svgw
OBSS.PIOC,OBSS(128+40*23+25:1:C) # "R" if obc ( same as under description!! )
OBSS.PIA0,OBSS(128+40*23+25:1:C) # "R" if ossa0(obc)
OBSS.PIA1,OBSS(128+40*24+25:1:C) # "R" if ossa1
OBSS.PIA2,OBSS(128+40*25+25:1:C) # "R" if ossa2
OBSS.PIA3,OBSS(128+40*26+25:1:C) # "R" if ossa3
OBSS.PIA4,OBSS(128+40*27+25:1:C) # "R" if ossa4
OBSS.PIA5,OBSS(128+40*28+25:1:C) # "R" if ossa5
OBSS.PIA6,OBSS(128+40*29+25:1:C) # "R" if ossa6
OBSS.PIA7,OBSS(128+40*30+25:1:C) # "R" if ossa7
OBSS.PIA8,OBSS(128+40*31+25:1:C) # "R" if ossa8
OBSS.PIA9,OBSS(128+40*32+25:1:C) # "R" if ossa9
OBSS.PIVW,OBSS(128+40*33+25:1:C) # "R" if vgw ( same as under description!! )
OBSS.PIB0,OBSS(128+40*33+25:1:C) # "R" if ossb0(vgw)
OBSS.PIB1,OBSS(128+40*34+25:1:C) # "R" if ossb1
OBSS.PIB2,OBSS(128+40*35+25:1:C) # "R" if ossb2
OBSS.PIB3,OBSS(128+40*36+25:1:C) # "R" if ossb3
OBSS.PIB4,OBSS(128+40*37+25:1:C) # "R" if ossb4
OBSS.PIB5,OBSS(128+40*38+25:1:C) # "R" if ossb5
OBSS.PIB6,OBSS(128+40*39+25:1:C) # "R" if ossb6
OBSS.PIB7,OBSS(128+40*40+25:1:C) # "R" if ossb7
OBSS.PIB8,OBSS(128+40*41+25:1:C) # "R" if ossb8
OBSS.PIB9,OBSS(128+40*42+25:1:C) # "R" if ossb9
OBSS.PI01,OBSS(128+40*43+25:1:C) # "R" if obcp1
OBSS.PI02,OBSS(128+40*44+25:1:C) # "R" if obcp2
OBSS.PI03,OBSS(128+40*45+25:1:C) # "R" if obcp3
OBSS.PI04,OBSS(128+40*46+25:1:C) # "R" if obcp4
OBSS.PI05,OBSS(128+40*47+25:1:C) # "R" if obcp5
OBSS.PI06,OBSS(128+40*48+25:1:C) # "R" if obcp6
OBSS.PI07,OBSS(128+40*49+25:1:C) # "R" if obcp7
OBSS.PI08,OBSS(128+40*50+25:1:C) # "R" if obcp8
OBSS.PI09,OBSS(128+40*51+25:1:C) # "R" if obcp9
OBSS.PI10,OBSS(128+40*52+25:1:C) # "R" if obcp10
OBSS.PI11,OBSS(128+40*53+25:1:C) # "R" if obcp11
OBSS.PI12,OBSS(128+40*54+25:1:C) # "R" if obcp12
OBSS.PI13,OBSS(128+40*55+25:1:C) # "R" if obcp13
OBSS.PI14,OBSS(128+40*56+25:1:C) # "R" if obcp14
OBSS.PI15,OBSS(128+40*57+25:1:C) # "R" if obcp15
OBSS.PI16,OBSS(128+40*58+25:1:C) # "R" if obcp16
OBSS.PI17,OBSS(128+40*59+25:1:C) # "R" if obcp17
OBSS.PI18,OBSS(128+40*60+25:1:C) # "R" if obcp18
OBSS.PI19,OBSS(128+40*61+25:1:C) # "R" if obcp19
OBSS.PI20,OBSS(128+40*62+25:1:C) # "R" if obcp20
OBSS.PI21,OBSS(128+40*63+25:1:C) # "R" if obcp21
OBSS.PI22,OBSS(128+40*64+25:1:C) # "R" if obcp22
OBSS.PI23,OBSS(128+40*65+25:1:C) # "R" if obcp23
OBSS.PI24,OBSS(128+40*66+25:1:C) # "R" if obcp24
OBSS.PI25,OBSS(128+40*67+25:1:C) # "R" if obcp25
OBSS.PI26,OBSS(128+40*68+25:1:C) # "R" if obcp26
OBSS.PI27,OBSS(128+40*69+25:1:C) # "R" if obcp27
OBSS.PI28,OBSS(128+40*70+25:1:C) # "R" if obcp28
OBSS.PI29,OBSS(128+40*71+25:1:C) # "R" if obcp29
OBSS.PI30,OBSS(128+40*72+25:1:C) # "R" if obcp30
OBSS.PI31,OBSS(128+40*73+25:1:C) # "R" if obcp31
OBSS.PI32,OBSS(128+40*74+25:1:C) # "R" if obcp32
#OBSS.PCON,OBSS(128+41*75+25:1:C) # "R" controller(2005.02.15 ukawa delete, this area can't be used)

# OSSO_MonSys (logger)
OBSL.RUN0,OBSL(128+40* 0+28:1:C) # "R" subsystem
OBSL.PCON,OBSL(128+40* 1+25:1:C) # "R" controller
OBSL.PMS0,OBSL(128+40* 2+25:1:C) # "R" monitor tscs 0
OBSL.PML0,OBSL(128+40* 3+25:1:C) # "R" monitor tscl 0
OBSL.PMV0,OBSL(128+40* 4+25:1:C) # "R" monitor tscv 0
OBSL.PMS1,OBSL(128+40* 5+25:1:C) # "R" monitor tscs 1
OBSL.PML1,OBSL(128+40* 6+25:1:C) # "R" monitor tscl 1
OBSL.PMV1,OBSL(128+40* 7+25:1:C) # "R" monitor tscv 1
OBSL.PMS2,OBSL(128+40* 8+25:1:C) # "R" monitor tscs 2
OBSL.PML2,OBSL(128+40* 9+25:1:C) # "R" monitor tscl 2
OBSL.PMV2,OBSL(128+40*10+25:1:C) # "R" monitor tscv 2
OBSL.PMS3,OBSL(128+40*11+25:1:C) # "R" monitor tscs 3
OBSL.PML3,OBSL(128+40*12+25:1:C) # "R" monitor tscl 3
OBSL.PMV3,OBSL(128+40*13+25:1:C) # "R" monitor tscv 3
OBSL.PMS4,OBSL(128+40*14+25:1:C) # "R" monitor tscs 4
OBSL.PML4,OBSL(128+40*15+25:1:C) # "R" monitor tscl 4
OBSL.PMV4,OBSL(128+40*16+25:1:C) # "R" monitor tscv 4
OBSL.PMS5,OBSL(128+40*17+25:1:C) # "R" monitor tscs 5
OBSL.PML5,OBSL(128+40*18+25:1:C) # "R" monitor tscl 5
OBSL.PMV5,OBSL(128+40*19+25:1:C) # "R" monitor tscv 5
OBSL.PMU1,OBSL(128+40*20+25:1:C) # "R" monitor unit 1
OBSL.PMU2,OBSL(128+40*21+25:1:C) # "R" monitor unit 2
OBSL.PMU3,OBSL(128+40*22+25:1:C) # "R" monitor unit 3
OBSL.PMU4,OBSL(128+40*23+25:1:C) # "R" monitor unit 4
OBSL.PMU5,OBSL(128+40*24+25:1:C) # "R" monitor unit 5
OBSL.PDIS,OBSL(128+40*25+25:1:C) # "R" distoributer
OBSL.PDSR,OBSL(128+40*26+25:1:C) # "R" status request
OBSL.PDSP,OBSL(128+40*27+25:1:C) # "R" special request
OBSL.PDST,OBSL(128+40*28+25:1:C) # "R" special req timer

# OSSO_MonSys (common)
OBSC.RUN0,OBSC(128+40* 0+28:1:C) # "R" subsystem
OBS1C.RUN0,OBS1C(128+40* 0+28:1:C) # "R" subsystem
OBS2C.RUN0,OBS2C(128+40* 0+28:1:C) # "R" subsystem
OWS1C.RUN0,OWS1C(128+40* 0+28:1:C) # "R" subsystem
OWS2C.RUN0,OWS2C(128+40* 0+28:1:C) # "R" subsystem
OWS3C.RUN0,OWS3C(128+40* 0+28:1:C) # "R" subsystem
DBSC.RUN0,DBSC(128+40* 0+28:1:C) # "R" subsystem
DBS1C.RUN0,DBS1C(128+40* 0+28:1:C) # "R" subsystem
DBS2C.RUN0,DBS2C(128+40* 0+28:1:C) # "R" subsystem

# OSSO_MonSys (daq) and OSST_syscheck
OBCD.DATE,OBCD(11:14:C) # "YYYYMMDDhhmmss"
OBCD.RUN0,OBCD(137:18:C) # "SLAVE ,NORMAL ;"
OBCD.RUN1,OBCD(137:8:C) # "SLAVE "
OBCD.RUN2,OBCD(146:8:C) # "NORMAL "
OBCD.HU1A,OBCD(6328:6:C) # DMS(A) head used for change < 3000 hour
OBCD.HU2A,OBCD(6335:6:C) # DMS(A) head used for cleaning < 50 hour
OBCD.HU3A,OBCD(6342:6:C) # DMS(A) head cleaning count < 50
OBCD.HU1B,OBCD(7259:6:C) # DMS(B) head used for change < 3000 hour
OBCD.HU2B,OBCD(7266:6:C) # DMS(B) head used for cleaning < 50 hour
OBCD.HU3B,OBCD(7273:6:C) # DMS(B) head cleaning count < 50

# OSSO_MonSys (vgw) and OSST_syscheck
VGWD.DATE,VGWD(11:14:C) # "YYYYMMDDhhmmss"
VGWD.RUN0,VGWD(137:18:C) # "SLAVE ,NORMAL ;"
VGWD.RUN1,VGWD(137:8:C) # "SLAVE "
VGWD.RUN2,VGWD(146:8:C) # "NORMAL "

# OSSO_MonSys (ana) and etc
ANAD.RUN0,ANAD(137:8:C) # "ALIVE " or "STOP "
ANAD.COMMAND.NUM,ANAD(146:8:C) # Queue command number
ANAD.COMMAND,ANAD(155:64:C) # Executing command name

# sh focus 
TSCV.SH_FOCUS,TSCV($TSCV0009+40:1:B:H1F)  # sh focus

# for TSC simulator (Optical simulator)
TSCV.AGDataSend,TSCV($TSCV0006+80:1:B:H03)
TSCV.SVDataSend,TSCV($TSCV0007+2:1:B:H03)
#TSCV.SHExpTime,TSCV($TSCV0009+4:4:L)
#TSCV.SHBinning,TSCV($TSCV0009+8:1:B:HFF)
TSCV.AGFocus,TSCV($TSCV0006+0:1:B:H1F)
TSCV.SVFocus,TSCV($TSCV0007+0:1:B:H1F)
TSCV.SHFocus,TSCV($TSCV0009+0:1:B:H1F)
OPTSIM.EL,OPTSIM(0:6:D)
OPTSIM.ROT,OPTSIM(6:6:D)
OPTSIM.ST_X,OPTSIM(12:6:D)
OPTSIM.ST_Y,OPTSIM(18:6:D)
OPTSIM.TOLQUE,OPTSIM(24:6:D)
OPTSIM.C_ND,OPTSIM(30:6:D)
OPTSIM.C_COLOR,OPTSIM(36:6:D)
OPTSIM.C_CON,OPTSIM(42:6:D)
OPTSIM.C_PINFOCUS,OPTSIM(48:6:D)
OPTSIM.C_LIGHT,OPTSIM(54:6:D)
OPTSIM.C_PINCHG,OPTSIM(60:6:D)
OPTSIM.P_ND,OPTSIM(66:6:D)
OPTSIM.P_COLOR,OPTSIM(72:6:D)
OPTSIM.P_LEN_SIM,OPTSIM(78:6:D)
OPTSIM.P_CON,OPTSIM(84:6:D)
OPTSIM.P_LEN_FLAT,OPTSIM(90:6:D)

# for OBC QDAS
# for IRCS
OBCQ.IRC.REGION.X1,OBCQIRC(175:4:C) # Region X1 (Pixcel)
OBCQ.IRC.REGION.Y1,OBCQIRC(180:4:C) # Region Y1 (Pixcel)
OBCQ.IRC.REGION.X2,OBCQIRC(185:4:C) # Region X2 (Pixcel)
OBCQ.IRC.REGION.Y2,OBCQIRC(190:4:C) # Region Y2 (Pixcel)
OBCQ.IRC.REGION.FWHM,OBCQIRC(195:10:C) # FWHM
OBCQ.IRC.REGION.BRIGHT,OBCQIRC(206:10:C) # Brightness
OBCQ.IRC.SN,OBCQIRC(303:10:C) # SN
OBCQ.IRC.STARSIZE.X,OBCQIRC(431:10:C) # StarSize X (arcsec)
OBCQ.IRC.STARSIZE.Y,OBCQIRC(442:10:C) # StarSize Y (arcsec)
OBCQ.IRC.SV.PIXDIF.X,OBCQIRC(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.IRC.SV.PIXDIF.Y,OBCQIRC(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.IRC.SV.SECDIF.RA,OBCQIRC(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.IRC.SV.SECDIF.DEC,OBCQIRC(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.IRC.PIXDIF.X,OBCQIRC(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.IRC.PIXDIF.Y,OBCQIRC(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.IRC.SECDIF.RA,OBCQIRC(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.IRC.SECDIF.DEC,OBCQIRC(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.IRC.BESTFOCUS,OBCQIRC(815:10:C) # BestFocus (mm)
OBCQ.IRC.FOCUSFLG,OBCQIRC(826:1:I) # Flag for BestFocus
OBCQ.IRC.OBE.PIXDIF,OBCQIRC(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.IRC.PIXRA,OBCQIRC(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.IRC.PIXDEC,OBCQIRC(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.IRC.PIXEQUINOX,OBCQIRC(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.IRC.RADEC_X,OBCQIRC(1199:10:C) # radectopix X (9999.9)
OBCQ.IRC.RADEC_Y,OBCQIRC(1210:10:C) # radectopix Y (9999.9)
OBCQ.IRC.SEEING.MEAN,OBCQIRC(1327:5:C) # Seeing mean value
OBCQ.IRC.SEEING.STDDEV,OBCQIRC(1333:5:C) # Seeing Standard deviation value
# for AO
OBCQ.AOS.REGION.X1,OBCQAOS(175:4:C) # Region X1 (Pixcel)
OBCQ.AOS.REGION.Y1,OBCQAOS(180:4:C) # Region Y1 (Pixcel)
OBCQ.AOS.REGION.X2,OBCQAOS(185:4:C) # Region X2 (Pixcel)
OBCQ.AOS.REGION.Y2,OBCQAOS(190:4:C) # Region Y2 (Pixcel)
OBCQ.AOS.REGION.FWHM,OBCQAOS(195:10:C) # FWHM
OBCQ.AOS.REGION.BRIGHT,OBCQAOS(206:10:C) # Brightness
OBCQ.AOS.SN,OBCQAOS(303:10:C) # SN
OBCQ.AOS.STARSIZE.X,OBCQAOS(431:10:C) # StarSize X (arcsec)
OBCQ.AOS.STARSIZE.Y,OBCQAOS(442:10:C) # StarSize Y (arcsec)
OBCQ.AOS.SV.PIXDIF.X,OBCQAOS(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.AOS.SV.PIXDIF.Y,OBCQAOS(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.AOS.SV.SECDIF.RA,OBCQAOS(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.AOS.SV.SECDIF.DEC,OBCQAOS(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.AOS.PIXDIF.X,OBCQAOS(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.AOS.PIXDIF.Y,OBCQAOS(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.AOS.SECDIF.RA,OBCQAOS(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.AOS.SECDIF.DEC,OBCQAOS(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.AOS.BESTFOCUS,OBCQAOS(815:10:C) # BestFocus (mm)
OBCQ.AOS.FOCUSFLG,OBCQAOS(826:1:I) # Flag for BestFocus
OBCQ.AOS.OBE.PIXDIF,OBCQAOS(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.AOS.PIXRA,OBCQAOS(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.AOS.PIXDEC,OBCQAOS(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.AOS.PIXEQUINOX,OBCQAOS(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.AOS.RADEC_X,OBCQAOS(1199:10:C) # radectopix X (9999.9)
OBCQ.AOS.RADEC_Y,OBCQAOS(1210:10:C) # radectopix Y (9999.9)
OBCQ.AOS.SEEING.MEAN,OBCQAOS(1327:5:C) # Seeing mean value
OBCQ.AOS.SEEING.STDDEV,OBCQAOS(1333:5:C) # Seeing Standard deviation value
# for CIAO
OBCQ.CIA.REGION.X1,OBCQCIA(175:4:C) # Region X1 (Pixcel)
OBCQ.CIA.REGION.Y1,OBCQCIA(180:4:C) # Region Y1 (Pixcel)
OBCQ.CIA.REGION.X2,OBCQCIA(185:4:C) # Region X2 (Pixcel)
OBCQ.CIA.REGION.Y2,OBCQCIA(190:4:C) # Region Y2 (Pixcel)
OBCQ.CIA.REGION.FWHM,OBCQCIA(195:10:C) # FWHM
OBCQ.CIA.REGION.BRIGHT,OBCQCIA(206:10:C) # Brightness
OBCQ.CIA.SN,OBCQCIA(303:10:C) # SN
OBCQ.CIA.STARSIZE.X,OBCQCIA(431:10:C) # StarSize X (arcsec)
OBCQ.CIA.STARSIZE.Y,OBCQCIA(442:10:C) # StarSize Y (arcsec)
OBCQ.CIA.SV.PIXDIF.X,OBCQCIA(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.CIA.SV.PIXDIF.Y,OBCQCIA(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.CIA.SV.SECDIF.RA,OBCQCIA(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.CIA.SV.SECDIF.DEC,OBCQCIA(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.CIA.PIXDIF.X,OBCQCIA(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.CIA.PIXDIF.Y,OBCQCIA(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.CIA.SECDIF.RA,OBCQCIA(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.CIA.SECDIF.DEC,OBCQCIA(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.CIA.BESTFOCUS,OBCQCIA(815:10:C) # BestFocus (mm)
OBCQ.CIA.FOCUSFLG,OBCQCIA(826:1:I) # Flag for BestFocus
OBCQ.CIA.OBE.PIXDIF,OBCQCIA(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.CIA.PIXRA,OBCQCIA(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.CIA.PIXDEC,OBCQCIA(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.CIA.PIXEQUINOX,OBCQCIA(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.CIA.RADEC_X,OBCQCIA(1199:10:C) # radectopix X (9999.9)
OBCQ.CIA.RADEC_Y,OBCQCIA(1210:10:C) # radectopix Y (9999.9)
OBCQ.CIA.SEEING.MEAN,OBCQCIA(1327:5:C) # Seeing mean value
OBCQ.CIA.SEEING.STDDEV,OBCQCIA(1333:5:C) # Seeing Standard deviation value
# for OHS
OBCQ.OHS.REGION.X1,OBCQOHS(175:4:C) # Region X1 (Pixcel)
OBCQ.OHS.REGION.Y1,OBCQOHS(180:4:C) # Region Y1 (Pixcel)
OBCQ.OHS.REGION.X2,OBCQOHS(185:4:C) # Region X2 (Pixcel)
OBCQ.OHS.REGION.Y2,OBCQOHS(190:4:C) # Region Y2 (Pixcel)
OBCQ.OHS.REGION.FWHM,OBCQOHS(195:10:C) # FWHM
OBCQ.OHS.REGION.BRIGHT,OBCQOHS(206:10:C) # Brightness
OBCQ.OHS.SN,OBCQOHS(303:10:C) # SN
OBCQ.OHS.STARSIZE.X,OBCQOHS(431:10:C) # StarSize X (arcsec)
OBCQ.OHS.STARSIZE.Y,OBCQOHS(442:10:C) # StarSize Y (arcsec)
OBCQ.OHS.SV.PIXDIF.X,OBCQOHS(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.OHS.SV.PIXDIF.Y,OBCQOHS(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.OHS.SV.SECDIF.RA,OBCQOHS(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.OHS.SV.SECDIF.DEC,OBCQOHS(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.OHS.PIXDIF.X,OBCQOHS(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.OHS.PIXDIF.Y,OBCQOHS(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.OHS.SECDIF.RA,OBCQOHS(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.OHS.SECDIF.DEC,OBCQOHS(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.OHS.BESTFOCUS,OBCQOHS(815:10:C) # BestFocus (mm)
OBCQ.OHS.FOCUSFLG,OBCQOHS(826:1:I) # Flag for BestFocus
OBCQ.OHS.OBE.PIXDIF,OBCQOHS(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.OHS.PIXRA,OBCQOHS(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.OHS.PIXDEC,OBCQOHS(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.OHS.PIXEQUINOX,OBCQOHS(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.OHS.RADEC_X,OBCQOHS(1199:10:C) # radectopix X (9999.9)
OBCQ.OHS.RADEC_Y,OBCQOHS(1210:10:C) # radectopix Y (9999.9)
OBCQ.OHS.SEEING.MEAN,OBCQOHS(1327:5:C) # Seeing mean value
OBCQ.OHS.SEEING.STDDEV,OBCQOHS(1333:5:C) # Seeing Standard deviation value
# for FOCAS
OBCQ.FCS.REGION.X1,OBCQFCS(175:4:C) # Region X1 (Pixcel)
OBCQ.FCS.REGION.Y1,OBCQFCS(180:4:C) # Region Y1 (Pixcel)
OBCQ.FCS.REGION.X2,OBCQFCS(185:4:C) # Region X2 (Pixcel)
OBCQ.FCS.REGION.Y2,OBCQFCS(190:4:C) # Region Y2 (Pixcel)
OBCQ.FCS.REGION.FWHM,OBCQFCS(195:10:C) # FWHM
OBCQ.FCS.REGION.BRIGHT,OBCQFCS(206:10:C) # Brightness
OBCQ.FCS.SN,OBCQFCS(303:10:C) # SN
OBCQ.FCS.STARSIZE.X,OBCQFCS(431:10:C) # StarSize X (arcsec)
OBCQ.FCS.STARSIZE.Y,OBCQFCS(442:10:C) # StarSize Y (arcsec)
OBCQ.FCS.SV.PIXDIF.X,OBCQFCS(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.FCS.SV.PIXDIF.Y,OBCQFCS(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.FCS.SV.SECDIF.RA,OBCQFCS(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.FCS.SV.SECDIF.DEC,OBCQFCS(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.FCS.PIXDIF.X,OBCQFCS(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.FCS.PIXDIF.Y,OBCQFCS(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.FCS.SECDIF.RA,OBCQFCS(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.FCS.SECDIF.DEC,OBCQFCS(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.FCS.BESTFOCUS,OBCQFCS(815:10:C) # BestFocus (mm)
OBCQ.FCS.FOCUSFLG,OBCQFCS(826:1:I) # Flag for BestFocus
OBCQ.FCS.OBE.PIXDIF,OBCQFCS(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.FCS.PIXRA,OBCQFCS(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.FCS.PIXDEC,OBCQFCS(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.FCS.PIXEQUINOX,OBCQFCS(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.FCS.RADEC_X,OBCQFCS(1199:10:C) # radectopix X (9999.9)
OBCQ.FCS.RADEC_Y,OBCQFCS(1210:10:C) # radectopix Y (9999.9)
OBCQ.FCS.SEEING.MEAN,OBCQFCS(1327:5:C) # Seeing mean value
OBCQ.FCS.SEEING.STDDEV,OBCQFCS(1333:5:C) # Seeing Standard deviation value
# for HDS
OBCQ.HDS.REGION.X1,OBCQHDS(175:4:C) # Region X1 (Pixcel)
OBCQ.HDS.REGION.Y1,OBCQHDS(180:4:C) # Region Y1 (Pixcel)
OBCQ.HDS.REGION.X2,OBCQHDS(185:4:C) # Region X2 (Pixcel)
OBCQ.HDS.REGION.Y2,OBCQHDS(190:4:C) # Region Y2 (Pixcel)
OBCQ.HDS.REGION.FWHM,OBCQHDS(195:10:C) # FWHM
OBCQ.HDS.REGION.BRIGHT,OBCQHDS(206:10:C) # Brightness
OBCQ.HDS.SN,OBCQHDS(303:10:C) # SN
OBCQ.HDS.STARSIZE.X,OBCQHDS(431:10:C) # StarSize X (arcsec)
OBCQ.HDS.STARSIZE.Y,OBCQHDS(442:10:C) # StarSize Y (arcsec)
OBCQ.HDS.SV.PIXDIF.X,OBCQHDS(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.HDS.SV.PIXDIF.Y,OBCQHDS(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.HDS.SV.SECDIF.RA,OBCQHDS(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.HDS.SV.SECDIF.DEC,OBCQHDS(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.HDS.PIXDIF.X,OBCQHDS(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.HDS.PIXDIF.Y,OBCQHDS(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.HDS.SECDIF.RA,OBCQHDS(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.HDS.SECDIF.DEC,OBCQHDS(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.HDS.BESTFOCUS,OBCQHDS(815:10:C) # BestFocus (mm)
OBCQ.HDS.FOCUSFLG,OBCQHDS(826:1:I) # Flag for BestFocus
OBCQ.HDS.OBE.PIXDIF,OBCQHDS(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.HDS.PIXRA,OBCQHDS(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.HDS.PIXDEC,OBCQHDS(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.HDS.PIXEQUINOX,OBCQHDS(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.HDS.RADEC_X,OBCQHDS(1199:10:C) # radectopix X (9999.9)
OBCQ.HDS.RADEC_Y,OBCQHDS(1210:10:C) # radectopix Y (9999.9)
OBCQ.HDS.SEEING.MEAN,OBCQHDS(1327:5:C) # Seeing mean value
OBCQ.HDS.SEEING.STDDEV,OBCQHDS(1333:5:C) # Seeing Standard deviation value
# for COMICS
OBCQ.COM.REGION.X1,OBCQCOM(175:4:C) # Region X1 (Pixcel)
OBCQ.COM.REGION.Y1,OBCQCOM(180:4:C) # Region Y1 (Pixcel)
OBCQ.COM.REGION.X2,OBCQCOM(185:4:C) # Region X2 (Pixcel)
OBCQ.COM.REGION.Y2,OBCQCOM(190:4:C) # Region Y2 (Pixcel)
OBCQ.COM.REGION.FWHM,OBCQCOM(195:10:C) # FWHM
OBCQ.COM.REGION.BRIGHT,OBCQCOM(206:10:C) # Brightness
OBCQ.COM.SN,OBCQCOM(303:10:C) # SN
OBCQ.COM.STARSIZE.X,OBCQCOM(431:10:C) # StarSize X (arcsec)
OBCQ.COM.STARSIZE.Y,OBCQCOM(442:10:C) # StarSize Y (arcsec)
OBCQ.COM.SV.PIXDIF.X,OBCQCOM(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.COM.SV.PIXDIF.Y,OBCQCOM(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.COM.SV.SECDIF.RA,OBCQCOM(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.COM.SV.SECDIF.DEC,OBCQCOM(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.COM.PIXDIF.X,OBCQCOM(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.COM.PIXDIF.Y,OBCQCOM(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.COM.SECDIF.RA,OBCQCOM(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.COM.SECDIF.DEC,OBCQCOM(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.COM.BESTFOCUS,OBCQCOM(815:10:C) # BestFocus (mm)
OBCQ.COM.FOCUSFLG,OBCQCOM(826:1:I) # Flag for BestFocus
OBCQ.COM.OBE.PIXDIF,OBCQCOM(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.COM.PIXRA,OBCQCOM(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.COM.PIXDEC,OBCQCOM(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.COM.PIXEQUINOX,OBCQCOM(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.COM.RADEC_X,OBCQCOM(1199:10:C) # radectopix X (9999.9)
OBCQ.COM.RADEC_Y,OBCQCOM(1210:10:C) # radectopix Y (9999.9)
OBCQ.COM.SEEING.MEAN,OBCQCOM(1327:5:C) # Seeing mean value
OBCQ.COM.SEEING.STDDEV,OBCQCOM(1333:5:C) # Seeing Standard deviation value
# for SPCAM
OBCQ.SUP.REGION.X1,OBCQSUP(175:4:C) # Region X1 (Pixcel)
OBCQ.SUP.REGION.Y1,OBCQSUP(180:4:C) # Region Y1 (Pixcel)
OBCQ.SUP.REGION.X2,OBCQSUP(185:4:C) # Region X2 (Pixcel)
OBCQ.SUP.REGION.Y2,OBCQSUP(190:4:C) # Region Y2 (Pixcel)
OBCQ.SUP.REGION.FWHM,OBCQSUP(195:10:C) # FWHM
OBCQ.SUP.REGION.BRIGHT,OBCQSUP(206:10:C) # Brightness
OBCQ.SUP.SN,OBCQSUP(303:10:C) # SN
OBCQ.SUP.STARSIZE.X,OBCQSUP(431:10:C) # StarSize X (arcsec)
OBCQ.SUP.STARSIZE.Y,OBCQSUP(442:10:C) # StarSize Y (arcsec)
OBCQ.SUP.SV.PIXDIF.X,OBCQSUP(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.SUP.SV.PIXDIF.Y,OBCQSUP(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.SUP.SV.SECDIF.RA,OBCQSUP(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.SUP.SV.SECDIF.DEC,OBCQSUP(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.SUP.PIXDIF.X,OBCQSUP(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.SUP.PIXDIF.Y,OBCQSUP(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.SUP.SECDIF.RA,OBCQSUP(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.SUP.SECDIF.DEC,OBCQSUP(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.SUP.BESTFOCUS,OBCQSUP(815:10:C) # BestFocus (mm)
OBCQ.SUP.FOCUSFLG,OBCQSUP(826:1:I) # Flag for BestFocus
OBCQ.SUP.OBE.PIXDIF,OBCQSUP(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.SUP.PIXRA,OBCQSUP(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.SUP.PIXDEC,OBCQSUP(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.SUP.PIXEQUINOX,OBCQSUP(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.SUP.RADEC_X,OBCQSUP(1199:10:C) # radectopix X (9999.9)
OBCQ.SUP.RADEC_Y,OBCQSUP(1210:10:C) # radectopix Y (9999.9)
OBCQ.SUP.SEEING.MEAN,OBCQSUP(1327:5:C) # Seeing mean value
OBCQ.SUP.SEEING.STDDEV,OBCQSUP(1333:5:C) # Seeing Standard deviation value
# for SUKA
OBCQ.SUK.REGION.X1,OBCQSUK(175:4:C) # Region X1 (Pixcel)
OBCQ.SUK.REGION.Y1,OBCQSUK(180:4:C) # Region Y1 (Pixcel)
OBCQ.SUK.REGION.X2,OBCQSUK(185:4:C) # Region X2 (Pixcel)
OBCQ.SUK.REGION.Y2,OBCQSUK(190:4:C) # Region Y2 (Pixcel)
OBCQ.SUK.REGION.FWHM,OBCQSUK(195:10:C) # FWHM
OBCQ.SUK.REGION.BRIGHT,OBCQSUK(206:10:C) # Brightness
OBCQ.SUK.SN,OBCQSUK(303:10:C) # SN
OBCQ.SUK.STARSIZE.X,OBCQSUK(431:10:C) # StarSize X (arcsec)
OBCQ.SUK.STARSIZE.Y,OBCQSUK(442:10:C) # StarSize Y (arcsec)
OBCQ.SUK.SV.PIXDIF.X,OBCQSUK(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.SUK.SV.PIXDIF.Y,OBCQSUK(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.SUK.SV.SECDIF.RA,OBCQSUK(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.SUK.SV.SECDIF.DEC,OBCQSUK(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.SUK.PIXDIF.X,OBCQSUK(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.SUK.PIXDIF.Y,OBCQSUK(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.SUK.SECDIF.RA,OBCQSUK(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.SUK.SECDIF.DEC,OBCQSUK(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.SUK.BESTFOCUS,OBCQSUK(815:10:C) # BestFocus (mm)
OBCQ.SUK.FOCUSFLG,OBCQSUK(826:1:I) # Flag for BestFocus
OBCQ.SUK.OBE.PIXDIF,OBCQSUK(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.SUK.PIXRA,OBCQSUK(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.SUK.PIXDEC,OBCQSUK(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.SUK.PIXEQUINOX,OBCQSUK(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.SUK.RADEC_X,OBCQSUK(1199:10:C) # radectopix X (9999.9)
OBCQ.SUK.RADEC_Y,OBCQSUK(1210:10:C) # radectopix Y (9999.9)
OBCQ.SUK.SEEING.MEAN,OBCQSUK(1327:5:C) # Seeing mean value
OBCQ.SUK.SEEING.STDDEV,OBCQSUK(1333:5:C) # Seeing Standard deviation value
# for MIRTOS
OBCQ.MIR.REGION.X1,OBCQMIR(175:4:C) # Region X1 (Pixcel)
OBCQ.MIR.REGION.Y1,OBCQMIR(180:4:C) # Region Y1 (Pixcel)
OBCQ.MIR.REGION.X2,OBCQMIR(185:4:C) # Region X2 (Pixcel)
OBCQ.MIR.REGION.Y2,OBCQMIR(190:4:C) # Region Y2 (Pixcel)
OBCQ.MIR.REGION.FWHM,OBCQMIR(195:10:C) # FWHM
OBCQ.MIR.REGION.BRIGHT,OBCQMIR(206:10:C) # Brightness
OBCQ.MIR.SN,OBCQMIR(303:10:C) # SN
OBCQ.MIR.STARSIZE.X,OBCQMIR(431:10:C) # StarSize X (arcsec)
OBCQ.MIR.STARSIZE.Y,OBCQMIR(442:10:C) # StarSize Y (arcsec)
OBCQ.MIR.SV.PIXDIF.X,OBCQMIR(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.MIR.SV.PIXDIF.Y,OBCQMIR(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.MIR.SV.SECDIF.RA,OBCQMIR(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.MIR.SV.SECDIF.DEC,OBCQMIR(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.MIR.PIXDIF.X,OBCQMIR(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.MIR.PIXDIF.Y,OBCQMIR(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.MIR.SECDIF.RA,OBCQMIR(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.MIR.SECDIF.DEC,OBCQMIR(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.MIR.BESTFOCUS,OBCQMIR(815:10:C) # BestFocus (mm)
OBCQ.MIR.FOCUSFLG,OBCQMIR(826:1:I) # Flag for BestFocus
OBCQ.MIR.OBE.PIXDIF,OBCQMIR(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.MIR.PIXRA,OBCQMIR(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.MIR.PIXDEC,OBCQMIR(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.MIR.PIXEQUINOX,OBCQMIR(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.MIR.RADEC_X,OBCQMIR(1199:10:C) # radectopix X (9999.9)
OBCQ.MIR.RADEC_Y,OBCQMIR(1210:10:C) # radectopix Y (9999.9)
OBCQ.MIR.SEEING.MEAN,OBCQMIR(1327:5:C) # Seeing mean value
OBCQ.MIR.SEEING.STDDEV,OBCQMIR(1333:5:C) # Seeing Standard deviation value
# for VTOS
OBCQ.VTO.REGION.X1,OBCQVTO(175:4:C) # Region X1 (Pixcel)
OBCQ.VTO.REGION.Y1,OBCQVTO(180:4:C) # Region Y1 (Pixcel)
OBCQ.VTO.REGION.X2,OBCQVTO(185:4:C) # Region X2 (Pixcel)
OBCQ.VTO.REGION.Y2,OBCQVTO(190:4:C) # Region Y2 (Pixcel)
OBCQ.VTO.REGION.FWHM,OBCQVTO(195:10:C) # FWHM
OBCQ.VTO.REGION.BRIGHT,OBCQVTO(206:10:C) # Brightness
OBCQ.VTO.SN,OBCQVTO(303:10:C) # SN
OBCQ.VTO.STARSIZE.X,OBCQVTO(431:10:C) # StarSize X (arcsec)
OBCQ.VTO.STARSIZE.Y,OBCQVTO(442:10:C) # StarSize Y (arcsec)
OBCQ.VTO.SV.PIXDIF.X,OBCQVTO(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.VTO.SV.PIXDIF.Y,OBCQVTO(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.VTO.SV.SECDIF.RA,OBCQVTO(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.VTO.SV.SECDIF.DEC,OBCQVTO(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.VTO.PIXDIF.X,OBCQVTO(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.VTO.PIXDIF.Y,OBCQVTO(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.VTO.SECDIF.RA,OBCQVTO(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.VTO.SECDIF.DEC,OBCQVTO(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.VTO.BESTFOCUS,OBCQVTO(815:10:C) # BestFocus (mm)
OBCQ.VTO.FOCUSFLG,OBCQVTO(826:1:I) # Flag for BestFocus
OBCQ.VTO.OBE.PIXDIF,OBCQVTO(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.VTO.PIXRA,OBCQVTO(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.VTO.PIXDEC,OBCQVTO(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.VTO.PIXEQUINOX,OBCQVTO(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.VTO.RADEC_X,OBCQVTO(1199:10:C) # radectopix X (9999.9)
OBCQ.VTO.RADEC_Y,OBCQVTO(1210:10:C) # radectopix Y (9999.9)
OBCQ.VTO.SEEING.MEAN,OBCQVTO(1327:5:C) # Seeing mean value
OBCQ.VTO.SEEING.STDDEV,OBCQVTO(1333:5:C) # Seeing Standard deviation value
# for CAC
OBCQ.CAC.REGION.X1,OBCQCAC(175:4:C) # Region X1 (Pixcel)
OBCQ.CAC.REGION.Y1,OBCQCAC(180:4:C) # Region Y1 (Pixcel)
OBCQ.CAC.REGION.X2,OBCQCAC(185:4:C) # Region X2 (Pixcel)
OBCQ.CAC.REGION.Y2,OBCQCAC(190:4:C) # Region Y2 (Pixcel)
OBCQ.CAC.REGION.FWHM,OBCQCAC(195:10:C) # FWHM
OBCQ.CAC.REGION.BRIGHT,OBCQCAC(206:10:C) # Brightness
OBCQ.CAC.SN,OBCQCAC(303:10:C) # SN
OBCQ.CAC.STARSIZE.X,OBCQCAC(431:10:C) # StarSize X (arcsec)
OBCQ.CAC.STARSIZE.Y,OBCQCAC(442:10:C) # StarSize Y (arcsec)
OBCQ.CAC.SV.PIXDIF.X,OBCQCAC(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.CAC.SV.PIXDIF.Y,OBCQCAC(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.CAC.SV.SECDIF.RA,OBCQCAC(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.CAC.SV.SECDIF.DEC,OBCQCAC(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.CAC.PIXDIF.X,OBCQCAC(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.CAC.PIXDIF.Y,OBCQCAC(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.CAC.SECDIF.RA,OBCQCAC(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.CAC.SECDIF.DEC,OBCQCAC(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.CAC.BESTFOCUS,OBCQCAC(815:10:C) # BestFocus (mm)
OBCQ.CAC.FOCUSFLG,OBCQCAC(826:1:I) # Flag for BestFocus
OBCQ.CAC.OBE.PIXDIF,OBCQCAC(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.CAC.PIXRA,OBCQCAC(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.CAC.PIXDEC,OBCQCAC(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.CAC.PIXEQUINOX,OBCQCAC(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.CAC.RADEC_X,OBCQCAC(1199:10:C) # radectopix X (9999.9)
OBCQ.CAC.RADEC_Y,OBCQCAC(1210:10:C) # radectopix Y (9999.9)
OBCQ.CAC.SEEING.MEAN,OBCQCAC(1327:5:C) # Seeing mean value
OBCQ.CAC.SEEING.STDDEV,OBCQCAC(1333:5:C) # Seeing Standard deviation value
# for SKYMON
OBCQ.SKY.REGION.X1,OBCQSKY(175:4:C) # Region X1 (Pixcel)
OBCQ.SKY.REGION.Y1,OBCQSKY(180:4:C) # Region Y1 (Pixcel)
OBCQ.SKY.REGION.X2,OBCQSKY(185:4:C) # Region X2 (Pixcel)
OBCQ.SKY.REGION.Y2,OBCQSKY(190:4:C) # Region Y2 (Pixcel)
OBCQ.SKY.REGION.FWHM,OBCQSKY(195:10:C) # FWHM
OBCQ.SKY.REGION.BRIGHT,OBCQSKY(206:10:C) # Brightness
OBCQ.SKY.SN,OBCQSKY(303:10:C) # SN
OBCQ.SKY.STARSIZE.X,OBCQSKY(431:10:C) # StarSize X (arcsec)
OBCQ.SKY.STARSIZE.Y,OBCQSKY(442:10:C) # StarSize Y (arcsec)
OBCQ.SKY.SV.PIXDIF.X,OBCQSKY(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.SKY.SV.PIXDIF.Y,OBCQSKY(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.SKY.SV.SECDIF.RA,OBCQSKY(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.SKY.SV.SECDIF.DEC,OBCQSKY(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.SKY.PIXDIF.X,OBCQSKY(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.SKY.PIXDIF.Y,OBCQSKY(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.SKY.SECDIF.RA,OBCQSKY(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.SKY.SECDIF.DEC,OBCQSKY(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.SKY.BESTFOCUS,OBCQSKY(815:10:C) # BestFocus (mm)
OBCQ.SKY.FOCUSFLG,OBCQSKY(826:1:I) # Flag for BestFocus
OBCQ.SKY.OBE.PIXDIF,OBCQSKY(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.SKY.PIXRA,OBCQSKY(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.SKY.PIXDEC,OBCQSKY(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.SKY.PIXEQUINOX,OBCQSKY(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.SKY.RADEC_X,OBCQSKY(1199:10:C) # radectopix X (9999.9)
OBCQ.SKY.RADEC_Y,OBCQSKY(1210:10:C) # radectopix Y (9999.9)
OBCQ.SKY.SEEING.MEAN,OBCQSKY(1327:5:C) # Seeing mean value
OBCQ.SKY.SEEING.STDDEV,OBCQSKY(1333:5:C) # Seeing Standard deviation value
# for PI1
OBCQ.PI1.REGION.X1,OBCQPI1(175:4:C) # Region X1 (Pixcel)
OBCQ.PI1.REGION.Y1,OBCQPI1(180:4:C) # Region Y1 (Pixcel)
OBCQ.PI1.REGION.X2,OBCQPI1(185:4:C) # Region X2 (Pixcel)
OBCQ.PI1.REGION.Y2,OBCQPI1(190:4:C) # Region Y2 (Pixcel)
OBCQ.PI1.REGION.FWHM,OBCQPI1(195:10:C) # FWHM
OBCQ.PI1.REGION.BRIGHT,OBCQPI1(206:10:C) # Brightness
OBCQ.PI1.SN,OBCQPI1(303:10:C) # SN
OBCQ.PI1.STARSIZE.X,OBCQPI1(431:10:C) # StarSize X (arcsec)
OBCQ.PI1.STARSIZE.Y,OBCQPI1(442:10:C) # StarSize Y (arcsec)
OBCQ.PI1.SV.PIXDIF.X,OBCQPI1(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.PI1.SV.PIXDIF.Y,OBCQPI1(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.PI1.SV.SECDIF.RA,OBCQPI1(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.PI1.SV.SECDIF.DEC,OBCQPI1(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.PI1.PIXDIF.X,OBCQPI1(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.PI1.PIXDIF.Y,OBCQPI1(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.PI1.SECDIF.RA,OBCQPI1(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.PI1.SECDIF.DEC,OBCQPI1(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.PI1.BESTFOCUS,OBCQPI1(815:10:C) # BestFocus (mm)
OBCQ.PI1.FOCUSFLG,OBCQPI1(826:1:I) # Flag for BestFocus
OBCQ.PI1.OBE.PIXDIF,OBCQPI1(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.PI1.PIXRA,OBCQPI1(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.PI1.PIXDEC,OBCQPI1(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.PI1.PIXEQUINOX,OBCQPI1(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.PI1.RADEC_X,OBCQPI1(1199:10:C) # radectopix X (9999.9)
OBCQ.PI1.RADEC_Y,OBCQPI1(1210:10:C) # radectopix Y (9999.9)
OBCQ.PI1.SEEING.MEAN,OBCQPI1(1327:5:C) # Seeing mean value
OBCQ.PI1.SEEING.STDDEV,OBCQPI1(1333:5:C) # Seeing Standard deviation value
# for K3D
OBCQ.K3D.REGION.X1,OBCQK3D(175:4:C) # Region X1 (Pixcel)
OBCQ.K3D.REGION.Y1,OBCQK3D(180:4:C) # Region Y1 (Pixcel)
OBCQ.K3D.REGION.X2,OBCQK3D(185:4:C) # Region X2 (Pixcel)
OBCQ.K3D.REGION.Y2,OBCQK3D(190:4:C) # Region Y2 (Pixcel)
OBCQ.K3D.REGION.FWHM,OBCQK3D(195:10:C) # FWHM
OBCQ.K3D.REGION.BRIGHT,OBCQK3D(206:10:C) # Brightness
OBCQ.K3D.SN,OBCQK3D(303:10:C) # SN
OBCQ.K3D.STARSIZE.X,OBCQK3D(431:10:C) # StarSize X (arcsec)
OBCQ.K3D.STARSIZE.Y,OBCQK3D(442:10:C) # StarSize Y (arcsec)
OBCQ.K3D.SV.PIXDIF.X,OBCQK3D(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.K3D.SV.PIXDIF.Y,OBCQK3D(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.K3D.SV.SECDIF.RA,OBCQK3D(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.K3D.SV.SECDIF.DEC,OBCQK3D(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.K3D.PIXDIF.X,OBCQK3D(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.K3D.PIXDIF.Y,OBCQK3D(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.K3D.SECDIF.RA,OBCQK3D(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.K3D.SECDIF.DEC,OBCQK3D(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.K3D.BESTFOCUS,OBCQK3D(815:10:C) # BestFocus (mm)
OBCQ.K3D.FOCUSFLG,OBCQK3D(826:1:I) # Flag for BestFocus
OBCQ.K3D.OBE.PIXDIF,OBCQK3D(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.K3D.PIXRA,OBCQK3D(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.K3D.PIXDEC,OBCQK3D(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.K3D.PIXEQUINOX,OBCQK3D(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.K3D.RADEC_X,OBCQK3D(1199:10:C) # radectopix X (9999.9)
OBCQ.K3D.RADEC_Y,OBCQK3D(1210:10:C) # radectopix Y (9999.9)
OBCQ.K3D.SEEING.MEAN,OBCQK3D(1327:5:C) # Seeing mean value
OBCQ.K3D.SEEING.STDDEV,OBCQK3D(1333:5:C) # Seeing Standard deviation value
# for OTHER16
OBCQ.O16.REGION.X1,OBCQO16(175:4:C) # Region X1 (Pixcel)
OBCQ.O16.REGION.Y1,OBCQO16(180:4:C) # Region Y1 (Pixcel)
OBCQ.O16.REGION.X2,OBCQO16(185:4:C) # Region X2 (Pixcel)
OBCQ.O16.REGION.Y2,OBCQO16(190:4:C) # Region Y2 (Pixcel)
OBCQ.O16.REGION.FWHM,OBCQO16(195:10:C) # FWHM
OBCQ.O16.REGION.BRIGHT,OBCQO16(206:10:C) # Brightness
OBCQ.O16.SN,OBCQO16(303:10:C) # SN
OBCQ.O16.STARSIZE.X,OBCQO16(431:10:C) # StarSize X (arcsec)
OBCQ.O16.STARSIZE.Y,OBCQO16(442:10:C) # StarSize Y (arcsec)
OBCQ.O16.SV.PIXDIF.X,OBCQO16(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.O16.SV.PIXDIF.Y,OBCQO16(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.O16.SV.SECDIF.RA,OBCQO16(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.O16.SV.SECDIF.DEC,OBCQO16(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.O16.PIXDIF.X,OBCQO16(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.O16.PIXDIF.Y,OBCQO16(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.O16.SECDIF.RA,OBCQO16(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.O16.SECDIF.DEC,OBCQO16(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.O16.BESTFOCUS,OBCQO16(815:10:C) # BestFocus (mm)
OBCQ.O16.FOCUSFLG,OBCQO16(826:1:I) # Flag for BestFocus
OBCQ.O16.OBE.PIXDIF,OBCQO16(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.O16.PIXRA,OBCQO16(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.O16.PIXDEC,OBCQO16(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.O16.PIXEQUINOX,OBCQO16(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.O16.RADEC_X,OBCQO16(1199:10:C) # radectopix X (9999.9)
OBCQ.O16.RADEC_Y,OBCQO16(1210:10:C) # radectopix Y (9999.9)
OBCQ.O16.SEEING.MEAN,OBCQO16(1327:5:C) # Seeing mean value
OBCQ.O16.SEEING.STDDEV,OBCQO16(1333:5:C) # Seeing Standard deviation value
# for MOIRCS
OBCQ.MCS.REGION.X1,OBCQMCS(175:4:C) # Region X1 (Pixcel)
OBCQ.MCS.REGION.Y1,OBCQMCS(180:4:C) # Region Y1 (Pixcel)
OBCQ.MCS.REGION.X2,OBCQMCS(185:4:C) # Region X2 (Pixcel)
OBCQ.MCS.REGION.Y2,OBCQMCS(190:4:C) # Region Y2 (Pixcel)
OBCQ.MCS.REGION.FWHM,OBCQMCS(195:10:C) # FWHM
OBCQ.MCS.REGION.BRIGHT,OBCQMCS(206:10:C) # Brightness
OBCQ.MCS.SN,OBCQMCS(303:10:C) # SN
OBCQ.MCS.STARSIZE.X,OBCQMCS(431:10:C) # StarSize X (arcsec)
OBCQ.MCS.STARSIZE.Y,OBCQMCS(442:10:C) # StarSize Y (arcsec)
OBCQ.MCS.SV.PIXDIF.X,OBCQMCS(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.MCS.SV.PIXDIF.Y,OBCQMCS(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.MCS.SV.SECDIF.RA,OBCQMCS(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.MCS.SV.SECDIF.DEC,OBCQMCS(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.MCS.PIXDIF.X,OBCQMCS(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.MCS.PIXDIF.Y,OBCQMCS(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.MCS.SECDIF.RA,OBCQMCS(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.MCS.SECDIF.DEC,OBCQMCS(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.MCS.BESTFOCUS,OBCQMCS(815:10:C) # BestFocus (mm)
OBCQ.MCS.FOCUSFLG,OBCQMCS(826:1:I) # Flag for BestFocus
OBCQ.MCS.OBE.PIXDIF,OBCQMCS(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.MCS.PIXRA,OBCQMCS(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.MCS.PIXDEC,OBCQMCS(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.MCS.PIXEQUINOX,OBCQMCS(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.MCS.RADEC_X,OBCQMCS(1199:10:C) # radectopix X (9999.9)
OBCQ.MCS.RADEC_Y,OBCQMCS(1210:10:C) # radectopix Y (9999.9)
OBCQ.MCS.SEEING.MEAN,OBCQMCS(1327:5:C) # Seeing mean value
OBCQ.MCS.SEEING.STDDEV,OBCQMCS(1333:5:C) # Seeing Standard deviation value
# for FMOS
OBCQ.FMS.REGION.X1,OBCQFMS(175:4:C) # Region X1 (Pixcel)
OBCQ.FMS.REGION.Y1,OBCQFMS(180:4:C) # Region Y1 (Pixcel)
OBCQ.FMS.REGION.X2,OBCQFMS(185:4:C) # Region X2 (Pixcel)
OBCQ.FMS.REGION.Y2,OBCQFMS(190:4:C) # Region Y2 (Pixcel)
OBCQ.FMS.REGION.FWHM,OBCQFMS(195:10:C) # FWHM
OBCQ.FMS.REGION.BRIGHT,OBCQFMS(206:10:C) # Brightness
OBCQ.FMS.SN,OBCQFMS(303:10:C) # SN
OBCQ.FMS.STARSIZE.X,OBCQFMS(431:10:C) # StarSize X (arcsec)
OBCQ.FMS.STARSIZE.Y,OBCQFMS(442:10:C) # StarSize Y (arcsec)
OBCQ.FMS.SV.PIXDIF.X,OBCQFMS(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.FMS.SV.PIXDIF.Y,OBCQFMS(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.FMS.SV.SECDIF.RA,OBCQFMS(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.FMS.SV.SECDIF.DEC,OBCQFMS(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.FMS.PIXDIF.X,OBCQFMS(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.FMS.PIXDIF.Y,OBCQFMS(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.FMS.SECDIF.RA,OBCQFMS(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.FMS.SECDIF.DEC,OBCQFMS(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.FMS.BESTFOCUS,OBCQFMS(815:10:C) # BestFocus (mm)
OBCQ.FMS.FOCUSFLG,OBCQFMS(826:1:I) # Flag for BestFocus
OBCQ.FMS.OBE.PIXDIF,OBCQFMS(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.FMS.PIXRA,OBCQFMS(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.FMS.PIXDEC,OBCQFMS(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.FMS.PIXEQUINOX,OBCQFMS(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.FMS.RADEC_X,OBCQFMS(1199:10:C) # radectopix X (9999.9)
OBCQ.FMS.RADEC_Y,OBCQFMS(1210:10:C) # radectopix Y (9999.9)
OBCQ.FMS.SEEING.MEAN,OBCQFMS(1327:5:C) # Seeing mean value
OBCQ.FMS.SEEING.STDDEV,OBCQFMS(1333:5:C) # Seeing Standard deviation value
# for FLDMON
OBCQ.FLD.REGION.X1,OBCQFLD(175:4:C) # Region X1 (Pixcel)
OBCQ.FLD.REGION.Y1,OBCQFLD(180:4:C) # Region Y1 (Pixcel)
OBCQ.FLD.REGION.X2,OBCQFLD(185:4:C) # Region X2 (Pixcel)
OBCQ.FLD.REGION.Y2,OBCQFLD(190:4:C) # Region Y2 (Pixcel)
OBCQ.FLD.REGION.FWHM,OBCQFLD(195:10:C) # FWHM
OBCQ.FLD.REGION.BRIGHT,OBCQFLD(206:10:C) # Brightness
OBCQ.FLD.SN,OBCQFLD(303:10:C) # SN
OBCQ.FLD.STARSIZE.X,OBCQFLD(431:10:C) # StarSize X (arcsec)
OBCQ.FLD.STARSIZE.Y,OBCQFLD(442:10:C) # StarSize Y (arcsec)
OBCQ.FLD.SV.PIXDIF.X,OBCQFLD(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.FLD.SV.PIXDIF.Y,OBCQFLD(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.FLD.SV.SECDIF.RA,OBCQFLD(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.FLD.SV.SECDIF.DEC,OBCQFLD(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.FLD.PIXDIF.X,OBCQFLD(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.FLD.PIXDIF.Y,OBCQFLD(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.FLD.SECDIF.RA,OBCQFLD(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.FLD.SECDIF.DEC,OBCQFLD(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.FLD.BESTFOCUS,OBCQFLD(815:10:C) # BestFocus (mm)
OBCQ.FLD.FOCUSFLG,OBCQFLD(826:1:I) # Flag for BestFocus
OBCQ.FLD.OBE.PIXDIF,OBCQFLD(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.FLD.PIXRA,OBCQFLD(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.FLD.PIXDEC,OBCQFLD(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.FLD.PIXEQUINOX,OBCQFLD(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.FLD.RADEC_X,OBCQFLD(1199:10:C) # radectopix X (9999.9)
OBCQ.FLD.RADEC_Y,OBCQFLD(1210:10:C) # radectopix Y (9999.9)
OBCQ.FLD.SEEING.MEAN,OBCQFLD(1327:5:C) # Seeing mean value
OBCQ.FLD.SEEING.STDDEV,OBCQFLD(1333:5:C) # Seeing Standard deviation value
# for AO188
OBCQ.AON.REGION.X1,OBCQAON(175:4:C) # Region X1 (Pixcel)
OBCQ.AON.REGION.Y1,OBCQAON(180:4:C) # Region Y1 (Pixcel)
OBCQ.AON.REGION.X2,OBCQAON(185:4:C) # Region X2 (Pixcel)
OBCQ.AON.REGION.Y2,OBCQAON(190:4:C) # Region Y2 (Pixcel)
OBCQ.AON.REGION.FWHM,OBCQAON(195:10:C) # FWHM
OBCQ.AON.REGION.BRIGHT,OBCQAON(206:10:C) # Brightness
OBCQ.AON.SN,OBCQAON(303:10:C) # SN
OBCQ.AON.STARSIZE.X,OBCQAON(431:10:C) # StarSize X (arcsec)
OBCQ.AON.STARSIZE.Y,OBCQAON(442:10:C) # StarSize Y (arcsec)
OBCQ.AON.SV.PIXDIF.X,OBCQAON(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.AON.SV.PIXDIF.Y,OBCQAON(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.AON.SV.SECDIF.RA,OBCQAON(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.AON.SV.SECDIF.DEC,OBCQAON(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.AON.PIXDIF.X,OBCQAON(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.AON.PIXDIF.Y,OBCQAON(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.AON.SECDIF.RA,OBCQAON(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.AON.SECDIF.DEC,OBCQAON(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.AON.BESTFOCUS,OBCQAON(815:10:C) # BestFocus (mm)
OBCQ.AON.FOCUSFLG,OBCQAON(826:1:I) # Flag for BestFocus
OBCQ.AON.OBE.PIXDIF,OBCQAON(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.AON.PIXRA,OBCQAON(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.AON.PIXDEC,OBCQAON(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.AON.PIXEQUINOX,OBCQAON(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.AON.RADEC_X,OBCQAON(1199:10:C) # radectopix X (9999.9)
OBCQ.AON.RADEC_Y,OBCQAON(1210:10:C) # radectopix Y (9999.9)
OBCQ.AON.SEEING.MEAN,OBCQAON(1327:5:C) # Seeing mean value
OBCQ.AON.SEEING.STDDEV,OBCQAON(1333:5:C) # Seeing Standard deviation value
# for HICIAO
OBCQ.HIC.REGION.X1,OBCQHIC(175:4:C) # Region X1 (Pixcel)
OBCQ.HIC.REGION.Y1,OBCQHIC(180:4:C) # Region Y1 (Pixcel)
OBCQ.HIC.REGION.X2,OBCQHIC(185:4:C) # Region X2 (Pixcel)
OBCQ.HIC.REGION.Y2,OBCQHIC(190:4:C) # Region Y2 (Pixcel)
OBCQ.HIC.REGION.FWHM,OBCQHIC(195:10:C) # FWHM
OBCQ.HIC.REGION.BRIGHT,OBCQHIC(206:10:C) # Brightness
OBCQ.HIC.SN,OBCQHIC(303:10:C) # SN
OBCQ.HIC.STARSIZE.X,OBCQHIC(431:10:C) # StarSize X (arcsec)
OBCQ.HIC.STARSIZE.Y,OBCQHIC(442:10:C) # StarSize Y (arcsec)
OBCQ.HIC.SV.PIXDIF.X,OBCQHIC(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.HIC.SV.PIXDIF.Y,OBCQHIC(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.HIC.SV.SECDIF.RA,OBCQHIC(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.HIC.SV.SECDIF.DEC,OBCQHIC(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.HIC.PIXDIF.X,OBCQHIC(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.HIC.PIXDIF.Y,OBCQHIC(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.HIC.SECDIF.RA,OBCQHIC(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.HIC.SECDIF.DEC,OBCQHIC(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.HIC.BESTFOCUS,OBCQHIC(815:10:C) # BestFocus (mm)
OBCQ.HIC.FOCUSFLG,OBCQHIC(826:1:I) # Flag for BestFocus
OBCQ.HIC.OBE.PIXDIF,OBCQHIC(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.HIC.PIXRA,OBCQHIC(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.HIC.PIXDEC,OBCQHIC(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.HIC.PIXEQUINOX,OBCQHIC(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.HIC.RADEC_X,OBCQHIC(1199:10:C) # radectopix X (9999.9)
OBCQ.HIC.RADEC_Y,OBCQHIC(1210:10:C) # radectopix Y (9999.9)
OBCQ.HIC.SEEING.MEAN,OBCQHIC(1327:5:C) # Seeing mean value
OBCQ.HIC.SEEING.STDDEV,OBCQHIC(1333:5:C) # Seeing Standard deviation value
# for WAVEPLATE
OBCQ.WAV.REGION.X1,OBCQWAV(175:4:C) # Region X1 (Pixcel)
OBCQ.WAV.REGION.Y1,OBCQWAV(180:4:C) # Region Y1 (Pixcel)
OBCQ.WAV.REGION.X2,OBCQWAV(185:4:C) # Region X2 (Pixcel)
OBCQ.WAV.REGION.Y2,OBCQWAV(190:4:C) # Region Y2 (Pixcel)
OBCQ.WAV.REGION.FWHM,OBCQWAV(195:10:C) # FWHM
OBCQ.WAV.REGION.BRIGHT,OBCQWAV(206:10:C) # Brightness
OBCQ.WAV.SN,OBCQWAV(303:10:C) # SN
OBCQ.WAV.STARSIZE.X,OBCQWAV(431:10:C) # StarSize X (arcsec)
OBCQ.WAV.STARSIZE.Y,OBCQWAV(442:10:C) # StarSize Y (arcsec)
OBCQ.WAV.SV.PIXDIF.X,OBCQWAV(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.WAV.SV.PIXDIF.Y,OBCQWAV(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.WAV.SV.SECDIF.RA,OBCQWAV(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.WAV.SV.SECDIF.DEC,OBCQWAV(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.WAV.PIXDIF.X,OBCQWAV(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.WAV.PIXDIF.Y,OBCQWAV(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.WAV.SECDIF.RA,OBCQWAV(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.WAV.SECDIF.DEC,OBCQWAV(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.WAV.BESTFOCUS,OBCQWAV(815:10:C) # BestFocus (mm)
OBCQ.WAV.FOCUSFLG,OBCQWAV(826:1:I) # Flag for BestFocus
OBCQ.WAV.OBE.PIXDIF,OBCQWAV(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.WAV.PIXRA,OBCQWAV(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.WAV.PIXDEC,OBCQWAV(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.WAV.PIXEQUINOX,OBCQWAV(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.WAV.RADEC_X,OBCQWAV(1199:10:C) # radectopix X (9999.9)
OBCQ.WAV.RADEC_Y,OBCQWAV(1210:10:C) # radectopix Y (9999.9)
OBCQ.WAV.SEEING.MEAN,OBCQWAV(1327:5:C) # Seeing mean value
OBCQ.WAV.SEEING.STDDEV,OBCQWAV(1333:5:C) # Seeing Standard deviation value
# for LGS
OBCQ.LGS.REGION.X1,OBCQLGS(175:4:C) # Region X1 (Pixcel)
OBCQ.LGS.REGION.Y1,OBCQLGS(180:4:C) # Region Y1 (Pixcel)
OBCQ.LGS.REGION.X2,OBCQLGS(185:4:C) # Region X2 (Pixcel)
OBCQ.LGS.REGION.Y2,OBCQLGS(190:4:C) # Region Y2 (Pixcel)
OBCQ.LGS.REGION.FWHM,OBCQLGS(195:10:C) # FWHM
OBCQ.LGS.REGION.BRIGHT,OBCQLGS(206:10:C) # Brightness
OBCQ.LGS.SN,OBCQLGS(303:10:C) # SN
OBCQ.LGS.STARSIZE.X,OBCQLGS(431:10:C) # StarSize X (arcsec)
OBCQ.LGS.STARSIZE.Y,OBCQLGS(442:10:C) # StarSize Y (arcsec)
OBCQ.LGS.SV.PIXDIF.X,OBCQLGS(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.LGS.SV.PIXDIF.Y,OBCQLGS(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.LGS.SV.SECDIF.RA,OBCQLGS(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.LGS.SV.SECDIF.DEC,OBCQLGS(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.LGS.PIXDIF.X,OBCQLGS(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.LGS.PIXDIF.Y,OBCQLGS(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.LGS.SECDIF.RA,OBCQLGS(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.LGS.SECDIF.DEC,OBCQLGS(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.LGS.BESTFOCUS,OBCQLGS(815:10:C) # BestFocus (mm)
OBCQ.LGS.FOCUSFLG,OBCQLGS(826:1:I) # Flag for BestFocus
OBCQ.LGS.OBE.PIXDIF,OBCQLGS(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.LGS.PIXRA,OBCQLGS(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.LGS.PIXDEC,OBCQLGS(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.LGS.PIXEQUINOX,OBCQLGS(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.LGS.RADEC_X,OBCQLGS(1199:10:C) # radectopix X (9999.9)
OBCQ.LGS.RADEC_Y,OBCQLGS(1210:10:C) # radectopix Y (9999.9)
OBCQ.LGS.SEEING.MEAN,OBCQLGS(1327:5:C) # Seeing mean value
OBCQ.LGS.SEEING.STDDEV,OBCQLGS(1333:5:C) # Seeing Standard deviation value
# for OTHER24
OBCQ.O24.REGION.X1,OBCQO24(175:4:C) # Region X1 (Pixcel)
OBCQ.O24.REGION.Y1,OBCQO24(180:4:C) # Region Y1 (Pixcel)
OBCQ.O24.REGION.X2,OBCQO24(185:4:C) # Region X2 (Pixcel)
OBCQ.O24.REGION.Y2,OBCQO24(190:4:C) # Region Y2 (Pixcel)
OBCQ.O24.REGION.FWHM,OBCQO24(195:10:C) # FWHM
OBCQ.O24.REGION.BRIGHT,OBCQO24(206:10:C) # Brightness
OBCQ.O24.SN,OBCQO24(303:10:C) # SN
OBCQ.O24.STARSIZE.X,OBCQO24(431:10:C) # StarSize X (arcsec)
OBCQ.O24.STARSIZE.Y,OBCQO24(442:10:C) # StarSize Y (arcsec)
OBCQ.O24.SV.PIXDIF.X,OBCQO24(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.O24.SV.PIXDIF.Y,OBCQO24(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.O24.SV.SECDIF.RA,OBCQO24(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.O24.SV.SECDIF.DEC,OBCQO24(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.O24.PIXDIF.X,OBCQO24(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.O24.PIXDIF.Y,OBCQO24(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.O24.SECDIF.RA,OBCQO24(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.O24.SECDIF.DEC,OBCQO24(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.O24.BESTFOCUS,OBCQO24(815:10:C) # BestFocus (mm)
OBCQ.O24.FOCUSFLG,OBCQO24(826:1:I) # Flag for BestFocus
OBCQ.O24.OBE.PIXDIF,OBCQO24(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.O24.PIXRA,OBCQO24(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.O24.PIXDEC,OBCQO24(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.O24.PIXEQUINOX,OBCQO24(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.O24.RADEC_X,OBCQO24(1199:10:C) # radectopix X (9999.9)
OBCQ.O24.RADEC_Y,OBCQO24(1210:10:C) # radectopix Y (9999.9)
OBCQ.O24.SEEING.MEAN,OBCQO24(1327:5:C) # Seeing mean value
OBCQ.O24.SEEING.STDDEV,OBCQO24(1333:5:C) # Seeing Standard deviation value
# for OTHER25
OBCQ.O25.REGION.X1,OBCQO25(175:4:C) # Region X1 (Pixcel)
OBCQ.O25.REGION.Y1,OBCQO25(180:4:C) # Region Y1 (Pixcel)
OBCQ.O25.REGION.X2,OBCQO25(185:4:C) # Region X2 (Pixcel)
OBCQ.O25.REGION.Y2,OBCQO25(190:4:C) # Region Y2 (Pixcel)
OBCQ.O25.REGION.FWHM,OBCQO25(195:10:C) # FWHM
OBCQ.O25.REGION.BRIGHT,OBCQO25(206:10:C) # Brightness
OBCQ.O25.SN,OBCQO25(303:10:C) # SN
OBCQ.O25.STARSIZE.X,OBCQO25(431:10:C) # StarSize X (arcsec)
OBCQ.O25.STARSIZE.Y,OBCQO25(442:10:C) # StarSize Y (arcsec)
OBCQ.O25.SV.PIXDIF.X,OBCQO25(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.O25.SV.PIXDIF.Y,OBCQO25(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.O25.SV.SECDIF.RA,OBCQO25(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.O25.SV.SECDIF.DEC,OBCQO25(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.O25.PIXDIF.X,OBCQO25(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.O25.PIXDIF.Y,OBCQO25(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.O25.SECDIF.RA,OBCQO25(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.O25.SECDIF.DEC,OBCQO25(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.O25.BESTFOCUS,OBCQO25(815:10:C) # BestFocus (mm)
OBCQ.O25.FOCUSFLG,OBCQO25(826:1:I) # Flag for BestFocus
OBCQ.O25.OBE.PIXDIF,OBCQO25(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.O25.PIXRA,OBCQO25(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.O25.PIXDEC,OBCQO25(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.O25.PIXEQUINOX,OBCQO25(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.O25.RADEC_X,OBCQO25(1199:10:C) # radectopix X (9999.9)
OBCQ.O25.RADEC_Y,OBCQO25(1210:10:C) # radectopix Y (9999.9)
OBCQ.O25.SEEING.MEAN,OBCQO25(1327:5:C) # Seeing mean value
OBCQ.O25.SEEING.STDDEV,OBCQO25(1333:5:C) # Seeing Standard deviation value
# for OTHER26
OBCQ.O26.REGION.X1,OBCQO26(175:4:C) # Region X1 (Pixcel)
OBCQ.O26.REGION.Y1,OBCQO26(180:4:C) # Region Y1 (Pixcel)
OBCQ.O26.REGION.X2,OBCQO26(185:4:C) # Region X2 (Pixcel)
OBCQ.O26.REGION.Y2,OBCQO26(190:4:C) # Region Y2 (Pixcel)
OBCQ.O26.REGION.FWHM,OBCQO26(195:10:C) # FWHM
OBCQ.O26.REGION.BRIGHT,OBCQO26(206:10:C) # Brightness
OBCQ.O26.SN,OBCQO26(303:10:C) # SN
OBCQ.O26.STARSIZE.X,OBCQO26(431:10:C) # StarSize X (arcsec)
OBCQ.O26.STARSIZE.Y,OBCQO26(442:10:C) # StarSize Y (arcsec)
OBCQ.O26.SV.PIXDIF.X,OBCQO26(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.O26.SV.PIXDIF.Y,OBCQO26(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.O26.SV.SECDIF.RA,OBCQO26(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.O26.SV.SECDIF.DEC,OBCQO26(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.O26.PIXDIF.X,OBCQO26(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.O26.PIXDIF.Y,OBCQO26(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.O26.SECDIF.RA,OBCQO26(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.O26.SECDIF.DEC,OBCQO26(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.O26.BESTFOCUS,OBCQO26(815:10:C) # BestFocus (mm)
OBCQ.O26.FOCUSFLG,OBCQO26(826:1:I) # Flag for BestFocus
OBCQ.O26.OBE.PIXDIF,OBCQO26(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.O26.PIXRA,OBCQO26(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.O26.PIXDEC,OBCQO26(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.O26.PIXEQUINOX,OBCQO26(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.O26.RADEC_X,OBCQO26(1199:10:C) # radectopix X (9999.9)
OBCQ.O26.RADEC_Y,OBCQO26(1210:10:C) # radectopix Y (9999.9)
OBCQ.O26.SEEING.MEAN,OBCQO26(1327:5:C) # Seeing mean value
OBCQ.O26.SEEING.STDDEV,OBCQO26(1333:5:C) # Seeing Standard deviation value
# for OTHER27
OBCQ.O27.REGION.X1,OBCQO27(175:4:C) # Region X1 (Pixcel)
OBCQ.O27.REGION.Y1,OBCQO27(180:4:C) # Region Y1 (Pixcel)
OBCQ.O27.REGION.X2,OBCQO27(185:4:C) # Region X2 (Pixcel)
OBCQ.O27.REGION.Y2,OBCQO27(190:4:C) # Region Y2 (Pixcel)
OBCQ.O27.REGION.FWHM,OBCQO27(195:10:C) # FWHM
OBCQ.O27.REGION.BRIGHT,OBCQO27(206:10:C) # Brightness
OBCQ.O27.SN,OBCQO27(303:10:C) # SN
OBCQ.O27.STARSIZE.X,OBCQO27(431:10:C) # StarSize X (arcsec)
OBCQ.O27.STARSIZE.Y,OBCQO27(442:10:C) # StarSize Y (arcsec)
OBCQ.O27.SV.PIXDIF.X,OBCQO27(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.O27.SV.PIXDIF.Y,OBCQO27(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.O27.SV.SECDIF.RA,OBCQO27(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.O27.SV.SECDIF.DEC,OBCQO27(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.O27.PIXDIF.X,OBCQO27(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.O27.PIXDIF.Y,OBCQO27(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.O27.SECDIF.RA,OBCQO27(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.O27.SECDIF.DEC,OBCQO27(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.O27.BESTFOCUS,OBCQO27(815:10:C) # BestFocus (mm)
OBCQ.O27.FOCUSFLG,OBCQO27(826:1:I) # Flag for BestFocus
OBCQ.O27.OBE.PIXDIF,OBCQO27(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.O27.PIXRA,OBCQO27(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.O27.PIXDEC,OBCQO27(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.O27.PIXEQUINOX,OBCQO27(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.O27.RADEC_X,OBCQO27(1199:10:C) # radectopix X (9999.9)
OBCQ.O27.RADEC_Y,OBCQO27(1210:10:C) # radectopix Y (9999.9)
OBCQ.O27.SEEING.MEAN,OBCQO27(1327:5:C) # Seeing mean value
OBCQ.O27.SEEING.STDDEV,OBCQO27(1333:5:C) # Seeing Standard deviation value
# for OTHER28
OBCQ.O28.REGION.X1,OBCQO28(175:4:C) # Region X1 (Pixcel)
OBCQ.O28.REGION.Y1,OBCQO28(180:4:C) # Region Y1 (Pixcel)
OBCQ.O28.REGION.X2,OBCQO28(185:4:C) # Region X2 (Pixcel)
OBCQ.O28.REGION.Y2,OBCQO28(190:4:C) # Region Y2 (Pixcel)
OBCQ.O28.REGION.FWHM,OBCQO28(195:10:C) # FWHM
OBCQ.O28.REGION.BRIGHT,OBCQO28(206:10:C) # Brightness
OBCQ.O28.SN,OBCQO28(303:10:C) # SN
OBCQ.O28.STARSIZE.X,OBCQO28(431:10:C) # StarSize X (arcsec)
OBCQ.O28.STARSIZE.Y,OBCQO28(442:10:C) # StarSize Y (arcsec)
OBCQ.O28.SV.PIXDIF.X,OBCQO28(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.O28.SV.PIXDIF.Y,OBCQO28(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.O28.SV.SECDIF.RA,OBCQO28(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.O28.SV.SECDIF.DEC,OBCQO28(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.O28.PIXDIF.X,OBCQO28(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.O28.PIXDIF.Y,OBCQO28(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.O28.SECDIF.RA,OBCQO28(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.O28.SECDIF.DEC,OBCQO28(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.O28.BESTFOCUS,OBCQO28(815:10:C) # BestFocus (mm)
OBCQ.O28.FOCUSFLG,OBCQO28(826:1:I) # Flag for BestFocus
OBCQ.O28.OBE.PIXDIF,OBCQO28(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.O28.PIXRA,OBCQO28(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.O28.PIXDEC,OBCQO28(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.O28.PIXEQUINOX,OBCQO28(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.O28.RADEC_X,OBCQO28(1199:10:C) # radectopix X (9999.9)
OBCQ.O28.RADEC_Y,OBCQO28(1210:10:C) # radectopix Y (9999.9)
OBCQ.O28.SEEING.MEAN,OBCQO28(1327:5:C) # Seeing mean value
OBCQ.O28.SEEING.STDDEV,OBCQO28(1333:5:C) # Seeing Standard deviation value
# for OTHER29
OBCQ.O29.REGION.X1,OBCQO29(175:4:C) # Region X1 (Pixcel)
OBCQ.O29.REGION.Y1,OBCQO29(180:4:C) # Region Y1 (Pixcel)
OBCQ.O29.REGION.X2,OBCQO29(185:4:C) # Region X2 (Pixcel)
OBCQ.O29.REGION.Y2,OBCQO29(190:4:C) # Region Y2 (Pixcel)
OBCQ.O29.REGION.FWHM,OBCQO29(195:10:C) # FWHM
OBCQ.O29.REGION.BRIGHT,OBCQO29(206:10:C) # Brightness
OBCQ.O29.SN,OBCQO29(303:10:C) # SN
OBCQ.O29.STARSIZE.X,OBCQO29(431:10:C) # StarSize X (arcsec)
OBCQ.O29.STARSIZE.Y,OBCQO29(442:10:C) # StarSize Y (arcsec)
OBCQ.O29.SV.PIXDIF.X,OBCQO29(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.O29.SV.PIXDIF.Y,OBCQO29(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.O29.SV.SECDIF.RA,OBCQO29(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.O29.SV.SECDIF.DEC,OBCQO29(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.O29.PIXDIF.X,OBCQO29(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.O29.PIXDIF.Y,OBCQO29(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.O29.SECDIF.RA,OBCQO29(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.O29.SECDIF.DEC,OBCQO29(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.O29.BESTFOCUS,OBCQO29(815:10:C) # BestFocus (mm)
OBCQ.O29.FOCUSFLG,OBCQO29(826:1:I) # Flag for BestFocus
OBCQ.O29.OBE.PIXDIF,OBCQO29(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.O29.PIXRA,OBCQO29(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.O29.PIXDEC,OBCQO29(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.O29.PIXEQUINOX,OBCQO29(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.O29.RADEC_X,OBCQO29(1199:10:C) # radectopix X (9999.9)
OBCQ.O29.RADEC_Y,OBCQO29(1210:10:C) # radectopix Y (9999.9)
OBCQ.O29.SEEING.MEAN,OBCQO29(1327:5:C) # Seeing mean value
OBCQ.O29.SEEING.STDDEV,OBCQO29(1333:5:C) # Seeing Standard deviation value
# for OTHER30
OBCQ.O30.REGION.X1,OBCQO30(175:4:C) # Region X1 (Pixcel)
OBCQ.O30.REGION.Y1,OBCQO30(180:4:C) # Region Y1 (Pixcel)
OBCQ.O30.REGION.X2,OBCQO30(185:4:C) # Region X2 (Pixcel)
OBCQ.O30.REGION.Y2,OBCQO30(190:4:C) # Region Y2 (Pixcel)
OBCQ.O30.REGION.FWHM,OBCQO30(195:10:C) # FWHM
OBCQ.O30.REGION.BRIGHT,OBCQO30(206:10:C) # Brightness
OBCQ.O30.SN,OBCQO30(303:10:C) # SN
OBCQ.O30.STARSIZE.X,OBCQO30(431:10:C) # StarSize X (arcsec)
OBCQ.O30.STARSIZE.Y,OBCQO30(442:10:C) # StarSize Y (arcsec)
OBCQ.O30.SV.PIXDIF.X,OBCQO30(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.O30.SV.PIXDIF.Y,OBCQO30(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.O30.SV.SECDIF.RA,OBCQO30(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.O30.SV.SECDIF.DEC,OBCQO30(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.O30.PIXDIF.X,OBCQO30(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.O30.PIXDIF.Y,OBCQO30(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.O30.SECDIF.RA,OBCQO30(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.O30.SECDIF.DEC,OBCQO30(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.O30.BESTFOCUS,OBCQO30(815:10:C) # BestFocus (mm)
OBCQ.O30.FOCUSFLG,OBCQO30(826:1:I) # Flag for BestFocus
OBCQ.O30.OBE.PIXDIF,OBCQO30(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.O30.PIXRA,OBCQO30(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.O30.PIXDEC,OBCQO30(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.O30.PIXEQUINOX,OBCQO30(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.O30.RADEC_X,OBCQO30(1199:10:C) # radectopix X (9999.9)
OBCQ.O30.RADEC_Y,OBCQO30(1210:10:C) # radectopix Y (9999.9)
OBCQ.O30.SEEING.MEAN,OBCQO30(1327:5:C) # Seeing mean value
OBCQ.O30.SEEING.STDDEV,OBCQO30(1333:5:C) # Seeing Standard deviation value
# for OTHER31
OBCQ.O31.REGION.X1,OBCQO31(175:4:C) # Region X1 (Pixcel)
OBCQ.O31.REGION.Y1,OBCQO31(180:4:C) # Region Y1 (Pixcel)
OBCQ.O31.REGION.X2,OBCQO31(185:4:C) # Region X2 (Pixcel)
OBCQ.O31.REGION.Y2,OBCQO31(190:4:C) # Region Y2 (Pixcel)
OBCQ.O31.REGION.FWHM,OBCQO31(195:10:C) # FWHM
OBCQ.O31.REGION.BRIGHT,OBCQO31(206:10:C) # Brightness
OBCQ.O31.SN,OBCQO31(303:10:C) # SN
OBCQ.O31.STARSIZE.X,OBCQO31(431:10:C) # StarSize X (arcsec)
OBCQ.O31.STARSIZE.Y,OBCQO31(442:10:C) # StarSize Y (arcsec)
OBCQ.O31.SV.PIXDIF.X,OBCQO31(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.O31.SV.PIXDIF.Y,OBCQO31(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.O31.SV.SECDIF.RA,OBCQO31(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.O31.SV.SECDIF.DEC,OBCQO31(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.O31.PIXDIF.X,OBCQO31(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.O31.PIXDIF.Y,OBCQO31(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.O31.SECDIF.RA,OBCQO31(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.O31.SECDIF.DEC,OBCQO31(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.O31.BESTFOCUS,OBCQO31(815:10:C) # BestFocus (mm)
OBCQ.O31.FOCUSFLG,OBCQO31(826:1:I) # Flag for BestFocus
OBCQ.O31.OBE.PIXDIF,OBCQO31(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.O31.PIXRA,OBCQO31(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.O31.PIXDEC,OBCQO31(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.O31.PIXEQUINOX,OBCQO31(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.O31.RADEC_X,OBCQO31(1199:10:C) # radectopix X (9999.9)
OBCQ.O31.RADEC_Y,OBCQO31(1210:10:C) # radectopix Y (9999.9)
OBCQ.O31.SEEING.MEAN,OBCQO31(1327:5:C) # Seeing mean value
OBCQ.O31.SEEING.STDDEV,OBCQO31(1333:5:C) # Seeing Standard deviation value
# for OTHER32
OBCQ.O32.REGION.X1,OBCQO32(175:4:C) # Region X1 (Pixcel)
OBCQ.O32.REGION.Y1,OBCQO32(180:4:C) # Region Y1 (Pixcel)
OBCQ.O32.REGION.X2,OBCQO32(185:4:C) # Region X2 (Pixcel)
OBCQ.O32.REGION.Y2,OBCQO32(190:4:C) # Region Y2 (Pixcel)
OBCQ.O32.REGION.FWHM,OBCQO32(195:10:C) # FWHM
OBCQ.O32.REGION.BRIGHT,OBCQO32(206:10:C) # Brightness
OBCQ.O32.SN,OBCQO32(303:10:C) # SN
OBCQ.O32.STARSIZE.X,OBCQO32(431:10:C) # StarSize X (arcsec)
OBCQ.O32.STARSIZE.Y,OBCQO32(442:10:C) # StarSize Y (arcsec)
OBCQ.O32.SV.PIXDIF.X,OBCQO32(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.O32.SV.PIXDIF.Y,OBCQO32(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.O32.SV.SECDIF.RA,OBCQO32(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.O32.SV.SECDIF.DEC,OBCQO32(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.O32.PIXDIF.X,OBCQO32(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.O32.PIXDIF.Y,OBCQO32(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.O32.SECDIF.RA,OBCQO32(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.O32.SECDIF.DEC,OBCQO32(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.O32.BESTFOCUS,OBCQO32(815:10:C) # BestFocus (mm)
OBCQ.O32.FOCUSFLG,OBCQO32(826:1:I) # Flag for BestFocus
OBCQ.O32.OBE.PIXDIF,OBCQO32(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.O32.PIXRA,OBCQO32(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.O32.PIXDEC,OBCQO32(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.O32.PIXEQUINOX,OBCQO32(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.O32.RADEC_X,OBCQO32(1199:10:C) # radectopix X (9999.9)
OBCQ.O32.RADEC_Y,OBCQO32(1210:10:C) # radectopix Y (9999.9)
OBCQ.O32.SEEING.MEAN,OBCQO32(1327:5:C) # Seeing mean value
OBCQ.O32.SEEING.STDDEV,OBCQO32(1333:5:C) # Seeing Standard deviation value
# for VGW
OBCQ.VGW.REGION.X1,OBCQVGW(175:4:C) # Region X1 (Pixcel)
OBCQ.VGW.REGION.Y1,OBCQVGW(180:4:C) # Region Y1 (Pixcel)
OBCQ.VGW.REGION.X2,OBCQVGW(185:4:C) # Region X2 (Pixcel)
OBCQ.VGW.REGION.Y2,OBCQVGW(190:4:C) # Region Y2 (Pixcel)
OBCQ.VGW.REGION.FWHM,OBCQVGW(195:10:C) # FWHM
OBCQ.VGW.REGION.BRIGHT,OBCQVGW(206:10:C) # Brightness
OBCQ.VGW.SN,OBCQVGW(303:10:C) # SN
OBCQ.VGW.STARSIZE.X,OBCQVGW(431:10:C) # StarSize X (arcsec)
OBCQ.VGW.STARSIZE.Y,OBCQVGW(442:10:C) # StarSize Y (arcsec)
OBCQ.VGW.SV.PIXDIF.X,OBCQVGW(559:10:C) # SV Telemove PIXDIF.X (Pixcel)
OBCQ.VGW.SV.PIXDIF.Y,OBCQVGW(570:10:C) # SV Telemove PIXDIF.Y (Pixcel)
OBCQ.VGW.SV.SECDIF.RA,OBCQVGW(581:10:C) # SV Telemove SECDIF.RA (arcsec)
OBCQ.VGW.SV.SECDIF.DEC,OBCQVGW(592:10:C) # SV Telemove SECDIF.DEC (arcsec)
OBCQ.VGW.PIXDIF.X,OBCQVGW(687:10:C) # DI Telemove PIXDIF.X (Pixcel)
OBCQ.VGW.PIXDIF.Y,OBCQVGW(698:10:C) # DI Telemove PIXDIF.Y (Pixcel)
OBCQ.VGW.SECDIF.RA,OBCQVGW(709:10:C) # DI Telemove SECDIF.RA (arcsec)
OBCQ.VGW.SECDIF.DEC,OBCQVGW(720:10:C) # DI Telemove SECDIF.DEC (arcsec)
OBCQ.VGW.BESTFOCUS,OBCQVGW(815:10:C) # BestFocus (mm)
OBCQ.VGW.FOCUSFLG,OBCQVGW(826:1:I) # Flag for BestFocus
OBCQ.VGW.OBE.PIXDIF,OBCQVGW(943:10:C) # OBE Focus PIXDIF (Pixcel)
OBCQ.VGW.PIXRA,OBCQVGW(1071:10:C) # Pixtoradec RA (HHMMSS.SSS)
OBCQ.VGW.PIXDEC,OBCQVGW(1082:10:C) # Pixtoradec DEC (+DDMMSS.SS)
OBCQ.VGW.PIXEQUINOX,OBCQVGW(1093:6:C) # Pixtoradec EQUINOX (9999.9)
OBCQ.VGW.RADEC_X,OBCQVGW(1199:10:C) # radectopix X (9999.9)
OBCQ.VGW.RADEC_Y,OBCQVGW(1210:10:C) # radectopix Y (9999.9)
OBCQ.VGW.SEEING.MEAN,OBCQVGW(1327:5:C) # Seeing mean value
OBCQ.VGW.SEEING.STDDEV,OBCQVGW(1333:5:C) # Seeing Standard deviation value

# for ANA QDAS
# for IRCS
ANAQ.IRC.CONFIRMATION,ANAQIRC(146:4:C) # Confirmation
ANAQ.IRC.UI1,ANAQIRC(151:64:C) # UserInput 1
ANAQ.IRC.UI2,ANAQIRC(216:64:C) # UserInput 2
ANAQ.IRC.UI3,ANAQIRC(281:64:C) # UserInput 3
ANAQ.IRC.UI4,ANAQIRC(346:64:C) # UserInput 4
ANAQ.IRC.UI5,ANAQIRC(411:64:C) # UserInput 5
ANAQ.IRC.UI6,ANAQIRC(476:64:C) # UserInput 6
ANAQ.IRC.UI7,ANAQIRC(541:64:C) # UserInput 7
ANAQ.IRC.UI8,ANAQIRC(606:64:C) # UserInput 8
ANAQ.IRC.UI9,ANAQIRC(671:64:C) # UserInput 9
# for AOS
ANAQ.AOS.CONFIRMATION,ANAQAOS(146:4:C) # Confirmation
ANAQ.AOS.UI1,ANAQAOS(151:64:C) # UserInput 1
ANAQ.AOS.UI2,ANAQAOS(216:64:C) # UserInput 2
ANAQ.AOS.UI3,ANAQAOS(281:64:C) # UserInput 3
ANAQ.AOS.UI4,ANAQAOS(346:64:C) # UserInput 4
ANAQ.AOS.UI5,ANAQAOS(411:64:C) # UserInput 5
ANAQ.AOS.UI6,ANAQAOS(476:64:C) # UserInput 6
ANAQ.AOS.UI7,ANAQAOS(541:64:C) # UserInput 7
ANAQ.AOS.UI8,ANAQAOS(606:64:C) # UserInput 8
ANAQ.AOS.UI9,ANAQAOS(671:64:C) # UserInput 9
# for CIA
ANAQ.CIA.CONFIRMATION,ANAQCIA(146:4:C) # Confirmation
ANAQ.CIA.UI1,ANAQCIA(151:64:C) # UserInput 1
ANAQ.CIA.UI2,ANAQCIA(216:64:C) # UserInput 2
ANAQ.CIA.UI3,ANAQCIA(281:64:C) # UserInput 3
ANAQ.CIA.UI4,ANAQCIA(346:64:C) # UserInput 4
ANAQ.CIA.UI5,ANAQCIA(411:64:C) # UserInput 5
ANAQ.CIA.UI6,ANAQCIA(476:64:C) # UserInput 6
ANAQ.CIA.UI7,ANAQCIA(541:64:C) # UserInput 7
ANAQ.CIA.UI8,ANAQCIA(606:64:C) # UserInput 8
ANAQ.CIA.UI9,ANAQCIA(671:64:C) # UserInput 9
# for OHS
ANAQ.OHS.CONFIRMATION,ANAQOHS(146:4:C) # Confirmation
ANAQ.OHS.UI1,ANAQOHS(151:64:C) # UserInput 1
ANAQ.OHS.UI2,ANAQOHS(216:64:C) # UserInput 2
ANAQ.OHS.UI3,ANAQOHS(281:64:C) # UserInput 3
ANAQ.OHS.UI4,ANAQOHS(346:64:C) # UserInput 4
ANAQ.OHS.UI5,ANAQOHS(411:64:C) # UserInput 5
ANAQ.OHS.UI6,ANAQOHS(476:64:C) # UserInput 6
ANAQ.OHS.UI7,ANAQOHS(541:64:C) # UserInput 7
ANAQ.OHS.UI8,ANAQOHS(606:64:C) # UserInput 8
ANAQ.OHS.UI9,ANAQOHS(671:64:C) # UserInput 9
# for FCS
ANAQ.FCS.CONFIRMATION,ANAQFCS(146:4:C) # Confirmation
ANAQ.FCS.UI1,ANAQFCS(151:64:C) # UserInput 1
ANAQ.FCS.UI2,ANAQFCS(216:64:C) # UserInput 2
ANAQ.FCS.UI3,ANAQFCS(281:64:C) # UserInput 3
ANAQ.FCS.UI4,ANAQFCS(346:64:C) # UserInput 4
ANAQ.FCS.UI5,ANAQFCS(411:64:C) # UserInput 5
ANAQ.FCS.UI6,ANAQFCS(476:64:C) # UserInput 6
ANAQ.FCS.UI7,ANAQFCS(541:64:C) # UserInput 7
ANAQ.FCS.UI8,ANAQFCS(606:64:C) # UserInput 8
ANAQ.FCS.UI9,ANAQFCS(671:64:C) # UserInput 9
# for HDS
ANAQ.HDS.CONFIRMATION,ANAQHDS(146:4:C) # Confirmation
ANAQ.HDS.UI1,ANAQHDS(151:64:C) # UserInput 1
ANAQ.HDS.UI2,ANAQHDS(216:64:C) # UserInput 2
ANAQ.HDS.UI3,ANAQHDS(281:64:C) # UserInput 3
ANAQ.HDS.UI4,ANAQHDS(346:64:C) # UserInput 4
ANAQ.HDS.UI5,ANAQHDS(411:64:C) # UserInput 5
ANAQ.HDS.UI6,ANAQHDS(476:64:C) # UserInput 6
ANAQ.HDS.UI7,ANAQHDS(541:64:C) # UserInput 7
ANAQ.HDS.UI8,ANAQHDS(606:64:C) # UserInput 8
ANAQ.HDS.UI9,ANAQHDS(671:64:C) # UserInput 9
# for COM
ANAQ.COM.CONFIRMATION,ANAQCOM(146:4:C) # Confirmation
ANAQ.COM.UI1,ANAQCOM(151:64:C) # UserInput 1
ANAQ.COM.UI2,ANAQCOM(216:64:C) # UserInput 2
ANAQ.COM.UI3,ANAQCOM(281:64:C) # UserInput 3
ANAQ.COM.UI4,ANAQCOM(346:64:C) # UserInput 4
ANAQ.COM.UI5,ANAQCOM(411:64:C) # UserInput 5
ANAQ.COM.UI6,ANAQCOM(476:64:C) # UserInput 6
ANAQ.COM.UI7,ANAQCOM(541:64:C) # UserInput 7
ANAQ.COM.UI8,ANAQCOM(606:64:C) # UserInput 8
ANAQ.COM.UI9,ANAQCOM(671:64:C) # UserInput 9
# for SUP
ANAQ.SUP.CONFIRMATION,ANAQSUP(146:4:C) # Confirmation
ANAQ.SUP.UI1,ANAQSUP(151:64:C) # UserInput 1
ANAQ.SUP.UI2,ANAQSUP(216:64:C) # UserInput 2
ANAQ.SUP.UI3,ANAQSUP(281:64:C) # UserInput 3
ANAQ.SUP.UI4,ANAQSUP(346:64:C) # UserInput 4
ANAQ.SUP.UI5,ANAQSUP(411:64:C) # UserInput 5
ANAQ.SUP.UI6,ANAQSUP(476:64:C) # UserInput 6
ANAQ.SUP.UI7,ANAQSUP(541:64:C) # UserInput 7
ANAQ.SUP.UI8,ANAQSUP(606:64:C) # UserInput 8
ANAQ.SUP.UI9,ANAQSUP(671:64:C) # UserInput 9
# for SUK
ANAQ.SUK.CONFIRMATION,ANAQSUK(146:4:C) # Confirmation
ANAQ.SUK.UI1,ANAQSUK(151:64:C) # UserInput 1
ANAQ.SUK.UI2,ANAQSUK(216:64:C) # UserInput 2
ANAQ.SUK.UI3,ANAQSUK(281:64:C) # UserInput 3
ANAQ.SUK.UI4,ANAQSUK(346:64:C) # UserInput 4
ANAQ.SUK.UI5,ANAQSUK(411:64:C) # UserInput 5
ANAQ.SUK.UI6,ANAQSUK(476:64:C) # UserInput 6
ANAQ.SUK.UI7,ANAQSUK(541:64:C) # UserInput 7
ANAQ.SUK.UI8,ANAQSUK(606:64:C) # UserInput 8
ANAQ.SUK.UI9,ANAQSUK(671:64:C) # UserInput 9
# for MIR
ANAQ.MIR.CONFIRMATION,ANAQMIR(146:4:C) # Confirmation
ANAQ.MIR.UI1,ANAQMIR(151:64:C) # UserInput 1
ANAQ.MIR.UI2,ANAQMIR(216:64:C) # UserInput 2
ANAQ.MIR.UI3,ANAQMIR(281:64:C) # UserInput 3
ANAQ.MIR.UI4,ANAQMIR(346:64:C) # UserInput 4
ANAQ.MIR.UI5,ANAQMIR(411:64:C) # UserInput 5
ANAQ.MIR.UI6,ANAQMIR(476:64:C) # UserInput 6
ANAQ.MIR.UI7,ANAQMIR(541:64:C) # UserInput 7
ANAQ.MIR.UI8,ANAQMIR(606:64:C) # UserInput 8
ANAQ.MIR.UI9,ANAQMIR(671:64:C) # UserInput 9
# for VTO
ANAQ.VTO.CONFIRMATION,ANAQVTO(146:4:C) # Confirmation
ANAQ.VTO.UI1,ANAQVTO(151:64:C) # UserInput 1
ANAQ.VTO.UI2,ANAQVTO(216:64:C) # UserInput 2
ANAQ.VTO.UI3,ANAQVTO(281:64:C) # UserInput 3
ANAQ.VTO.UI4,ANAQVTO(346:64:C) # UserInput 4
ANAQ.VTO.UI5,ANAQVTO(411:64:C) # UserInput 5
ANAQ.VTO.UI6,ANAQVTO(476:64:C) # UserInput 6
ANAQ.VTO.UI7,ANAQVTO(541:64:C) # UserInput 7
ANAQ.VTO.UI8,ANAQVTO(606:64:C) # UserInput 8
ANAQ.VTO.UI9,ANAQVTO(671:64:C) # UserInput 9
# for CAC
ANAQ.CAC.CONFIRMATION,ANAQCAC(146:4:C) # Confirmation
ANAQ.CAC.UI1,ANAQCAC(151:64:C) # UserInput 1
ANAQ.CAC.UI2,ANAQCAC(216:64:C) # UserInput 2
ANAQ.CAC.UI3,ANAQCAC(281:64:C) # UserInput 3
ANAQ.CAC.UI4,ANAQCAC(346:64:C) # UserInput 4
ANAQ.CAC.UI5,ANAQCAC(411:64:C) # UserInput 5
ANAQ.CAC.UI6,ANAQCAC(476:64:C) # UserInput 6
ANAQ.CAC.UI7,ANAQCAC(541:64:C) # UserInput 7
ANAQ.CAC.UI8,ANAQCAC(606:64:C) # UserInput 8
ANAQ.CAC.UI9,ANAQCAC(671:64:C) # UserInput 9
# for SKY
ANAQ.SKY.CONFIRMATION,ANAQSKY(146:4:C) # Confirmation
ANAQ.SKY.UI1,ANAQSKY(151:64:C) # UserInput 1
ANAQ.SKY.UI2,ANAQSKY(216:64:C) # UserInput 2
ANAQ.SKY.UI3,ANAQSKY(281:64:C) # UserInput 3
ANAQ.SKY.UI4,ANAQSKY(346:64:C) # UserInput 4
ANAQ.SKY.UI5,ANAQSKY(411:64:C) # UserInput 5
ANAQ.SKY.UI6,ANAQSKY(476:64:C) # UserInput 6
ANAQ.SKY.UI7,ANAQSKY(541:64:C) # UserInput 7
ANAQ.SKY.UI8,ANAQSKY(606:64:C) # UserInput 8
ANAQ.SKY.UI9,ANAQSKY(671:64:C) # UserInput 9
# for PI1
ANAQ.PI1.CONFIRMATION,ANAQPI1(146:4:C) # Confirmation
ANAQ.PI1.UI1,ANAQPI1(151:64:C) # UserInput 1
ANAQ.PI1.UI2,ANAQPI1(216:64:C) # UserInput 2
ANAQ.PI1.UI3,ANAQPI1(281:64:C) # UserInput 3
ANAQ.PI1.UI4,ANAQPI1(346:64:C) # UserInput 4
ANAQ.PI1.UI5,ANAQPI1(411:64:C) # UserInput 5
ANAQ.PI1.UI6,ANAQPI1(476:64:C) # UserInput 6
ANAQ.PI1.UI7,ANAQPI1(541:64:C) # UserInput 7
ANAQ.PI1.UI8,ANAQPI1(606:64:C) # UserInput 8
ANAQ.PI1.UI9,ANAQPI1(671:64:C) # UserInput 9
# for K3D
ANAQ.K3D.CONFIRMATION,ANAQK3D(146:4:C) # Confirmation
ANAQ.K3D.UI1,ANAQK3D(151:64:C) # UserInput 1
ANAQ.K3D.UI2,ANAQK3D(216:64:C) # UserInput 2
ANAQ.K3D.UI3,ANAQK3D(281:64:C) # UserInput 3
ANAQ.K3D.UI4,ANAQK3D(346:64:C) # UserInput 4
ANAQ.K3D.UI5,ANAQK3D(411:64:C) # UserInput 5
ANAQ.K3D.UI6,ANAQK3D(476:64:C) # UserInput 6
ANAQ.K3D.UI7,ANAQK3D(541:64:C) # UserInput 7
ANAQ.K3D.UI8,ANAQK3D(606:64:C) # UserInput 8
ANAQ.K3D.UI9,ANAQK3D(671:64:C) # UserInput 9
# for O16
ANAQ.O16.CONFIRMATION,ANAQO16(146:4:C) # Confirmation
ANAQ.O16.UI1,ANAQO16(151:64:C) # UserInput 1
ANAQ.O16.UI2,ANAQO16(216:64:C) # UserInput 2
ANAQ.O16.UI3,ANAQO16(281:64:C) # UserInput 3
ANAQ.O16.UI4,ANAQO16(346:64:C) # UserInput 4
ANAQ.O16.UI5,ANAQO16(411:64:C) # UserInput 5
ANAQ.O16.UI6,ANAQO16(476:64:C) # UserInput 6
ANAQ.O16.UI7,ANAQO16(541:64:C) # UserInput 7
ANAQ.O16.UI8,ANAQO16(606:64:C) # UserInput 8
ANAQ.O16.UI9,ANAQO16(671:64:C) # UserInput 9
# for MCS
ANAQ.MCS.CONFIRMATION,ANAQMCS(146:4:C) # Confirmation
ANAQ.MCS.UI1,ANAQMCS(151:64:C) # UserInput 1
ANAQ.MCS.UI2,ANAQMCS(216:64:C) # UserInput 2
ANAQ.MCS.UI3,ANAQMCS(281:64:C) # UserInput 3
ANAQ.MCS.UI4,ANAQMCS(346:64:C) # UserInput 4
ANAQ.MCS.UI5,ANAQMCS(411:64:C) # UserInput 5
ANAQ.MCS.UI6,ANAQMCS(476:64:C) # UserInput 6
ANAQ.MCS.UI7,ANAQMCS(541:64:C) # UserInput 7
ANAQ.MCS.UI8,ANAQMCS(606:64:C) # UserInput 8
ANAQ.MCS.UI9,ANAQMCS(671:64:C) # UserInput 9
# for FMS
ANAQ.FMS.CONFIRMATION,ANAQFMS(146:4:C) # Confirmation
ANAQ.FMS.UI1,ANAQFMS(151:64:C) # UserInput 1
ANAQ.FMS.UI2,ANAQFMS(216:64:C) # UserInput 2
ANAQ.FMS.UI3,ANAQFMS(281:64:C) # UserInput 3
ANAQ.FMS.UI4,ANAQFMS(346:64:C) # UserInput 4
ANAQ.FMS.UI5,ANAQFMS(411:64:C) # UserInput 5
ANAQ.FMS.UI6,ANAQFMS(476:64:C) # UserInput 6
ANAQ.FMS.UI7,ANAQFMS(541:64:C) # UserInput 7
ANAQ.FMS.UI8,ANAQFMS(606:64:C) # UserInput 8
ANAQ.FMS.UI9,ANAQFMS(671:64:C) # UserInput 9
# for FLD
ANAQ.FLD.CONFIRMATION,ANAQFLD(146:4:C) # Confirmation
ANAQ.FLD.UI1,ANAQFLD(151:64:C) # UserInput 1
ANAQ.FLD.UI2,ANAQFLD(216:64:C) # UserInput 2
ANAQ.FLD.UI3,ANAQFLD(281:64:C) # UserInput 3
ANAQ.FLD.UI4,ANAQFLD(346:64:C) # UserInput 4
ANAQ.FLD.UI5,ANAQFLD(411:64:C) # UserInput 5
ANAQ.FLD.UI6,ANAQFLD(476:64:C) # UserInput 6
ANAQ.FLD.UI7,ANAQFLD(541:64:C) # UserInput 7
ANAQ.FLD.UI8,ANAQFLD(606:64:C) # UserInput 8
ANAQ.FLD.UI9,ANAQFLD(671:64:C) # UserInput 9
# for AON
ANAQ.AON.CONFIRMATION,ANAQAON(146:4:C) # Confirmation
ANAQ.AON.UI1,ANAQAON(151:64:C) # UserInput 1
ANAQ.AON.UI2,ANAQAON(216:64:C) # UserInput 2
ANAQ.AON.UI3,ANAQAON(281:64:C) # UserInput 3
ANAQ.AON.UI4,ANAQAON(346:64:C) # UserInput 4
ANAQ.AON.UI5,ANAQAON(411:64:C) # UserInput 5
ANAQ.AON.UI6,ANAQAON(476:64:C) # UserInput 6
ANAQ.AON.UI7,ANAQAON(541:64:C) # UserInput 7
ANAQ.AON.UI8,ANAQAON(606:64:C) # UserInput 8
ANAQ.AON.UI9,ANAQAON(671:64:C) # UserInput 9
# for HIC
ANAQ.HIC.CONFIRMATION,ANAQHIC(146:4:C) # Confirmation
ANAQ.HIC.UI1,ANAQHIC(151:64:C) # UserInput 1
ANAQ.HIC.UI2,ANAQHIC(216:64:C) # UserInput 2
ANAQ.HIC.UI3,ANAQHIC(281:64:C) # UserInput 3
ANAQ.HIC.UI4,ANAQHIC(346:64:C) # UserInput 4
ANAQ.HIC.UI5,ANAQHIC(411:64:C) # UserInput 5
ANAQ.HIC.UI6,ANAQHIC(476:64:C) # UserInput 6
ANAQ.HIC.UI7,ANAQHIC(541:64:C) # UserInput 7
ANAQ.HIC.UI8,ANAQHIC(606:64:C) # UserInput 8
ANAQ.HIC.UI9,ANAQHIC(671:64:C) # UserInput 9
# for WAV
ANAQ.WAV.CONFIRMATION,ANAQWAV(146:4:C) # Confirmation
ANAQ.WAV.UI1,ANAQWAV(151:64:C) # UserInput 1
ANAQ.WAV.UI2,ANAQWAV(216:64:C) # UserInput 2
ANAQ.WAV.UI3,ANAQWAV(281:64:C) # UserInput 3
ANAQ.WAV.UI4,ANAQWAV(346:64:C) # UserInput 4
ANAQ.WAV.UI5,ANAQWAV(411:64:C) # UserInput 5
ANAQ.WAV.UI6,ANAQWAV(476:64:C) # UserInput 6
ANAQ.WAV.UI7,ANAQWAV(541:64:C) # UserInput 7
ANAQ.WAV.UI8,ANAQWAV(606:64:C) # UserInput 8
ANAQ.WAV.UI9,ANAQWAV(671:64:C) # UserInput 9
# for LGS
ANAQ.LGS.CONFIRMATION,ANAQLGS(146:4:C) # Confirmation
ANAQ.LGS.UI1,ANAQLGS(151:64:C) # UserInput 1
ANAQ.LGS.UI2,ANAQLGS(216:64:C) # UserInput 2
ANAQ.LGS.UI3,ANAQLGS(281:64:C) # UserInput 3
ANAQ.LGS.UI4,ANAQLGS(346:64:C) # UserInput 4
ANAQ.LGS.UI5,ANAQLGS(411:64:C) # UserInput 5
ANAQ.LGS.UI6,ANAQLGS(476:64:C) # UserInput 6
ANAQ.LGS.UI7,ANAQLGS(541:64:C) # UserInput 7
ANAQ.LGS.UI8,ANAQLGS(606:64:C) # UserInput 8
ANAQ.LGS.UI9,ANAQLGS(671:64:C) # UserInput 9
# for O24
ANAQ.O24.CONFIRMATION,ANAQO24(146:4:C) # Confirmation
ANAQ.O24.UI1,ANAQO24(151:64:C) # UserInput 1
ANAQ.O24.UI2,ANAQO24(216:64:C) # UserInput 2
ANAQ.O24.UI3,ANAQO24(281:64:C) # UserInput 3
ANAQ.O24.UI4,ANAQO24(346:64:C) # UserInput 4
ANAQ.O24.UI5,ANAQO24(411:64:C) # UserInput 5
ANAQ.O24.UI6,ANAQO24(476:64:C) # UserInput 6
ANAQ.O24.UI7,ANAQO24(541:64:C) # UserInput 7
ANAQ.O24.UI8,ANAQO24(606:64:C) # UserInput 8
ANAQ.O24.UI9,ANAQO24(671:64:C) # UserInput 9
# for O25
ANAQ.O25.CONFIRMATION,ANAQO25(146:4:C) # Confirmation
ANAQ.O25.UI1,ANAQO25(151:64:C) # UserInput 1
ANAQ.O25.UI2,ANAQO25(216:64:C) # UserInput 2
ANAQ.O25.UI3,ANAQO25(281:64:C) # UserInput 3
ANAQ.O25.UI4,ANAQO25(346:64:C) # UserInput 4
ANAQ.O25.UI5,ANAQO25(411:64:C) # UserInput 5
ANAQ.O25.UI6,ANAQO25(476:64:C) # UserInput 6
ANAQ.O25.UI7,ANAQO25(541:64:C) # UserInput 7
ANAQ.O25.UI8,ANAQO25(606:64:C) # UserInput 8
ANAQ.O25.UI9,ANAQO25(671:64:C) # UserInput 9
# for O26
ANAQ.O26.CONFIRMATION,ANAQO26(146:4:C) # Confirmation
ANAQ.O26.UI1,ANAQO26(151:64:C) # UserInput 1
ANAQ.O26.UI2,ANAQO26(216:64:C) # UserInput 2
ANAQ.O26.UI3,ANAQO26(281:64:C) # UserInput 3
ANAQ.O26.UI4,ANAQO26(346:64:C) # UserInput 4
ANAQ.O26.UI5,ANAQO26(411:64:C) # UserInput 5
ANAQ.O26.UI6,ANAQO26(476:64:C) # UserInput 6
ANAQ.O26.UI7,ANAQO26(541:64:C) # UserInput 7
ANAQ.O26.UI8,ANAQO26(606:64:C) # UserInput 8
ANAQ.O26.UI9,ANAQO26(671:64:C) # UserInput 9
# for O27
ANAQ.O27.CONFIRMATION,ANAQO27(146:4:C) # Confirmation
ANAQ.O27.UI1,ANAQO27(151:64:C) # UserInput 1
ANAQ.O27.UI2,ANAQO27(216:64:C) # UserInput 2
ANAQ.O27.UI3,ANAQO27(281:64:C) # UserInput 3
ANAQ.O27.UI4,ANAQO27(346:64:C) # UserInput 4
ANAQ.O27.UI5,ANAQO27(411:64:C) # UserInput 5
ANAQ.O27.UI6,ANAQO27(476:64:C) # UserInput 6
ANAQ.O27.UI7,ANAQO27(541:64:C) # UserInput 7
ANAQ.O27.UI8,ANAQO27(606:64:C) # UserInput 8
ANAQ.O27.UI9,ANAQO27(671:64:C) # UserInput 9
# for O28
ANAQ.O28.CONFIRMATION,ANAQO28(146:4:C) # Confirmation
ANAQ.O28.UI1,ANAQO28(151:64:C) # UserInput 1
ANAQ.O28.UI2,ANAQO28(216:64:C) # UserInput 2
ANAQ.O28.UI3,ANAQO28(281:64:C) # UserInput 3
ANAQ.O28.UI4,ANAQO28(346:64:C) # UserInput 4
ANAQ.O28.UI5,ANAQO28(411:64:C) # UserInput 5
ANAQ.O28.UI6,ANAQO28(476:64:C) # UserInput 6
ANAQ.O28.UI7,ANAQO28(541:64:C) # UserInput 7
ANAQ.O28.UI8,ANAQO28(606:64:C) # UserInput 8
ANAQ.O28.UI9,ANAQO28(671:64:C) # UserInput 9
# for O29
ANAQ.O29.CONFIRMATION,ANAQO29(146:4:C) # Confirmation
ANAQ.O29.UI1,ANAQO29(151:64:C) # UserInput 1
ANAQ.O29.UI2,ANAQO29(216:64:C) # UserInput 2
ANAQ.O29.UI3,ANAQO29(281:64:C) # UserInput 3
ANAQ.O29.UI4,ANAQO29(346:64:C) # UserInput 4
ANAQ.O29.UI5,ANAQO29(411:64:C) # UserInput 5
ANAQ.O29.UI6,ANAQO29(476:64:C) # UserInput 6
ANAQ.O29.UI7,ANAQO29(541:64:C) # UserInput 7
ANAQ.O29.UI8,ANAQO29(606:64:C) # UserInput 8
ANAQ.O29.UI9,ANAQO29(671:64:C) # UserInput 9
# for O30
ANAQ.O30.CONFIRMATION,ANAQO30(146:4:C) # Confirmation
ANAQ.O30.UI1,ANAQO30(151:64:C) # UserInput 1
ANAQ.O30.UI2,ANAQO30(216:64:C) # UserInput 2
ANAQ.O30.UI3,ANAQO30(281:64:C) # UserInput 3
ANAQ.O30.UI4,ANAQO30(346:64:C) # UserInput 4
ANAQ.O30.UI5,ANAQO30(411:64:C) # UserInput 5
ANAQ.O30.UI6,ANAQO30(476:64:C) # UserInput 6
ANAQ.O30.UI7,ANAQO30(541:64:C) # UserInput 7
ANAQ.O30.UI8,ANAQO30(606:64:C) # UserInput 8
ANAQ.O30.UI9,ANAQO30(671:64:C) # UserInput 9
# for O31
ANAQ.O31.CONFIRMATION,ANAQO31(146:4:C) # Confirmation
ANAQ.O31.UI1,ANAQO31(151:64:C) # UserInput 1
ANAQ.O31.UI2,ANAQO31(216:64:C) # UserInput 2
ANAQ.O31.UI3,ANAQO31(281:64:C) # UserInput 3
ANAQ.O31.UI4,ANAQO31(346:64:C) # UserInput 4
ANAQ.O31.UI5,ANAQO31(411:64:C) # UserInput 5
ANAQ.O31.UI6,ANAQO31(476:64:C) # UserInput 6
ANAQ.O31.UI7,ANAQO31(541:64:C) # UserInput 7
ANAQ.O31.UI8,ANAQO31(606:64:C) # UserInput 8
ANAQ.O31.UI9,ANAQO31(671:64:C) # UserInput 9
# for O32
ANAQ.O32.CONFIRMATION,ANAQO32(146:4:C) # Confirmation
ANAQ.O32.UI1,ANAQO32(151:64:C) # UserInput 1
ANAQ.O32.UI2,ANAQO32(216:64:C) # UserInput 2
ANAQ.O32.UI3,ANAQO32(281:64:C) # UserInput 3
ANAQ.O32.UI4,ANAQO32(346:64:C) # UserInput 4
ANAQ.O32.UI5,ANAQO32(411:64:C) # UserInput 5
ANAQ.O32.UI6,ANAQO32(476:64:C) # UserInput 6
ANAQ.O32.UI7,ANAQO32(541:64:C) # UserInput 7
ANAQ.O32.UI8,ANAQO32(606:64:C) # UserInput 8
ANAQ.O32.UI9,ANAQO32(671:64:C) # UserInput 9
# for CMN
ANAQ.CMN.CONFIRMATION,ANAQCMN(146:4:C) # Confirmation
ANAQ.CMN.UI1,ANAQCMN(151:64:C) # UserInput 1
ANAQ.CMN.UI2,ANAQCMN(216:64:C) # UserInput 2
ANAQ.CMN.UI3,ANAQCMN(281:64:C) # UserInput 3
ANAQ.CMN.UI4,ANAQCMN(346:64:C) # UserInput 4
ANAQ.CMN.UI5,ANAQCMN(411:64:C) # UserInput 5
ANAQ.CMN.UI6,ANAQCMN(476:64:C) # UserInput 6
ANAQ.CMN.UI7,ANAQCMN(541:64:C) # UserInput 7
ANAQ.CMN.UI8,ANAQCMN(606:64:C) # UserInput 8
ANAQ.CMN.UI9,ANAQCMN(671:64:C) # UserInput 9

# for VGW Sub System ( and for PFU )
TSCL.M2POS1,TSCL($TSCL_SMCU+1:6:D) # M2-POS1 (chg kawai 99.08.23)
TSCL.M2POS2,TSCL($TSCL_SMCU+7:6:D) # M2-POS2 (chg kawai 99.08.23)
TSCL.M2POS3,TSCL($TSCL_SMCU+13:6:D) # M2-POS3(mm) (add ooto 00.07.11)
TSCL.M2ANG1,TSCL($TSCL_SMCU+19:6:D) # M2 TX (chg kusu 99.07.12)
TSCL.M2ANG2,TSCL($TSCL_SMCU+25:6:D) # M2 TY (chg kusu 99.07.12)
TSCL.M2ANG3,TSCL($TSCL_SMCU+169:6:D) # M2 TZ(arcmin) (add ooto 00.07.11)
TSCL.AGPRBR,TSCL($TSCL_FPCI+1:6:D) # AGr (chg kusu 99.07.12)
TSCL.AGPRBT,TSCL($TSCL_FPCI+7:6:D) # AGTheta (chg kusu 99.07.12)
TSCL.SVPRB,TSCL($TSCL_SV+1:4:S:0.001) # SVPos (chg kusu 99.07.12)
TSCL.DETTMPAG,TSCL($TSCL_AG+29:4:S:0.01) # DET-TMP AG (chg kusu 99.07.12)
TSCL.DETTMPSV,TSCL($TSCL_SV+5:4:S:0.01) # DET-TMP SV (chg kusu 99.07.12)
TSCL.DETTMPSH,TSCL($TSCL_SH+4:4:S:0.01) # DET-TMP SH (chg kusu 99.07.12)
TSCV.FILTER01,TSCV($TSCV0007+23:1:L) # SVFILTER (chg kusu 99.07.12)

# STATU table alias 
# create : /soss/SRC/product/OSSL/OSSL_StatU.d/alias.sh
# change kusu 2002.01.21
FITS.SBR.ADC-TYPE,STATU(64*1:64:C) # ADC-TYPE(%-30s)
FITS.SBR.ADC_TYPE,STATU(64*1:64:C) # ADC-TYPE(%-30s)
FITS.SBR.ADC,STATU(64*2:64:C) # ADC(%7.3f)
FITS.SBR.AIRMASS,STATU(64*3:64:C) # AIRMASS(%9.5f)
FITS.SBR.ALTITUDE,STATU(64*4:64:C) # ALTITUDE(=EL)(%8.5f)
FITS.SBR.AZIMUTH,STATU(64*5:64:C) # AZIMUTH(AZ+540%360)(%9.5f)
FITS.IRC.DATASET,STATU(64*6:64:C) # OBCP01 DATASETID(%-64s)
FITS.AOS.DATASET,STATU(64*7:64:C) # OBCP02 DATASETID(%-64s)
FITS.CIA.DATASET,STATU(64*8:64:C) # OBCP03 DATASETID(%-64s)
FITS.OHS.DATASET,STATU(64*9:64:C) # OBCP04 DATASETID(%-64s)
FITS.FCS.DATASET,STATU(64*10:64:C) # OBCP05 DATASETID(%-64s)
FITS.HDS.DATASET,STATU(64*11:64:C) # OBCP06 DATASETID(%-64s)
FITS.COM.DATASET,STATU(64*12:64:C) # OBCP07 DATASETID(%-64s)
FITS.SUP.DATASET,STATU(64*13:64:C) # OBCP08 DATASETID(%-64s)
FITS.SUK.DATASET,STATU(64*14:64:C) # OBCP09 DATASETID(%-64s)
FITS.MIR.DATASET,STATU(64*15:64:C) # OBCP10 DATASETID(%-64s)
FITS.VTO.DATASET,STATU(64*16:64:C) # OBCP11 DATASETID(%-64s)
FITS.CAC.DATASET,STATU(64*17:64:C) # OBCP12 DATASETID(%-64s)
FITS.SKY.DATASET,STATU(64*18:64:C) # OBCP13 DATASETID(%-64s)
FITS.PI1.DATASET,STATU(64*19:64:C) # OBCP14 DATASETID(%-64s)
FITS.K3D.DATASET,STATU(64*20:64:C) # OBCP15 DATASETID(%-64s)
FITS.O16.DATASET,STATU(64*21:64:C) # OBCP16 DATASETID(%-64s)
FITS.MCS.DATASET,STATU(64*22:64:C) # OBCP17 DATASETID(%-64s)
FITS.FMS.DATASET,STATU(64*23:64:C) # OBCP18 DATASETID(%-64s)
FITS.FLD.DATASET,STATU(64*24:64:C) # OBCP19 DATASETID(%-64s)
FITS.AON.DATASET,STATU(64*25:64:C) # OBCP20 DATASETID(%-64s)
FITS.HIC.DATASET,STATU(64*26:64:C) # OBCP21 DATASETID(%-64s)
FITS.WAV.DATASET,STATU(64*27:64:C) # OBCP22 DATASETID(%-64s)
FITS.LGS.DATASET,STATU(64*28:64:C) # OBCP23 DATASETID(%-64s)
FITS.O24.DATASET,STATU(64*29:64:C) # OBCP24 DATASETID(%-64s)
FITS.O25.DATASET,STATU(64*30:64:C) # OBCP25 DATASETID(%-64s)
FITS.O26.DATASET,STATU(64*31:64:C) # OBCP26 DATASETID(%-64s)
FITS.O27.DATASET,STATU(64*32:64:C) # OBCP27 DATASETID(%-64s)
FITS.O28.DATASET,STATU(64*33:64:C) # OBCP28 DATASETID(%-64s)
FITS.O29.DATASET,STATU(64*34:64:C) # OBCP29 DATASETID(%-64s)
FITS.O30.DATASET,STATU(64*35:64:C) # OBCP30 DATASETID(%-64s)
FITS.O31.DATASET,STATU(64*36:64:C) # OBCP31 DATASETID(%-64s)
FITS.O32.DATASET,STATU(64*37:64:C) # OBCP32 DATASETID(%-64s)
FITS.VGW.DATASET,STATU(64*38:64:C) # VGW DATASETID(%-64s)
FITS.SBR.DEC,STATU(64*39:64:C) # DEC(+dd:mm:ss.sss)
FITS.SBR.DOM-HUM,STATU(64*40:64:C) # Dome Humidity(%5.1f)
FITS.SBR.DOM_HUM,STATU(64*40:64:C) # Dome Humidity(%5.1f)
FITS.SBR.DOM-PRS,STATU(64*41:64:C) # Dome Pressure(%7.2f)
FITS.SBR.DOM_PRS,STATU(64*41:64:C) # Dome Pressure(%7.2f)
FITS.SBR.DOM-TMP,STATU(64*42:64:C) # Dome Temperature(%6.2f)
FITS.SBR.DOM_TMP,STATU(64*42:64:C) # Dome Temperature(%6.2f)
FITS.SBR.DOM-WND,STATU(64*43:64:C) # Dome Windspeed(%5.2f)
FITS.SBR.DOM_WND,STATU(64*43:64:C) # Dome Windspeed(%5.2f)
FITS.SBR.EQUINOX,STATU(64*44:64:C) # Equinox(%6.1f)
FITS.IRC.FOC-POS,STATU(64*45:64:C) # OBCP01 Focus Position(%-12s)
FITS.IRC.FOC_POS,STATU(64*45:64:C) # OBCP02 Focus Position(%-12s)
FITS.AOS.FOC-POS,STATU(64*46:64:C) # OBCP03 Focus Position(%-12s)
FITS.AOS.FOC_POS,STATU(64*46:64:C) # OBCP04 Focus Position(%-12s)
FITS.CIA.FOC-POS,STATU(64*47:64:C) # OBCP05 Focus Position(%-12s)
FITS.CIA.FOC_POS,STATU(64*47:64:C) # OBCP06 Focus Position(%-12s)
FITS.OHS.FOC-POS,STATU(64*48:64:C) # OBCP07 Focus Position(%-12s)
FITS.OHS.FOC_POS,STATU(64*48:64:C) # OBCP08 Focus Position(%-12s)
FITS.FCS.FOC-POS,STATU(64*49:64:C) # OBCP09 Focus Position(%-12s)
FITS.FCS.FOC_POS,STATU(64*49:64:C) # OBCP10 Focus Position(%-12s)
FITS.HDS.FOC-POS,STATU(64*50:64:C) # OBCP11 Focus Position(%-12s)
FITS.HDS.FOC_POS,STATU(64*50:64:C) # OBCP12 Focus Position(%-12s)
FITS.COM.FOC-POS,STATU(64*51:64:C) # OBCP13 Focus Position(%-12s)
FITS.COM.FOC_POS,STATU(64*51:64:C) # OBCP14 Focus Position(%-12s)
FITS.SUP.FOC-POS,STATU(64*52:64:C) # OBCP15 Focus Position(%-12s)
FITS.SUP.FOC_POS,STATU(64*52:64:C) # OBCP16 Focus Position(%-12s)
FITS.SUK.FOC-POS,STATU(64*53:64:C) # OBCP17 Focus Position(%-12s)
FITS.SUK.FOC_POS,STATU(64*53:64:C) # OBCP18 Focus Position(%-12s)
FITS.MIR.FOC-POS,STATU(64*54:64:C) # OBCP19 Focus Position(%-12s)
FITS.MIR.FOC_POS,STATU(64*54:64:C) # OBCP20 Focus Position(%-12s)
FITS.VTO.FOC-POS,STATU(64*55:64:C) # OBCP21 Focus Position(%-12s)
FITS.VTO.FOC_POS,STATU(64*55:64:C) # OBCP22 Focus Position(%-12s)
FITS.CAC.FOC-POS,STATU(64*56:64:C) # OBCP23 Focus Position(%-12s)
FITS.CAC.FOC_POS,STATU(64*56:64:C) # OBCP24 Focus Position(%-12s)
FITS.SKY.FOC-POS,STATU(64*57:64:C) # OBCP25 Focus Position(%-12s)
FITS.SKY.FOC_POS,STATU(64*57:64:C) # OBCP26 Focus Position(%-12s)
FITS.PI1.FOC-POS,STATU(64*58:64:C) # OBCP27 Focus Position(%-12s)
FITS.PI1.FOC_POS,STATU(64*58:64:C) # OBCP28 Focus Position(%-12s)
FITS.K3D.FOC-POS,STATU(64*59:64:C) # OBCP29 Focus Position(%-12s)
FITS.K3D.FOC_POS,STATU(64*59:64:C) # OBCP30 Focus Position(%-12s)
FITS.O16.FOC-POS,STATU(64*60:64:C) # OBCP31 Focus Position(%-12s)
FITS.O16.FOC_POS,STATU(64*60:64:C) # OBCP32 Focus Position(%-12s)
FITS.MCS.FOC-POS,STATU(64*61:64:C) # VGW Focus Position(%-12s)
FITS.MCS.FOC_POS,STATU(64*61:64:C) # OBCP34 Focus Position(%-12s)
FITS.FMS.FOC-POS,STATU(64*62:64:C) # OBCP35 Focus Position(%-12s)
FITS.FMS.FOC_POS,STATU(64*62:64:C) # OBCP36 Focus Position(%-12s)
FITS.FLD.FOC-POS,STATU(64*63:64:C) # OBCP37 Focus Position(%-12s)
FITS.FLD.FOC_POS,STATU(64*63:64:C) # OBCP38 Focus Position(%-12s)
FITS.AON.FOC-POS,STATU(64*64:64:C) # OBCP39 Focus Position(%-12s)
FITS.AON.FOC_POS,STATU(64*64:64:C) # OBCP40 Focus Position(%-12s)
FITS.HIC.FOC-POS,STATU(64*65:64:C) # OBCP41 Focus Position(%-12s)
FITS.HIC.FOC_POS,STATU(64*65:64:C) # OBCP42 Focus Position(%-12s)
FITS.WAV.FOC-POS,STATU(64*66:64:C) # OBCP43 Focus Position(%-12s)
FITS.WAV.FOC_POS,STATU(64*66:64:C) # OBCP44 Focus Position(%-12s)
FITS.LGS.FOC-POS,STATU(64*67:64:C) # OBCP45 Focus Position(%-12s)
FITS.LGS.FOC_POS,STATU(64*67:64:C) # OBCP46 Focus Position(%-12s)
FITS.O24.FOC-POS,STATU(64*68:64:C) # OBCP47 Focus Position(%-12s)
FITS.O24.FOC_POS,STATU(64*68:64:C) # OBCP48 Focus Position(%-12s)
FITS.O25.FOC-POS,STATU(64*69:64:C) # OBCP49 Focus Position(%-12s)
FITS.O25.FOC_POS,STATU(64*69:64:C) # OBCP50 Focus Position(%-12s)
FITS.O26.FOC-POS,STATU(64*70:64:C) # OBCP51 Focus Position(%-12s)
FITS.O26.FOC_POS,STATU(64*70:64:C) # OBCP52 Focus Position(%-12s)
FITS.O27.FOC-POS,STATU(64*71:64:C) # OBCP53 Focus Position(%-12s)
FITS.O27.FOC_POS,STATU(64*71:64:C) # OBCP54 Focus Position(%-12s)
FITS.O28.FOC-POS,STATU(64*72:64:C) # OBCP55 Focus Position(%-12s)
FITS.O28.FOC_POS,STATU(64*72:64:C) # OBCP56 Focus Position(%-12s)
FITS.O29.FOC-POS,STATU(64*73:64:C) # OBCP57 Focus Position(%-12s)
FITS.O29.FOC_POS,STATU(64*73:64:C) # OBCP58 Focus Position(%-12s)
FITS.O30.FOC-POS,STATU(64*74:64:C) # OBCP59 Focus Position(%-12s)
FITS.O30.FOC_POS,STATU(64*74:64:C) # OBCP60 Focus Position(%-12s)
FITS.O31.FOC-POS,STATU(64*75:64:C) # OBCP61 Focus Position(%-12s)
FITS.O31.FOC_POS,STATU(64*75:64:C) # OBCP62 Focus Position(%-12s)
FITS.O32.FOC-POS,STATU(64*76:64:C) # OBCP63 Focus Position(%-12s)
FITS.O32.FOC_POS,STATU(64*76:64:C) # OBCP64 Focus Position(%-12s)
FITS.VGW.FOC-POS,STATU(64*77:64:C) # OBCP65 Focus Position(%-12s)
FITS.VGW.FOC_POS,STATU(64*77:64:C) # OBCP66 Focus Position(%-12s)
FITS.SBR.FOC-VAL,STATU(64*78:64:C) # Z (%10.3f)
FITS.SBR.FOC_VAL,STATU(64*78:64:C) # Z (%10.3f)
FITS.SBR.IMR-TYPE,STATU(64*79:64:C) # ImgRot type(%-20s)
FITS.SBR.IMR_TYPE,STATU(64*79:64:C) # ImgRot type(%-20s)
FITS.SBR.IMGROT,STATU(64*80:64:C) # ImgRot position(%-8.3f)
FITS.SBR.INSROT,STATU(64*81:64:C) # InsRot position(%-8.3f)
FITS.IRC.OBJECT,STATU(64*82:64:C) # OBCP01 Object name(%-64s)
FITS.AOS.OBJECT,STATU(64*83:64:C) # OBCP02 Object name(%-64s)
FITS.CIA.OBJECT,STATU(64*84:64:C) # OBCP03 Object name(%-64s)
FITS.OHS.OBJECT,STATU(64*85:64:C) # OBCP04 Object name(%-64s)
FITS.FCS.OBJECT,STATU(64*86:64:C) # OBCP05 Object name(%-64s)
FITS.HDS.OBJECT,STATU(64*87:64:C) # OBCP06 Object name(%-64s)
FITS.COM.OBJECT,STATU(64*88:64:C) # OBCP07 Object name(%-64s)
FITS.SUP.OBJECT,STATU(64*89:64:C) # OBCP08 Object name(%-64s)
FITS.SUK.OBJECT,STATU(64*90:64:C) # OBCP09 Object name(%-64s)
FITS.MIR.OBJECT,STATU(64*91:64:C) # OBCP10 Object name(%-64s)
FITS.VTO.OBJECT,STATU(64*92:64:C) # OBCP11 Object name(%-64s)
FITS.CAC.OBJECT,STATU(64*93:64:C) # OBCP12 Object name(%-64s)
FITS.SKY.OBJECT,STATU(64*94:64:C) # OBCP13 Object name(%-64s)
FITS.PI1.OBJECT,STATU(64*95:64:C) # OBCP14 Object name(%-64s)
FITS.K3D.OBJECT,STATU(64*96:64:C) # OBCP15 Object name(%-64s)
FITS.O16.OBJECT,STATU(64*97:64:C) # OBCP16 Object name(%-64s)
FITS.MCS.OBJECT,STATU(64*98:64:C) # OBCP17 Object name(%-64s)
FITS.FMS.OBJECT,STATU(64*99:64:C) # OBCP18 Object name(%-64s)
FITS.FLD.OBJECT,STATU(64*100:64:C) # OBCP19 Object name(%-64s)
FITS.AON.OBJECT,STATU(64*101:64:C) # OBCP20 Object name(%-64s)
FITS.HIC.OBJECT,STATU(64*102:64:C) # OBCP21 Object name(%-64s)
FITS.WAV.OBJECT,STATU(64*103:64:C) # OBCP22 Object name(%-64s)
FITS.LGS.OBJECT,STATU(64*104:64:C) # OBCP23 Object name(%-64s)
FITS.O24.OBJECT,STATU(64*105:64:C) # OBCP24 Object name(%-64s)
FITS.O25.OBJECT,STATU(64*106:64:C) # OBCP25 Object name(%-64s)
FITS.O26.OBJECT,STATU(64*107:64:C) # OBCP26 Object name(%-64s)
FITS.O27.OBJECT,STATU(64*108:64:C) # OBCP27 Object name(%-64s)
FITS.O28.OBJECT,STATU(64*109:64:C) # OBCP28 Object name(%-64s)
FITS.O29.OBJECT,STATU(64*110:64:C) # OBCP29 Object name(%-64s)
FITS.O30.OBJECT,STATU(64*111:64:C) # OBCP30 Object name(%-64s)
FITS.O31.OBJECT,STATU(64*112:64:C) # OBCP31 Object name(%-64s)
FITS.O32.OBJECT,STATU(64*113:64:C) # OBCP32 Object name(%-64s)
FITS.VGW.OBJECT,STATU(64*114:64:C) # VGW Object name(%-64s)
FITS.IRC.OBSERVER,STATU(64*115:64:C) # OBCP01 Observer name(%-64s)
FITS.AOS.OBSERVER,STATU(64*116:64:C) # OBCP02 Observer name(%-64s)
FITS.CIA.OBSERVER,STATU(64*117:64:C) # OBCP03 Observer name(%-64s)
FITS.OHS.OBSERVER,STATU(64*118:64:C) # OBCP04 Observer name(%-64s)
FITS.FCS.OBSERVER,STATU(64*119:64:C) # OBCP05 Observer name(%-64s)
FITS.HDS.OBSERVER,STATU(64*120:64:C) # OBCP06 Observer name(%-64s)
FITS.COM.OBSERVER,STATU(64*121:64:C) # OBCP07 Observer name(%-64s)
FITS.SUP.OBSERVER,STATU(64*122:64:C) # OBCP08 Observer name(%-64s)
FITS.SUK.OBSERVER,STATU(64*123:64:C) # OBCP09 Observer name(%-64s)
FITS.MIR.OBSERVER,STATU(64*124:64:C) # OBCP10 Observer name(%-64s)
FITS.VTO.OBSERVER,STATU(64*125:64:C) # OBCP11 Observer name(%-64s)
FITS.CAC.OBSERVER,STATU(64*126:64:C) # OBCP12 Observer name(%-64s)
FITS.SKY.OBSERVER,STATU(64*127:64:C) # OBCP13 Observer name(%-64s)
FITS.PI1.OBSERVER,STATU(64*128:64:C) # OBCP14 Observer name(%-64s)
FITS.K3D.OBSERVER,STATU(64*129:64:C) # OBCP15 Observer name(%-64s)
FITS.O16.OBSERVER,STATU(64*130:64:C) # OBCP16 Observer name(%-64s)
FITS.MCS.OBSERVER,STATU(64*131:64:C) # OBCP17 Observer name(%-64s)
FITS.FMS.OBSERVER,STATU(64*132:64:C) # OBCP18 Observer name(%-64s)
FITS.FLD.OBSERVER,STATU(64*133:64:C) # OBCP19 Observer name(%-64s)
FITS.AON.OBSERVER,STATU(64*134:64:C) # OBCP20 Observer name(%-64s)
FITS.HIC.OBSERVER,STATU(64*135:64:C) # OBCP21 Observer name(%-64s)
FITS.WAV.OBSERVER,STATU(64*136:64:C) # OBCP22 Observer name(%-64s)
FITS.LGS.OBSERVER,STATU(64*137:64:C) # OBCP23 Observer name(%-64s)
FITS.O24.OBSERVER,STATU(64*138:64:C) # OBCP24 Observer name(%-64s)
FITS.O25.OBSERVER,STATU(64*139:64:C) # OBCP25 Observer name(%-64s)
FITS.O26.OBSERVER,STATU(64*140:64:C) # OBCP26 Observer name(%-64s)
FITS.O27.OBSERVER,STATU(64*141:64:C) # OBCP27 Observer name(%-64s)
FITS.O28.OBSERVER,STATU(64*142:64:C) # OBCP28 Observer name(%-64s)
FITS.O29.OBSERVER,STATU(64*143:64:C) # OBCP29 Observer name(%-64s)
FITS.O30.OBSERVER,STATU(64*144:64:C) # OBCP30 Observer name(%-64s)
FITS.O31.OBSERVER,STATU(64*145:64:C) # OBCP31 Observer name(%-64s)
FITS.O32.OBSERVER,STATU(64*146:64:C) # OBCP32 Observer name(%-64s)
FITS.VGW.OBSERVER,STATU(64*147:64:C) # VGW Observer name(%-64s)
FITS.SBR.OUT-HUM,STATU(64*148:64:C) # Outside Humidity(%5.1f)
FITS.SBR.OUT_HUM,STATU(64*148:64:C) # Outside Humidity(%5.1f)
FITS.SBR.OUT-PRS,STATU(64*149:64:C) # Outside Prssure(%7.2f)
FITS.SBR.OUT_PRS,STATU(64*149:64:C) # Outside Prssure(%7.2f)
FITS.SBR.OUT-TMP,STATU(64*150:64:C) # Outside Tempretre(%6.2f)
FITS.SBR.OUT_TMP,STATU(64*150:64:C) # Outside Tempretre(%6.2f)
FITS.SBR.OUT-WND,STATU(64*151:64:C) # Outside Windspeed(%5.2f)
FITS.SBR.OUT_WND,STATU(64*151:64:C) # Outside Windspeed(%5.2f)
FITS.IRC.PROP-ID,STATU(64*152:64:C) # OBCP01 Proposal ID(%-8s)
FITS.IRC.PROP_ID,STATU(64*152:64:C) # OBCP02 Proposal ID(%-8s)
FITS.AOS.PROP-ID,STATU(64*153:64:C) # OBCP03 Proposal ID(%-8s)
FITS.AOS.PROP_ID,STATU(64*153:64:C) # OBCP04 Proposal ID(%-8s)
FITS.CIA.PROP-ID,STATU(64*154:64:C) # OBCP05 Proposal ID(%-8s)
FITS.CIA.PROP_ID,STATU(64*154:64:C) # OBCP06 Proposal ID(%-8s)
FITS.OHS.PROP-ID,STATU(64*155:64:C) # OBCP07 Proposal ID(%-8s)
FITS.OHS.PROP_ID,STATU(64*155:64:C) # OBCP08 Proposal ID(%-8s)
FITS.FCS.PROP-ID,STATU(64*156:64:C) # OBCP09 Proposal ID(%-8s)
FITS.FCS.PROP_ID,STATU(64*156:64:C) # OBCP10 Proposal ID(%-8s)
FITS.HDS.PROP-ID,STATU(64*157:64:C) # OBCP11 Proposal ID(%-8s)
FITS.HDS.PROP_ID,STATU(64*157:64:C) # OBCP12 Proposal ID(%-8s)
FITS.COM.PROP-ID,STATU(64*158:64:C) # OBCP13 Proposal ID(%-8s)
FITS.COM.PROP_ID,STATU(64*158:64:C) # OBCP14 Proposal ID(%-8s)
FITS.SUP.PROP-ID,STATU(64*159:64:C) # OBCP15 Proposal ID(%-8s)
FITS.SUP.PROP_ID,STATU(64*159:64:C) # OBCP16 Proposal ID(%-8s)
FITS.SUK.PROP-ID,STATU(64*160:64:C) # OBCP17 Proposal ID(%-8s)
FITS.SUK.PROP_ID,STATU(64*160:64:C) # OBCP18 Proposal ID(%-8s)
FITS.MIR.PROP-ID,STATU(64*161:64:C) # OBCP19 Proposal ID(%-8s)
FITS.MIR.PROP_ID,STATU(64*161:64:C) # OBCP20 Proposal ID(%-8s)
FITS.VTO.PROP-ID,STATU(64*162:64:C) # OBCP21 Proposal ID(%-8s)
FITS.VTO.PROP_ID,STATU(64*162:64:C) # OBCP22 Proposal ID(%-8s)
FITS.CAC.PROP-ID,STATU(64*163:64:C) # OBCP23 Proposal ID(%-8s)
FITS.CAC.PROP_ID,STATU(64*163:64:C) # OBCP24 Proposal ID(%-8s)
FITS.SKY.PROP-ID,STATU(64*164:64:C) # OBCP25 Proposal ID(%-8s)
FITS.SKY.PROP_ID,STATU(64*164:64:C) # OBCP26 Proposal ID(%-8s)
FITS.PI1.PROP-ID,STATU(64*165:64:C) # OBCP27 Proposal ID(%-8s)
FITS.PI1.PROP_ID,STATU(64*165:64:C) # OBCP28 Proposal ID(%-8s)
FITS.K3D.PROP-ID,STATU(64*166:64:C) # OBCP29 Proposal ID(%-8s)
FITS.K3D.PROP_ID,STATU(64*166:64:C) # OBCP30 Proposal ID(%-8s)
FITS.O16.PROP-ID,STATU(64*167:64:C) # OBCP31 Proposal ID(%-8s)
FITS.O16.PROP_ID,STATU(64*167:64:C) # OBCP32 Proposal ID(%-8s)
FITS.MCS.PROP-ID,STATU(64*168:64:C) # VGW Proposal ID(%-8s)
FITS.MCS.PROP_ID,STATU(64*168:64:C) # OBCP34 Proposal ID(%-8s)
FITS.FMS.PROP-ID,STATU(64*169:64:C) # OBCP35 Proposal ID(%-8s)
FITS.FMS.PROP_ID,STATU(64*169:64:C) # OBCP36 Proposal ID(%-8s)
FITS.FLD.PROP-ID,STATU(64*170:64:C) # OBCP37 Proposal ID(%-8s)
FITS.FLD.PROP_ID,STATU(64*170:64:C) # OBCP38 Proposal ID(%-8s)
FITS.AON.PROP-ID,STATU(64*171:64:C) # OBCP39 Proposal ID(%-8s)
FITS.AON.PROP_ID,STATU(64*171:64:C) # OBCP40 Proposal ID(%-8s)
FITS.HIC.PROP-ID,STATU(64*172:64:C) # OBCP41 Proposal ID(%-8s)
FITS.HIC.PROP_ID,STATU(64*172:64:C) # OBCP42 Proposal ID(%-8s)
FITS.WAV.PROP-ID,STATU(64*173:64:C) # OBCP43 Proposal ID(%-8s)
FITS.WAV.PROP_ID,STATU(64*173:64:C) # OBCP44 Proposal ID(%-8s)
FITS.LGS.PROP-ID,STATU(64*174:64:C) # OBCP45 Proposal ID(%-8s)
FITS.LGS.PROP_ID,STATU(64*174:64:C) # OBCP46 Proposal ID(%-8s)
FITS.O24.PROP-ID,STATU(64*175:64:C) # OBCP47 Proposal ID(%-8s)
FITS.O24.PROP_ID,STATU(64*175:64:C) # OBCP48 Proposal ID(%-8s)
FITS.O25.PROP-ID,STATU(64*176:64:C) # OBCP49 Proposal ID(%-8s)
FITS.O25.PROP_ID,STATU(64*176:64:C) # OBCP50 Proposal ID(%-8s)
FITS.O26.PROP-ID,STATU(64*177:64:C) # OBCP51 Proposal ID(%-8s)
FITS.O26.PROP_ID,STATU(64*177:64:C) # OBCP52 Proposal ID(%-8s)
FITS.O27.PROP-ID,STATU(64*178:64:C) # OBCP53 Proposal ID(%-8s)
FITS.O27.PROP_ID,STATU(64*178:64:C) # OBCP54 Proposal ID(%-8s)
FITS.O28.PROP-ID,STATU(64*179:64:C) # OBCP55 Proposal ID(%-8s)
FITS.O28.PROP_ID,STATU(64*179:64:C) # OBCP56 Proposal ID(%-8s)
FITS.O29.PROP-ID,STATU(64*180:64:C) # OBCP57 Proposal ID(%-8s)
FITS.O29.PROP_ID,STATU(64*180:64:C) # OBCP58 Proposal ID(%-8s)
FITS.O30.PROP-ID,STATU(64*181:64:C) # OBCP59 Proposal ID(%-8s)
FITS.O30.PROP_ID,STATU(64*181:64:C) # OBCP60 Proposal ID(%-8s)
FITS.O31.PROP-ID,STATU(64*182:64:C) # OBCP61 Proposal ID(%-8s)
FITS.O31.PROP_ID,STATU(64*182:64:C) # OBCP62 Proposal ID(%-8s)
FITS.O32.PROP-ID,STATU(64*183:64:C) # OBCP63 Proposal ID(%-8s)
FITS.O32.PROP_ID,STATU(64*183:64:C) # OBCP64 Proposal ID(%-8s)
FITS.VGW.PROP-ID,STATU(64*184:64:C) # OBCP65 Proposal ID(%-8s)
FITS.VGW.PROP_ID,STATU(64*184:64:C) # OBCP66 Proposal ID(%-8s)
FITS.SBR.RA,STATU(64*185:64:C) # RA(hh:mm:ss.sss)
FITS.SBR.SECZ,STATU(64*186:64:C) # SECZ(sec(90-EL))(%6.3f)
FITS.SBR.SEEING,STATU(64*187:64:C) # Seeing(%10.4f)
FITS.SBR.WEATHER,STATU(64*188:64:C) # Weather(%-20s)
FITS.SBR.ZD,STATU(64*189:64:C) # ZD(90-EL)(%6.3f)
FITS.SBR.INST-PA,STATU(64*190:64:C) # INST-PA(%7.3f)
FITS.SBR.INST_PA,STATU(64*190:64:C) # INST-PA(%7.3f)
FITS.SBR.UT1-UTC,STATU(64*191:64:C) # UT1-UTC(%+8.5f)
FITS.SBR.UT1_UTC,STATU(64*191:64:C) # UT1-UTC(%+8.5f)
FITS.SBR.TRANSP,STATU(64*192:64:C) # Transperancy(%5.3f)
FITS.IRC.FRAMEID,STATU(64*193:64:C) # OBCP01 A FrameID (%-12s)
FITS.AOS.FRAMEID,STATU(64*194:64:C) # OBCP02 A FrameID (%-12s)
FITS.CIA.FRAMEID,STATU(64*195:64:C) # OBCP03 A FrameID (%-12s)
FITS.OHS.FRAMEID,STATU(64*196:64:C) # OBCP04 A FrameID (%-12s)
FITS.FCS.FRAMEID,STATU(64*197:64:C) # OBCP05 A FrameID (%-12s)
FITS.HDS.FRAMEID,STATU(64*198:64:C) # OBCP06 A FrameID (%-12s)
FITS.COM.FRAMEID,STATU(64*199:64:C) # OBCP07 A FrameID (%-12s)
FITS.SUP.FRAMEID,STATU(64*200:64:C) # OBCP08 A FrameID (%-12s)
FITS.SUK.FRAMEID,STATU(64*201:64:C) # OBCP09 A FrameID (%-12s)
FITS.MIR.FRAMEID,STATU(64*202:64:C) # OBCP10 A FrameID (%-12s)
FITS.VTO.FRAMEID,STATU(64*203:64:C) # OBCP11 A FrameID (%-12s)
FITS.CAC.FRAMEID,STATU(64*204:64:C) # OBCP12 A FrameID (%-12s)
FITS.SKY.FRAMEID,STATU(64*205:64:C) # OBCP13 A FrameID (%-12s)
FITS.PI1.FRAMEID,STATU(64*206:64:C) # OBCP14 A FrameID (%-12s)
FITS.K3D.FRAMEID,STATU(64*207:64:C) # OBCP15 A FrameID (%-12s)
FITS.O16.FRAMEID,STATU(64*208:64:C) # OBCP16 A FrameID (%-12s)
FITS.MCS.FRAMEID,STATU(64*209:64:C) # OBCP17 A FrameID (%-12s)
FITS.FMS.FRAMEID,STATU(64*210:64:C) # OBCP18 A FrameID (%-12s)
FITS.FLD.FRAMEID,STATU(64*211:64:C) # OBCP19 A FrameID (%-12s)
FITS.AON.FRAMEID,STATU(64*212:64:C) # OBCP20 A FrameID (%-12s)
FITS.HIC.FRAMEID,STATU(64*213:64:C) # OBCP21 A FrameID (%-12s)
FITS.WAV.FRAMEID,STATU(64*214:64:C) # OBCP22 A FrameID (%-12s)
FITS.LGS.FRAMEID,STATU(64*215:64:C) # OBCP23 A FrameID (%-12s)
FITS.O24.FRAMEID,STATU(64*216:64:C) # OBCP24 A FrameID (%-12s)
FITS.O25.FRAMEID,STATU(64*217:64:C) # OBCP25 A FrameID (%-12s)
FITS.O26.FRAMEID,STATU(64*218:64:C) # OBCP26 A FrameID (%-12s)
FITS.O27.FRAMEID,STATU(64*219:64:C) # OBCP27 A FrameID (%-12s)
FITS.O28.FRAMEID,STATU(64*220:64:C) # OBCP28 A FrameID (%-12s)
FITS.O29.FRAMEID,STATU(64*221:64:C) # OBCP29 A FrameID (%-12s)
FITS.O30.FRAMEID,STATU(64*222:64:C) # OBCP30 A FrameID (%-12s)
FITS.O31.FRAMEID,STATU(64*223:64:C) # OBCP31 A FrameID (%-12s)
FITS.O32.FRAMEID,STATU(64*224:64:C) # OBCP32 A FrameID (%-12s)
FITS.VGW.FRAMEID,STATU(64*225:64:C) # VGW A FrameID (%-12s)
FITS.IRC.OBS-ALOC,STATU(64*226:64:C) # OBCP01 OBS-ALLOC(%-12s)
FITS.IRC.OBS_ALOC,STATU(64*226:64:C) # OBCP02 OBS-ALLOC(%-12s)
FITS.AOS.OBS-ALOC,STATU(64*227:64:C) # OBCP03 OBS-ALLOC(%-12s)
FITS.AOS.OBS_ALOC,STATU(64*227:64:C) # OBCP04 OBS-ALLOC(%-12s)
FITS.CIA.OBS-ALOC,STATU(64*228:64:C) # OBCP05 OBS-ALLOC(%-12s)
FITS.CIA.OBS_ALOC,STATU(64*228:64:C) # OBCP06 OBS-ALLOC(%-12s)
FITS.OHS.OBS-ALOC,STATU(64*229:64:C) # OBCP07 OBS-ALLOC(%-12s)
FITS.OHS.OBS_ALOC,STATU(64*229:64:C) # OBCP08 OBS-ALLOC(%-12s)
FITS.FCS.OBS-ALOC,STATU(64*230:64:C) # OBCP09 OBS-ALLOC(%-12s)
FITS.FCS.OBS_ALOC,STATU(64*230:64:C) # OBCP10 OBS-ALLOC(%-12s)
FITS.HDS.OBS-ALOC,STATU(64*231:64:C) # OBCP11 OBS-ALLOC(%-12s)
FITS.HDS.OBS_ALOC,STATU(64*231:64:C) # OBCP12 OBS-ALLOC(%-12s)
FITS.COM.OBS-ALOC,STATU(64*232:64:C) # OBCP13 OBS-ALLOC(%-12s)
FITS.COM.OBS_ALOC,STATU(64*232:64:C) # OBCP14 OBS-ALLOC(%-12s)
FITS.SUP.OBS-ALOC,STATU(64*233:64:C) # OBCP15 OBS-ALLOC(%-12s)
FITS.SUP.OBS_ALOC,STATU(64*233:64:C) # OBCP16 OBS-ALLOC(%-12s)
FITS.SUK.OBS-ALOC,STATU(64*234:64:C) # OBCP17 OBS-ALLOC(%-12s)
FITS.SUK.OBS_ALOC,STATU(64*234:64:C) # OBCP18 OBS-ALLOC(%-12s)
FITS.MIR.OBS-ALOC,STATU(64*235:64:C) # OBCP19 OBS-ALLOC(%-12s)
FITS.MIR.OBS_ALOC,STATU(64*235:64:C) # OBCP20 OBS-ALLOC(%-12s)
FITS.VTO.OBS-ALOC,STATU(64*236:64:C) # OBCP21 OBS-ALLOC(%-12s)
FITS.VTO.OBS_ALOC,STATU(64*236:64:C) # OBCP22 OBS-ALLOC(%-12s)
FITS.CAC.OBS-ALOC,STATU(64*237:64:C) # OBCP23 OBS-ALLOC(%-12s)
FITS.CAC.OBS_ALOC,STATU(64*237:64:C) # OBCP24 OBS-ALLOC(%-12s)
FITS.SKY.OBS-ALOC,STATU(64*238:64:C) # OBCP25 OBS-ALLOC(%-12s)
FITS.SKY.OBS_ALOC,STATU(64*238:64:C) # OBCP26 OBS-ALLOC(%-12s)
FITS.PI1.OBS-ALOC,STATU(64*239:64:C) # OBCP27 OBS-ALLOC(%-12s)
FITS.PI1.OBS_ALOC,STATU(64*239:64:C) # OBCP28 OBS-ALLOC(%-12s)
FITS.K3D.OBS-ALOC,STATU(64*240:64:C) # OBCP29 OBS-ALLOC(%-12s)
FITS.K3D.OBS_ALOC,STATU(64*240:64:C) # OBCP30 OBS-ALLOC(%-12s)
FITS.O16.OBS-ALOC,STATU(64*241:64:C) # OBCP31 OBS-ALLOC(%-12s)
FITS.O16.OBS_ALOC,STATU(64*241:64:C) # OBCP32 OBS-ALLOC(%-12s)
FITS.MCS.OBS-ALOC,STATU(64*242:64:C) # VGW OBS-ALLOC(%-12s)
FITS.MCS.OBS_ALOC,STATU(64*242:64:C) # OBCP34 OBS-ALLOC(%-12s)
FITS.FMS.OBS-ALOC,STATU(64*243:64:C) # OBCP35 OBS-ALLOC(%-12s)
FITS.FMS.OBS_ALOC,STATU(64*243:64:C) # OBCP36 OBS-ALLOC(%-12s)
FITS.FLD.OBS-ALOC,STATU(64*244:64:C) # OBCP37 OBS-ALLOC(%-12s)
FITS.FLD.OBS_ALOC,STATU(64*244:64:C) # OBCP38 OBS-ALLOC(%-12s)
FITS.AON.OBS-ALOC,STATU(64*245:64:C) # OBCP39 OBS-ALLOC(%-12s)
FITS.AON.OBS_ALOC,STATU(64*245:64:C) # OBCP40 OBS-ALLOC(%-12s)
FITS.HIC.OBS-ALOC,STATU(64*246:64:C) # OBCP41 OBS-ALLOC(%-12s)
FITS.HIC.OBS_ALOC,STATU(64*246:64:C) # OBCP42 OBS-ALLOC(%-12s)
FITS.WAV.OBS-ALOC,STATU(64*247:64:C) # OBCP43 OBS-ALLOC(%-12s)
FITS.WAV.OBS_ALOC,STATU(64*247:64:C) # OBCP44 OBS-ALLOC(%-12s)
FITS.LGS.OBS-ALOC,STATU(64*248:64:C) # OBCP45 OBS-ALLOC(%-12s)
FITS.LGS.OBS_ALOC,STATU(64*248:64:C) # OBCP46 OBS-ALLOC(%-12s)
FITS.O24.OBS-ALOC,STATU(64*249:64:C) # OBCP47 OBS-ALLOC(%-12s)
FITS.O24.OBS_ALOC,STATU(64*249:64:C) # OBCP48 OBS-ALLOC(%-12s)
FITS.O25.OBS-ALOC,STATU(64*250:64:C) # OBCP49 OBS-ALLOC(%-12s)
FITS.O25.OBS_ALOC,STATU(64*250:64:C) # OBCP50 OBS-ALLOC(%-12s)
FITS.O26.OBS-ALOC,STATU(64*251:64:C) # OBCP51 OBS-ALLOC(%-12s)
FITS.O26.OBS_ALOC,STATU(64*251:64:C) # OBCP52 OBS-ALLOC(%-12s)
FITS.O27.OBS-ALOC,STATU(64*252:64:C) # OBCP53 OBS-ALLOC(%-12s)
FITS.O27.OBS_ALOC,STATU(64*252:64:C) # OBCP54 OBS-ALLOC(%-12s)
FITS.O28.OBS-ALOC,STATU(64*253:64:C) # OBCP55 OBS-ALLOC(%-12s)
FITS.O28.OBS_ALOC,STATU(64*253:64:C) # OBCP56 OBS-ALLOC(%-12s)
FITS.O29.OBS-ALOC,STATU(64*254:64:C) # OBCP57 OBS-ALLOC(%-12s)
FITS.O29.OBS_ALOC,STATU(64*254:64:C) # OBCP58 OBS-ALLOC(%-12s)
FITS.O30.OBS-ALOC,STATU(64*255:64:C) # OBCP59 OBS-ALLOC(%-12s)
FITS.O30.OBS_ALOC,STATU(64*255:64:C) # OBCP60 OBS-ALLOC(%-12s)
FITS.O31.OBS-ALOC,STATU(64*256:64:C) # OBCP61 OBS-ALLOC(%-12s)
FITS.O31.OBS_ALOC,STATU(64*256:64:C) # OBCP62 OBS-ALLOC(%-12s)
FITS.O32.OBS-ALOC,STATU(64*257:64:C) # OBCP63 OBS-ALLOC(%-12s)
FITS.O32.OBS_ALOC,STATU(64*257:64:C) # OBCP64 OBS-ALLOC(%-12s)
FITS.VGW.OBS-ALOC,STATU(64*258:64:C) # OBCP65 OBS-ALLOC(%-12s)
FITS.VGW.OBS_ALOC,STATU(64*258:64:C) # OBCP66 OBS-ALLOC(%-12s)
FITS.SBR.TELESCOP,STATU(64*259:64:C) # TELESCOPE(%-32s)
FITS.SBR.TELFOCUS,STATU(64*260:64:C) # TELESCOPE FOCUS(%-12s)
FITS.SBR.MAINOBCP,STATU(64*261:64:C) # MAIN OBCP(%-8s)
FITS.SBR.AUTOGUID,STATU(64*262:64:C) # AUTOGUIDE(%-8s)
FITS.SBR.M2-POS1,STATU(64*263:64:C) # M2-POS1 (add kusu 99.07.12)
FITS.SBR.M2_POS1,STATU(64*263:64:C) # M2-POS1 (add kusu 99.07.12)
FITS.SBR.M2-POS2,STATU(64*264:64:C) # M2-POS2 (add kusu 99.07.12)
FITS.SBR.M2_POS2,STATU(64*264:64:C) # M2-POS2 (add kusu 99.07.12)
FITS.SBR.M2-ANG1,STATU(64*265:64:C) # M2-TX (add kusu 99.07.12)
FITS.SBR.M2_ANG1,STATU(64*265:64:C) # M2-TX (add kusu 99.07.12)
FITS.SBR.M2-ANG2,STATU(64*266:64:C) # M2-TY (add kusu 99.07.12)
FITS.SBR.M2_ANG2,STATU(64*266:64:C) # M2-TY (add kusu 99.07.12)
FITS.SBR.AG-PRBR,STATU(64*267:64:C) # AGr (add kusu 99.07.12)
FITS.SBR.AG_PRBR,STATU(64*267:64:C) # AGr (add kusu 99.07.12)
FITS.SBR.AG-PRBT,STATU(64*268:64:C) # AGTheata (add kusu 99.07.12)
FITS.SBR.AG_PRBT,STATU(64*268:64:C) # AGTheata (add kusu 99.07.12)
FITS.SBR.AG-PRBX,STATU(64*269:64:C) # AGx (add kusu 99.07.12)
FITS.SBR.AG_PRBX,STATU(64*269:64:C) # AGx (add kusu 99.07.12)
FITS.SBR.AG-PRBY,STATU(64*270:64:C) # AGy (add kusu 99.07.12)
FITS.SBR.AG_PRBY,STATU(64*270:64:C) # AGy (add kusu 99.07.12)
FITS.SBR.AG-PRBZ,STATU(64*271:64:C) # AGz (add kusu 99.08.23)
FITS.SBR.AG_PRBZ,STATU(64*271:64:C) # AGz (add kusu 99.08.23)
FITS.SBR.SV-PRB,STATU(64*272:64:C) # SVPos (add kusu 99.07.12)
FITS.SBR.SV_PRB,STATU(64*272:64:C) # SVPos (add kusu 99.07.12)
FITS.SBR.DET-TMPAG,STATU(64*273:64:C) # DET-TMP AG (add kusu 99.07.12)
FITS.SBR.DET_TMPAG,STATU(64*273:64:C) # DET-TMP AG (add kusu 99.07.12)
FITS.SBR.DET-TMPSV,STATU(64*274:64:C) # DET-TMP SV (add kusu 99.07.12)
FITS.SBR.DET_TMPSV,STATU(64*274:64:C) # DET-TMP SV (add kusu 99.07.12)
FITS.SBR.DET-TMPSH,STATU(64*275:64:C) # DET-TMP SH (add kusu 99.07.12)
FITS.SBR.DET_TMPSH,STATU(64*275:64:C) # DET-TMP SH (add kusu 99.07.12)
FITS.VGW.FILTER01,STATU(64*276:64:C) # SVFILTER (add kusu 99.07.12)
FITS.IRC.FRAMEIDQ,STATU(64*277:64:C) # OBCP01 Q FrameID (%-12s)
FITS.AOS.FRAMEIDQ,STATU(64*278:64:C) # OBCP02 Q FrameID (%-12s)
FITS.CIA.FRAMEIDQ,STATU(64*279:64:C) # OBCP03 Q FrameID (%-12s)
FITS.OHS.FRAMEIDQ,STATU(64*280:64:C) # OBCP04 Q FrameID (%-12s)
FITS.FCS.FRAMEIDQ,STATU(64*281:64:C) # OBCP05 Q FrameID (%-12s)
FITS.HDS.FRAMEIDQ,STATU(64*282:64:C) # OBCP06 Q FrameID (%-12s)
FITS.COM.FRAMEIDQ,STATU(64*283:64:C) # OBCP07 Q FrameID (%-12s)
FITS.SUP.FRAMEIDQ,STATU(64*284:64:C) # OBCP08 Q FrameID (%-12s)
FITS.SUK.FRAMEIDQ,STATU(64*285:64:C) # OBCP09 Q FrameID (%-12s)
FITS.MIR.FRAMEIDQ,STATU(64*286:64:C) # OBCP10 Q FrameID (%-12s)
FITS.VTO.FRAMEIDQ,STATU(64*287:64:C) # OBCP11 Q FrameID (%-12s)
FITS.CAC.FRAMEIDQ,STATU(64*288:64:C) # OBCP12 Q FrameID (%-12s)
FITS.SKY.FRAMEIDQ,STATU(64*289:64:C) # OBCP13 Q FrameID (%-12s)
FITS.PI1.FRAMEIDQ,STATU(64*290:64:C) # OBCP14 Q FrameID (%-12s)
FITS.K3D.FRAMEIDQ,STATU(64*291:64:C) # OBCP15 Q FrameID (%-12s)
FITS.O16.FRAMEIDQ,STATU(64*292:64:C) # OBCP16 Q FrameID (%-12s)
FITS.MCS.FRAMEIDQ,STATU(64*293:64:C) # OBCP17 Q FrameID (%-12s)
FITS.FMS.FRAMEIDQ,STATU(64*294:64:C) # OBCP18 Q FrameID (%-12s)
FITS.FLD.FRAMEIDQ,STATU(64*295:64:C) # OBCP19 Q FrameID (%-12s)
FITS.AON.FRAMEIDQ,STATU(64*296:64:C) # OBCP20 Q FrameID (%-12s)
FITS.HIC.FRAMEIDQ,STATU(64*297:64:C) # OBCP21 Q FrameID (%-12s)
FITS.WAV.FRAMEIDQ,STATU(64*298:64:C) # OBCP22 Q FrameID (%-12s)
FITS.LGS.FRAMEIDQ,STATU(64*299:64:C) # OBCP23 Q FrameID (%-12s)
FITS.O24.FRAMEIDQ,STATU(64*300:64:C) # OBCP24 Q FrameID (%-12s)
FITS.O25.FRAMEIDQ,STATU(64*301:64:C) # OBCP25 Q FrameID (%-12s)
FITS.O26.FRAMEIDQ,STATU(64*302:64:C) # OBCP26 Q FrameID (%-12s)
FITS.O27.FRAMEIDQ,STATU(64*303:64:C) # OBCP27 Q FrameID (%-12s)
FITS.O28.FRAMEIDQ,STATU(64*304:64:C) # OBCP28 Q FrameID (%-12s)
FITS.O29.FRAMEIDQ,STATU(64*305:64:C) # OBCP29 Q FrameID (%-12s)
FITS.O30.FRAMEIDQ,STATU(64*306:64:C) # OBCP30 Q FrameID (%-12s)
FITS.O31.FRAMEIDQ,STATU(64*307:64:C) # OBCP31 Q FrameID (%-12s)
FITS.O32.FRAMEIDQ,STATU(64*308:64:C) # OBCP32 Q FrameID (%-12s)
FITS.VGW.FRAMEIDQ,STATU(64*309:64:C) # VGW Q FrameID (%-12s)
FITS.SBR.M2-TIP,STATU(64*310:64:C) # M2-TIP (add iwai 991116)
FITS.SBR.M2_TIP,STATU(64*310:64:C) # M2-TIP (add iwai 991116)
FITS.SBR.M2-TYPE,STATU(64*311:64:C) # M2-TYPE (add iwai 991116)
FITS.SBR.M2_TYPE,STATU(64*311:64:C) # M2-TYPE (add iwai 991116)
FITS.IRC.OBS-MOD,STATU(64*312:64:C) # OBCP01 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.IRC.OBS_MOD,STATU(64*312:64:C) # OBCP02 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.AOS.OBS-MOD,STATU(64*313:64:C) # OBCP03 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.AOS.OBS_MOD,STATU(64*313:64:C) # OBCP04 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.CIA.OBS-MOD,STATU(64*314:64:C) # OBCP05 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.CIA.OBS_MOD,STATU(64*314:64:C) # OBCP06 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.OHS.OBS-MOD,STATU(64*315:64:C) # OBCP07 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.OHS.OBS_MOD,STATU(64*315:64:C) # OBCP08 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.FCS.OBS-MOD,STATU(64*316:64:C) # OBCP09 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.FCS.OBS_MOD,STATU(64*316:64:C) # OBCP10 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.HDS.OBS-MOD,STATU(64*317:64:C) # OBCP11 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.HDS.OBS_MOD,STATU(64*317:64:C) # OBCP12 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.COM.OBS-MOD,STATU(64*318:64:C) # OBCP13 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.COM.OBS_MOD,STATU(64*318:64:C) # OBCP14 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.SUP.OBS-MOD,STATU(64*319:64:C) # OBCP15 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.SUP.OBS_MOD,STATU(64*319:64:C) # OBCP16 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.SUK.OBS-MOD,STATU(64*320:64:C) # OBCP17 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.SUK.OBS_MOD,STATU(64*320:64:C) # OBCP18 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.MIR.OBS-MOD,STATU(64*321:64:C) # OBCP19 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.MIR.OBS_MOD,STATU(64*321:64:C) # OBCP20 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.VTO.OBS-MOD,STATU(64*322:64:C) # OBCP21 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.VTO.OBS_MOD,STATU(64*322:64:C) # OBCP22 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.CAC.OBS-MOD,STATU(64*323:64:C) # OBCP23 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.CAC.OBS_MOD,STATU(64*323:64:C) # OBCP24 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.SKY.OBS-MOD,STATU(64*324:64:C) # OBCP25 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.SKY.OBS_MOD,STATU(64*324:64:C) # OBCP26 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.PI1.OBS-MOD,STATU(64*325:64:C) # OBCP27 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.PI1.OBS_MOD,STATU(64*325:64:C) # OBCP28 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.K3D.OBS-MOD,STATU(64*326:64:C) # OBCP29 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.K3D.OBS_MOD,STATU(64*326:64:C) # OBCP30 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.O16.OBS-MOD,STATU(64*327:64:C) # OBCP31 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.O16.OBS_MOD,STATU(64*327:64:C) # OBCP32 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.MCS.OBS-MOD,STATU(64*328:64:C) # VGW OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.MCS.OBS_MOD,STATU(64*328:64:C) # OBCP34 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.FMS.OBS-MOD,STATU(64*329:64:C) # OBCP35 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.FMS.OBS_MOD,STATU(64*329:64:C) # OBCP36 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.FLD.OBS-MOD,STATU(64*330:64:C) # OBCP37 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.FLD.OBS_MOD,STATU(64*330:64:C) # OBCP38 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.AON.OBS-MOD,STATU(64*331:64:C) # OBCP39 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.AON.OBS_MOD,STATU(64*331:64:C) # OBCP40 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.HIC.OBS-MOD,STATU(64*332:64:C) # OBCP41 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.HIC.OBS_MOD,STATU(64*332:64:C) # OBCP42 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.WAV.OBS-MOD,STATU(64*333:64:C) # OBCP43 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.WAV.OBS_MOD,STATU(64*333:64:C) # OBCP44 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.LGS.OBS-MOD,STATU(64*334:64:C) # OBCP45 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.LGS.OBS_MOD,STATU(64*334:64:C) # OBCP46 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.O24.OBS-MOD,STATU(64*335:64:C) # OBCP47 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.O24.OBS_MOD,STATU(64*335:64:C) # OBCP48 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.O25.OBS-MOD,STATU(64*336:64:C) # OBCP49 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.O25.OBS_MOD,STATU(64*336:64:C) # OBCP50 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.O26.OBS-MOD,STATU(64*337:64:C) # OBCP51 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.O26.OBS_MOD,STATU(64*337:64:C) # OBCP52 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.O27.OBS-MOD,STATU(64*338:64:C) # OBCP53 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.O27.OBS_MOD,STATU(64*338:64:C) # OBCP54 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.O28.OBS-MOD,STATU(64*339:64:C) # OBCP55 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.O28.OBS_MOD,STATU(64*339:64:C) # OBCP56 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.O29.OBS-MOD,STATU(64*340:64:C) # OBCP57 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.O29.OBS_MOD,STATU(64*340:64:C) # OBCP58 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.O30.OBS-MOD,STATU(64*341:64:C) # OBCP59 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.O30.OBS_MOD,STATU(64*341:64:C) # OBCP60 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.O31.OBS-MOD,STATU(64*342:64:C) # OBCP61 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.O31.OBS_MOD,STATU(64*342:64:C) # OBCP62 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.O32.OBS-MOD,STATU(64*343:64:C) # OBCP63 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.O32.OBS_MOD,STATU(64*343:64:C) # OBCP64 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.VGW.OBS-MOD,STATU(64*344:64:C) # OBCP65 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.VGW.OBS_MOD,STATU(64*344:64:C) # OBCP66 OBS-MOD(=OBE_ID) (add kusu 99.12.13)
FITS.SBR.CHP-PA,STATU(64*345:64:C) # CHP-PA (add iwai 991221)
FITS.SBR.CHP_PA,STATU(64*345:64:C) # CHP-PA (add iwai 991221)
FITS.SBR.CHP-WID,STATU(64*346:64:C) # CHP-WID (add iwai 991221)
FITS.SBR.CHP_WID,STATU(64*346:64:C) # CHP-WID (add iwai 991221)
FITS.VGW.IROT_TELESCOPE,STATU(64*347:64:C) # IROT_TELESCOPE (add ooto 000705)
FITS.VGW.IMGROT_FLG,STATU(64*348:64:C) # IMGROT_FLG (add ooto 000705)
FITS.VGW.INSROTPA,STATU(64*349:64:C) # INSROTPA (add ooto 000705)
FITS.SBR.M2-POS3,STATU(64*350:64:C) # M2-POS3 (add ooto 000711)
FITS.SBR.M2_POS3,STATU(64*350:64:C) # M2-POS3 (add ooto 000711)
FITS.SBR.M2-ANG3,STATU(64*351:64:C) # M2-ANG3 (add ooto 000711)
FITS.SBR.M2_ANG3,STATU(64*351:64:C) # M2-ANG3 (add ooto 000711)
FITS.PFU.OFFSET-X,STATU(64*352:64:C) # PFU OFFSET-X (add ooto 000711)
FITS.PFU.OFFSET_X,STATU(64*352:64:C) # PFU OFFSET-X (add ooto 000711)
FITS.PFU.OFFSET-Y,STATU(64*353:64:C) # PFU OFFSET-Y (add ooto 000711)
FITS.PFU.OFFSET_Y,STATU(64*353:64:C) # PFU OFFSET-Y (add ooto 000711)
FITS.PFU.OFFSET-Z,STATU(64*354:64:C) # PFU OFFSET-Z (add ooto 000711)
FITS.PFU.OFFSET_Z,STATU(64*354:64:C) # PFU OFFSET-Z (add ooto 000711)
FITS.PFU.OFFSET-TX,STATU(64*355:64:C) # PFU OFFSET-TX (add ooto 000711)
FITS.PFU.OFFSET_TX,STATU(64*355:64:C) # PFU OFFSET-TX (add ooto 000711)
FITS.PFU.OFFSET-TY,STATU(64*356:64:C) # PFU OFFSET-TY (add ooto 000711)
FITS.PFU.OFFSET_TY,STATU(64*356:64:C) # PFU OFFSET-TY (add ooto 000711)
FITS.PFU.OFFSET-TZ,STATU(64*357:64:C) # PFU OFFSET-TZ (add ooto 000711)
FITS.PFU.OFFSET_TZ,STATU(64*357:64:C) # PFU OFFSET-TZ (add ooto 000711)

# for OHS/CISCO
OHS.STAT.INST,OHSS0001(136:5:C)
OHS.STAT.MTYP,OHSS0001(142:2:C)
OHS.STAT.OBE,OHSS0001(145:9:C)
OHS.STAT.CMOD,OHSS0001(155:5:C)
OHS.STAT.OMOD,OHSS0001(161:12:C)
OHS.MOT.SLX,OHSS0001(174:6:C)
OHS.MOT.SLY,OHSS0001(181:6:C)
OHS.MOT.FL1,OHSS0001(188:7:C)
OHS.MOT.FL2,OHSS0001(196:7:C)
OHS.COV.CAM,OHSS0001(204:5:C)
OHS.COV.MSK,OHSS0001(210:5:C)
OHS.COV.COL,OHSS0001(216:5:C)
OHS.COV.GRT,OHSS0001(222:5:C)
OHS.COV.PIC,OHSS0001(228:5:C)
OHS.MOT.MSK,OHSS0001(234:7:C)
OHS.MOT.FOC,OHSS0001(242:7:C)
OHS.MOT.OSL,OHSS0001(250:7:C)
OHS.DAT.PATH,OHSS0001(258:30:C)
OHS.DAT.FILE,OHSS0001(289:30:C)
OHS.DAT.INUM,OHSS0001(320:4:C)
OHS.DAT.OBJ,OHSS0001(325:30:C)
OHS.DAT.DTYP,OHSS0001(356:10:C)
OHS.DAT.EXP,OHSS0001(367:6:C)
OHS.HKP.DTMP,OHSS0001(374:6:C)
OHS.HKP.STMP,OHSS0001(381:6:C)
OHS.HKP.FTMP,OHSS0001(388:6:C)
OHS.HKP.CTMP,OHSS0001(395:6:C)
OHS.HKP.VDD,OHSS0001(402:6:C)
OHS.HKP.VRES,OHSS0001(409:6:C)
OHS.HKP.HIGH,OHSS0001(416:6:C)
OHS.HKP.BPOW,OHSS0001(423:6:C)
OHS.HKP.CWEL,OHSS0001(430:6:C)
OHS.HKP.NTMP,OHSS0001(437:6:C)

# for AO
AOS.ALIVE,AOSS0001(137:5:C)     # add 2003.10.30
AOS.M1M6.POS,AOSS0001(143:5:C)  # add 2003.10.30
AOS.M1M6.PULS,AOSS0001(149:9:C) # add 2003.10.30
AO.STATUS,AOSS0002(128:512:C)
# AOSS0003
AOS.TT.TT1,AOSS0003(137:10:F) # add 2003.07.03
AOS.TT.TT2,AOSS0003(148:10:F) # add 2003.07.03
AOS.TT.DM1,AOSS0003(159:10:F) # add 2003.07.03
AOS.TT.DM2,AOSS0003(170:10:F) # add 2003.07.03
AOS.APD.AVRG,AOSS0003(181:10:F) # add 2003.12.22
AOS.APD.MAX,AOSS0003(192:10:F) # add 2003.12.22
AOS.APD.RMAG,AOSS0003(203:10:F) # add 2003.12.22
# AOSS0004
AOS.RTS.INS,AOSS0004(137:5:C) # add 2003.12.22
AOS.RTS.STATUS,AOSS0004(143:5:C) # add 2003.12.22
AOS.RTS.DMGAIN,AOSS0004(148:10:F) # add 2003.12.22
AOS.RTS.TTGAIN,AOSS0004(159:8:F) # add 2003.12.22
# AOSS0005
AOS.FG.VOLT,AOSS0005(137:8:F) # add 2003.12.22
AOS.FG.FREQ,AOSS0005(146:7:F) # add 2003.12.22
# AOSS0006
AOS.DAQ.SHUTTER,AOSS0006(137:5:C) # add 2003.12.22
# AOSS0007
AOS.GSAU.R.PULS,AOSS0007(137:10:I) # add 2003.12.22
AOS.GSAU.T.PULS,AOSS0007(148:10:I) # add 2003.12.22
AOS.IRIS.PULS,AOSS0007(159:10:I) # add 2003.12.22
AOS.IRIS.PHI,AOSS0007(170:5:F) # add 2003.12.22
AOS.APD.FW.PULS,AOSS0007(176:10:I) # add 2003.12.22
AOS.APD.FW.MAG,AOSS0007(187:5:F) # add 2003.12.22
# AOSS0008 add 2004.08.03
AOS.PWR.AOL1,AOSS0008(137:3:I)
AOS.PWR.AOL2,AOSS0008(141:3:I)
AOS.PWR.AOL3,AOSS0008(145:3:I)
AOS.PWR.AOL4,AOSS0008(149:3:I)
AOS.PWR.AOL5,AOSS0008(153:3:I)
AOS.PWR.AOL6,AOSS0008(157:3:I)
AOS.PWR.AOL7,AOSS0008(161:3:I)
AOS.PWR.AOL8,AOSS0008(165:3:I)
AOS.PWR.AOL9,AOSS0008(169:3:I)
AOS.PWR.AOL10,AOSS0008(173:3:I)
AOS.PWR.AOL11,AOSS0008(177:3:I)
AOS.PWR.AOL12,AOSS0008(181:3:I)
AOS.PWR.AOL13,AOSS0008(185:3:I)
AOS.PWR.AOL14,AOSS0008(189:3:I)
AOS.PWR.AOL15,AOSS0008(193:3:I)
AOS.PWR.AOL16,AOSS0008(197:3:I)
AOS.PWR.WFS1,AOSS0008(201:3:I)
AOS.PWR.WFS2,AOSS0008(205:3:I)
AOS.PWR.WFS3,AOSS0008(209:3:I)
AOS.PWR.WFS4,AOSS0008(213:3:I)
AOS.PWR.WFS5,AOSS0008(217:3:I)
AOS.PWR.WFS6,AOSS0008(221:3:I)
AOS.PWR.WFS7,AOSS0008(225:3:I)
AOS.PWR.WFS8,AOSS0008(229:3:I)
AOS.PWR.WFS9,AOSS0008(233:3:I)
AOS.PWR.WFS10,AOSS0008(237:3:I)
AOS.PWR.WFS11,AOSS0008(241:3:I)
AOS.PWR.WFS12,AOSS0008(245:3:I)
AOS.PWR.WFS13,AOSS0008(249:3:I)
AOS.PWR.WFS14,AOSS0008(253:3:I)
AOS.PWR.WFS15,AOSS0008(257:3:I)
AOS.PWR.WFS16,AOSS0008(261:3:I)

# AO188 (modified 2011.02.15....Minowa)
AON.STATUS,AONS0001(137:8:C)
AON.BENCH.STATE,AONS0001(146:8:C)
AON.ENSHUT,AONS0001(155:12:C)
AON.ENSHUT.POS,AONS0001(168:9:F)
AON.ENSHUT.STEP,AONS0001(178:8:I)
AON.CAL.X,AONS0001(187:12:C)
AON.CAL.X.POS,AONS0001(200:9:F)
AON.CAL.X.STEP,AONS0001(210:8:I)
AON.CAL.Z,AONS0001(219:12:C)
AON.CAL.Z.POS,AONS0001(232:9:F)
AON.CAL.Z.STEP,AONS0001(242:8:I)
AON.CAL.LD1,AONS0001(251:8:C)
AON.CAL.LD1I,AONS0001(260:8:F)
AON.CAL.LD1P,AONS0001(269:8:F)
AON.CAL.LD2,AONS0001(278:8:C)
AON.CAL.LD2I,AONS0001(287:8:F)
AON.CAL.LD2P,AONS0001(296:8:F)
AON.CAL.LD3,AONS0001(305:8:C)
AON.CAL.LD3I,AONS0001(314:8:F)
AON.CAL.LD3P,AONS0001(323:8:F)
AON.CAL.NGS.FOC,AONS0001(332:12:C)
AON.CAL.NGS.FOC.POS,AONS0001(345:9:F)
AON.CAL.NGS.FOC.STEP,AONS0001(355:8:I)
AON.CAL.LGS.FOC,AONS0001(364:12:C)
AON.CAL.LGS.FOC.POS,AONS0001(377:9:F)
AON.CAL.LGS.FOC.STEP,AONS0001(387:8:I)
AON.CAL.TP1,AONS0001(396:12:C)
AON.CAL.TP1.POS,AONS0001(409:9:F)
AON.CAL.TP1.STEP,AONS0001(419:8:I)
AON.CAL.TP1.ROT,AONS0001(428:12:C)
AON.CAL.TP1.ROT.SPEED,AONS0001(441:9:F)
AON.CAL.TP1.ROT.POS,AONS0001(451:9:F)
AON.CAL.TP1.ROT.STEP,AONS0001(461:8:I)
AON.CAL.TP2,AONS0001(470:12:C)
AON.CAL.TP2.POS,AONS0001(483:9:F)
AON.CAL.TP2.STEP,AONS0001(493:8:I)
AON.CAL.TP2.ROT,AONS0001(502:12:C)
AON.CAL.TP2.ROT.SPEED,AONS0001(515:9:F)
AON.CAL.TP2.ROT.POS,AONS0001(525:9:F)
AON.CAL.TP2.ROT.STEP,AONS0001(535:8:I)
AON.CAL.M3X,AONS0001(544:12:C)
AON.CAL.M3X.POS,AONS0001(557:9:F)
AON.CAL.M3X.STEP,AONS0001(567:8:I)
AON.CAL.M3Y,AONS0001(576:12:C)
AON.CAL.M3Y.POS,AONS0001(589:9:F)
AON.CAL.M3Y.STEP,AONS0001(599:8:I)
AON.BS1,AONS0001(608:12:C)
AON.BS1.POS,AONS0001(621:9:F)
AON.BS1.STEP,AONS0001(631:10:I)
AON.BS2,AONS0001(642:12:C)
AON.BS2.POS,AONS0001(655:9:F)
AON.BS2.STEP,AONS0001(665:10:I)
AON.FCONV,AONS0001(676:12:C)
AON.FCONV.POS,AONS0001(689:9:F)
AON.HWFS.NGSAP,AONS0001(699:12:C)
AON.HWFS.NGSAP.POS,AONS0001(712:9:F)
AON.HWFS.NGSAP.STEP,AONS0001(722:10:I)
AON.HWFS.LGSAP,AONS0001(733:12:C)
AON.HWFS.LGSAP.POS,AONS0001(746:9:F)
AON.HWFS.LGSAP.STEP,AONS0001(756:10:I)
AON.HWFS.ADC,AONS0001(767:12:C)
AON.HWFS.ADC.POS,AONS0001(780:9:F)
AON.HWFS.ADC.STEP,AONS0001(790:10:I)
AON.HWFS.ABS,AONS0001(801:12:C)
AON.HWFS.ABS.POS,AONS0001(814:9:F)
AON.HWFS.ABS.STEP,AONS0001(824:10:I)
AON.HWFS.AFW1,AONS0001(835:12:C)
AON.HWFS.AFW1.POS,AONS0001(848:9:F)
AON.HWFS.AFW1.STEP,AONS0001(858:10:I)
AON.HWFS.AFW2,AONS0001(869:12:C)
AON.HWFS.AFW2.POS,AONS0001(882:9:F)
AON.HWFS.AFW2.STEP,AONS0001(892:10:I)
AON.HWFS.HBS,AONS0001(903:12:C)
AON.HWFS.HBS.POS,AONS0001(916:9:F)
AON.HWFS.HBS.STEP,AONS0001(926:10:I)
AON.HWFS.PBS,AONS0001(937:12:C)
AON.HWFS.PBS.POS,AONS0001(950:9:F)
AON.HWFS.PBS.STEP,AONS0001(960:10:I)
AON.HWFS.LAZ,AONS0001(971:12:C)
AON.HWFS.LAZ.POS,AONS0001(984:9:F)
AON.HWFS.LAZ.STEP,AONS0001(994:10:I)
AON.HWFS.LAFW,AONS0001(1005:12:C)
AON.HWFS.LAFW.POS,AONS0001(1018:9:F)
AON.HWFS.LAFW.STEP,AONS0001(1028:10:I)
AON.HWFS.LASH,AONS0001(1039:8:C)
AON.LWFS.AP1,AONS0001(1048:12:C)
AON.LWFS.AP1.POS,AONS0001(1061:9:F)
AON.LWFS.AP1.STEP,AONS0001(1071:10:I)
AON.LWFS.ADC,AONS0001(1082:12:C)
AON.LWFS.ADC.POS,AONS0001(1095:9:F)
AON.LWFS.ADC.STEP,AONS0001(1105:10:I)
AON.LWFS.ABS,AONS0001(1116:12:C)
AON.LWFS.ABS.POS,AONS0001(1129:9:F)
AON.LWFS.ABS.STEP,AONS0001(1139:10:I)
AON.LWFS.AFW1,AONS0001(1150:12:C)
AON.LWFS.AFW1.POS,AONS0001(1163:9:F)
AON.LWFS.AFW1.STEP,AONS0001(1173:10:I)
AON.LWFS.AFW2,AONS0001(1184:12:C)
AON.LWFS.AFW2.POS,AONS0001(1197:9:F)
AON.LWFS.AFW2.STEP,AONS0001(1207:10:I)
AON.LWFS.AP2,AONS0001(1218:12:C)
AON.LWFS.AP2.SIZE,AONS0001(1231:9:F)
AON.LWFS.AP2.STEP,AONS0001(1241:10:I)
AON.LWFS.PBS,AONS0001(1252:12:C)
AON.LWFS.PBS.POS,AONS0001(1265:9:F)
AON.LWFS.PBS.STEP,AONS0001(1275:10:I)
AON.LWFS.LAZ,AONS0001(1286:12:C)
AON.LWFS.LAZ.POS,AONS0001(1299:9:F)
AON.LWFS.LAZ.STEP,AONS0001(1309:10:I)
AON.LWFS.LAFW,AONS0001(1320:12:C)
AON.LWFS.LAFW.POS,AONS0001(1333:9:F)
AON.LWFS.LAFW.STEP,AONS0001(1343:10:I)
AON.LWFS.LASH,AONS0001(1354:8:C)
AON.HWFS.VMAP,AONS0001(1363:12:C)
AON.HWFS.VMAP.SIZE,AONS0001(1376:9:F)
AON.HWFS.VMAP.STEP,AONS0001(1386:10:I)
AON.ENV.APDTI,AONS0001(1397:6:F)
AON.ENV.APDTO,AONS0001(1404:6:F)
AON.ENV.BNCTI,AONS0001(1411:6:F)
AON.ENV.BNCTO,AONS0001(1418:6:F)
AON.ENV.BNCHI,AONS0001(1425:6:F)
AON.ENV.BNCHO,AONS0001(1432:6:F)

AON.GS.MODE,AONS0002(137:8:C)
AON.IMR.STAT,AONS0002(146:12:C)
AON.IMR.MODE,AONS0002(159:12:C)
AON.IMR.ANGLE,AONS0002(172:9:F)
AON.IMR.PAD,AONS0002(182:9:F)
AON.IMR.PAP,AONS0002(192:9:F)
AON.IMR.RA,AONS0002(202:16:C)
AON.IMR.DEC,AONS0002(219:16:C)
AON.ADC,AONS0002(236:12:C)
AON.ADC.POS,AONS0002(249:9:F)
AON.ADC.STEP,AONS0002(259:10:I)
AON.ADC.STAT,AONS0002(270:12:C)
AON.ADC.MODE,AONS0002(283:12:C)
AON.ADC.FC,AONS0002(296:9:F)
AON.ADC.RA,AONS0002(306:16:C)
AON.ADC.DEC,AONS0002(323:16:C)
AON.ADC.PA,AONS0002(340:9:F)
AON.ADC.ANG1,AONS0002(350:9:F)
AON.ADC.STEP1,AONS0002(360:10:I)
AON.ADC.ANG2,AONS0002(371:9:F)
AON.ADC.STEP2,AONS0002(381:10:I)
AON.AU1.XMM,AONS0002(392:9:F)
AON.AU1.YMM,AONS0002(402:9:F)
AON.AU1.XASEC,AONS0002(412:9:F)
AON.AU1.YASEC,AONS0002(422:9:F)
AON.AU1.FOC,AONS0002(432:9:F)
AON.AU1.TILTX,AONS0002(442:9:F)
AON.AU1.TILTY,AONS0002(452:9:F)
AON.AU1.M1X,AONS0002(462:9:F)
AON.AU1.M1Y,AONS0002(472:9:F)
AON.AU1.M1Z,AONS0002(482:9:F)
AON.AU1.M2X,AONS0002(492:9:F)
AON.AU1.M2Y,AONS0002(502:9:F)
AON.AU1.GSX,AONS0002(512:9:F)
AON.AU1.GSY,AONS0002(522:9:F)
AON.AU2.XMM,AONS0002(532:9:F)
AON.AU2.YMM,AONS0002(542:9:F)
AON.AU2.XASEC,AONS0002(552:9:F)
AON.AU2.YASEC,AONS0002(562:9:F)
AON.AU2.FOC,AONS0002(572:9:F)
AON.AU2.TILTX,AONS0002(582:9:F)
AON.AU2.TILTY,AONS0002(592:9:F)
AON.AU2.M1X,AONS0002(602:9:F)
AON.AU2.M1Y,AONS0002(612:9:F)
AON.AU2.M1Z,AONS0002(622:9:F)
AON.AU2.M2X,AONS0002(632:9:F)
AON.AU2.M2Y,AONS0002(642:9:F)
AON.AU2.GSX,AONS0002(652:9:F)
AON.AU2.GSY,AONS0002(662:9:F)
AON.VM.DRIVE,AONS0002(672:8:C)
AON.VM.VOLT,AONS0002(681:6:F)
AON.VM.FREQ,AONS0002(688:6:F)
AON.VM.PHASE,AONS0002(695:6:F)
AON.HWFS.ADC.STAT,AONS0002(702:12:C)
AON.HWFS.ADC.MODE,AONS0002(715:12:C)
AON.HWFS.ADC.FC,AONS0002(728:9:F)
AON.HWFS.ADC.RA,AONS0002(738:16:C)
AON.HWFS.ADC.DEC,AONS0002(755:16:C)
AON.HWFS.ADC.PA,AONS0002(772:9:F)
AON.HWFS.ADC.ANG1,AONS0002(782:9:F)
AON.HWFS.ADC.STEP1,AONS0002(792:10:I)
AON.HWFS.ADC.ANG2,AONS0002(803:9:F)
AON.HWFS.ADC.STEP2,AONS0002(813:10:I)
AON.LWFS.ADC.STAT,AONS0002(824:12:C)
AON.LWFS.ADC.MODE,AONS0002(837:12:C)
AON.LWFS.ADC.FC,AONS0002(850:9:F)
AON.LWFS.ADC.RA,AONS0002(860:16:C)
AON.LWFS.ADC.DEC,AONS0002(877:16:C)
AON.LWFS.ADC.PA,AONS0002(894:9:F)
AON.LWFS.ADC.ANG1,AONS0002(904:9:F)
AON.LWFS.ADC.STEP1,AONS0002(914:10:I)
AON.LWFS.ADC.ANG2,AONS0002(925:9:F)
AON.LWFS.ADC.STEP2,AONS0002(935:10:I)
AON.HWFS.APDAV,AONS0002(946:8:F)
AON.LWFS.APDAV,AONS0002(955:8:F)
AON.RTS.LOOP,AONS0002(964:8:C)
AON.RTS.DMGAIN,AONS0002(973:7:F)
AON.RTS.TTGAIN,AONS0002(981:7:F)
AON.RTS.PSUBGAIN,AONS0002(989:7:F)
AON.RTS.WTTGAIN,AONS0002(997:7:F)
AON.RTS.LTTGAIN,AONS0002(1005:7:F)
AON.RTS.LDFGAIN,AONS0002(1013:7:F)
AON.RTS.HTTGAIN,AONS0002(1021:7:F)
AON.RTS.HDFGAIN,AONS0002(1029:7:F)
AON.RTS.ADFGAIN,AONS0002(1037:7:F)
AON.RTS.STTGAIN,AONS0002(1045:7:F)
AON.TT.TTX,AONS0002(1053:8:F)
AON.TT.TTY,AONS0002(1062:8:F)
AON.TT.WTTC1,AONS0002(1071:8:F)
AON.TT.WTTC2,AONS0002(1080:8:F)
AON.TT.CTTC1,AONS0002(1089:8:F)
AON.TT.CTTC2,AONS0002(1098:8:F)
AON.RTS.DMCMTX,AONS0002(1107:16:C)
AON.RTS.TTCMTX,AONS0002(1124:16:C)

# added 2011-10-19
AON.AU1.TRACK.STAT,AONS0002(1141:12:C)
AON.AU1.TRACK.MODE,AONS0002(1154:12:C)
AON.AU1.TRACK.IMRMODE,AONS0002(1167:12:C)
AON.AU1.TRACK.RA,AONS0002(1180:16:C)
AON.AU1.TRACK.DEC,AONS0002(1197:16:C)
AON.AU1.TRACK.PA,AONS0002(1214:9:F)
AON.AU1.TRACK.REFWL,AONS0002(1224:9:F)
AON.AU1.TRACK.OBSWL,AONS0002(1234:9:F)
AON.AU1.TRACK.TEMP,AONS0002(1244:9:F)
AON.AU1.TRACK.PRES,AONS0002(1254:9:F)
AON.AU1.TRACK.RH,AONS0002(1264:9:F)
AON.AU1.TRACK.FILE,AONS0002(1274:16:C)
AON.AU2.TRACK.STAT,AONS0002(1291:12:C)
AON.AU2.TRACK.MODE,AONS0002(1304:12:C)
AON.AU2.TRACK.IMRMODE,AONS0002(1317:12:C)
AON.AU2.TRACK.RA,AONS0002(1330:16:C)
AON.AU2.TRACK.DEC,AONS0002(1347:16:C)
AON.AU2.TRACK.PA,AONS0002(1364:9:F)
AON.AU2.TRACK.REFWL,AONS0002(1374:9:F)
AON.AU2.TRACK.OBSWL,AONS0002(1384:9:F)
AON.AU2.TRACK.TEMP,AONS0002(1394:9:F)
AON.AU2.TRACK.PRES,AONS0002(1404:9:F)
AON.AU2.TRACK.RH,AONS0002(1414:9:F)
AON.AU2.TRACK.FILE,AONS0002(1424:16:C)





# LGS
LGS.STATUS,LGSS0001(137:8:C)
LGS.LASER.STATE,LGSS0001(146:12:C)
LGS.LASER.1064.CHL,LGSS0001(159:12:C)
LGS.LASER.1319.CHL,LGSS0001(172:12:C)
LGS.LASER.1064.RFP,LGSS0001(185:12:C)
LGS.LASER.1319.RFP,LGSS0001(198:12:C)
LGS.LASER.1064.LDC,LGSS0001(211:6:F)
LGS.LASER.1064.LDPWS,LGSS0001(218:12:C)
LGS.LASER.1319.LDC,LGSS0001(231:6:F)
LGS.LASER.1319.LDPWS,LGSS0001(238:12:C)
LGS.LASER.1064.SHUTTER,LGSS0001(251:12:C)
LGS.LASER.1319.SHUTTER,LGSS0001(264:12:C)
LGS.LASER.589.SHUTTER,LGSS0001(277:12:C)
LGS.LASER.SFGCSTL.TCTL,LGSS0001(290:12:C)
LGS.LASER.SFGCSTL.STMP,LGSS0001(303:6:F)
LGS.LASER.SFGCSTL.TMP,LGSS0001(310:6:F)
LGS.LASER.1064.ETL.TCTL,LGSS0001(317:12:C)
LGS.LASER.1064.ETL.STMP,LGSS0001(330:6:F)
LGS.LASER.1064.ETL.TMP,LGSS0001(337:6:F)
LGS.LASER.1319.ETL.TCTL,LGSS0001(344:12:C)
LGS.LASER.1319.ETL.STMP,LGSS0001(357:6:F)
LGS.LASER.1319.ETL.TMP,LGSS0001(364:6:F)
LGS.LASER.LHEAD.TMP,LGSS0001(371:6:F)
LGS.LASER.LENCL.TMP1,LGSS0001(378:6:F)
LGS.LASER.LENCL.TMP2,LGSS0001(385:6:F)
LGS.LASER.LENCL.TMP3,LGSS0001(392:6:F)
LGS.LASER.1064.PWR,LGSS0001(399:6:F)
LGS.LASER.1319.PWR,LGSS0001(406:6:F)
LGS.LASER.589.PWR,LGSS0001(413:6:F)
LGS.LASER.ML.DRV.FREQ,LGSS0001(420:8:F)
LGS.LASER.ML.DRV.PHASE,LGSS0001(429:6:F)
LGS.LASER.REP.RATE,LGSS0001(436:8:F)
LGS.LASER.PCU.STAT,LGSS0001(445:16:C)
LGS.LASER.RCU.STAT,LGSS0001(462:16:C)
LGS.LDS.HWP1.POS,LGSS0001(479:6:F)
LGS.LDS.HWP1.STEP,LGSS0001(486:8:I)
LGS.LDS.HWP2.POS,LGSS0001(495:6:F)
LGS.LDS.HWP2.STEP,LGSS0001(502:8:I)
LGS.LDS.HWP3.POS,LGSS0001(511:6:F)
LGS.LDS.HWP3.STEP,LGSS0001(518:8:I)
LGS.LDS.QWP.POS,LGSS0001(527:6:F)
LGS.LDS.QWP.STEP,LGSS0001(534:8:I)
LGS.LDS.SODCELL,LGSS0001(543:6:F)
LGS.LDS.SODCELL.PMTG,LGSS0001(550:6:F)
LGS.LDS.SODCELL.TMP,LGSS0001(557:6:F)
LGS.FIBER.ID,LGSS0001(564:8:I)
LGS.FIBER.CPLENS.POS.X,LGSS0001(573:9:F)
LGS.FIBER.CPLENS.POS.Y,LGSS0001(583:9:F)
LGS.FIBER.CPLENS.POS.Z,LGSS0001(593:9:F)
LGS.FIBER.FIBHOLD.POS.X,LGSS0001(603:9:F)
LGS.FIBER.FIBHOLD.POS.Y,LGSS0001(613:9:F)
LGS.FIBER.FIBHOLD.POS.Z,LGSS0001(623:9:F)
LGS.FIBER.RETPWR,LGSS0001(633:6:F)
LGS.FIBER.RETPWR.RANGE,LGSS0001(640:4:I)
LGS.FIBER.THROUGHPUT,LGSS0001(645:6:F)
LGS.LSROOM.STATE,LGSS0001(652:12:C)
LGS.LSROOM.STMP,LGSS0001(665:6:F)
LGS.LSROOM.1064.HEFAN,LGSS0001(672:12:C)
LGS.LSROOM.1319.HEFAN,LGSS0001(685:12:C)
LGS.LSROOM.ROOF.HEFAN,LGSS0001(698:12:C)
LGS.LSROOM.VALV.STAT.H,LGSS0001(711:12:C)
LGS.LSROOM.VALV.STAT.L,LGSS0001(724:12:C)
LGS.LSROOM.COL.FLWRATE,LGSS0001(737:6:F)
LGS.LSROOM.LCR.HUM,LGSS0001(744:6:F)
LGS.LSROOM.LCR.TMP1,LGSS0001(751:6:F)
LGS.LSROOM.LCR.TMP2,LGSS0001(758:6:F)
LGS.LSROOM.LCR.TMP3,LGSS0001(765:6:F)
LGS.LSROOM.LCR.TMP4,LGSS0001(772:6:F)
LGS.LSROOM.LCR.TMP5,LGSS0001(779:6:F)
LGS.LSROOM.CTR.TMP1,LGSS0001(786:6:F)
LGS.LSROOM.CTR.TMP2,LGSS0001(793:6:F)
LGS.LSROOM.CTR.TMP3,LGSS0001(800:6:F)
LGS.LSROOM.CTR.TMP4,LGSS0001(807:6:F)
LGS.LSROOM.CTR.TMP5,LGSS0001(814:6:F)
LGS.LLT.LAUNCH.STATE,LGSS0001(821:12:C)
LGS.LLT.COLLENS.X.POS,LGSS0001(834:10:F)
LGS.LLT.COLLENS.X.STEP,LGSS0001(845:8:I)
LGS.LLT.COLLENS.Y.POS,LGSS0001(854:10:F)
LGS.LLT.COLLENS.Y.STEP,LGSS0001(865:8:I)
LGS.LLT.COLLENS.Z.POS,LGSS0001(874:10:F)
LGS.LLT.COLLENS.Z.STEP,LGSS0001(885:8:I)
LGS.LLT.M3.X.POS,LGSS0001(894:10:F)
LGS.LLT.M3.X.STEP,LGSS0001(905:8:I)
LGS.LLT.M3.Z.POS,LGSS0001(914:10:F)
LGS.LLT.M3.Z.STEP,LGSS0001(925:8:I)
LGS.LLT.LASER.PWR,LGSS0001(934:6:F)
LGS.LLT.TMP.OPT,LGSS0001(941:6:F)
LGS.LLT.TMP.IR,LGSS0001(948:6:F)
LGS.LLT.TMP.FRONT,LGSS0001(955:6:F)
LGS.LLT.TMP.REAR,LGSS0001(962:6:F)
LGS.LLT.SHUT,LGSS0001(969:12:C)
LGS.LLT.COVER,LGSS0001(982:12:C)
LGS.EMGSHUT.STAT.E,LGSS0001(995:12:C)
LGS.EMGSHUT.STAT.W,LGSS0001(1008:12:C)
LGS.EMGSHUT.STAT.C,LGSS0001(1021:12:C)
LGS.LTCS.POLICY,LGSS0001(1034:12:C)
LGS.LTCS.SHUT.STAT,LGSS0001(1047:12:C)
LGS.LTCS.LASER.STAT,LGSS0001(1060:12:C)
LGS.LTCS.TELCOL.STAT,LGSS0001(1073:12:C)
LGS.LTCS.SATCOL.STAT,LGSS0001(1086:12:C)
LGS.LTCS.TELCOL.TWIN,LGSS0001(1099:8:I)
LGS.LTCS.SATCOL.TWIN,LGSS0001(1108:8:I)


# CIAO
CIAO.STATUS,CIAS0001(137:5:C) # add 2003.07.03
CIAO.ALIVE,CIAS0001(137:5:C)  # added 2007.09.19
CIAO.OBSCONF.OBJXPOS,CIAS0002(137:5:F) # add 2003.07.03
CIAO.OBSCONF.OBJYPOS,CIAS0002(143:5:F) # add 2003.07.03
CIAO.OBSCONF.DESTXPOS,CIAS0002(149:6:F) # add 2003.07.03
CIAO.OBSCONF.DESTYPOS,CIAS0002(156:6:F) # add 2003.07.03
CIAO.OBSCONF.MASKXPOS,CIAS0002(163:5:F) # add 2003.07.03
CIAO.OBSCONF.MASKYPOS,CIAS0002(169:5:F) # add 2003.07.03
CIAO.OBSCONF.SLTCPIX1,CIAS0002(175:5:F) # add 2003.07.03
CIAO.OBSCONF.SLTCPIX2,CIAS0002(181:5:F) # add 2003.07.03
CIAO.OBSCONF.AOPNTX,CIAS0002(187:6:F) # add 2003.07.03
CIAO.OBSCONF.AOPNTY,CIAS0002(194:6:F) # add 2003.07.03
CIAO.OBSCONF.FWHM,CIAS0002(201:5:F) # add 2003.07.03
CIAO.OBSCONF.STREHL,CIAS0002(207:4:F) # add 2003.07.03
CIAO.OBSCONF.PEAK,CIAS0002(212:8:I) # add 2003.07.03
CIAO.GENCONF.SHTSTAT,CIAS0004(137:5:C) # add 2003.07.03
CIAO.GENCONF.MASKID,CIAS0004(143:8:C) # add 2003.07.03
CIAO.GENCONF.MASKPOS,CIAS0004(152:8:I) # add 2003.07.03
CIAO.GENCONF.COLX,CIAS0004(161:8:I) # add 2003.07.03
CIAO.GENCONF.COLY,CIAS0004(170:8:I) # add 2003.07.03
CIAO.GENCONF.STOPID,CIAS0004(179:8:C) # add 2003.07.03
CIAO.GENCONF.STOPANG,CIAS0004(188:6:F) # add 2003.07.03
CIAO.GENCONF.STOPROT,CIAS0004(195:4:C) # add 2003.07.03
CIAO.GENCONF.FLT1ID,CIAS0004(200:8:C) # add 2003.07.03
CIAO.GENCONF.FLT2ID,CIAS0004(209:8:C) # add 2003.07.03
CIAO.GENCONF.FLT3ID,CIAS0004(218:8:C) # add 2003.07.03
CIAO.GENCONF.CAMERA,CIAS0004(227:8:C) # add 2003.07.03
CIAO.GENCONF.DETPOS,CIAS0004(236:8:I) # add 2003.07.03
CIAO.POLCONF.POL1ID,CIAS0005(137:8:C) # add 2003.07.03
CIAO.POLCONF.POL2ID,CIAS0005(146:8:C) # add 2003.07.03
CIAO.POLCONF.POL2ANG,CIAS0005(155:5:F) # add 2003.07.03
CIAO.POLCONF.POL2OFS,CIAS0005(161:4:F) # add 2003.07.03
CIAO.POLCONF.POL3ID,CIAS0005(166:8:C) # add 2003.07.03
CIAO.POLCONF.POL3ANG,CIAS0005(175:5:F) # add 2003.07.03
CIAO.POLCONF.POL3OFS,CIAS0005(181:4:F) # add 2003.07.03
CIAO.POLCONF.POLARIZER,CIAS0005(186:8:C) # add 2003.07.03

# CAC
CAC.COOLER,CACS0001(144:4:C) # CAC status
CAC.SHUTTER,CACS0001(159:4:C) # CAC status
CAC.FILTER1,CACS0001(173:6:C) # CAC status
CAC.FILTER2,CACS0001(195:6:C) # CAC status
CAC.DET-TMP,CACS0001(216:7:C) # CAC status
# for - (2001.09.06 ooto)
CAC.DET_TMP,CACS0001(216:7:C) # CAC status

# for FMS       added 2008-06-17 (BB)
FMS.ALIVE,FMSS0001(137:20:C:)
FMS.STATCNT,FMSS0001(158:32:C:)
FMS.ECH.RA.OFFSET,FMSS0001(191:32:C:)
FMS.ECH.DEC.OFFSET,FMSS0001(224:32:C:)
FMS.ECH.PA.OFFSET,FMSS0001(257:32:C:)
FMS.ECH.CNFFLD.ERR,FMSS0001(290:32:C:)  # added 2008-08-25 (BB)
FMS.ECH.CHKFLD.ERR,FMSS0001(323:32:C:)  # added 2008-08-25 (BB)
FMS.ECH.BS.DRA,FMSS0001(356:32:C:)      # added 2009-04-16 (PJT)
FMS.ECH.BS.DDEC,FMSS0001(389:32:C:)     # added 2009-04-16 (PJT)
FMS.ECH.FLD.RA,FMSS0001(422:32:C:)      # added 2009-04-17 (PJT)
FMS.ECH.FLD.DEC,FMSS0001(455:32:C:)     # added 2009-04-17 (PJT)
FMS.ECH.FLD.PA,FMSS0001(488:32:C:)      # added 2009-04-17 (PJT)
FMS.ECH.EQUINOX,FMSS0001(521:32:C:)     # added 2009-07-21 (PJT)
FMS.IRS2.NDWELL,FMSS0001(554:32:C:)     # added 2009-07-21 (PJT)
FMS.IRS2.NSAMP,FMSS0001(587:32:C:)      # added 2009-07-21 (PJT)
FMS.CALC.ELEV,FMSS0001(620:32:C:)       # added 2009-11-30 takeshi

# for WAV       added 2007.09.19, modified 2007-11-21 (BB)
WAV.ALIVE,WAVS0001(137:20:C:)
WAV.STG1,WAVS0001(157:10:C:)
WAV.STG1_PS,WAVS0001(167:10:C:)
WAV.STG2,WAVS0001(177:10:C:)
WAV.STG2_PS,WAVS0001(187:10:C:)
WAV.STG3,WAVS0001(197:10:C:)
WAV.STG3_PS,WAVS0001(207:10:C:)
WAV.RT_PLT1,WAVS0001(217:10:C:)
WAV.RT_ANG1,WAVS0001(227:10:C:)
WAV.RT_POS1,WAVS0001(237:10:C:)
WAV.RT_MD1,WAVS0001(247:10:C:)
WAV.RT_PLT2,WAVS0001(257:10:C:)
WAV.RT_ANG2,WAVS0001(267:10:C:)
WAV.RT_POS2,WAVS0001(277:10:C:)
WAV.RT_MD2,WAVS0001(287:10:C:)
WAV.RT_PLT3,WAVS0001(297:10:C:)
WAV.RT_ANG3,WAVS0001(307:10:C:)
WAV.RT_POS3,WAVS0001(317:10:C:)
WAV.RT_MD3,WAVS0001(327:10:C:)
WAV.RT_PLT4,WAVS0001(337:10:C:)
WAV.RT_ANG4,WAVS0001(347:10:C:)
WAV.RT_POS4,WAVS0001(357:10:C:)
WAV.RT_MD4,WAVS0001(367:10:C:)
WAV.POLARIZ1,WAVS0001(377:10:C:)

# for OTSUBO
STATUS.MLP2_L2,TSCL($TSCL_MLP2+1:1160:B)
STATUS.MLP2_L3A,TSCL($TSCL_MLP2_L3+1:976:B)
STATUS.MLP2_L3F,TSCL($TSCL_MLP2_L3+1017:46:B)
STATUS.MLP2_VZ,TSCV($TSCV00B2+132:587:B)
STATUS.MLP2_V2,TSCV($TSCV00B2+770:191:B)
STATUS.AG_V,TSCV($TSCV0006+1:100:B)
STATUS.AG_L,TSCL($TSCL_AG+1:56:B)

# for exec OBS STATUSCHECK command use
AG.AG1DX,TSCL($TSCL_AG+9:4:S:0.01) # AG1dX
AG.AG1DY,TSCL($TSCL_AG+13:4:S:0.01) # AG1dY
AG.AG2dX,TSCL($TSCL_AG+19:4:S:0.01) # AG2dX
AG.AG2dY,TSCL($TSCL_AG+23:4:S:0.01) # AG2dY
AG.AG1CX,TSCV($TSCV0006+46:4:S:0.01) # AG1 original position X
AG.AG1CY,TSCV($TSCV0006+50:4:S:0.01) # AG1 original position Y
AG.AG2CX,TSCV($TSCV0006+54:4:S:0.01) # AG2 original position X
AG.AG2CY,TSCV($TSCV0006+58:4:S:0.01) # AG2 original position Y
AG.AGPIRDX,TSCL($TSCL_OBCP+9:4:S:0.01) # AG for SH Error dX(marcsec) (add ukawa 2005.02.17)
AG.AGPIRDY,TSCL($TSCL_OBCP+13:4:S:0.01) # AG for SH Error dY(marcsec) (add ukawa 2005.02.17)
AG.AGPIRCX,TSCV($TSCV003B+26:4:S:0.01) # AG for SH original position X(pixel)(add ukawa 2005.02.17)
AG.AGPIRCY,TSCV($TSCV003B+30:4:S:0.01) # AG for SH original position Y(pixel)(add ukawa 2005.02.17)

# for VGW T.B.D.(SV move) command use 
VGWCMD.IMGROT_FLG,TSCV($TSCV0004+12:1:B:H0A) # VGW command (ImgRot 12:blue 0c:red 14:out or else) (1999.02.18 add Mr.kosugi) (2001.04.19 modify ooto)
#VGWCMD.IMGROT_FLG,TSCV($TSCV0004+12:1:B:H06)  # VGW command (ImgRot 02:blue 04:red 00:out or else) (1999.02.18 add Mr.kosugi)
VGWCMD.ADC_FLG,TSCV($TSCV0004+30:1:B:H04) # VGW command (ADC 04:in 00:out or else) (1999.02.18 add Mr.kosugi)

# for CXWS use status (2001.05.15 add ooto)
CXWS.TSCS.EL,TSCS($TSCS_MTDR+7:6:D) # EL(deg)
CXWS.TSCV.TELDRIVE,TSCV($TSCV0002+4:1:B:H3F) # AZ,EL Drive On,Off,Ready
CXWS.TSCV.STOW_1,TSCV($TSCV0002+9:1:B:H7F) # STOW status
CXWS.TSCV.STOW_2,TSCV($TSCV0027+1:1:B:H70) # STOW status
CXWS.TSCS.INSROT,TSCS($TSCS_FRAD+1:6:D) # InsRot Real Angle(deg)
CXWS.TSCV.SHUTTER,TSCV($TSCV0030+4:1:B) # Shutter Open,Close,Limit
CXWS.TSCV.POWER_V1,TSCV($TSCV0032+1:22:B) # BOLT status
CXWS.TSCV.POWER_V2,TSCL($TSCL_BOLT+25:96:B) # BOLT status
CXWS.TSCV.POWER_V3,TSCL($TSCL_MLP3+41:8:B) # BOLT status
CXWS.TSCL.Z_SENSOR,TSCL($TSCL_BOLT+1:24:B) # Z sensor
CXWS.TSCV.0_SENSOR,TSCV($TSCV00B3+39:1:B) # 0/-4 sensor
CXWS.TSCL.POWER,TSCL($TSCL_BOLT+113:28:B) # Power supply

# for CXWS use status (2002.07.01 add watanabe)
CXWS.TSCV.OBE_ID,TSCV($TSCV00A1+629:20:B) # OBE NAME
CXWS.TSCV.CIAX_MLP3_FAULT,TSCV($TSCV00B3+5:1:B:H10) # CIAX-MLP3 fault
CXWS.TSCV.COML_PWR,TSCV($TSCV00A1+12:1:B) # Power Fail Status

# for CXWS use status (2003.09.22 add ukawa)
CXWS.TSCV.OBE_INR,TSCV($TSCV00A1+66:4:C)

# for CIAX (2001,10,31 add yamamoto)
TSCV.TSC.LOGIN0,TSCV($TSCV00A1+75:6:C)  # Which computer login to TSC
TSCV.TSC.LOGIN1,TSCV($TSCV00A1+105:6:C) # Which computer login to TSC
TSCV.TSC.LOGIN2,TSCV($TSCV00A1+135:6:C) # Which computer login to TSC
TSCV.TSC.LOGIN3,TSCV($TSCV00A1+165:6:C) # Which computer login to TSC
TSCV.TSC.LOGIN4,TSCV($TSCV00A1+195:6:C) # Which computer login to TSC
TSCV.TSC.LOGIN5,TSCV($TSCV00A1+225:6:C) # Which computer login to TSC
TSCV.TSC.LOGIN6,TSCV($TSCV00A1+255:6:C) # Which computer login to TSC
TSCV.TSC.LOGIN7,TSCV($TSCV00A1+285:6:C) # Which computer login to TSC
TSCV.TSC.LOGIN8,TSCV($TSCV00A1+315:6:C) # Which computer login to TSC
TSCV.TSC.LOGIN9,TSCV($TSCV00A1+345:6:C) # Which computer login to TSC

# for DomeUPS (2001.05.18 add ooto)
TSCV.DOMEUPS,TSCV($TSCV00B3+25:1:B:H80) # DomeUPS status (2004.02.26 ukawa changed)
TSCV.UPS2INFO1,TSCV($TSCV00B3+53:1:B:HF0) # DomeUPS status
TSCV.UPS2INFO2,TSCV($TSCV00B3+54:1:B:H7F) # DomeUPS status
TSCV.UPS2ALRM,TSCV($TSCV0002+168:1:B:H40) # DomeUPS status

# for VGW skymonitor (2001.06.19 add ooto)
TSCS.AZ_CMD,TSCS($TSCS_MTDR+13:6:D) # command AZ(deg)
TSCS.EL_CMD,TSCS($TSCS_MTDR+19:6:D) # command EL(deg)
TSCS.AZ_REAL,TSCS($TSCS_MTDR+1:6:D) # command AZ(deg) real
TSCS.EL_REAL,TSCS($TSCS_MTDR+7:6:D) # command EL(deg) real

# for TEST stat1024
Z101.RUN,Z101(40:8:C)
Z200.RUN,Z200(40:8:C)

# add 2002.08.26
TSCL.WIND_MAX_SPEED,TSCL($TSCL_WMON+19:6:D)
TSCL.WS,TSCL($TSCL_THRM+1:6:D)
TSCL.TSF,TSCL($TSCL_THRM+7:6:D)
TSCL.TSR,TSCL($TSCL_THRM+13:6:D)

# add 2004.02.11 for limit
TSCL.LIMIT_EL_LOW,TSCL($TSCL_TSC+217:4:S) # EL Low Limit Timer(min)
TSCL.LIMIT_EL_HIGH,TSCL($TSCL_TSC+221:4:S) # EL High Limit Timer(min)
TSCL.LIMIT_AZ,TSCL($TSCL_TSC+225:4:S) # AZ Limit Timer(min)
TSCL.LIMIT_ROT,TSCL($TSCL_TSC+229:4:S) # Rotator Limit Timer(min)
TSCL.LIMIT_FLAG,TSCL($TSCL_TSC+234:1:B:H0F) # Rotator Limit Timer(min)

# add 2004.05.13 for limit
TSCV.PROBE_LINK,TSCV($TSCV00B1+7:1:B:H01) # AG/SH Position(mount sync) mode 2004.05.13

# for DOMEFF (add ukawa 2004.05.14)
TSCL.DOMEFF_A_CUR,TSCL($TSCL_DOMEFLAT+1:6:D)
TSCL.DOMEFF_A_CUR_CMD,TSCL($TSCL_DOMEFLAT+7:6:D)
TSCL.DOMEFF_1B_CUR,TSCL($TSCL_DOMEFLAT+13:6:D)
TSCL.DOMEFF_1B_CUR_CMD,TSCL($TSCL_DOMEFLAT+19:6:D)
TSCL.DOMEFF_2B_CUR,TSCL($TSCL_DOMEFLAT+25:6:D)
TSCL.DOMEFF_2B_CUR_CMD,TSCL($TSCL_DOMEFLAT+31:6:D)
TSCL.DOMEFF_3B_CUR,TSCL($TSCL_DOMEFLAT+37:6:D)
TSCL.DOMEFF_3B_CUR_CMD,TSCL($TSCL_DOMEFLAT+43:6:D)
TSCL.DOMEFF_4B_CUR,TSCL($TSCL_DOMEFLAT+49:6:D)
TSCL.DOMEFF_4B_CUR_CMD,TSCL($TSCL_DOMEFLAT+55:6:D)
TSCL.DOMEFF_A_VOL,TSCL($TSCL_DOMEFLAT+61:6:D)
TSCL.DOMEFF_A_VOL_CMD,TSCL($TSCL_DOMEFLAT+67:6:D)
TSCL.DOMEFF_1B_VOL,TSCL($TSCL_DOMEFLAT+73:6:D)
TSCL.DOMEFF_1B_VOL_CMD,TSCL($TSCL_DOMEFLAT+79:6:D)
TSCL.DOMEFF_2B_VOL,TSCL($TSCL_DOMEFLAT+85:6:D)
TSCL.DOMEFF_2B_VOL_CMD,TSCL($TSCL_DOMEFLAT+91:6:D)
TSCL.DOMEFF_3B_VOL,TSCL($TSCL_DOMEFLAT+97:6:D)
TSCL.DOMEFF_3B_VOL_CMD,TSCL($TSCL_DOMEFLAT+103:6:D)
TSCL.DOMEFF_4B_VOL,TSCL($TSCL_DOMEFLAT+109:6:D)
TSCL.DOMEFF_4B_VOL_CMD,TSCL($TSCL_DOMEFLAT+115:6:D)

# for Pump/Chiller A (add ukawa 2004.05.25)
TSCL.HEATEX_A.TEMP_CHILLER_OUT,TSCL($TSCL_HT_EXH+1:6:D)
TSCL.HEATEX_A.TEMP_CHILLER_IN,TSCL($TSCL_HT_EXH+7:6:D)
TSCL.HEATEX_A.TEMP_TLSCP,TSCL($TSCL_HT_EXH+13:6:D)
TSCL.HEATEX_A.TEMP_TLSCP_RET,TSCL($TSCL_HT_EXH+19:6:D)
TSCL.HEATEX_A.TEMP_MIRROR,TSCL($TSCL_HT_EXH+25:6:D)
TSCL.HEATEX_A.TEMP_MIRROR_RET,TSCL($TSCL_HT_EXH+31:6:D)
TSCL.HEATEX_A.FLOW_TLSCP,TSCL($TSCL_HT_EXH+37:6:D)
TSCL.HEATEX_A.FLOW_MIRROR,TSCL($TSCL_HT_EXH+43:6:D)
TSCL.HEATEX_A.PRESS_TLSCP,TSCL($TSCL_HT_EXH+49:6:D)
TSCL.HEATEX_A.PRESS_MIRROR,TSCL($TSCL_HT_EXH+55:6:D)
# Additional Pump/Chiller A items (added by rkackley 2011.11.3)
TSCL.HEATEX_A.TEMP_TLSCP_CMD,TSCL($TSCL_HT_EXH+61:6:D) # Heat Exh TLSCP Coolant Temp CMD
TSCL.HEATEX_A.TEMP_MIRROR_CMD_HT_EXH,TSCL($TSCL_HT_EXH+67:6:D) # Heat Exh Mirror Coolant Temp CMD on HT EXH
TSCV.HEATEX_A.PUMP_CHILLER,TSCV($TSCV0031+1:1:B:H30) # Heat Exh Chiller Pump OPN and Stop
TSCV.HEATEX_A.PUMP_TLSCP,TSCV($TSCV0031+2:1:B:H03) # Heat Exh TLSCP Pump OPN and Stop
TSCV.HEATEX_A.PUMP_MIRROR,TSCV($TSCV0031+2:1:B:H30) # Heat Exh Mirror Pump OPN and Stop
TSCV.HEATEX_A.PUMP_CHILLER_A,TSCV($TSCV0031+3:1:B:H03) # Heat Exh Pump Chiller-A OPN and Stop
#
# for Pump/Chiller B (add ukawa 2004.05.25)
TSCL.HEATEX_B.TEMP_CHILLER_OUT,TSCL($TSCL_HEAT_EXH+1:6:D)
TSCL.HEATEX_B.TEMP_CHILLER_IN,TSCL($TSCL_HEAT_EXH+7:6:D)
TSCL.HEATEX_B.TEMP_INST,TSCL($TSCL_HEAT_EXH+13:6:D)
TSCL.HEATEX_B.TEMP_INST_RET,TSCL($TSCL_HEAT_EXH+19:6:D)
TSCL.HEATEX_B.FLOW_INST,TSCL($TSCL_HEAT_EXH+25:6:D)
TSCL.HEATEX_B.PRESS_INST,TSCL($TSCL_HEAT_EXH+31:6:D)
# Additional Pump/Chiller B items (added by rkackley 2011.11.3)
TSCV.HEATEX_B.PUMP_CHILLER,TSCV($TSCV0038+1:1:B:H03) # Cryogenics Exh Chiller Pump OPN and Stop
TSCV.HEATEX_B.PUMP,TSCV($TSCV0038+1:1:B:H30) # Cryogenics Exh Pump OPN and Stop
TSCV.HEATEX_B.PUMP_CHILLER_B,TSCV($TSCV0038+2:1:B:H03) # Cryogenics Exh Chiller-B OPN and Stop
#
# for Pump/Chiller D (add ukawa 2004.05.25)
TSCL.HEATEX_D.TEMP_CHILLER_IN,TSCL($TSCL_RED_EXH+1:6:D)
TSCL.HEATEX_D.TEMP_CHILLER_OUT,TSCL($TSCL_RED_EXH+7:6:D)
TSCL.HEATEX_D.TEMP_TLSCP,TSCL($TSCL_RED_EXH+13:6:D)
TSCL.HEATEX_D.TEMP_TLSCP_RET,TSCL($TSCL_RED_EXH+19:6:D)
TSCL.HEATEX_D.TEMP_MIRROR,TSCL($TSCL_RED_EXH+25:6:D)
TSCL.HEATEX_D.TEMP_MIRROR_RET,TSCL($TSCL_RED_EXH+31:6:D)
TSCL.HEATEX_D.FLOW_TLSCP,TSCL($TSCL_RED_EXH+37:6:D)
TSCL.HEATEX_D.FLOW_MIRROR,TSCL($TSCL_RED_EXH+43:6:D)
TSCL.HEATEX_D.PRESS_TLSCP,TSCL($TSCL_RED_EXH+49:6:D)
TSCL.HEATEX_D.PRESS_MIRROR,TSCL($TSCL_RED_EXH+55:6:D)
TSCL.HEATEX_D.PRESS_SYSTEM,TSCL($TSCL_RED_EXH+61:6:D)
TSCL.HEATEX_D.TEMP_TLSCP_CMD,TSCL($TSCL_RED_EXH+67:6:D)
TSCL.HEATEX_D.TEMP_MIRROR_CMD,TSCL($TSCL_RED_EXH+73:6:D)
# Additional Pump/Chiller D items (added by rkackley 2011.11.3)
TSCV.HEATEX_D.PUMP_CHILLER,TSCV($TSCV0039+1:1:B:H30) # Rdn Exh Chiller Pump OPN and Stop
TSCV.HEATEX_D.PUMP_TLSCP,TSCV($TSCV0039+2:1:B:H03) # Rdn Exh A(TLSCP)/B Pump OPN and Stop
TSCV.HEATEX_D.PUMP_MIRROR,TSCV($TSCV0039+2:1:B:H30) # Rdn Exh A(Mirror)/B Pump OPN and Stop
TSCV.HEATEX_D.CHILLER,TSCV($TSCV0039+3:1:B:H03) # Rdn Exh Chiller OPN and Stop



###############################
# 1284 - 1400 rezerve
###############################
# cleate : /soss/SRC/product/OSSS/OSSS_InterfaceOBS.d/alias2.sh
# change nwata 2003.12.05
###############################
# Add STATOBS for extended MEMORY COMMAND
# IRC
STATOBS.IRC.K01,STATOBS(64*1401:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K02,STATOBS(64*1402:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K03,STATOBS(64*1403:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K04,STATOBS(64*1404:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K05,STATOBS(64*1405:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K06,STATOBS(64*1406:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K07,STATOBS(64*1407:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K08,STATOBS(64*1408:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K09,STATOBS(64*1409:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K10,STATOBS(64*1410:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K11,STATOBS(64*1411:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K12,STATOBS(64*1412:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K13,STATOBS(64*1413:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K14,STATOBS(64*1414:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K15,STATOBS(64*1415:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K16,STATOBS(64*1416:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K17,STATOBS(64*1417:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K18,STATOBS(64*1418:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K19,STATOBS(64*1419:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K20,STATOBS(64*1420:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K21,STATOBS(64*1421:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K22,STATOBS(64*1422:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K23,STATOBS(64*1423:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K24,STATOBS(64*1424:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K25,STATOBS(64*1425:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K26,STATOBS(64*1426:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K27,STATOBS(64*1427:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K28,STATOBS(64*1428:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K29,STATOBS(64*1429:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K30,STATOBS(64*1430:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K31,STATOBS(64*1431:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K32,STATOBS(64*1432:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K33,STATOBS(64*1433:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K34,STATOBS(64*1434:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K35,STATOBS(64*1435:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K36,STATOBS(64*1436:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K37,STATOBS(64*1437:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K38,STATOBS(64*1438:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K39,STATOBS(64*1439:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K40,STATOBS(64*1440:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K41,STATOBS(64*1441:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K42,STATOBS(64*1442:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K43,STATOBS(64*1443:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K44,STATOBS(64*1444:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K45,STATOBS(64*1445:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K46,STATOBS(64*1446:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K47,STATOBS(64*1447:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K48,STATOBS(64*1448:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K49,STATOBS(64*1449:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K50,STATOBS(64*1450:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K51,STATOBS(64*1451:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K52,STATOBS(64*1452:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K53,STATOBS(64*1453:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K54,STATOBS(64*1454:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K55,STATOBS(64*1455:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K56,STATOBS(64*1456:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K57,STATOBS(64*1457:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K58,STATOBS(64*1458:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K59,STATOBS(64*1459:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K60,STATOBS(64*1460:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K61,STATOBS(64*1461:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K62,STATOBS(64*1462:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K63,STATOBS(64*1463:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.K64,STATOBS(64*1464:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V01,STATOBS(64*1465:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V02,STATOBS(64*1466:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V03,STATOBS(64*1467:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V04,STATOBS(64*1468:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V05,STATOBS(64*1469:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V06,STATOBS(64*1470:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V07,STATOBS(64*1471:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V08,STATOBS(64*1472:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V09,STATOBS(64*1473:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V10,STATOBS(64*1474:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V11,STATOBS(64*1475:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V12,STATOBS(64*1476:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V13,STATOBS(64*1477:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V14,STATOBS(64*1478:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V15,STATOBS(64*1479:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V16,STATOBS(64*1480:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V17,STATOBS(64*1481:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V18,STATOBS(64*1482:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V19,STATOBS(64*1483:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V20,STATOBS(64*1484:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V21,STATOBS(64*1485:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V22,STATOBS(64*1486:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V23,STATOBS(64*1487:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V24,STATOBS(64*1488:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V25,STATOBS(64*1489:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V26,STATOBS(64*1490:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V27,STATOBS(64*1491:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V28,STATOBS(64*1492:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V29,STATOBS(64*1493:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V30,STATOBS(64*1494:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V31,STATOBS(64*1495:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V32,STATOBS(64*1496:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V33,STATOBS(64*1497:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V34,STATOBS(64*1498:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V35,STATOBS(64*1499:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V36,STATOBS(64*1500:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V37,STATOBS(64*1501:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V38,STATOBS(64*1502:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V39,STATOBS(64*1503:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V40,STATOBS(64*1504:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V41,STATOBS(64*1505:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V42,STATOBS(64*1506:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V43,STATOBS(64*1507:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V44,STATOBS(64*1508:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V45,STATOBS(64*1509:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V46,STATOBS(64*1510:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V47,STATOBS(64*1511:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V48,STATOBS(64*1512:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V49,STATOBS(64*1513:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V50,STATOBS(64*1514:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V51,STATOBS(64*1515:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V52,STATOBS(64*1516:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V53,STATOBS(64*1517:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V54,STATOBS(64*1518:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V55,STATOBS(64*1519:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V56,STATOBS(64*1520:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V57,STATOBS(64*1521:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V58,STATOBS(64*1522:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V59,STATOBS(64*1523:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V60,STATOBS(64*1524:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V61,STATOBS(64*1525:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V62,STATOBS(64*1526:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V63,STATOBS(64*1527:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.V64,STATOBS(64*1528:64:C)         # Extended MEMORY data (IRC)
STATOBS.IRC.MEMORY,STATOBS(64*1529:64:C)      # Extended MEMORY num IRC
# AOS
STATOBS.AOS.K01,STATOBS(64*1530:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K02,STATOBS(64*1531:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K03,STATOBS(64*1532:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K04,STATOBS(64*1533:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K05,STATOBS(64*1534:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K06,STATOBS(64*1535:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K07,STATOBS(64*1536:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K08,STATOBS(64*1537:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K09,STATOBS(64*1538:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K10,STATOBS(64*1539:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K11,STATOBS(64*1540:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K12,STATOBS(64*1541:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K13,STATOBS(64*1542:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K14,STATOBS(64*1543:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K15,STATOBS(64*1544:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K16,STATOBS(64*1545:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K17,STATOBS(64*1546:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K18,STATOBS(64*1547:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K19,STATOBS(64*1548:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K20,STATOBS(64*1549:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K21,STATOBS(64*1550:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K22,STATOBS(64*1551:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K23,STATOBS(64*1552:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K24,STATOBS(64*1553:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K25,STATOBS(64*1554:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K26,STATOBS(64*1555:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K27,STATOBS(64*1556:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K28,STATOBS(64*1557:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K29,STATOBS(64*1558:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K30,STATOBS(64*1559:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K31,STATOBS(64*1560:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K32,STATOBS(64*1561:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K33,STATOBS(64*1562:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K34,STATOBS(64*1563:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K35,STATOBS(64*1564:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K36,STATOBS(64*1565:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K37,STATOBS(64*1566:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K38,STATOBS(64*1567:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K39,STATOBS(64*1568:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K40,STATOBS(64*1569:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K41,STATOBS(64*1570:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K42,STATOBS(64*1571:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K43,STATOBS(64*1572:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K44,STATOBS(64*1573:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K45,STATOBS(64*1574:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K46,STATOBS(64*1575:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K47,STATOBS(64*1576:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K48,STATOBS(64*1577:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K49,STATOBS(64*1578:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K50,STATOBS(64*1579:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K51,STATOBS(64*1580:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K52,STATOBS(64*1581:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K53,STATOBS(64*1582:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K54,STATOBS(64*1583:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K55,STATOBS(64*1584:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K56,STATOBS(64*1585:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K57,STATOBS(64*1586:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K58,STATOBS(64*1587:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K59,STATOBS(64*1588:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K60,STATOBS(64*1589:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K61,STATOBS(64*1590:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K62,STATOBS(64*1591:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K63,STATOBS(64*1592:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.K64,STATOBS(64*1593:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V01,STATOBS(64*1594:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V02,STATOBS(64*1595:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V03,STATOBS(64*1596:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V04,STATOBS(64*1597:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V05,STATOBS(64*1598:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V06,STATOBS(64*1599:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V07,STATOBS(64*1600:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V08,STATOBS(64*1601:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V09,STATOBS(64*1602:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V10,STATOBS(64*1603:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V11,STATOBS(64*1604:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V12,STATOBS(64*1605:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V13,STATOBS(64*1606:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V14,STATOBS(64*1607:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V15,STATOBS(64*1608:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V16,STATOBS(64*1609:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V17,STATOBS(64*1610:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V18,STATOBS(64*1611:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V19,STATOBS(64*1612:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V20,STATOBS(64*1613:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V21,STATOBS(64*1614:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V22,STATOBS(64*1615:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V23,STATOBS(64*1616:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V24,STATOBS(64*1617:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V25,STATOBS(64*1618:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V26,STATOBS(64*1619:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V27,STATOBS(64*1620:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V28,STATOBS(64*1621:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V29,STATOBS(64*1622:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V30,STATOBS(64*1623:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V31,STATOBS(64*1624:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V32,STATOBS(64*1625:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V33,STATOBS(64*1626:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V34,STATOBS(64*1627:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V35,STATOBS(64*1628:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V36,STATOBS(64*1629:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V37,STATOBS(64*1630:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V38,STATOBS(64*1631:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V39,STATOBS(64*1632:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V40,STATOBS(64*1633:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V41,STATOBS(64*1634:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V42,STATOBS(64*1635:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V43,STATOBS(64*1636:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V44,STATOBS(64*1637:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V45,STATOBS(64*1638:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V46,STATOBS(64*1639:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V47,STATOBS(64*1640:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V48,STATOBS(64*1641:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V49,STATOBS(64*1642:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V50,STATOBS(64*1643:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V51,STATOBS(64*1644:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V52,STATOBS(64*1645:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V53,STATOBS(64*1646:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V54,STATOBS(64*1647:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V55,STATOBS(64*1648:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V56,STATOBS(64*1649:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V57,STATOBS(64*1650:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V58,STATOBS(64*1651:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V59,STATOBS(64*1652:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V60,STATOBS(64*1653:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V61,STATOBS(64*1654:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V62,STATOBS(64*1655:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V63,STATOBS(64*1656:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.V64,STATOBS(64*1657:64:C)         # Extended MEMORY data (AOS)
STATOBS.AOS.MEMORY,STATOBS(64*1658:64:C)      # Extended MEMORY num AOS
# CIA
STATOBS.CIA.K01,STATOBS(64*1659:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K02,STATOBS(64*1660:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K03,STATOBS(64*1661:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K04,STATOBS(64*1662:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K05,STATOBS(64*1663:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K06,STATOBS(64*1664:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K07,STATOBS(64*1665:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K08,STATOBS(64*1666:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K09,STATOBS(64*1667:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K10,STATOBS(64*1668:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K11,STATOBS(64*1669:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K12,STATOBS(64*1670:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K13,STATOBS(64*1671:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K14,STATOBS(64*1672:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K15,STATOBS(64*1673:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K16,STATOBS(64*1674:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K17,STATOBS(64*1675:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K18,STATOBS(64*1676:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K19,STATOBS(64*1677:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K20,STATOBS(64*1678:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K21,STATOBS(64*1679:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K22,STATOBS(64*1680:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K23,STATOBS(64*1681:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K24,STATOBS(64*1682:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K25,STATOBS(64*1683:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K26,STATOBS(64*1684:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K27,STATOBS(64*1685:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K28,STATOBS(64*1686:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K29,STATOBS(64*1687:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K30,STATOBS(64*1688:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K31,STATOBS(64*1689:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K32,STATOBS(64*1690:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K33,STATOBS(64*1691:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K34,STATOBS(64*1692:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K35,STATOBS(64*1693:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K36,STATOBS(64*1694:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K37,STATOBS(64*1695:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K38,STATOBS(64*1696:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K39,STATOBS(64*1697:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K40,STATOBS(64*1698:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K41,STATOBS(64*1699:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K42,STATOBS(64*1700:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K43,STATOBS(64*1701:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K44,STATOBS(64*1702:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K45,STATOBS(64*1703:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K46,STATOBS(64*1704:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K47,STATOBS(64*1705:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K48,STATOBS(64*1706:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K49,STATOBS(64*1707:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K50,STATOBS(64*1708:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K51,STATOBS(64*1709:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K52,STATOBS(64*1710:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K53,STATOBS(64*1711:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K54,STATOBS(64*1712:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K55,STATOBS(64*1713:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K56,STATOBS(64*1714:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K57,STATOBS(64*1715:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K58,STATOBS(64*1716:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K59,STATOBS(64*1717:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K60,STATOBS(64*1718:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K61,STATOBS(64*1719:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K62,STATOBS(64*1720:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K63,STATOBS(64*1721:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.K64,STATOBS(64*1722:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V01,STATOBS(64*1723:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V02,STATOBS(64*1724:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V03,STATOBS(64*1725:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V04,STATOBS(64*1726:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V05,STATOBS(64*1727:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V06,STATOBS(64*1728:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V07,STATOBS(64*1729:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V08,STATOBS(64*1730:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V09,STATOBS(64*1731:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V10,STATOBS(64*1732:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V11,STATOBS(64*1733:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V12,STATOBS(64*1734:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V13,STATOBS(64*1735:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V14,STATOBS(64*1736:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V15,STATOBS(64*1737:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V16,STATOBS(64*1738:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V17,STATOBS(64*1739:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V18,STATOBS(64*1740:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V19,STATOBS(64*1741:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V20,STATOBS(64*1742:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V21,STATOBS(64*1743:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V22,STATOBS(64*1744:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V23,STATOBS(64*1745:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V24,STATOBS(64*1746:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V25,STATOBS(64*1747:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V26,STATOBS(64*1748:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V27,STATOBS(64*1749:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V28,STATOBS(64*1750:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V29,STATOBS(64*1751:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V30,STATOBS(64*1752:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V31,STATOBS(64*1753:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V32,STATOBS(64*1754:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V33,STATOBS(64*1755:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V34,STATOBS(64*1756:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V35,STATOBS(64*1757:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V36,STATOBS(64*1758:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V37,STATOBS(64*1759:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V38,STATOBS(64*1760:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V39,STATOBS(64*1761:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V40,STATOBS(64*1762:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V41,STATOBS(64*1763:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V42,STATOBS(64*1764:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V43,STATOBS(64*1765:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V44,STATOBS(64*1766:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V45,STATOBS(64*1767:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V46,STATOBS(64*1768:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V47,STATOBS(64*1769:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V48,STATOBS(64*1770:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V49,STATOBS(64*1771:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V50,STATOBS(64*1772:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V51,STATOBS(64*1773:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V52,STATOBS(64*1774:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V53,STATOBS(64*1775:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V54,STATOBS(64*1776:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V55,STATOBS(64*1777:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V56,STATOBS(64*1778:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V57,STATOBS(64*1779:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V58,STATOBS(64*1780:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V59,STATOBS(64*1781:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V60,STATOBS(64*1782:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V61,STATOBS(64*1783:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V62,STATOBS(64*1784:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V63,STATOBS(64*1785:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.V64,STATOBS(64*1786:64:C)         # Extended MEMORY data (CIA)
STATOBS.CIA.MEMORY,STATOBS(64*1787:64:C)      # Extended MEMORY num CIA
# OHS
STATOBS.OHS.K01,STATOBS(64*1788:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K02,STATOBS(64*1789:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K03,STATOBS(64*1790:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K04,STATOBS(64*1791:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K05,STATOBS(64*1792:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K06,STATOBS(64*1793:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K07,STATOBS(64*1794:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K08,STATOBS(64*1795:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K09,STATOBS(64*1796:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K10,STATOBS(64*1797:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K11,STATOBS(64*1798:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K12,STATOBS(64*1799:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K13,STATOBS(64*1800:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K14,STATOBS(64*1801:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K15,STATOBS(64*1802:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K16,STATOBS(64*1803:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K17,STATOBS(64*1804:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K18,STATOBS(64*1805:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K19,STATOBS(64*1806:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K20,STATOBS(64*1807:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K21,STATOBS(64*1808:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K22,STATOBS(64*1809:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K23,STATOBS(64*1810:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K24,STATOBS(64*1811:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K25,STATOBS(64*1812:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K26,STATOBS(64*1813:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K27,STATOBS(64*1814:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K28,STATOBS(64*1815:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K29,STATOBS(64*1816:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K30,STATOBS(64*1817:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K31,STATOBS(64*1818:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K32,STATOBS(64*1819:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K33,STATOBS(64*1820:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K34,STATOBS(64*1821:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K35,STATOBS(64*1822:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K36,STATOBS(64*1823:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K37,STATOBS(64*1824:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K38,STATOBS(64*1825:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K39,STATOBS(64*1826:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K40,STATOBS(64*1827:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K41,STATOBS(64*1828:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K42,STATOBS(64*1829:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K43,STATOBS(64*1830:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K44,STATOBS(64*1831:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K45,STATOBS(64*1832:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K46,STATOBS(64*1833:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K47,STATOBS(64*1834:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K48,STATOBS(64*1835:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K49,STATOBS(64*1836:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K50,STATOBS(64*1837:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K51,STATOBS(64*1838:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K52,STATOBS(64*1839:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K53,STATOBS(64*1840:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K54,STATOBS(64*1841:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K55,STATOBS(64*1842:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K56,STATOBS(64*1843:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K57,STATOBS(64*1844:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K58,STATOBS(64*1845:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K59,STATOBS(64*1846:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K60,STATOBS(64*1847:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K61,STATOBS(64*1848:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K62,STATOBS(64*1849:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K63,STATOBS(64*1850:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.K64,STATOBS(64*1851:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V01,STATOBS(64*1852:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V02,STATOBS(64*1853:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V03,STATOBS(64*1854:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V04,STATOBS(64*1855:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V05,STATOBS(64*1856:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V06,STATOBS(64*1857:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V07,STATOBS(64*1858:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V08,STATOBS(64*1859:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V09,STATOBS(64*1860:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V10,STATOBS(64*1861:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V11,STATOBS(64*1862:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V12,STATOBS(64*1863:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V13,STATOBS(64*1864:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V14,STATOBS(64*1865:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V15,STATOBS(64*1866:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V16,STATOBS(64*1867:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V17,STATOBS(64*1868:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V18,STATOBS(64*1869:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V19,STATOBS(64*1870:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V20,STATOBS(64*1871:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V21,STATOBS(64*1872:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V22,STATOBS(64*1873:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V23,STATOBS(64*1874:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V24,STATOBS(64*1875:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V25,STATOBS(64*1876:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V26,STATOBS(64*1877:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V27,STATOBS(64*1878:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V28,STATOBS(64*1879:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V29,STATOBS(64*1880:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V30,STATOBS(64*1881:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V31,STATOBS(64*1882:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V32,STATOBS(64*1883:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V33,STATOBS(64*1884:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V34,STATOBS(64*1885:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V35,STATOBS(64*1886:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V36,STATOBS(64*1887:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V37,STATOBS(64*1888:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V38,STATOBS(64*1889:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V39,STATOBS(64*1890:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V40,STATOBS(64*1891:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V41,STATOBS(64*1892:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V42,STATOBS(64*1893:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V43,STATOBS(64*1894:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V44,STATOBS(64*1895:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V45,STATOBS(64*1896:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V46,STATOBS(64*1897:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V47,STATOBS(64*1898:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V48,STATOBS(64*1899:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V49,STATOBS(64*1900:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V50,STATOBS(64*1901:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V51,STATOBS(64*1902:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V52,STATOBS(64*1903:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V53,STATOBS(64*1904:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V54,STATOBS(64*1905:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V55,STATOBS(64*1906:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V56,STATOBS(64*1907:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V57,STATOBS(64*1908:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V58,STATOBS(64*1909:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V59,STATOBS(64*1910:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V60,STATOBS(64*1911:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V61,STATOBS(64*1912:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V62,STATOBS(64*1913:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V63,STATOBS(64*1914:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.V64,STATOBS(64*1915:64:C)         # Extended MEMORY data (OHS)
STATOBS.OHS.MEMORY,STATOBS(64*1916:64:C)      # Extended MEMORY num OHS
# FCS
STATOBS.FCS.K01,STATOBS(64*1917:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K02,STATOBS(64*1918:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K03,STATOBS(64*1919:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K04,STATOBS(64*1920:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K05,STATOBS(64*1921:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K06,STATOBS(64*1922:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K07,STATOBS(64*1923:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K08,STATOBS(64*1924:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K09,STATOBS(64*1925:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K10,STATOBS(64*1926:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K11,STATOBS(64*1927:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K12,STATOBS(64*1928:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K13,STATOBS(64*1929:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K14,STATOBS(64*1930:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K15,STATOBS(64*1931:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K16,STATOBS(64*1932:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K17,STATOBS(64*1933:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K18,STATOBS(64*1934:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K19,STATOBS(64*1935:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K20,STATOBS(64*1936:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K21,STATOBS(64*1937:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K22,STATOBS(64*1938:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K23,STATOBS(64*1939:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K24,STATOBS(64*1940:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K25,STATOBS(64*1941:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K26,STATOBS(64*1942:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K27,STATOBS(64*1943:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K28,STATOBS(64*1944:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K29,STATOBS(64*1945:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K30,STATOBS(64*1946:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K31,STATOBS(64*1947:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K32,STATOBS(64*1948:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K33,STATOBS(64*1949:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K34,STATOBS(64*1950:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K35,STATOBS(64*1951:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K36,STATOBS(64*1952:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K37,STATOBS(64*1953:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K38,STATOBS(64*1954:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K39,STATOBS(64*1955:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K40,STATOBS(64*1956:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K41,STATOBS(64*1957:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K42,STATOBS(64*1958:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K43,STATOBS(64*1959:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K44,STATOBS(64*1960:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K45,STATOBS(64*1961:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K46,STATOBS(64*1962:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K47,STATOBS(64*1963:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K48,STATOBS(64*1964:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K49,STATOBS(64*1965:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K50,STATOBS(64*1966:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K51,STATOBS(64*1967:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K52,STATOBS(64*1968:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K53,STATOBS(64*1969:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K54,STATOBS(64*1970:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K55,STATOBS(64*1971:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K56,STATOBS(64*1972:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K57,STATOBS(64*1973:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K58,STATOBS(64*1974:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K59,STATOBS(64*1975:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K60,STATOBS(64*1976:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K61,STATOBS(64*1977:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K62,STATOBS(64*1978:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K63,STATOBS(64*1979:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.K64,STATOBS(64*1980:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V01,STATOBS(64*1981:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V02,STATOBS(64*1982:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V03,STATOBS(64*1983:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V04,STATOBS(64*1984:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V05,STATOBS(64*1985:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V06,STATOBS(64*1986:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V07,STATOBS(64*1987:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V08,STATOBS(64*1988:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V09,STATOBS(64*1989:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V10,STATOBS(64*1990:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V11,STATOBS(64*1991:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V12,STATOBS(64*1992:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V13,STATOBS(64*1993:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V14,STATOBS(64*1994:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V15,STATOBS(64*1995:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V16,STATOBS(64*1996:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V17,STATOBS(64*1997:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V18,STATOBS(64*1998:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V19,STATOBS(64*1999:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V20,STATOBS(64*2000:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V21,STATOBS(64*2001:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V22,STATOBS(64*2002:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V23,STATOBS(64*2003:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V24,STATOBS(64*2004:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V25,STATOBS(64*2005:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V26,STATOBS(64*2006:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V27,STATOBS(64*2007:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V28,STATOBS(64*2008:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V29,STATOBS(64*2009:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V30,STATOBS(64*2010:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V31,STATOBS(64*2011:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V32,STATOBS(64*2012:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V33,STATOBS(64*2013:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V34,STATOBS(64*2014:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V35,STATOBS(64*2015:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V36,STATOBS(64*2016:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V37,STATOBS(64*2017:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V38,STATOBS(64*2018:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V39,STATOBS(64*2019:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V40,STATOBS(64*2020:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V41,STATOBS(64*2021:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V42,STATOBS(64*2022:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V43,STATOBS(64*2023:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V44,STATOBS(64*2024:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V45,STATOBS(64*2025:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V46,STATOBS(64*2026:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V47,STATOBS(64*2027:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V48,STATOBS(64*2028:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V49,STATOBS(64*2029:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V50,STATOBS(64*2030:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V51,STATOBS(64*2031:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V52,STATOBS(64*2032:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V53,STATOBS(64*2033:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V54,STATOBS(64*2034:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V55,STATOBS(64*2035:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V56,STATOBS(64*2036:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V57,STATOBS(64*2037:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V58,STATOBS(64*2038:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V59,STATOBS(64*2039:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V60,STATOBS(64*2040:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V61,STATOBS(64*2041:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V62,STATOBS(64*2042:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V63,STATOBS(64*2043:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.V64,STATOBS(64*2044:64:C)         # Extended MEMORY data (FCS)
STATOBS.FCS.MEMORY,STATOBS(64*2045:64:C)      # Extended MEMORY num FCS
# HDS
STATOBS.HDS.K01,STATOBS(64*2046:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K02,STATOBS(64*2047:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K03,STATOBS(64*2048:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K04,STATOBS(64*2049:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K05,STATOBS(64*2050:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K06,STATOBS(64*2051:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K07,STATOBS(64*2052:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K08,STATOBS(64*2053:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K09,STATOBS(64*2054:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K10,STATOBS(64*2055:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K11,STATOBS(64*2056:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K12,STATOBS(64*2057:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K13,STATOBS(64*2058:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K14,STATOBS(64*2059:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K15,STATOBS(64*2060:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K16,STATOBS(64*2061:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K17,STATOBS(64*2062:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K18,STATOBS(64*2063:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K19,STATOBS(64*2064:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K20,STATOBS(64*2065:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K21,STATOBS(64*2066:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K22,STATOBS(64*2067:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K23,STATOBS(64*2068:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K24,STATOBS(64*2069:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K25,STATOBS(64*2070:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K26,STATOBS(64*2071:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K27,STATOBS(64*2072:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K28,STATOBS(64*2073:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K29,STATOBS(64*2074:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K30,STATOBS(64*2075:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K31,STATOBS(64*2076:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K32,STATOBS(64*2077:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K33,STATOBS(64*2078:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K34,STATOBS(64*2079:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K35,STATOBS(64*2080:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K36,STATOBS(64*2081:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K37,STATOBS(64*2082:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K38,STATOBS(64*2083:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K39,STATOBS(64*2084:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K40,STATOBS(64*2085:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K41,STATOBS(64*2086:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K42,STATOBS(64*2087:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K43,STATOBS(64*2088:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K44,STATOBS(64*2089:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K45,STATOBS(64*2090:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K46,STATOBS(64*2091:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K47,STATOBS(64*2092:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K48,STATOBS(64*2093:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K49,STATOBS(64*2094:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K50,STATOBS(64*2095:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K51,STATOBS(64*2096:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K52,STATOBS(64*2097:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K53,STATOBS(64*2098:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K54,STATOBS(64*2099:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K55,STATOBS(64*2100:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K56,STATOBS(64*2101:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K57,STATOBS(64*2102:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K58,STATOBS(64*2103:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K59,STATOBS(64*2104:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K60,STATOBS(64*2105:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K61,STATOBS(64*2106:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K62,STATOBS(64*2107:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K63,STATOBS(64*2108:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.K64,STATOBS(64*2109:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V01,STATOBS(64*2110:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V02,STATOBS(64*2111:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V03,STATOBS(64*2112:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V04,STATOBS(64*2113:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V05,STATOBS(64*2114:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V06,STATOBS(64*2115:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V07,STATOBS(64*2116:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V08,STATOBS(64*2117:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V09,STATOBS(64*2118:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V10,STATOBS(64*2119:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V11,STATOBS(64*2120:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V12,STATOBS(64*2121:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V13,STATOBS(64*2122:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V14,STATOBS(64*2123:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V15,STATOBS(64*2124:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V16,STATOBS(64*2125:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V17,STATOBS(64*2126:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V18,STATOBS(64*2127:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V19,STATOBS(64*2128:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V20,STATOBS(64*2129:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V21,STATOBS(64*2130:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V22,STATOBS(64*2131:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V23,STATOBS(64*2132:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V24,STATOBS(64*2133:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V25,STATOBS(64*2134:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V26,STATOBS(64*2135:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V27,STATOBS(64*2136:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V28,STATOBS(64*2137:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V29,STATOBS(64*2138:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V30,STATOBS(64*2139:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V31,STATOBS(64*2140:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V32,STATOBS(64*2141:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V33,STATOBS(64*2142:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V34,STATOBS(64*2143:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V35,STATOBS(64*2144:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V36,STATOBS(64*2145:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V37,STATOBS(64*2146:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V38,STATOBS(64*2147:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V39,STATOBS(64*2148:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V40,STATOBS(64*2149:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V41,STATOBS(64*2150:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V42,STATOBS(64*2151:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V43,STATOBS(64*2152:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V44,STATOBS(64*2153:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V45,STATOBS(64*2154:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V46,STATOBS(64*2155:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V47,STATOBS(64*2156:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V48,STATOBS(64*2157:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V49,STATOBS(64*2158:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V50,STATOBS(64*2159:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V51,STATOBS(64*2160:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V52,STATOBS(64*2161:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V53,STATOBS(64*2162:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V54,STATOBS(64*2163:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V55,STATOBS(64*2164:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V56,STATOBS(64*2165:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V57,STATOBS(64*2166:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V58,STATOBS(64*2167:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V59,STATOBS(64*2168:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V60,STATOBS(64*2169:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V61,STATOBS(64*2170:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V62,STATOBS(64*2171:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V63,STATOBS(64*2172:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.V64,STATOBS(64*2173:64:C)         # Extended MEMORY data (HDS)
STATOBS.HDS.MEMORY,STATOBS(64*2174:64:C)      # Extended MEMORY num HDS
# COM
STATOBS.COM.K01,STATOBS(64*2175:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K02,STATOBS(64*2176:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K03,STATOBS(64*2177:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K04,STATOBS(64*2178:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K05,STATOBS(64*2179:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K06,STATOBS(64*2180:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K07,STATOBS(64*2181:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K08,STATOBS(64*2182:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K09,STATOBS(64*2183:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K10,STATOBS(64*2184:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K11,STATOBS(64*2185:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K12,STATOBS(64*2186:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K13,STATOBS(64*2187:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K14,STATOBS(64*2188:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K15,STATOBS(64*2189:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K16,STATOBS(64*2190:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K17,STATOBS(64*2191:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K18,STATOBS(64*2192:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K19,STATOBS(64*2193:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K20,STATOBS(64*2194:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K21,STATOBS(64*2195:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K22,STATOBS(64*2196:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K23,STATOBS(64*2197:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K24,STATOBS(64*2198:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K25,STATOBS(64*2199:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K26,STATOBS(64*2200:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K27,STATOBS(64*2201:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K28,STATOBS(64*2202:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K29,STATOBS(64*2203:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K30,STATOBS(64*2204:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K31,STATOBS(64*2205:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K32,STATOBS(64*2206:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K33,STATOBS(64*2207:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K34,STATOBS(64*2208:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K35,STATOBS(64*2209:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K36,STATOBS(64*2210:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K37,STATOBS(64*2211:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K38,STATOBS(64*2212:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K39,STATOBS(64*2213:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K40,STATOBS(64*2214:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K41,STATOBS(64*2215:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K42,STATOBS(64*2216:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K43,STATOBS(64*2217:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K44,STATOBS(64*2218:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K45,STATOBS(64*2219:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K46,STATOBS(64*2220:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K47,STATOBS(64*2221:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K48,STATOBS(64*2222:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K49,STATOBS(64*2223:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K50,STATOBS(64*2224:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K51,STATOBS(64*2225:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K52,STATOBS(64*2226:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K53,STATOBS(64*2227:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K54,STATOBS(64*2228:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K55,STATOBS(64*2229:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K56,STATOBS(64*2230:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K57,STATOBS(64*2231:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K58,STATOBS(64*2232:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K59,STATOBS(64*2233:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K60,STATOBS(64*2234:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K61,STATOBS(64*2235:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K62,STATOBS(64*2236:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K63,STATOBS(64*2237:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.K64,STATOBS(64*2238:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V01,STATOBS(64*2239:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V02,STATOBS(64*2240:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V03,STATOBS(64*2241:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V04,STATOBS(64*2242:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V05,STATOBS(64*2243:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V06,STATOBS(64*2244:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V07,STATOBS(64*2245:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V08,STATOBS(64*2246:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V09,STATOBS(64*2247:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V10,STATOBS(64*2248:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V11,STATOBS(64*2249:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V12,STATOBS(64*2250:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V13,STATOBS(64*2251:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V14,STATOBS(64*2252:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V15,STATOBS(64*2253:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V16,STATOBS(64*2254:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V17,STATOBS(64*2255:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V18,STATOBS(64*2256:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V19,STATOBS(64*2257:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V20,STATOBS(64*2258:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V21,STATOBS(64*2259:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V22,STATOBS(64*2260:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V23,STATOBS(64*2261:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V24,STATOBS(64*2262:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V25,STATOBS(64*2263:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V26,STATOBS(64*2264:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V27,STATOBS(64*2265:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V28,STATOBS(64*2266:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V29,STATOBS(64*2267:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V30,STATOBS(64*2268:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V31,STATOBS(64*2269:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V32,STATOBS(64*2270:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V33,STATOBS(64*2271:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V34,STATOBS(64*2272:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V35,STATOBS(64*2273:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V36,STATOBS(64*2274:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V37,STATOBS(64*2275:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V38,STATOBS(64*2276:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V39,STATOBS(64*2277:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V40,STATOBS(64*2278:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V41,STATOBS(64*2279:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V42,STATOBS(64*2280:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V43,STATOBS(64*2281:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V44,STATOBS(64*2282:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V45,STATOBS(64*2283:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V46,STATOBS(64*2284:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V47,STATOBS(64*2285:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V48,STATOBS(64*2286:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V49,STATOBS(64*2287:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V50,STATOBS(64*2288:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V51,STATOBS(64*2289:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V52,STATOBS(64*2290:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V53,STATOBS(64*2291:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V54,STATOBS(64*2292:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V55,STATOBS(64*2293:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V56,STATOBS(64*2294:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V57,STATOBS(64*2295:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V58,STATOBS(64*2296:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V59,STATOBS(64*2297:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V60,STATOBS(64*2298:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V61,STATOBS(64*2299:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V62,STATOBS(64*2300:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V63,STATOBS(64*2301:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.V64,STATOBS(64*2302:64:C)         # Extended MEMORY data (COM)
STATOBS.COM.MEMORY,STATOBS(64*2303:64:C)      # Extended MEMORY num COM
# SUP
STATOBS.SUP.K01,STATOBS(64*2304:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K02,STATOBS(64*2305:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K03,STATOBS(64*2306:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K04,STATOBS(64*2307:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K05,STATOBS(64*2308:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K06,STATOBS(64*2309:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K07,STATOBS(64*2310:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K08,STATOBS(64*2311:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K09,STATOBS(64*2312:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K10,STATOBS(64*2313:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K11,STATOBS(64*2314:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K12,STATOBS(64*2315:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K13,STATOBS(64*2316:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K14,STATOBS(64*2317:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K15,STATOBS(64*2318:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K16,STATOBS(64*2319:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K17,STATOBS(64*2320:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K18,STATOBS(64*2321:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K19,STATOBS(64*2322:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K20,STATOBS(64*2323:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K21,STATOBS(64*2324:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K22,STATOBS(64*2325:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K23,STATOBS(64*2326:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K24,STATOBS(64*2327:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K25,STATOBS(64*2328:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K26,STATOBS(64*2329:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K27,STATOBS(64*2330:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K28,STATOBS(64*2331:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K29,STATOBS(64*2332:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K30,STATOBS(64*2333:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K31,STATOBS(64*2334:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K32,STATOBS(64*2335:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K33,STATOBS(64*2336:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K34,STATOBS(64*2337:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K35,STATOBS(64*2338:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K36,STATOBS(64*2339:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K37,STATOBS(64*2340:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K38,STATOBS(64*2341:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K39,STATOBS(64*2342:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K40,STATOBS(64*2343:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K41,STATOBS(64*2344:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K42,STATOBS(64*2345:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K43,STATOBS(64*2346:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K44,STATOBS(64*2347:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K45,STATOBS(64*2348:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K46,STATOBS(64*2349:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K47,STATOBS(64*2350:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K48,STATOBS(64*2351:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K49,STATOBS(64*2352:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K50,STATOBS(64*2353:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K51,STATOBS(64*2354:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K52,STATOBS(64*2355:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K53,STATOBS(64*2356:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K54,STATOBS(64*2357:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K55,STATOBS(64*2358:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K56,STATOBS(64*2359:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K57,STATOBS(64*2360:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K58,STATOBS(64*2361:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K59,STATOBS(64*2362:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K60,STATOBS(64*2363:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K61,STATOBS(64*2364:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K62,STATOBS(64*2365:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K63,STATOBS(64*2366:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.K64,STATOBS(64*2367:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V01,STATOBS(64*2368:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V02,STATOBS(64*2369:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V03,STATOBS(64*2370:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V04,STATOBS(64*2371:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V05,STATOBS(64*2372:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V06,STATOBS(64*2373:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V07,STATOBS(64*2374:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V08,STATOBS(64*2375:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V09,STATOBS(64*2376:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V10,STATOBS(64*2377:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V11,STATOBS(64*2378:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V12,STATOBS(64*2379:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V13,STATOBS(64*2380:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V14,STATOBS(64*2381:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V15,STATOBS(64*2382:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V16,STATOBS(64*2383:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V17,STATOBS(64*2384:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V18,STATOBS(64*2385:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V19,STATOBS(64*2386:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V20,STATOBS(64*2387:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V21,STATOBS(64*2388:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V22,STATOBS(64*2389:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V23,STATOBS(64*2390:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V24,STATOBS(64*2391:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V25,STATOBS(64*2392:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V26,STATOBS(64*2393:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V27,STATOBS(64*2394:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V28,STATOBS(64*2395:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V29,STATOBS(64*2396:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V30,STATOBS(64*2397:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V31,STATOBS(64*2398:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V32,STATOBS(64*2399:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V33,STATOBS(64*2400:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V34,STATOBS(64*2401:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V35,STATOBS(64*2402:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V36,STATOBS(64*2403:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V37,STATOBS(64*2404:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V38,STATOBS(64*2405:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V39,STATOBS(64*2406:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V40,STATOBS(64*2407:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V41,STATOBS(64*2408:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V42,STATOBS(64*2409:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V43,STATOBS(64*2410:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V44,STATOBS(64*2411:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V45,STATOBS(64*2412:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V46,STATOBS(64*2413:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V47,STATOBS(64*2414:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V48,STATOBS(64*2415:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V49,STATOBS(64*2416:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V50,STATOBS(64*2417:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V51,STATOBS(64*2418:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V52,STATOBS(64*2419:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V53,STATOBS(64*2420:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V54,STATOBS(64*2421:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V55,STATOBS(64*2422:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V56,STATOBS(64*2423:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V57,STATOBS(64*2424:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V58,STATOBS(64*2425:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V59,STATOBS(64*2426:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V60,STATOBS(64*2427:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V61,STATOBS(64*2428:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V62,STATOBS(64*2429:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V63,STATOBS(64*2430:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.V64,STATOBS(64*2431:64:C)         # Extended MEMORY data (SUP)
STATOBS.SUP.MEMORY,STATOBS(64*2432:64:C)      # Extended MEMORY num SUP
# SUK
STATOBS.SUK.K01,STATOBS(64*2433:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K02,STATOBS(64*2434:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K03,STATOBS(64*2435:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K04,STATOBS(64*2436:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K05,STATOBS(64*2437:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K06,STATOBS(64*2438:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K07,STATOBS(64*2439:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K08,STATOBS(64*2440:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K09,STATOBS(64*2441:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K10,STATOBS(64*2442:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K11,STATOBS(64*2443:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K12,STATOBS(64*2444:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K13,STATOBS(64*2445:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K14,STATOBS(64*2446:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K15,STATOBS(64*2447:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K16,STATOBS(64*2448:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K17,STATOBS(64*2449:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K18,STATOBS(64*2450:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K19,STATOBS(64*2451:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K20,STATOBS(64*2452:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K21,STATOBS(64*2453:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K22,STATOBS(64*2454:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K23,STATOBS(64*2455:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K24,STATOBS(64*2456:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K25,STATOBS(64*2457:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K26,STATOBS(64*2458:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K27,STATOBS(64*2459:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K28,STATOBS(64*2460:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K29,STATOBS(64*2461:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K30,STATOBS(64*2462:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K31,STATOBS(64*2463:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K32,STATOBS(64*2464:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K33,STATOBS(64*2465:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K34,STATOBS(64*2466:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K35,STATOBS(64*2467:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K36,STATOBS(64*2468:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K37,STATOBS(64*2469:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K38,STATOBS(64*2470:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K39,STATOBS(64*2471:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K40,STATOBS(64*2472:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K41,STATOBS(64*2473:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K42,STATOBS(64*2474:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K43,STATOBS(64*2475:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K44,STATOBS(64*2476:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K45,STATOBS(64*2477:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K46,STATOBS(64*2478:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K47,STATOBS(64*2479:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K48,STATOBS(64*2480:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K49,STATOBS(64*2481:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K50,STATOBS(64*2482:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K51,STATOBS(64*2483:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K52,STATOBS(64*2484:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K53,STATOBS(64*2485:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K54,STATOBS(64*2486:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K55,STATOBS(64*2487:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K56,STATOBS(64*2488:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K57,STATOBS(64*2489:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K58,STATOBS(64*2490:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K59,STATOBS(64*2491:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K60,STATOBS(64*2492:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K61,STATOBS(64*2493:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K62,STATOBS(64*2494:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K63,STATOBS(64*2495:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.K64,STATOBS(64*2496:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V01,STATOBS(64*2497:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V02,STATOBS(64*2498:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V03,STATOBS(64*2499:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V04,STATOBS(64*2500:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V05,STATOBS(64*2501:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V06,STATOBS(64*2502:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V07,STATOBS(64*2503:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V08,STATOBS(64*2504:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V09,STATOBS(64*2505:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V10,STATOBS(64*2506:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V11,STATOBS(64*2507:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V12,STATOBS(64*2508:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V13,STATOBS(64*2509:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V14,STATOBS(64*2510:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V15,STATOBS(64*2511:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V16,STATOBS(64*2512:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V17,STATOBS(64*2513:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V18,STATOBS(64*2514:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V19,STATOBS(64*2515:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V20,STATOBS(64*2516:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V21,STATOBS(64*2517:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V22,STATOBS(64*2518:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V23,STATOBS(64*2519:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V24,STATOBS(64*2520:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V25,STATOBS(64*2521:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V26,STATOBS(64*2522:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V27,STATOBS(64*2523:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V28,STATOBS(64*2524:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V29,STATOBS(64*2525:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V30,STATOBS(64*2526:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V31,STATOBS(64*2527:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V32,STATOBS(64*2528:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V33,STATOBS(64*2529:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V34,STATOBS(64*2530:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V35,STATOBS(64*2531:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V36,STATOBS(64*2532:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V37,STATOBS(64*2533:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V38,STATOBS(64*2534:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V39,STATOBS(64*2535:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V40,STATOBS(64*2536:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V41,STATOBS(64*2537:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V42,STATOBS(64*2538:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V43,STATOBS(64*2539:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V44,STATOBS(64*2540:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V45,STATOBS(64*2541:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V46,STATOBS(64*2542:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V47,STATOBS(64*2543:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V48,STATOBS(64*2544:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V49,STATOBS(64*2545:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V50,STATOBS(64*2546:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V51,STATOBS(64*2547:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V52,STATOBS(64*2548:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V53,STATOBS(64*2549:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V54,STATOBS(64*2550:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V55,STATOBS(64*2551:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V56,STATOBS(64*2552:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V57,STATOBS(64*2553:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V58,STATOBS(64*2554:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V59,STATOBS(64*2555:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V60,STATOBS(64*2556:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V61,STATOBS(64*2557:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V62,STATOBS(64*2558:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V63,STATOBS(64*2559:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.V64,STATOBS(64*2560:64:C)         # Extended MEMORY data (SUK)
STATOBS.SUK.MEMORY,STATOBS(64*2561:64:C)      # Extended MEMORY num SUK
# MIR
STATOBS.MIR.K01,STATOBS(64*2562:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K02,STATOBS(64*2563:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K03,STATOBS(64*2564:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K04,STATOBS(64*2565:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K05,STATOBS(64*2566:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K06,STATOBS(64*2567:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K07,STATOBS(64*2568:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K08,STATOBS(64*2569:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K09,STATOBS(64*2570:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K10,STATOBS(64*2571:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K11,STATOBS(64*2572:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K12,STATOBS(64*2573:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K13,STATOBS(64*2574:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K14,STATOBS(64*2575:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K15,STATOBS(64*2576:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K16,STATOBS(64*2577:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K17,STATOBS(64*2578:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K18,STATOBS(64*2579:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K19,STATOBS(64*2580:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K20,STATOBS(64*2581:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K21,STATOBS(64*2582:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K22,STATOBS(64*2583:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K23,STATOBS(64*2584:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K24,STATOBS(64*2585:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K25,STATOBS(64*2586:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K26,STATOBS(64*2587:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K27,STATOBS(64*2588:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K28,STATOBS(64*2589:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K29,STATOBS(64*2590:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K30,STATOBS(64*2591:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K31,STATOBS(64*2592:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K32,STATOBS(64*2593:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K33,STATOBS(64*2594:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K34,STATOBS(64*2595:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K35,STATOBS(64*2596:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K36,STATOBS(64*2597:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K37,STATOBS(64*2598:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K38,STATOBS(64*2599:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K39,STATOBS(64*2600:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K40,STATOBS(64*2601:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K41,STATOBS(64*2602:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K42,STATOBS(64*2603:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K43,STATOBS(64*2604:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K44,STATOBS(64*2605:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K45,STATOBS(64*2606:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K46,STATOBS(64*2607:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K47,STATOBS(64*2608:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K48,STATOBS(64*2609:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K49,STATOBS(64*2610:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K50,STATOBS(64*2611:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K51,STATOBS(64*2612:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K52,STATOBS(64*2613:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K53,STATOBS(64*2614:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K54,STATOBS(64*2615:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K55,STATOBS(64*2616:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K56,STATOBS(64*2617:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K57,STATOBS(64*2618:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K58,STATOBS(64*2619:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K59,STATOBS(64*2620:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K60,STATOBS(64*2621:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K61,STATOBS(64*2622:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K62,STATOBS(64*2623:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K63,STATOBS(64*2624:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.K64,STATOBS(64*2625:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V01,STATOBS(64*2626:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V02,STATOBS(64*2627:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V03,STATOBS(64*2628:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V04,STATOBS(64*2629:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V05,STATOBS(64*2630:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V06,STATOBS(64*2631:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V07,STATOBS(64*2632:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V08,STATOBS(64*2633:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V09,STATOBS(64*2634:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V10,STATOBS(64*2635:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V11,STATOBS(64*2636:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V12,STATOBS(64*2637:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V13,STATOBS(64*2638:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V14,STATOBS(64*2639:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V15,STATOBS(64*2640:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V16,STATOBS(64*2641:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V17,STATOBS(64*2642:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V18,STATOBS(64*2643:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V19,STATOBS(64*2644:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V20,STATOBS(64*2645:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V21,STATOBS(64*2646:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V22,STATOBS(64*2647:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V23,STATOBS(64*2648:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V24,STATOBS(64*2649:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V25,STATOBS(64*2650:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V26,STATOBS(64*2651:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V27,STATOBS(64*2652:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V28,STATOBS(64*2653:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V29,STATOBS(64*2654:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V30,STATOBS(64*2655:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V31,STATOBS(64*2656:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V32,STATOBS(64*2657:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V33,STATOBS(64*2658:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V34,STATOBS(64*2659:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V35,STATOBS(64*2660:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V36,STATOBS(64*2661:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V37,STATOBS(64*2662:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V38,STATOBS(64*2663:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V39,STATOBS(64*2664:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V40,STATOBS(64*2665:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V41,STATOBS(64*2666:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V42,STATOBS(64*2667:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V43,STATOBS(64*2668:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V44,STATOBS(64*2669:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V45,STATOBS(64*2670:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V46,STATOBS(64*2671:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V47,STATOBS(64*2672:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V48,STATOBS(64*2673:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V49,STATOBS(64*2674:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V50,STATOBS(64*2675:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V51,STATOBS(64*2676:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V52,STATOBS(64*2677:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V53,STATOBS(64*2678:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V54,STATOBS(64*2679:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V55,STATOBS(64*2680:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V56,STATOBS(64*2681:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V57,STATOBS(64*2682:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V58,STATOBS(64*2683:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V59,STATOBS(64*2684:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V60,STATOBS(64*2685:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V61,STATOBS(64*2686:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V62,STATOBS(64*2687:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V63,STATOBS(64*2688:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.V64,STATOBS(64*2689:64:C)         # Extended MEMORY data (MIR)
STATOBS.MIR.MEMORY,STATOBS(64*2690:64:C)      # Extended MEMORY num MIR
# VTO
STATOBS.VTO.K01,STATOBS(64*2691:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K02,STATOBS(64*2692:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K03,STATOBS(64*2693:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K04,STATOBS(64*2694:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K05,STATOBS(64*2695:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K06,STATOBS(64*2696:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K07,STATOBS(64*2697:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K08,STATOBS(64*2698:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K09,STATOBS(64*2699:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K10,STATOBS(64*2700:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K11,STATOBS(64*2701:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K12,STATOBS(64*2702:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K13,STATOBS(64*2703:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K14,STATOBS(64*2704:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K15,STATOBS(64*2705:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K16,STATOBS(64*2706:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K17,STATOBS(64*2707:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K18,STATOBS(64*2708:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K19,STATOBS(64*2709:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K20,STATOBS(64*2710:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K21,STATOBS(64*2711:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K22,STATOBS(64*2712:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K23,STATOBS(64*2713:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K24,STATOBS(64*2714:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K25,STATOBS(64*2715:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K26,STATOBS(64*2716:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K27,STATOBS(64*2717:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K28,STATOBS(64*2718:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K29,STATOBS(64*2719:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K30,STATOBS(64*2720:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K31,STATOBS(64*2721:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K32,STATOBS(64*2722:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K33,STATOBS(64*2723:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K34,STATOBS(64*2724:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K35,STATOBS(64*2725:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K36,STATOBS(64*2726:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K37,STATOBS(64*2727:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K38,STATOBS(64*2728:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K39,STATOBS(64*2729:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K40,STATOBS(64*2730:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K41,STATOBS(64*2731:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K42,STATOBS(64*2732:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K43,STATOBS(64*2733:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K44,STATOBS(64*2734:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K45,STATOBS(64*2735:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K46,STATOBS(64*2736:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K47,STATOBS(64*2737:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K48,STATOBS(64*2738:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K49,STATOBS(64*2739:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K50,STATOBS(64*2740:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K51,STATOBS(64*2741:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K52,STATOBS(64*2742:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K53,STATOBS(64*2743:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K54,STATOBS(64*2744:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K55,STATOBS(64*2745:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K56,STATOBS(64*2746:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K57,STATOBS(64*2747:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K58,STATOBS(64*2748:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K59,STATOBS(64*2749:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K60,STATOBS(64*2750:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K61,STATOBS(64*2751:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K62,STATOBS(64*2752:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K63,STATOBS(64*2753:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.K64,STATOBS(64*2754:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V01,STATOBS(64*2755:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V02,STATOBS(64*2756:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V03,STATOBS(64*2757:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V04,STATOBS(64*2758:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V05,STATOBS(64*2759:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V06,STATOBS(64*2760:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V07,STATOBS(64*2761:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V08,STATOBS(64*2762:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V09,STATOBS(64*2763:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V10,STATOBS(64*2764:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V11,STATOBS(64*2765:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V12,STATOBS(64*2766:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V13,STATOBS(64*2767:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V14,STATOBS(64*2768:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V15,STATOBS(64*2769:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V16,STATOBS(64*2770:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V17,STATOBS(64*2771:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V18,STATOBS(64*2772:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V19,STATOBS(64*2773:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V20,STATOBS(64*2774:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V21,STATOBS(64*2775:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V22,STATOBS(64*2776:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V23,STATOBS(64*2777:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V24,STATOBS(64*2778:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V25,STATOBS(64*2779:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V26,STATOBS(64*2780:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V27,STATOBS(64*2781:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V28,STATOBS(64*2782:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V29,STATOBS(64*2783:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V30,STATOBS(64*2784:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V31,STATOBS(64*2785:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V32,STATOBS(64*2786:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V33,STATOBS(64*2787:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V34,STATOBS(64*2788:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V35,STATOBS(64*2789:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V36,STATOBS(64*2790:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V37,STATOBS(64*2791:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V38,STATOBS(64*2792:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V39,STATOBS(64*2793:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V40,STATOBS(64*2794:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V41,STATOBS(64*2795:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V42,STATOBS(64*2796:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V43,STATOBS(64*2797:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V44,STATOBS(64*2798:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V45,STATOBS(64*2799:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V46,STATOBS(64*2800:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V47,STATOBS(64*2801:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V48,STATOBS(64*2802:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V49,STATOBS(64*2803:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V50,STATOBS(64*2804:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V51,STATOBS(64*2805:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V52,STATOBS(64*2806:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V53,STATOBS(64*2807:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V54,STATOBS(64*2808:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V55,STATOBS(64*2809:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V56,STATOBS(64*2810:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V57,STATOBS(64*2811:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V58,STATOBS(64*2812:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V59,STATOBS(64*2813:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V60,STATOBS(64*2814:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V61,STATOBS(64*2815:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V62,STATOBS(64*2816:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V63,STATOBS(64*2817:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.V64,STATOBS(64*2818:64:C)         # Extended MEMORY data (VTO)
STATOBS.VTO.MEMORY,STATOBS(64*2819:64:C)      # Extended MEMORY num VTO
# CAC
STATOBS.CAC.K01,STATOBS(64*2820:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K02,STATOBS(64*2821:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K03,STATOBS(64*2822:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K04,STATOBS(64*2823:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K05,STATOBS(64*2824:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K06,STATOBS(64*2825:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K07,STATOBS(64*2826:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K08,STATOBS(64*2827:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K09,STATOBS(64*2828:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K10,STATOBS(64*2829:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K11,STATOBS(64*2830:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K12,STATOBS(64*2831:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K13,STATOBS(64*2832:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K14,STATOBS(64*2833:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K15,STATOBS(64*2834:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K16,STATOBS(64*2835:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K17,STATOBS(64*2836:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K18,STATOBS(64*2837:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K19,STATOBS(64*2838:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K20,STATOBS(64*2839:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K21,STATOBS(64*2840:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K22,STATOBS(64*2841:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K23,STATOBS(64*2842:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K24,STATOBS(64*2843:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K25,STATOBS(64*2844:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K26,STATOBS(64*2845:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K27,STATOBS(64*2846:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K28,STATOBS(64*2847:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K29,STATOBS(64*2848:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K30,STATOBS(64*2849:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K31,STATOBS(64*2850:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K32,STATOBS(64*2851:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K33,STATOBS(64*2852:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K34,STATOBS(64*2853:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K35,STATOBS(64*2854:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K36,STATOBS(64*2855:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K37,STATOBS(64*2856:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K38,STATOBS(64*2857:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K39,STATOBS(64*2858:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K40,STATOBS(64*2859:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K41,STATOBS(64*2860:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K42,STATOBS(64*2861:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K43,STATOBS(64*2862:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K44,STATOBS(64*2863:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K45,STATOBS(64*2864:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K46,STATOBS(64*2865:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K47,STATOBS(64*2866:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K48,STATOBS(64*2867:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K49,STATOBS(64*2868:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K50,STATOBS(64*2869:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K51,STATOBS(64*2870:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K52,STATOBS(64*2871:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K53,STATOBS(64*2872:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K54,STATOBS(64*2873:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K55,STATOBS(64*2874:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K56,STATOBS(64*2875:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K57,STATOBS(64*2876:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K58,STATOBS(64*2877:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K59,STATOBS(64*2878:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K60,STATOBS(64*2879:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K61,STATOBS(64*2880:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K62,STATOBS(64*2881:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K63,STATOBS(64*2882:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.K64,STATOBS(64*2883:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V01,STATOBS(64*2884:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V02,STATOBS(64*2885:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V03,STATOBS(64*2886:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V04,STATOBS(64*2887:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V05,STATOBS(64*2888:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V06,STATOBS(64*2889:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V07,STATOBS(64*2890:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V08,STATOBS(64*2891:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V09,STATOBS(64*2892:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V10,STATOBS(64*2893:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V11,STATOBS(64*2894:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V12,STATOBS(64*2895:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V13,STATOBS(64*2896:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V14,STATOBS(64*2897:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V15,STATOBS(64*2898:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V16,STATOBS(64*2899:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V17,STATOBS(64*2900:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V18,STATOBS(64*2901:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V19,STATOBS(64*2902:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V20,STATOBS(64*2903:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V21,STATOBS(64*2904:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V22,STATOBS(64*2905:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V23,STATOBS(64*2906:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V24,STATOBS(64*2907:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V25,STATOBS(64*2908:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V26,STATOBS(64*2909:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V27,STATOBS(64*2910:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V28,STATOBS(64*2911:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V29,STATOBS(64*2912:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V30,STATOBS(64*2913:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V31,STATOBS(64*2914:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V32,STATOBS(64*2915:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V33,STATOBS(64*2916:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V34,STATOBS(64*2917:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V35,STATOBS(64*2918:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V36,STATOBS(64*2919:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V37,STATOBS(64*2920:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V38,STATOBS(64*2921:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V39,STATOBS(64*2922:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V40,STATOBS(64*2923:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V41,STATOBS(64*2924:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V42,STATOBS(64*2925:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V43,STATOBS(64*2926:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V44,STATOBS(64*2927:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V45,STATOBS(64*2928:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V46,STATOBS(64*2929:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V47,STATOBS(64*2930:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V48,STATOBS(64*2931:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V49,STATOBS(64*2932:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V50,STATOBS(64*2933:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V51,STATOBS(64*2934:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V52,STATOBS(64*2935:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V53,STATOBS(64*2936:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V54,STATOBS(64*2937:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V55,STATOBS(64*2938:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V56,STATOBS(64*2939:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V57,STATOBS(64*2940:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V58,STATOBS(64*2941:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V59,STATOBS(64*2942:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V60,STATOBS(64*2943:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V61,STATOBS(64*2944:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V62,STATOBS(64*2945:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V63,STATOBS(64*2946:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.V64,STATOBS(64*2947:64:C)         # Extended MEMORY data (CAC)
STATOBS.CAC.MEMORY,STATOBS(64*2948:64:C)      # Extended MEMORY num CAC
# SKY
STATOBS.SKY.K01,STATOBS(64*2949:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K02,STATOBS(64*2950:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K03,STATOBS(64*2951:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K04,STATOBS(64*2952:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K05,STATOBS(64*2953:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K06,STATOBS(64*2954:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K07,STATOBS(64*2955:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K08,STATOBS(64*2956:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K09,STATOBS(64*2957:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K10,STATOBS(64*2958:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K11,STATOBS(64*2959:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K12,STATOBS(64*2960:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K13,STATOBS(64*2961:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K14,STATOBS(64*2962:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K15,STATOBS(64*2963:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K16,STATOBS(64*2964:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K17,STATOBS(64*2965:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K18,STATOBS(64*2966:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K19,STATOBS(64*2967:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K20,STATOBS(64*2968:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K21,STATOBS(64*2969:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K22,STATOBS(64*2970:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K23,STATOBS(64*2971:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K24,STATOBS(64*2972:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K25,STATOBS(64*2973:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K26,STATOBS(64*2974:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K27,STATOBS(64*2975:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K28,STATOBS(64*2976:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K29,STATOBS(64*2977:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K30,STATOBS(64*2978:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K31,STATOBS(64*2979:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K32,STATOBS(64*2980:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K33,STATOBS(64*2981:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K34,STATOBS(64*2982:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K35,STATOBS(64*2983:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K36,STATOBS(64*2984:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K37,STATOBS(64*2985:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K38,STATOBS(64*2986:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K39,STATOBS(64*2987:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K40,STATOBS(64*2988:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K41,STATOBS(64*2989:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K42,STATOBS(64*2990:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K43,STATOBS(64*2991:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K44,STATOBS(64*2992:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K45,STATOBS(64*2993:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K46,STATOBS(64*2994:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K47,STATOBS(64*2995:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K48,STATOBS(64*2996:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K49,STATOBS(64*2997:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K50,STATOBS(64*2998:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K51,STATOBS(64*2999:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K52,STATOBS(64*3000:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K53,STATOBS(64*3001:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K54,STATOBS(64*3002:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K55,STATOBS(64*3003:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K56,STATOBS(64*3004:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K57,STATOBS(64*3005:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K58,STATOBS(64*3006:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K59,STATOBS(64*3007:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K60,STATOBS(64*3008:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K61,STATOBS(64*3009:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K62,STATOBS(64*3010:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K63,STATOBS(64*3011:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.K64,STATOBS(64*3012:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V01,STATOBS(64*3013:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V02,STATOBS(64*3014:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V03,STATOBS(64*3015:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V04,STATOBS(64*3016:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V05,STATOBS(64*3017:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V06,STATOBS(64*3018:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V07,STATOBS(64*3019:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V08,STATOBS(64*3020:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V09,STATOBS(64*3021:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V10,STATOBS(64*3022:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V11,STATOBS(64*3023:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V12,STATOBS(64*3024:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V13,STATOBS(64*3025:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V14,STATOBS(64*3026:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V15,STATOBS(64*3027:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V16,STATOBS(64*3028:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V17,STATOBS(64*3029:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V18,STATOBS(64*3030:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V19,STATOBS(64*3031:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V20,STATOBS(64*3032:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V21,STATOBS(64*3033:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V22,STATOBS(64*3034:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V23,STATOBS(64*3035:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V24,STATOBS(64*3036:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V25,STATOBS(64*3037:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V26,STATOBS(64*3038:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V27,STATOBS(64*3039:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V28,STATOBS(64*3040:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V29,STATOBS(64*3041:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V30,STATOBS(64*3042:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V31,STATOBS(64*3043:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V32,STATOBS(64*3044:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V33,STATOBS(64*3045:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V34,STATOBS(64*3046:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V35,STATOBS(64*3047:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V36,STATOBS(64*3048:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V37,STATOBS(64*3049:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V38,STATOBS(64*3050:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V39,STATOBS(64*3051:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V40,STATOBS(64*3052:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V41,STATOBS(64*3053:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V42,STATOBS(64*3054:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V43,STATOBS(64*3055:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V44,STATOBS(64*3056:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V45,STATOBS(64*3057:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V46,STATOBS(64*3058:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V47,STATOBS(64*3059:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V48,STATOBS(64*3060:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V49,STATOBS(64*3061:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V50,STATOBS(64*3062:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V51,STATOBS(64*3063:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V52,STATOBS(64*3064:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V53,STATOBS(64*3065:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V54,STATOBS(64*3066:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V55,STATOBS(64*3067:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V56,STATOBS(64*3068:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V57,STATOBS(64*3069:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V58,STATOBS(64*3070:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V59,STATOBS(64*3071:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V60,STATOBS(64*3072:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V61,STATOBS(64*3073:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V62,STATOBS(64*3074:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V63,STATOBS(64*3075:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.V64,STATOBS(64*3076:64:C)         # Extended MEMORY data (SKY)
STATOBS.SKY.MEMORY,STATOBS(64*3077:64:C)      # Extended MEMORY num SKY
# PI1
STATOBS.PI1.K01,STATOBS(64*3078:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K02,STATOBS(64*3079:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K03,STATOBS(64*3080:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K04,STATOBS(64*3081:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K05,STATOBS(64*3082:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K06,STATOBS(64*3083:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K07,STATOBS(64*3084:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K08,STATOBS(64*3085:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K09,STATOBS(64*3086:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K10,STATOBS(64*3087:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K11,STATOBS(64*3088:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K12,STATOBS(64*3089:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K13,STATOBS(64*3090:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K14,STATOBS(64*3091:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K15,STATOBS(64*3092:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K16,STATOBS(64*3093:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K17,STATOBS(64*3094:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K18,STATOBS(64*3095:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K19,STATOBS(64*3096:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K20,STATOBS(64*3097:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K21,STATOBS(64*3098:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K22,STATOBS(64*3099:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K23,STATOBS(64*3100:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K24,STATOBS(64*3101:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K25,STATOBS(64*3102:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K26,STATOBS(64*3103:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K27,STATOBS(64*3104:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K28,STATOBS(64*3105:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K29,STATOBS(64*3106:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K30,STATOBS(64*3107:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K31,STATOBS(64*3108:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K32,STATOBS(64*3109:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K33,STATOBS(64*3110:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K34,STATOBS(64*3111:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K35,STATOBS(64*3112:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K36,STATOBS(64*3113:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K37,STATOBS(64*3114:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K38,STATOBS(64*3115:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K39,STATOBS(64*3116:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K40,STATOBS(64*3117:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K41,STATOBS(64*3118:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K42,STATOBS(64*3119:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K43,STATOBS(64*3120:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K44,STATOBS(64*3121:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K45,STATOBS(64*3122:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K46,STATOBS(64*3123:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K47,STATOBS(64*3124:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K48,STATOBS(64*3125:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K49,STATOBS(64*3126:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K50,STATOBS(64*3127:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K51,STATOBS(64*3128:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K52,STATOBS(64*3129:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K53,STATOBS(64*3130:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K54,STATOBS(64*3131:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K55,STATOBS(64*3132:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K56,STATOBS(64*3133:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K57,STATOBS(64*3134:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K58,STATOBS(64*3135:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K59,STATOBS(64*3136:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K60,STATOBS(64*3137:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K61,STATOBS(64*3138:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K62,STATOBS(64*3139:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K63,STATOBS(64*3140:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.K64,STATOBS(64*3141:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V01,STATOBS(64*3142:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V02,STATOBS(64*3143:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V03,STATOBS(64*3144:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V04,STATOBS(64*3145:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V05,STATOBS(64*3146:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V06,STATOBS(64*3147:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V07,STATOBS(64*3148:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V08,STATOBS(64*3149:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V09,STATOBS(64*3150:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V10,STATOBS(64*3151:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V11,STATOBS(64*3152:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V12,STATOBS(64*3153:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V13,STATOBS(64*3154:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V14,STATOBS(64*3155:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V15,STATOBS(64*3156:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V16,STATOBS(64*3157:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V17,STATOBS(64*3158:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V18,STATOBS(64*3159:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V19,STATOBS(64*3160:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V20,STATOBS(64*3161:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V21,STATOBS(64*3162:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V22,STATOBS(64*3163:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V23,STATOBS(64*3164:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V24,STATOBS(64*3165:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V25,STATOBS(64*3166:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V26,STATOBS(64*3167:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V27,STATOBS(64*3168:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V28,STATOBS(64*3169:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V29,STATOBS(64*3170:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V30,STATOBS(64*3171:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V31,STATOBS(64*3172:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V32,STATOBS(64*3173:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V33,STATOBS(64*3174:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V34,STATOBS(64*3175:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V35,STATOBS(64*3176:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V36,STATOBS(64*3177:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V37,STATOBS(64*3178:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V38,STATOBS(64*3179:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V39,STATOBS(64*3180:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V40,STATOBS(64*3181:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V41,STATOBS(64*3182:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V42,STATOBS(64*3183:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V43,STATOBS(64*3184:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V44,STATOBS(64*3185:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V45,STATOBS(64*3186:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V46,STATOBS(64*3187:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V47,STATOBS(64*3188:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V48,STATOBS(64*3189:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V49,STATOBS(64*3190:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V50,STATOBS(64*3191:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V51,STATOBS(64*3192:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V52,STATOBS(64*3193:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V53,STATOBS(64*3194:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V54,STATOBS(64*3195:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V55,STATOBS(64*3196:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V56,STATOBS(64*3197:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V57,STATOBS(64*3198:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V58,STATOBS(64*3199:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V59,STATOBS(64*3200:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V60,STATOBS(64*3201:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V61,STATOBS(64*3202:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V62,STATOBS(64*3203:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V63,STATOBS(64*3204:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.V64,STATOBS(64*3205:64:C)         # Extended MEMORY data (PI1)
STATOBS.PI1.MEMORY,STATOBS(64*3206:64:C)      # Extended MEMORY num PI1
# K3D
STATOBS.K3D.K01,STATOBS(64*3207:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K02,STATOBS(64*3208:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K03,STATOBS(64*3209:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K04,STATOBS(64*3210:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K05,STATOBS(64*3211:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K06,STATOBS(64*3212:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K07,STATOBS(64*3213:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K08,STATOBS(64*3214:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K09,STATOBS(64*3215:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K10,STATOBS(64*3216:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K11,STATOBS(64*3217:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K12,STATOBS(64*3218:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K13,STATOBS(64*3219:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K14,STATOBS(64*3220:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K15,STATOBS(64*3221:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K16,STATOBS(64*3222:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K17,STATOBS(64*3223:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K18,STATOBS(64*3224:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K19,STATOBS(64*3225:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K20,STATOBS(64*3226:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K21,STATOBS(64*3227:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K22,STATOBS(64*3228:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K23,STATOBS(64*3229:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K24,STATOBS(64*3230:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K25,STATOBS(64*3231:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K26,STATOBS(64*3232:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K27,STATOBS(64*3233:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K28,STATOBS(64*3234:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K29,STATOBS(64*3235:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K30,STATOBS(64*3236:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K31,STATOBS(64*3237:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K32,STATOBS(64*3238:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K33,STATOBS(64*3239:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K34,STATOBS(64*3240:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K35,STATOBS(64*3241:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K36,STATOBS(64*3242:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K37,STATOBS(64*3243:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K38,STATOBS(64*3244:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K39,STATOBS(64*3245:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K40,STATOBS(64*3246:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K41,STATOBS(64*3247:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K42,STATOBS(64*3248:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K43,STATOBS(64*3249:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K44,STATOBS(64*3250:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K45,STATOBS(64*3251:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K46,STATOBS(64*3252:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K47,STATOBS(64*3253:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K48,STATOBS(64*3254:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K49,STATOBS(64*3255:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K50,STATOBS(64*3256:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K51,STATOBS(64*3257:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K52,STATOBS(64*3258:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K53,STATOBS(64*3259:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K54,STATOBS(64*3260:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K55,STATOBS(64*3261:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K56,STATOBS(64*3262:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K57,STATOBS(64*3263:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K58,STATOBS(64*3264:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K59,STATOBS(64*3265:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K60,STATOBS(64*3266:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K61,STATOBS(64*3267:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K62,STATOBS(64*3268:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K63,STATOBS(64*3269:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.K64,STATOBS(64*3270:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V01,STATOBS(64*3271:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V02,STATOBS(64*3272:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V03,STATOBS(64*3273:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V04,STATOBS(64*3274:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V05,STATOBS(64*3275:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V06,STATOBS(64*3276:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V07,STATOBS(64*3277:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V08,STATOBS(64*3278:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V09,STATOBS(64*3279:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V10,STATOBS(64*3280:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V11,STATOBS(64*3281:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V12,STATOBS(64*3282:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V13,STATOBS(64*3283:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V14,STATOBS(64*3284:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V15,STATOBS(64*3285:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V16,STATOBS(64*3286:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V17,STATOBS(64*3287:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V18,STATOBS(64*3288:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V19,STATOBS(64*3289:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V20,STATOBS(64*3290:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V21,STATOBS(64*3291:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V22,STATOBS(64*3292:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V23,STATOBS(64*3293:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V24,STATOBS(64*3294:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V25,STATOBS(64*3295:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V26,STATOBS(64*3296:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V27,STATOBS(64*3297:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V28,STATOBS(64*3298:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V29,STATOBS(64*3299:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V30,STATOBS(64*3300:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V31,STATOBS(64*3301:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V32,STATOBS(64*3302:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V33,STATOBS(64*3303:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V34,STATOBS(64*3304:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V35,STATOBS(64*3305:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V36,STATOBS(64*3306:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V37,STATOBS(64*3307:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V38,STATOBS(64*3308:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V39,STATOBS(64*3309:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V40,STATOBS(64*3310:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V41,STATOBS(64*3311:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V42,STATOBS(64*3312:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V43,STATOBS(64*3313:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V44,STATOBS(64*3314:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V45,STATOBS(64*3315:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V46,STATOBS(64*3316:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V47,STATOBS(64*3317:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V48,STATOBS(64*3318:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V49,STATOBS(64*3319:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V50,STATOBS(64*3320:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V51,STATOBS(64*3321:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V52,STATOBS(64*3322:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V53,STATOBS(64*3323:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V54,STATOBS(64*3324:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V55,STATOBS(64*3325:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V56,STATOBS(64*3326:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V57,STATOBS(64*3327:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V58,STATOBS(64*3328:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V59,STATOBS(64*3329:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V60,STATOBS(64*3330:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V61,STATOBS(64*3331:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V62,STATOBS(64*3332:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V63,STATOBS(64*3333:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.V64,STATOBS(64*3334:64:C)         # Extended MEMORY data (K3D)
STATOBS.K3D.MEMORY,STATOBS(64*3335:64:C)      # Extended MEMORY num K3D
# O16
STATOBS.O16.K01,STATOBS(64*3336:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K02,STATOBS(64*3337:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K03,STATOBS(64*3338:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K04,STATOBS(64*3339:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K05,STATOBS(64*3340:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K06,STATOBS(64*3341:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K07,STATOBS(64*3342:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K08,STATOBS(64*3343:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K09,STATOBS(64*3344:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K10,STATOBS(64*3345:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K11,STATOBS(64*3346:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K12,STATOBS(64*3347:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K13,STATOBS(64*3348:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K14,STATOBS(64*3349:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K15,STATOBS(64*3350:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K16,STATOBS(64*3351:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K17,STATOBS(64*3352:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K18,STATOBS(64*3353:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K19,STATOBS(64*3354:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K20,STATOBS(64*3355:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K21,STATOBS(64*3356:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K22,STATOBS(64*3357:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K23,STATOBS(64*3358:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K24,STATOBS(64*3359:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K25,STATOBS(64*3360:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K26,STATOBS(64*3361:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K27,STATOBS(64*3362:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K28,STATOBS(64*3363:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K29,STATOBS(64*3364:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K30,STATOBS(64*3365:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K31,STATOBS(64*3366:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K32,STATOBS(64*3367:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K33,STATOBS(64*3368:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K34,STATOBS(64*3369:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K35,STATOBS(64*3370:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K36,STATOBS(64*3371:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K37,STATOBS(64*3372:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K38,STATOBS(64*3373:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K39,STATOBS(64*3374:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K40,STATOBS(64*3375:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K41,STATOBS(64*3376:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K42,STATOBS(64*3377:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K43,STATOBS(64*3378:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K44,STATOBS(64*3379:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K45,STATOBS(64*3380:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K46,STATOBS(64*3381:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K47,STATOBS(64*3382:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K48,STATOBS(64*3383:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K49,STATOBS(64*3384:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K50,STATOBS(64*3385:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K51,STATOBS(64*3386:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K52,STATOBS(64*3387:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K53,STATOBS(64*3388:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K54,STATOBS(64*3389:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K55,STATOBS(64*3390:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K56,STATOBS(64*3391:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K57,STATOBS(64*3392:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K58,STATOBS(64*3393:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K59,STATOBS(64*3394:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K60,STATOBS(64*3395:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K61,STATOBS(64*3396:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K62,STATOBS(64*3397:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K63,STATOBS(64*3398:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.K64,STATOBS(64*3399:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V01,STATOBS(64*3400:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V02,STATOBS(64*3401:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V03,STATOBS(64*3402:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V04,STATOBS(64*3403:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V05,STATOBS(64*3404:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V06,STATOBS(64*3405:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V07,STATOBS(64*3406:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V08,STATOBS(64*3407:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V09,STATOBS(64*3408:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V10,STATOBS(64*3409:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V11,STATOBS(64*3410:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V12,STATOBS(64*3411:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V13,STATOBS(64*3412:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V14,STATOBS(64*3413:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V15,STATOBS(64*3414:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V16,STATOBS(64*3415:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V17,STATOBS(64*3416:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V18,STATOBS(64*3417:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V19,STATOBS(64*3418:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V20,STATOBS(64*3419:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V21,STATOBS(64*3420:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V22,STATOBS(64*3421:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V23,STATOBS(64*3422:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V24,STATOBS(64*3423:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V25,STATOBS(64*3424:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V26,STATOBS(64*3425:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V27,STATOBS(64*3426:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V28,STATOBS(64*3427:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V29,STATOBS(64*3428:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V30,STATOBS(64*3429:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V31,STATOBS(64*3430:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V32,STATOBS(64*3431:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V33,STATOBS(64*3432:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V34,STATOBS(64*3433:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V35,STATOBS(64*3434:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V36,STATOBS(64*3435:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V37,STATOBS(64*3436:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V38,STATOBS(64*3437:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V39,STATOBS(64*3438:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V40,STATOBS(64*3439:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V41,STATOBS(64*3440:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V42,STATOBS(64*3441:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V43,STATOBS(64*3442:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V44,STATOBS(64*3443:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V45,STATOBS(64*3444:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V46,STATOBS(64*3445:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V47,STATOBS(64*3446:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V48,STATOBS(64*3447:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V49,STATOBS(64*3448:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V50,STATOBS(64*3449:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V51,STATOBS(64*3450:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V52,STATOBS(64*3451:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V53,STATOBS(64*3452:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V54,STATOBS(64*3453:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V55,STATOBS(64*3454:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V56,STATOBS(64*3455:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V57,STATOBS(64*3456:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V58,STATOBS(64*3457:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V59,STATOBS(64*3458:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V60,STATOBS(64*3459:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V61,STATOBS(64*3460:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V62,STATOBS(64*3461:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V63,STATOBS(64*3462:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.V64,STATOBS(64*3463:64:C)         # Extended MEMORY data (O16)
STATOBS.O16.MEMORY,STATOBS(64*3464:64:C)      # Extended MEMORY num O16
# MCS
STATOBS.MCS.K01,STATOBS(64*3465:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K02,STATOBS(64*3466:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K03,STATOBS(64*3467:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K04,STATOBS(64*3468:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K05,STATOBS(64*3469:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K06,STATOBS(64*3470:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K07,STATOBS(64*3471:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K08,STATOBS(64*3472:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K09,STATOBS(64*3473:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K10,STATOBS(64*3474:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K11,STATOBS(64*3475:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K12,STATOBS(64*3476:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K13,STATOBS(64*3477:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K14,STATOBS(64*3478:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K15,STATOBS(64*3479:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K16,STATOBS(64*3480:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K17,STATOBS(64*3481:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K18,STATOBS(64*3482:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K19,STATOBS(64*3483:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K20,STATOBS(64*3484:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K21,STATOBS(64*3485:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K22,STATOBS(64*3486:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K23,STATOBS(64*3487:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K24,STATOBS(64*3488:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K25,STATOBS(64*3489:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K26,STATOBS(64*3490:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K27,STATOBS(64*3491:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K28,STATOBS(64*3492:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K29,STATOBS(64*3493:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K30,STATOBS(64*3494:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K31,STATOBS(64*3495:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K32,STATOBS(64*3496:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K33,STATOBS(64*3497:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K34,STATOBS(64*3498:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K35,STATOBS(64*3499:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K36,STATOBS(64*3500:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K37,STATOBS(64*3501:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K38,STATOBS(64*3502:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K39,STATOBS(64*3503:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K40,STATOBS(64*3504:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K41,STATOBS(64*3505:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K42,STATOBS(64*3506:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K43,STATOBS(64*3507:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K44,STATOBS(64*3508:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K45,STATOBS(64*3509:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K46,STATOBS(64*3510:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K47,STATOBS(64*3511:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K48,STATOBS(64*3512:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K49,STATOBS(64*3513:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K50,STATOBS(64*3514:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K51,STATOBS(64*3515:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K52,STATOBS(64*3516:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K53,STATOBS(64*3517:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K54,STATOBS(64*3518:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K55,STATOBS(64*3519:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K56,STATOBS(64*3520:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K57,STATOBS(64*3521:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K58,STATOBS(64*3522:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K59,STATOBS(64*3523:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K60,STATOBS(64*3524:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K61,STATOBS(64*3525:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K62,STATOBS(64*3526:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K63,STATOBS(64*3527:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.K64,STATOBS(64*3528:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V01,STATOBS(64*3529:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V02,STATOBS(64*3530:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V03,STATOBS(64*3531:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V04,STATOBS(64*3532:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V05,STATOBS(64*3533:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V06,STATOBS(64*3534:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V07,STATOBS(64*3535:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V08,STATOBS(64*3536:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V09,STATOBS(64*3537:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V10,STATOBS(64*3538:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V11,STATOBS(64*3539:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V12,STATOBS(64*3540:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V13,STATOBS(64*3541:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V14,STATOBS(64*3542:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V15,STATOBS(64*3543:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V16,STATOBS(64*3544:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V17,STATOBS(64*3545:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V18,STATOBS(64*3546:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V19,STATOBS(64*3547:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V20,STATOBS(64*3548:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V21,STATOBS(64*3549:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V22,STATOBS(64*3550:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V23,STATOBS(64*3551:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V24,STATOBS(64*3552:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V25,STATOBS(64*3553:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V26,STATOBS(64*3554:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V27,STATOBS(64*3555:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V28,STATOBS(64*3556:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V29,STATOBS(64*3557:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V30,STATOBS(64*3558:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V31,STATOBS(64*3559:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V32,STATOBS(64*3560:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V33,STATOBS(64*3561:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V34,STATOBS(64*3562:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V35,STATOBS(64*3563:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V36,STATOBS(64*3564:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V37,STATOBS(64*3565:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V38,STATOBS(64*3566:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V39,STATOBS(64*3567:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V40,STATOBS(64*3568:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V41,STATOBS(64*3569:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V42,STATOBS(64*3570:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V43,STATOBS(64*3571:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V44,STATOBS(64*3572:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V45,STATOBS(64*3573:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V46,STATOBS(64*3574:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V47,STATOBS(64*3575:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V48,STATOBS(64*3576:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V49,STATOBS(64*3577:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V50,STATOBS(64*3578:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V51,STATOBS(64*3579:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V52,STATOBS(64*3580:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V53,STATOBS(64*3581:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V54,STATOBS(64*3582:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V55,STATOBS(64*3583:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V56,STATOBS(64*3584:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V57,STATOBS(64*3585:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V58,STATOBS(64*3586:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V59,STATOBS(64*3587:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V60,STATOBS(64*3588:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V61,STATOBS(64*3589:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V62,STATOBS(64*3590:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V63,STATOBS(64*3591:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.V64,STATOBS(64*3592:64:C)         # Extended MEMORY data (MCS)
STATOBS.MCS.MEMORY,STATOBS(64*3593:64:C)      # Extended MEMORY num MCS
# FMS
STATOBS.FMS.K01,STATOBS(64*3594:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K02,STATOBS(64*3595:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K03,STATOBS(64*3596:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K04,STATOBS(64*3597:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K05,STATOBS(64*3598:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K06,STATOBS(64*3599:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K07,STATOBS(64*3600:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K08,STATOBS(64*3601:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K09,STATOBS(64*3602:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K10,STATOBS(64*3603:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K11,STATOBS(64*3604:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K12,STATOBS(64*3605:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K13,STATOBS(64*3606:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K14,STATOBS(64*3607:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K15,STATOBS(64*3608:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K16,STATOBS(64*3609:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K17,STATOBS(64*3610:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K18,STATOBS(64*3611:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K19,STATOBS(64*3612:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K20,STATOBS(64*3613:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K21,STATOBS(64*3614:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K22,STATOBS(64*3615:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K23,STATOBS(64*3616:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K24,STATOBS(64*3617:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K25,STATOBS(64*3618:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K26,STATOBS(64*3619:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K27,STATOBS(64*3620:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K28,STATOBS(64*3621:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K29,STATOBS(64*3622:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K30,STATOBS(64*3623:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K31,STATOBS(64*3624:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K32,STATOBS(64*3625:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K33,STATOBS(64*3626:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K34,STATOBS(64*3627:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K35,STATOBS(64*3628:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K36,STATOBS(64*3629:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K37,STATOBS(64*3630:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K38,STATOBS(64*3631:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K39,STATOBS(64*3632:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K40,STATOBS(64*3633:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K41,STATOBS(64*3634:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K42,STATOBS(64*3635:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K43,STATOBS(64*3636:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K44,STATOBS(64*3637:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K45,STATOBS(64*3638:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K46,STATOBS(64*3639:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K47,STATOBS(64*3640:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K48,STATOBS(64*3641:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K49,STATOBS(64*3642:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K50,STATOBS(64*3643:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K51,STATOBS(64*3644:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K52,STATOBS(64*3645:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K53,STATOBS(64*3646:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K54,STATOBS(64*3647:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K55,STATOBS(64*3648:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K56,STATOBS(64*3649:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K57,STATOBS(64*3650:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K58,STATOBS(64*3651:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K59,STATOBS(64*3652:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K60,STATOBS(64*3653:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K61,STATOBS(64*3654:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K62,STATOBS(64*3655:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K63,STATOBS(64*3656:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.K64,STATOBS(64*3657:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V01,STATOBS(64*3658:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V02,STATOBS(64*3659:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V03,STATOBS(64*3660:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V04,STATOBS(64*3661:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V05,STATOBS(64*3662:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V06,STATOBS(64*3663:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V07,STATOBS(64*3664:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V08,STATOBS(64*3665:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V09,STATOBS(64*3666:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V10,STATOBS(64*3667:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V11,STATOBS(64*3668:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V12,STATOBS(64*3669:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V13,STATOBS(64*3670:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V14,STATOBS(64*3671:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V15,STATOBS(64*3672:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V16,STATOBS(64*3673:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V17,STATOBS(64*3674:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V18,STATOBS(64*3675:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V19,STATOBS(64*3676:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V20,STATOBS(64*3677:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V21,STATOBS(64*3678:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V22,STATOBS(64*3679:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V23,STATOBS(64*3680:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V24,STATOBS(64*3681:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V25,STATOBS(64*3682:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V26,STATOBS(64*3683:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V27,STATOBS(64*3684:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V28,STATOBS(64*3685:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V29,STATOBS(64*3686:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V30,STATOBS(64*3687:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V31,STATOBS(64*3688:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V32,STATOBS(64*3689:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V33,STATOBS(64*3690:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V34,STATOBS(64*3691:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V35,STATOBS(64*3692:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V36,STATOBS(64*3693:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V37,STATOBS(64*3694:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V38,STATOBS(64*3695:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V39,STATOBS(64*3696:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V40,STATOBS(64*3697:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V41,STATOBS(64*3698:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V42,STATOBS(64*3699:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V43,STATOBS(64*3700:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V44,STATOBS(64*3701:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V45,STATOBS(64*3702:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V46,STATOBS(64*3703:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V47,STATOBS(64*3704:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V48,STATOBS(64*3705:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V49,STATOBS(64*3706:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V50,STATOBS(64*3707:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V51,STATOBS(64*3708:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V52,STATOBS(64*3709:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V53,STATOBS(64*3710:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V54,STATOBS(64*3711:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V55,STATOBS(64*3712:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V56,STATOBS(64*3713:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V57,STATOBS(64*3714:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V58,STATOBS(64*3715:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V59,STATOBS(64*3716:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V60,STATOBS(64*3717:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V61,STATOBS(64*3718:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V62,STATOBS(64*3719:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V63,STATOBS(64*3720:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.V64,STATOBS(64*3721:64:C)         # Extended MEMORY data (FMS)
STATOBS.FMS.MEMORY,STATOBS(64*3722:64:C)      # Extended MEMORY num FMS
# FLD
STATOBS.FLD.K01,STATOBS(64*3723:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K02,STATOBS(64*3724:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K03,STATOBS(64*3725:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K04,STATOBS(64*3726:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K05,STATOBS(64*3727:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K06,STATOBS(64*3728:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K07,STATOBS(64*3729:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K08,STATOBS(64*3730:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K09,STATOBS(64*3731:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K10,STATOBS(64*3732:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K11,STATOBS(64*3733:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K12,STATOBS(64*3734:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K13,STATOBS(64*3735:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K14,STATOBS(64*3736:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K15,STATOBS(64*3737:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K16,STATOBS(64*3738:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K17,STATOBS(64*3739:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K18,STATOBS(64*3740:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K19,STATOBS(64*3741:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K20,STATOBS(64*3742:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K21,STATOBS(64*3743:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K22,STATOBS(64*3744:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K23,STATOBS(64*3745:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K24,STATOBS(64*3746:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K25,STATOBS(64*3747:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K26,STATOBS(64*3748:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K27,STATOBS(64*3749:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K28,STATOBS(64*3750:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K29,STATOBS(64*3751:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K30,STATOBS(64*3752:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K31,STATOBS(64*3753:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K32,STATOBS(64*3754:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K33,STATOBS(64*3755:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K34,STATOBS(64*3756:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K35,STATOBS(64*3757:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K36,STATOBS(64*3758:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K37,STATOBS(64*3759:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K38,STATOBS(64*3760:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K39,STATOBS(64*3761:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K40,STATOBS(64*3762:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K41,STATOBS(64*3763:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K42,STATOBS(64*3764:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K43,STATOBS(64*3765:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K44,STATOBS(64*3766:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K45,STATOBS(64*3767:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K46,STATOBS(64*3768:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K47,STATOBS(64*3769:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K48,STATOBS(64*3770:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K49,STATOBS(64*3771:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K50,STATOBS(64*3772:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K51,STATOBS(64*3773:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K52,STATOBS(64*3774:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K53,STATOBS(64*3775:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K54,STATOBS(64*3776:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K55,STATOBS(64*3777:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K56,STATOBS(64*3778:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K57,STATOBS(64*3779:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K58,STATOBS(64*3780:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K59,STATOBS(64*3781:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K60,STATOBS(64*3782:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K61,STATOBS(64*3783:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K62,STATOBS(64*3784:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K63,STATOBS(64*3785:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.K64,STATOBS(64*3786:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V01,STATOBS(64*3787:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V02,STATOBS(64*3788:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V03,STATOBS(64*3789:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V04,STATOBS(64*3790:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V05,STATOBS(64*3791:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V06,STATOBS(64*3792:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V07,STATOBS(64*3793:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V08,STATOBS(64*3794:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V09,STATOBS(64*3795:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V10,STATOBS(64*3796:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V11,STATOBS(64*3797:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V12,STATOBS(64*3798:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V13,STATOBS(64*3799:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V14,STATOBS(64*3800:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V15,STATOBS(64*3801:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V16,STATOBS(64*3802:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V17,STATOBS(64*3803:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V18,STATOBS(64*3804:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V19,STATOBS(64*3805:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V20,STATOBS(64*3806:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V21,STATOBS(64*3807:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V22,STATOBS(64*3808:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V23,STATOBS(64*3809:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V24,STATOBS(64*3810:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V25,STATOBS(64*3811:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V26,STATOBS(64*3812:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V27,STATOBS(64*3813:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V28,STATOBS(64*3814:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V29,STATOBS(64*3815:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V30,STATOBS(64*3816:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V31,STATOBS(64*3817:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V32,STATOBS(64*3818:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V33,STATOBS(64*3819:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V34,STATOBS(64*3820:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V35,STATOBS(64*3821:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V36,STATOBS(64*3822:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V37,STATOBS(64*3823:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V38,STATOBS(64*3824:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V39,STATOBS(64*3825:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V40,STATOBS(64*3826:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V41,STATOBS(64*3827:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V42,STATOBS(64*3828:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V43,STATOBS(64*3829:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V44,STATOBS(64*3830:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V45,STATOBS(64*3831:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V46,STATOBS(64*3832:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V47,STATOBS(64*3833:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V48,STATOBS(64*3834:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V49,STATOBS(64*3835:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V50,STATOBS(64*3836:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V51,STATOBS(64*3837:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V52,STATOBS(64*3838:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V53,STATOBS(64*3839:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V54,STATOBS(64*3840:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V55,STATOBS(64*3841:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V56,STATOBS(64*3842:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V57,STATOBS(64*3843:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V58,STATOBS(64*3844:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V59,STATOBS(64*3845:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V60,STATOBS(64*3846:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V61,STATOBS(64*3847:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V62,STATOBS(64*3848:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V63,STATOBS(64*3849:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.V64,STATOBS(64*3850:64:C)         # Extended MEMORY data (FLD)
STATOBS.FLD.MEMORY,STATOBS(64*3851:64:C)      # Extended MEMORY num FLD
# AON
STATOBS.AON.K01,STATOBS(64*3852:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K02,STATOBS(64*3853:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K03,STATOBS(64*3854:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K04,STATOBS(64*3855:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K05,STATOBS(64*3856:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K06,STATOBS(64*3857:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K07,STATOBS(64*3858:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K08,STATOBS(64*3859:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K09,STATOBS(64*3860:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K10,STATOBS(64*3861:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K11,STATOBS(64*3862:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K12,STATOBS(64*3863:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K13,STATOBS(64*3864:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K14,STATOBS(64*3865:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K15,STATOBS(64*3866:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K16,STATOBS(64*3867:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K17,STATOBS(64*3868:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K18,STATOBS(64*3869:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K19,STATOBS(64*3870:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K20,STATOBS(64*3871:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K21,STATOBS(64*3872:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K22,STATOBS(64*3873:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K23,STATOBS(64*3874:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K24,STATOBS(64*3875:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K25,STATOBS(64*3876:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K26,STATOBS(64*3877:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K27,STATOBS(64*3878:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K28,STATOBS(64*3879:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K29,STATOBS(64*3880:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K30,STATOBS(64*3881:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K31,STATOBS(64*3882:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K32,STATOBS(64*3883:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K33,STATOBS(64*3884:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K34,STATOBS(64*3885:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K35,STATOBS(64*3886:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K36,STATOBS(64*3887:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K37,STATOBS(64*3888:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K38,STATOBS(64*3889:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K39,STATOBS(64*3890:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K40,STATOBS(64*3891:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K41,STATOBS(64*3892:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K42,STATOBS(64*3893:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K43,STATOBS(64*3894:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K44,STATOBS(64*3895:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K45,STATOBS(64*3896:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K46,STATOBS(64*3897:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K47,STATOBS(64*3898:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K48,STATOBS(64*3899:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K49,STATOBS(64*3900:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K50,STATOBS(64*3901:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K51,STATOBS(64*3902:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K52,STATOBS(64*3903:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K53,STATOBS(64*3904:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K54,STATOBS(64*3905:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K55,STATOBS(64*3906:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K56,STATOBS(64*3907:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K57,STATOBS(64*3908:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K58,STATOBS(64*3909:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K59,STATOBS(64*3910:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K60,STATOBS(64*3911:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K61,STATOBS(64*3912:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K62,STATOBS(64*3913:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K63,STATOBS(64*3914:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.K64,STATOBS(64*3915:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V01,STATOBS(64*3916:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V02,STATOBS(64*3917:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V03,STATOBS(64*3918:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V04,STATOBS(64*3919:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V05,STATOBS(64*3920:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V06,STATOBS(64*3921:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V07,STATOBS(64*3922:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V08,STATOBS(64*3923:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V09,STATOBS(64*3924:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V10,STATOBS(64*3925:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V11,STATOBS(64*3926:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V12,STATOBS(64*3927:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V13,STATOBS(64*3928:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V14,STATOBS(64*3929:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V15,STATOBS(64*3930:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V16,STATOBS(64*3931:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V17,STATOBS(64*3932:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V18,STATOBS(64*3933:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V19,STATOBS(64*3934:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V20,STATOBS(64*3935:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V21,STATOBS(64*3936:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V22,STATOBS(64*3937:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V23,STATOBS(64*3938:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V24,STATOBS(64*3939:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V25,STATOBS(64*3940:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V26,STATOBS(64*3941:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V27,STATOBS(64*3942:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V28,STATOBS(64*3943:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V29,STATOBS(64*3944:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V30,STATOBS(64*3945:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V31,STATOBS(64*3946:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V32,STATOBS(64*3947:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V33,STATOBS(64*3948:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V34,STATOBS(64*3949:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V35,STATOBS(64*3950:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V36,STATOBS(64*3951:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V37,STATOBS(64*3952:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V38,STATOBS(64*3953:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V39,STATOBS(64*3954:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V40,STATOBS(64*3955:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V41,STATOBS(64*3956:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V42,STATOBS(64*3957:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V43,STATOBS(64*3958:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V44,STATOBS(64*3959:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V45,STATOBS(64*3960:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V46,STATOBS(64*3961:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V47,STATOBS(64*3962:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V48,STATOBS(64*3963:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V49,STATOBS(64*3964:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V50,STATOBS(64*3965:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V51,STATOBS(64*3966:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V52,STATOBS(64*3967:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V53,STATOBS(64*3968:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V54,STATOBS(64*3969:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V55,STATOBS(64*3970:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V56,STATOBS(64*3971:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V57,STATOBS(64*3972:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V58,STATOBS(64*3973:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V59,STATOBS(64*3974:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V60,STATOBS(64*3975:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V61,STATOBS(64*3976:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V62,STATOBS(64*3977:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V63,STATOBS(64*3978:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.V64,STATOBS(64*3979:64:C)         # Extended MEMORY data (AON)
STATOBS.AON.MEMORY,STATOBS(64*3980:64:C)      # Extended MEMORY num AON
# HIC
STATOBS.HIC.K01,STATOBS(64*3981:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K02,STATOBS(64*3982:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K03,STATOBS(64*3983:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K04,STATOBS(64*3984:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K05,STATOBS(64*3985:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K06,STATOBS(64*3986:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K07,STATOBS(64*3987:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K08,STATOBS(64*3988:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K09,STATOBS(64*3989:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K10,STATOBS(64*3990:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K11,STATOBS(64*3991:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K12,STATOBS(64*3992:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K13,STATOBS(64*3993:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K14,STATOBS(64*3994:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K15,STATOBS(64*3995:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K16,STATOBS(64*3996:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K17,STATOBS(64*3997:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K18,STATOBS(64*3998:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K19,STATOBS(64*3999:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K20,STATOBS(64*4000:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K21,STATOBS(64*4001:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K22,STATOBS(64*4002:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K23,STATOBS(64*4003:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K24,STATOBS(64*4004:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K25,STATOBS(64*4005:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K26,STATOBS(64*4006:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K27,STATOBS(64*4007:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K28,STATOBS(64*4008:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K29,STATOBS(64*4009:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K30,STATOBS(64*4010:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K31,STATOBS(64*4011:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K32,STATOBS(64*4012:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K33,STATOBS(64*4013:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K34,STATOBS(64*4014:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K35,STATOBS(64*4015:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K36,STATOBS(64*4016:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K37,STATOBS(64*4017:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K38,STATOBS(64*4018:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K39,STATOBS(64*4019:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K40,STATOBS(64*4020:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K41,STATOBS(64*4021:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K42,STATOBS(64*4022:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K43,STATOBS(64*4023:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K44,STATOBS(64*4024:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K45,STATOBS(64*4025:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K46,STATOBS(64*4026:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K47,STATOBS(64*4027:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K48,STATOBS(64*4028:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K49,STATOBS(64*4029:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K50,STATOBS(64*4030:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K51,STATOBS(64*4031:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K52,STATOBS(64*4032:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K53,STATOBS(64*4033:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K54,STATOBS(64*4034:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K55,STATOBS(64*4035:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K56,STATOBS(64*4036:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K57,STATOBS(64*4037:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K58,STATOBS(64*4038:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K59,STATOBS(64*4039:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K60,STATOBS(64*4040:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K61,STATOBS(64*4041:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K62,STATOBS(64*4042:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K63,STATOBS(64*4043:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.K64,STATOBS(64*4044:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V01,STATOBS(64*4045:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V02,STATOBS(64*4046:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V03,STATOBS(64*4047:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V04,STATOBS(64*4048:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V05,STATOBS(64*4049:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V06,STATOBS(64*4050:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V07,STATOBS(64*4051:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V08,STATOBS(64*4052:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V09,STATOBS(64*4053:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V10,STATOBS(64*4054:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V11,STATOBS(64*4055:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V12,STATOBS(64*4056:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V13,STATOBS(64*4057:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V14,STATOBS(64*4058:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V15,STATOBS(64*4059:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V16,STATOBS(64*4060:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V17,STATOBS(64*4061:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V18,STATOBS(64*4062:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V19,STATOBS(64*4063:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V20,STATOBS(64*4064:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V21,STATOBS(64*4065:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V22,STATOBS(64*4066:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V23,STATOBS(64*4067:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V24,STATOBS(64*4068:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V25,STATOBS(64*4069:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V26,STATOBS(64*4070:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V27,STATOBS(64*4071:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V28,STATOBS(64*4072:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V29,STATOBS(64*4073:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V30,STATOBS(64*4074:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V31,STATOBS(64*4075:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V32,STATOBS(64*4076:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V33,STATOBS(64*4077:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V34,STATOBS(64*4078:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V35,STATOBS(64*4079:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V36,STATOBS(64*4080:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V37,STATOBS(64*4081:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V38,STATOBS(64*4082:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V39,STATOBS(64*4083:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V40,STATOBS(64*4084:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V41,STATOBS(64*4085:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V42,STATOBS(64*4086:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V43,STATOBS(64*4087:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V44,STATOBS(64*4088:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V45,STATOBS(64*4089:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V46,STATOBS(64*4090:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V47,STATOBS(64*4091:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V48,STATOBS(64*4092:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V49,STATOBS(64*4093:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V50,STATOBS(64*4094:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V51,STATOBS(64*4095:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V52,STATOBS(64*4096:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V53,STATOBS(64*4097:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V54,STATOBS(64*4098:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V55,STATOBS(64*4099:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V56,STATOBS(64*4100:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V57,STATOBS(64*4101:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V58,STATOBS(64*4102:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V59,STATOBS(64*4103:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V60,STATOBS(64*4104:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V61,STATOBS(64*4105:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V62,STATOBS(64*4106:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V63,STATOBS(64*4107:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.V64,STATOBS(64*4108:64:C)         # Extended MEMORY data (HIC)
STATOBS.HIC.MEMORY,STATOBS(64*4109:64:C)      # Extended MEMORY num HIC
# WAV
STATOBS.WAV.K01,STATOBS(64*4110:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K02,STATOBS(64*4111:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K03,STATOBS(64*4112:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K04,STATOBS(64*4113:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K05,STATOBS(64*4114:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K06,STATOBS(64*4115:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K07,STATOBS(64*4116:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K08,STATOBS(64*4117:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K09,STATOBS(64*4118:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K10,STATOBS(64*4119:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K11,STATOBS(64*4120:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K12,STATOBS(64*4121:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K13,STATOBS(64*4122:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K14,STATOBS(64*4123:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K15,STATOBS(64*4124:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K16,STATOBS(64*4125:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K17,STATOBS(64*4126:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K18,STATOBS(64*4127:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K19,STATOBS(64*4128:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K20,STATOBS(64*4129:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K21,STATOBS(64*4130:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K22,STATOBS(64*4131:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K23,STATOBS(64*4132:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K24,STATOBS(64*4133:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K25,STATOBS(64*4134:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K26,STATOBS(64*4135:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K27,STATOBS(64*4136:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K28,STATOBS(64*4137:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K29,STATOBS(64*4138:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K30,STATOBS(64*4139:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K31,STATOBS(64*4140:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K32,STATOBS(64*4141:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K33,STATOBS(64*4142:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K34,STATOBS(64*4143:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K35,STATOBS(64*4144:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K36,STATOBS(64*4145:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K37,STATOBS(64*4146:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K38,STATOBS(64*4147:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K39,STATOBS(64*4148:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K40,STATOBS(64*4149:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K41,STATOBS(64*4150:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K42,STATOBS(64*4151:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K43,STATOBS(64*4152:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K44,STATOBS(64*4153:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K45,STATOBS(64*4154:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K46,STATOBS(64*4155:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K47,STATOBS(64*4156:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K48,STATOBS(64*4157:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K49,STATOBS(64*4158:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K50,STATOBS(64*4159:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K51,STATOBS(64*4160:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K52,STATOBS(64*4161:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K53,STATOBS(64*4162:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K54,STATOBS(64*4163:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K55,STATOBS(64*4164:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K56,STATOBS(64*4165:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K57,STATOBS(64*4166:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K58,STATOBS(64*4167:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K59,STATOBS(64*4168:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K60,STATOBS(64*4169:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K61,STATOBS(64*4170:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K62,STATOBS(64*4171:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K63,STATOBS(64*4172:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.K64,STATOBS(64*4173:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V01,STATOBS(64*4174:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V02,STATOBS(64*4175:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V03,STATOBS(64*4176:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V04,STATOBS(64*4177:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V05,STATOBS(64*4178:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V06,STATOBS(64*4179:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V07,STATOBS(64*4180:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V08,STATOBS(64*4181:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V09,STATOBS(64*4182:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V10,STATOBS(64*4183:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V11,STATOBS(64*4184:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V12,STATOBS(64*4185:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V13,STATOBS(64*4186:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V14,STATOBS(64*4187:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V15,STATOBS(64*4188:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V16,STATOBS(64*4189:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V17,STATOBS(64*4190:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V18,STATOBS(64*4191:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V19,STATOBS(64*4192:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V20,STATOBS(64*4193:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V21,STATOBS(64*4194:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V22,STATOBS(64*4195:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V23,STATOBS(64*4196:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V24,STATOBS(64*4197:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V25,STATOBS(64*4198:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V26,STATOBS(64*4199:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V27,STATOBS(64*4200:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V28,STATOBS(64*4201:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V29,STATOBS(64*4202:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V30,STATOBS(64*4203:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V31,STATOBS(64*4204:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V32,STATOBS(64*4205:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V33,STATOBS(64*4206:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V34,STATOBS(64*4207:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V35,STATOBS(64*4208:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V36,STATOBS(64*4209:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V37,STATOBS(64*4210:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V38,STATOBS(64*4211:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V39,STATOBS(64*4212:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V40,STATOBS(64*4213:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V41,STATOBS(64*4214:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V42,STATOBS(64*4215:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V43,STATOBS(64*4216:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V44,STATOBS(64*4217:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V45,STATOBS(64*4218:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V46,STATOBS(64*4219:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V47,STATOBS(64*4220:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V48,STATOBS(64*4221:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V49,STATOBS(64*4222:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V50,STATOBS(64*4223:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V51,STATOBS(64*4224:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V52,STATOBS(64*4225:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V53,STATOBS(64*4226:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V54,STATOBS(64*4227:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V55,STATOBS(64*4228:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V56,STATOBS(64*4229:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V57,STATOBS(64*4230:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V58,STATOBS(64*4231:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V59,STATOBS(64*4232:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V60,STATOBS(64*4233:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V61,STATOBS(64*4234:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V62,STATOBS(64*4235:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V63,STATOBS(64*4236:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.V64,STATOBS(64*4237:64:C)         # Extended MEMORY data (WAV)
STATOBS.WAV.MEMORY,STATOBS(64*4238:64:C)      # Extended MEMORY num WAV
# LGS
STATOBS.LGS.K01,STATOBS(64*4239:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K02,STATOBS(64*4240:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K03,STATOBS(64*4241:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K04,STATOBS(64*4242:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K05,STATOBS(64*4243:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K06,STATOBS(64*4244:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K07,STATOBS(64*4245:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K08,STATOBS(64*4246:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K09,STATOBS(64*4247:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K10,STATOBS(64*4248:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K11,STATOBS(64*4249:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K12,STATOBS(64*4250:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K13,STATOBS(64*4251:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K14,STATOBS(64*4252:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K15,STATOBS(64*4253:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K16,STATOBS(64*4254:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K17,STATOBS(64*4255:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K18,STATOBS(64*4256:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K19,STATOBS(64*4257:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K20,STATOBS(64*4258:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K21,STATOBS(64*4259:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K22,STATOBS(64*4260:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K23,STATOBS(64*4261:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K24,STATOBS(64*4262:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K25,STATOBS(64*4263:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K26,STATOBS(64*4264:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K27,STATOBS(64*4265:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K28,STATOBS(64*4266:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K29,STATOBS(64*4267:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K30,STATOBS(64*4268:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K31,STATOBS(64*4269:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K32,STATOBS(64*4270:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K33,STATOBS(64*4271:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K34,STATOBS(64*4272:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K35,STATOBS(64*4273:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K36,STATOBS(64*4274:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K37,STATOBS(64*4275:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K38,STATOBS(64*4276:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K39,STATOBS(64*4277:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K40,STATOBS(64*4278:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K41,STATOBS(64*4279:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K42,STATOBS(64*4280:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K43,STATOBS(64*4281:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K44,STATOBS(64*4282:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K45,STATOBS(64*4283:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K46,STATOBS(64*4284:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K47,STATOBS(64*4285:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K48,STATOBS(64*4286:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K49,STATOBS(64*4287:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K50,STATOBS(64*4288:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K51,STATOBS(64*4289:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K52,STATOBS(64*4290:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K53,STATOBS(64*4291:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K54,STATOBS(64*4292:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K55,STATOBS(64*4293:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K56,STATOBS(64*4294:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K57,STATOBS(64*4295:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K58,STATOBS(64*4296:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K59,STATOBS(64*4297:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K60,STATOBS(64*4298:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K61,STATOBS(64*4299:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K62,STATOBS(64*4300:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K63,STATOBS(64*4301:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.K64,STATOBS(64*4302:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V01,STATOBS(64*4303:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V02,STATOBS(64*4304:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V03,STATOBS(64*4305:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V04,STATOBS(64*4306:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V05,STATOBS(64*4307:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V06,STATOBS(64*4308:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V07,STATOBS(64*4309:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V08,STATOBS(64*4310:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V09,STATOBS(64*4311:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V10,STATOBS(64*4312:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V11,STATOBS(64*4313:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V12,STATOBS(64*4314:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V13,STATOBS(64*4315:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V14,STATOBS(64*4316:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V15,STATOBS(64*4317:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V16,STATOBS(64*4318:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V17,STATOBS(64*4319:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V18,STATOBS(64*4320:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V19,STATOBS(64*4321:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V20,STATOBS(64*4322:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V21,STATOBS(64*4323:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V22,STATOBS(64*4324:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V23,STATOBS(64*4325:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V24,STATOBS(64*4326:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V25,STATOBS(64*4327:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V26,STATOBS(64*4328:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V27,STATOBS(64*4329:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V28,STATOBS(64*4330:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V29,STATOBS(64*4331:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V30,STATOBS(64*4332:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V31,STATOBS(64*4333:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V32,STATOBS(64*4334:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V33,STATOBS(64*4335:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V34,STATOBS(64*4336:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V35,STATOBS(64*4337:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V36,STATOBS(64*4338:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V37,STATOBS(64*4339:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V38,STATOBS(64*4340:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V39,STATOBS(64*4341:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V40,STATOBS(64*4342:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V41,STATOBS(64*4343:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V42,STATOBS(64*4344:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V43,STATOBS(64*4345:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V44,STATOBS(64*4346:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V45,STATOBS(64*4347:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V46,STATOBS(64*4348:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V47,STATOBS(64*4349:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V48,STATOBS(64*4350:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V49,STATOBS(64*4351:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V50,STATOBS(64*4352:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V51,STATOBS(64*4353:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V52,STATOBS(64*4354:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V53,STATOBS(64*4355:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V54,STATOBS(64*4356:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V55,STATOBS(64*4357:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V56,STATOBS(64*4358:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V57,STATOBS(64*4359:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V58,STATOBS(64*4360:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V59,STATOBS(64*4361:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V60,STATOBS(64*4362:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V61,STATOBS(64*4363:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V62,STATOBS(64*4364:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V63,STATOBS(64*4365:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.V64,STATOBS(64*4366:64:C)         # Extended MEMORY data (LGS)
STATOBS.LGS.MEMORY,STATOBS(64*4367:64:C)      # Extended MEMORY num LGS
# O24
STATOBS.O24.K01,STATOBS(64*4368:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K02,STATOBS(64*4369:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K03,STATOBS(64*4370:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K04,STATOBS(64*4371:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K05,STATOBS(64*4372:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K06,STATOBS(64*4373:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K07,STATOBS(64*4374:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K08,STATOBS(64*4375:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K09,STATOBS(64*4376:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K10,STATOBS(64*4377:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K11,STATOBS(64*4378:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K12,STATOBS(64*4379:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K13,STATOBS(64*4380:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K14,STATOBS(64*4381:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K15,STATOBS(64*4382:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K16,STATOBS(64*4383:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K17,STATOBS(64*4384:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K18,STATOBS(64*4385:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K19,STATOBS(64*4386:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K20,STATOBS(64*4387:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K21,STATOBS(64*4388:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K22,STATOBS(64*4389:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K23,STATOBS(64*4390:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K24,STATOBS(64*4391:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K25,STATOBS(64*4392:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K26,STATOBS(64*4393:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K27,STATOBS(64*4394:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K28,STATOBS(64*4395:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K29,STATOBS(64*4396:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K30,STATOBS(64*4397:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K31,STATOBS(64*4398:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K32,STATOBS(64*4399:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K33,STATOBS(64*4400:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K34,STATOBS(64*4401:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K35,STATOBS(64*4402:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K36,STATOBS(64*4403:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K37,STATOBS(64*4404:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K38,STATOBS(64*4405:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K39,STATOBS(64*4406:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K40,STATOBS(64*4407:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K41,STATOBS(64*4408:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K42,STATOBS(64*4409:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K43,STATOBS(64*4410:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K44,STATOBS(64*4411:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K45,STATOBS(64*4412:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K46,STATOBS(64*4413:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K47,STATOBS(64*4414:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K48,STATOBS(64*4415:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K49,STATOBS(64*4416:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K50,STATOBS(64*4417:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K51,STATOBS(64*4418:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K52,STATOBS(64*4419:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K53,STATOBS(64*4420:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K54,STATOBS(64*4421:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K55,STATOBS(64*4422:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K56,STATOBS(64*4423:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K57,STATOBS(64*4424:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K58,STATOBS(64*4425:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K59,STATOBS(64*4426:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K60,STATOBS(64*4427:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K61,STATOBS(64*4428:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K62,STATOBS(64*4429:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K63,STATOBS(64*4430:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.K64,STATOBS(64*4431:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V01,STATOBS(64*4432:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V02,STATOBS(64*4433:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V03,STATOBS(64*4434:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V04,STATOBS(64*4435:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V05,STATOBS(64*4436:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V06,STATOBS(64*4437:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V07,STATOBS(64*4438:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V08,STATOBS(64*4439:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V09,STATOBS(64*4440:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V10,STATOBS(64*4441:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V11,STATOBS(64*4442:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V12,STATOBS(64*4443:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V13,STATOBS(64*4444:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V14,STATOBS(64*4445:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V15,STATOBS(64*4446:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V16,STATOBS(64*4447:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V17,STATOBS(64*4448:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V18,STATOBS(64*4449:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V19,STATOBS(64*4450:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V20,STATOBS(64*4451:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V21,STATOBS(64*4452:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V22,STATOBS(64*4453:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V23,STATOBS(64*4454:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V24,STATOBS(64*4455:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V25,STATOBS(64*4456:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V26,STATOBS(64*4457:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V27,STATOBS(64*4458:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V28,STATOBS(64*4459:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V29,STATOBS(64*4460:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V30,STATOBS(64*4461:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V31,STATOBS(64*4462:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V32,STATOBS(64*4463:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V33,STATOBS(64*4464:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V34,STATOBS(64*4465:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V35,STATOBS(64*4466:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V36,STATOBS(64*4467:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V37,STATOBS(64*4468:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V38,STATOBS(64*4469:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V39,STATOBS(64*4470:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V40,STATOBS(64*4471:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V41,STATOBS(64*4472:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V42,STATOBS(64*4473:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V43,STATOBS(64*4474:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V44,STATOBS(64*4475:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V45,STATOBS(64*4476:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V46,STATOBS(64*4477:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V47,STATOBS(64*4478:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V48,STATOBS(64*4479:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V49,STATOBS(64*4480:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V50,STATOBS(64*4481:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V51,STATOBS(64*4482:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V52,STATOBS(64*4483:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V53,STATOBS(64*4484:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V54,STATOBS(64*4485:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V55,STATOBS(64*4486:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V56,STATOBS(64*4487:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V57,STATOBS(64*4488:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V58,STATOBS(64*4489:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V59,STATOBS(64*4490:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V60,STATOBS(64*4491:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V61,STATOBS(64*4492:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V62,STATOBS(64*4493:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V63,STATOBS(64*4494:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.V64,STATOBS(64*4495:64:C)         # Extended MEMORY data (O24)
STATOBS.O24.MEMORY,STATOBS(64*4496:64:C)      # Extended MEMORY num O24
# O25
STATOBS.O25.K01,STATOBS(64*4497:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K02,STATOBS(64*4498:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K03,STATOBS(64*4499:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K04,STATOBS(64*4500:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K05,STATOBS(64*4501:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K06,STATOBS(64*4502:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K07,STATOBS(64*4503:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K08,STATOBS(64*4504:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K09,STATOBS(64*4505:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K10,STATOBS(64*4506:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K11,STATOBS(64*4507:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K12,STATOBS(64*4508:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K13,STATOBS(64*4509:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K14,STATOBS(64*4510:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K15,STATOBS(64*4511:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K16,STATOBS(64*4512:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K17,STATOBS(64*4513:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K18,STATOBS(64*4514:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K19,STATOBS(64*4515:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K20,STATOBS(64*4516:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K21,STATOBS(64*4517:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K22,STATOBS(64*4518:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K23,STATOBS(64*4519:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K24,STATOBS(64*4520:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K25,STATOBS(64*4521:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K26,STATOBS(64*4522:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K27,STATOBS(64*4523:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K28,STATOBS(64*4524:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K29,STATOBS(64*4525:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K30,STATOBS(64*4526:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K31,STATOBS(64*4527:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K32,STATOBS(64*4528:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K33,STATOBS(64*4529:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K34,STATOBS(64*4530:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K35,STATOBS(64*4531:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K36,STATOBS(64*4532:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K37,STATOBS(64*4533:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K38,STATOBS(64*4534:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K39,STATOBS(64*4535:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K40,STATOBS(64*4536:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K41,STATOBS(64*4537:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K42,STATOBS(64*4538:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K43,STATOBS(64*4539:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K44,STATOBS(64*4540:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K45,STATOBS(64*4541:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K46,STATOBS(64*4542:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K47,STATOBS(64*4543:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K48,STATOBS(64*4544:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K49,STATOBS(64*4545:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K50,STATOBS(64*4546:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K51,STATOBS(64*4547:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K52,STATOBS(64*4548:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K53,STATOBS(64*4549:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K54,STATOBS(64*4550:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K55,STATOBS(64*4551:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K56,STATOBS(64*4552:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K57,STATOBS(64*4553:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K58,STATOBS(64*4554:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K59,STATOBS(64*4555:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K60,STATOBS(64*4556:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K61,STATOBS(64*4557:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K62,STATOBS(64*4558:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K63,STATOBS(64*4559:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.K64,STATOBS(64*4560:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V01,STATOBS(64*4561:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V02,STATOBS(64*4562:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V03,STATOBS(64*4563:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V04,STATOBS(64*4564:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V05,STATOBS(64*4565:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V06,STATOBS(64*4566:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V07,STATOBS(64*4567:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V08,STATOBS(64*4568:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V09,STATOBS(64*4569:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V10,STATOBS(64*4570:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V11,STATOBS(64*4571:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V12,STATOBS(64*4572:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V13,STATOBS(64*4573:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V14,STATOBS(64*4574:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V15,STATOBS(64*4575:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V16,STATOBS(64*4576:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V17,STATOBS(64*4577:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V18,STATOBS(64*4578:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V19,STATOBS(64*4579:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V20,STATOBS(64*4580:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V21,STATOBS(64*4581:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V22,STATOBS(64*4582:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V23,STATOBS(64*4583:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V24,STATOBS(64*4584:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V25,STATOBS(64*4585:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V26,STATOBS(64*4586:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V27,STATOBS(64*4587:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V28,STATOBS(64*4588:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V29,STATOBS(64*4589:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V30,STATOBS(64*4590:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V31,STATOBS(64*4591:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V32,STATOBS(64*4592:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V33,STATOBS(64*4593:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V34,STATOBS(64*4594:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V35,STATOBS(64*4595:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V36,STATOBS(64*4596:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V37,STATOBS(64*4597:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V38,STATOBS(64*4598:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V39,STATOBS(64*4599:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V40,STATOBS(64*4600:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V41,STATOBS(64*4601:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V42,STATOBS(64*4602:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V43,STATOBS(64*4603:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V44,STATOBS(64*4604:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V45,STATOBS(64*4605:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V46,STATOBS(64*4606:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V47,STATOBS(64*4607:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V48,STATOBS(64*4608:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V49,STATOBS(64*4609:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V50,STATOBS(64*4610:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V51,STATOBS(64*4611:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V52,STATOBS(64*4612:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V53,STATOBS(64*4613:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V54,STATOBS(64*4614:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V55,STATOBS(64*4615:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V56,STATOBS(64*4616:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V57,STATOBS(64*4617:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V58,STATOBS(64*4618:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V59,STATOBS(64*4619:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V60,STATOBS(64*4620:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V61,STATOBS(64*4621:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V62,STATOBS(64*4622:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V63,STATOBS(64*4623:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.V64,STATOBS(64*4624:64:C)         # Extended MEMORY data (O25)
STATOBS.O25.MEMORY,STATOBS(64*4625:64:C)      # Extended MEMORY num O25
# O26
STATOBS.O26.K01,STATOBS(64*4626:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K02,STATOBS(64*4627:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K03,STATOBS(64*4628:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K04,STATOBS(64*4629:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K05,STATOBS(64*4630:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K06,STATOBS(64*4631:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K07,STATOBS(64*4632:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K08,STATOBS(64*4633:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K09,STATOBS(64*4634:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K10,STATOBS(64*4635:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K11,STATOBS(64*4636:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K12,STATOBS(64*4637:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K13,STATOBS(64*4638:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K14,STATOBS(64*4639:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K15,STATOBS(64*4640:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K16,STATOBS(64*4641:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K17,STATOBS(64*4642:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K18,STATOBS(64*4643:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K19,STATOBS(64*4644:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K20,STATOBS(64*4645:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K21,STATOBS(64*4646:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K22,STATOBS(64*4647:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K23,STATOBS(64*4648:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K24,STATOBS(64*4649:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K25,STATOBS(64*4650:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K26,STATOBS(64*4651:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K27,STATOBS(64*4652:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K28,STATOBS(64*4653:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K29,STATOBS(64*4654:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K30,STATOBS(64*4655:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K31,STATOBS(64*4656:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K32,STATOBS(64*4657:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K33,STATOBS(64*4658:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K34,STATOBS(64*4659:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K35,STATOBS(64*4660:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K36,STATOBS(64*4661:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K37,STATOBS(64*4662:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K38,STATOBS(64*4663:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K39,STATOBS(64*4664:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K40,STATOBS(64*4665:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K41,STATOBS(64*4666:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K42,STATOBS(64*4667:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K43,STATOBS(64*4668:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K44,STATOBS(64*4669:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K45,STATOBS(64*4670:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K46,STATOBS(64*4671:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K47,STATOBS(64*4672:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K48,STATOBS(64*4673:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K49,STATOBS(64*4674:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K50,STATOBS(64*4675:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K51,STATOBS(64*4676:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K52,STATOBS(64*4677:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K53,STATOBS(64*4678:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K54,STATOBS(64*4679:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K55,STATOBS(64*4680:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K56,STATOBS(64*4681:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K57,STATOBS(64*4682:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K58,STATOBS(64*4683:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K59,STATOBS(64*4684:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K60,STATOBS(64*4685:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K61,STATOBS(64*4686:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K62,STATOBS(64*4687:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K63,STATOBS(64*4688:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.K64,STATOBS(64*4689:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V01,STATOBS(64*4690:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V02,STATOBS(64*4691:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V03,STATOBS(64*4692:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V04,STATOBS(64*4693:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V05,STATOBS(64*4694:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V06,STATOBS(64*4695:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V07,STATOBS(64*4696:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V08,STATOBS(64*4697:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V09,STATOBS(64*4698:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V10,STATOBS(64*4699:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V11,STATOBS(64*4700:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V12,STATOBS(64*4701:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V13,STATOBS(64*4702:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V14,STATOBS(64*4703:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V15,STATOBS(64*4704:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V16,STATOBS(64*4705:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V17,STATOBS(64*4706:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V18,STATOBS(64*4707:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V19,STATOBS(64*4708:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V20,STATOBS(64*4709:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V21,STATOBS(64*4710:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V22,STATOBS(64*4711:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V23,STATOBS(64*4712:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V24,STATOBS(64*4713:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V25,STATOBS(64*4714:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V26,STATOBS(64*4715:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V27,STATOBS(64*4716:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V28,STATOBS(64*4717:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V29,STATOBS(64*4718:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V30,STATOBS(64*4719:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V31,STATOBS(64*4720:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V32,STATOBS(64*4721:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V33,STATOBS(64*4722:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V34,STATOBS(64*4723:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V35,STATOBS(64*4724:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V36,STATOBS(64*4725:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V37,STATOBS(64*4726:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V38,STATOBS(64*4727:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V39,STATOBS(64*4728:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V40,STATOBS(64*4729:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V41,STATOBS(64*4730:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V42,STATOBS(64*4731:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V43,STATOBS(64*4732:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V44,STATOBS(64*4733:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V45,STATOBS(64*4734:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V46,STATOBS(64*4735:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V47,STATOBS(64*4736:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V48,STATOBS(64*4737:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V49,STATOBS(64*4738:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V50,STATOBS(64*4739:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V51,STATOBS(64*4740:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V52,STATOBS(64*4741:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V53,STATOBS(64*4742:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V54,STATOBS(64*4743:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V55,STATOBS(64*4744:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V56,STATOBS(64*4745:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V57,STATOBS(64*4746:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V58,STATOBS(64*4747:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V59,STATOBS(64*4748:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V60,STATOBS(64*4749:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V61,STATOBS(64*4750:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V62,STATOBS(64*4751:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V63,STATOBS(64*4752:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.V64,STATOBS(64*4753:64:C)         # Extended MEMORY data (O26)
STATOBS.O26.MEMORY,STATOBS(64*4754:64:C)      # Extended MEMORY num O26
# O27
STATOBS.O27.K01,STATOBS(64*4755:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K02,STATOBS(64*4756:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K03,STATOBS(64*4757:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K04,STATOBS(64*4758:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K05,STATOBS(64*4759:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K06,STATOBS(64*4760:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K07,STATOBS(64*4761:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K08,STATOBS(64*4762:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K09,STATOBS(64*4763:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K10,STATOBS(64*4764:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K11,STATOBS(64*4765:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K12,STATOBS(64*4766:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K13,STATOBS(64*4767:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K14,STATOBS(64*4768:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K15,STATOBS(64*4769:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K16,STATOBS(64*4770:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K17,STATOBS(64*4771:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K18,STATOBS(64*4772:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K19,STATOBS(64*4773:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K20,STATOBS(64*4774:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K21,STATOBS(64*4775:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K22,STATOBS(64*4776:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K23,STATOBS(64*4777:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K24,STATOBS(64*4778:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K25,STATOBS(64*4779:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K26,STATOBS(64*4780:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K27,STATOBS(64*4781:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K28,STATOBS(64*4782:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K29,STATOBS(64*4783:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K30,STATOBS(64*4784:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K31,STATOBS(64*4785:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K32,STATOBS(64*4786:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K33,STATOBS(64*4787:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K34,STATOBS(64*4788:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K35,STATOBS(64*4789:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K36,STATOBS(64*4790:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K37,STATOBS(64*4791:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K38,STATOBS(64*4792:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K39,STATOBS(64*4793:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K40,STATOBS(64*4794:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K41,STATOBS(64*4795:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K42,STATOBS(64*4796:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K43,STATOBS(64*4797:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K44,STATOBS(64*4798:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K45,STATOBS(64*4799:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K46,STATOBS(64*4800:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K47,STATOBS(64*4801:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K48,STATOBS(64*4802:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K49,STATOBS(64*4803:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K50,STATOBS(64*4804:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K51,STATOBS(64*4805:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K52,STATOBS(64*4806:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K53,STATOBS(64*4807:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K54,STATOBS(64*4808:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K55,STATOBS(64*4809:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K56,STATOBS(64*4810:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K57,STATOBS(64*4811:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K58,STATOBS(64*4812:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K59,STATOBS(64*4813:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K60,STATOBS(64*4814:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K61,STATOBS(64*4815:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K62,STATOBS(64*4816:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K63,STATOBS(64*4817:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.K64,STATOBS(64*4818:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V01,STATOBS(64*4819:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V02,STATOBS(64*4820:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V03,STATOBS(64*4821:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V04,STATOBS(64*4822:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V05,STATOBS(64*4823:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V06,STATOBS(64*4824:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V07,STATOBS(64*4825:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V08,STATOBS(64*4826:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V09,STATOBS(64*4827:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V10,STATOBS(64*4828:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V11,STATOBS(64*4829:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V12,STATOBS(64*4830:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V13,STATOBS(64*4831:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V14,STATOBS(64*4832:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V15,STATOBS(64*4833:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V16,STATOBS(64*4834:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V17,STATOBS(64*4835:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V18,STATOBS(64*4836:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V19,STATOBS(64*4837:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V20,STATOBS(64*4838:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V21,STATOBS(64*4839:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V22,STATOBS(64*4840:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V23,STATOBS(64*4841:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V24,STATOBS(64*4842:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V25,STATOBS(64*4843:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V26,STATOBS(64*4844:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V27,STATOBS(64*4845:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V28,STATOBS(64*4846:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V29,STATOBS(64*4847:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V30,STATOBS(64*4848:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V31,STATOBS(64*4849:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V32,STATOBS(64*4850:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V33,STATOBS(64*4851:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V34,STATOBS(64*4852:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V35,STATOBS(64*4853:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V36,STATOBS(64*4854:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V37,STATOBS(64*4855:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V38,STATOBS(64*4856:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V39,STATOBS(64*4857:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V40,STATOBS(64*4858:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V41,STATOBS(64*4859:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V42,STATOBS(64*4860:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V43,STATOBS(64*4861:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V44,STATOBS(64*4862:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V45,STATOBS(64*4863:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V46,STATOBS(64*4864:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V47,STATOBS(64*4865:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V48,STATOBS(64*4866:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V49,STATOBS(64*4867:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V50,STATOBS(64*4868:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V51,STATOBS(64*4869:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V52,STATOBS(64*4870:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V53,STATOBS(64*4871:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V54,STATOBS(64*4872:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V55,STATOBS(64*4873:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V56,STATOBS(64*4874:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V57,STATOBS(64*4875:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V58,STATOBS(64*4876:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V59,STATOBS(64*4877:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V60,STATOBS(64*4878:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V61,STATOBS(64*4879:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V62,STATOBS(64*4880:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V63,STATOBS(64*4881:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.V64,STATOBS(64*4882:64:C)         # Extended MEMORY data (O27)
STATOBS.O27.MEMORY,STATOBS(64*4883:64:C)      # Extended MEMORY num O27
# O28
STATOBS.O28.K01,STATOBS(64*4884:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K02,STATOBS(64*4885:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K03,STATOBS(64*4886:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K04,STATOBS(64*4887:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K05,STATOBS(64*4888:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K06,STATOBS(64*4889:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K07,STATOBS(64*4890:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K08,STATOBS(64*4891:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K09,STATOBS(64*4892:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K10,STATOBS(64*4893:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K11,STATOBS(64*4894:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K12,STATOBS(64*4895:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K13,STATOBS(64*4896:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K14,STATOBS(64*4897:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K15,STATOBS(64*4898:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K16,STATOBS(64*4899:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K17,STATOBS(64*4900:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K18,STATOBS(64*4901:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K19,STATOBS(64*4902:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K20,STATOBS(64*4903:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K21,STATOBS(64*4904:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K22,STATOBS(64*4905:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K23,STATOBS(64*4906:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K24,STATOBS(64*4907:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K25,STATOBS(64*4908:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K26,STATOBS(64*4909:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K27,STATOBS(64*4910:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K28,STATOBS(64*4911:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K29,STATOBS(64*4912:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K30,STATOBS(64*4913:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K31,STATOBS(64*4914:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K32,STATOBS(64*4915:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K33,STATOBS(64*4916:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K34,STATOBS(64*4917:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K35,STATOBS(64*4918:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K36,STATOBS(64*4919:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K37,STATOBS(64*4920:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K38,STATOBS(64*4921:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K39,STATOBS(64*4922:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K40,STATOBS(64*4923:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K41,STATOBS(64*4924:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K42,STATOBS(64*4925:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K43,STATOBS(64*4926:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K44,STATOBS(64*4927:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K45,STATOBS(64*4928:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K46,STATOBS(64*4929:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K47,STATOBS(64*4930:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K48,STATOBS(64*4931:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K49,STATOBS(64*4932:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K50,STATOBS(64*4933:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K51,STATOBS(64*4934:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K52,STATOBS(64*4935:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K53,STATOBS(64*4936:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K54,STATOBS(64*4937:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K55,STATOBS(64*4938:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K56,STATOBS(64*4939:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K57,STATOBS(64*4940:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K58,STATOBS(64*4941:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K59,STATOBS(64*4942:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K60,STATOBS(64*4943:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K61,STATOBS(64*4944:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K62,STATOBS(64*4945:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K63,STATOBS(64*4946:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.K64,STATOBS(64*4947:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V01,STATOBS(64*4948:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V02,STATOBS(64*4949:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V03,STATOBS(64*4950:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V04,STATOBS(64*4951:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V05,STATOBS(64*4952:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V06,STATOBS(64*4953:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V07,STATOBS(64*4954:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V08,STATOBS(64*4955:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V09,STATOBS(64*4956:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V10,STATOBS(64*4957:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V11,STATOBS(64*4958:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V12,STATOBS(64*4959:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V13,STATOBS(64*4960:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V14,STATOBS(64*4961:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V15,STATOBS(64*4962:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V16,STATOBS(64*4963:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V17,STATOBS(64*4964:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V18,STATOBS(64*4965:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V19,STATOBS(64*4966:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V20,STATOBS(64*4967:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V21,STATOBS(64*4968:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V22,STATOBS(64*4969:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V23,STATOBS(64*4970:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V24,STATOBS(64*4971:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V25,STATOBS(64*4972:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V26,STATOBS(64*4973:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V27,STATOBS(64*4974:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V28,STATOBS(64*4975:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V29,STATOBS(64*4976:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V30,STATOBS(64*4977:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V31,STATOBS(64*4978:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V32,STATOBS(64*4979:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V33,STATOBS(64*4980:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V34,STATOBS(64*4981:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V35,STATOBS(64*4982:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V36,STATOBS(64*4983:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V37,STATOBS(64*4984:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V38,STATOBS(64*4985:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V39,STATOBS(64*4986:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V40,STATOBS(64*4987:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V41,STATOBS(64*4988:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V42,STATOBS(64*4989:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V43,STATOBS(64*4990:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V44,STATOBS(64*4991:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V45,STATOBS(64*4992:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V46,STATOBS(64*4993:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V47,STATOBS(64*4994:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V48,STATOBS(64*4995:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V49,STATOBS(64*4996:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V50,STATOBS(64*4997:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V51,STATOBS(64*4998:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V52,STATOBS(64*4999:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V53,STATOBS(64*5000:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V54,STATOBS(64*5001:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V55,STATOBS(64*5002:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V56,STATOBS(64*5003:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V57,STATOBS(64*5004:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V58,STATOBS(64*5005:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V59,STATOBS(64*5006:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V60,STATOBS(64*5007:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V61,STATOBS(64*5008:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V62,STATOBS(64*5009:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V63,STATOBS(64*5010:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.V64,STATOBS(64*5011:64:C)         # Extended MEMORY data (O28)
STATOBS.O28.MEMORY,STATOBS(64*5012:64:C)      # Extended MEMORY num O28
# O29
STATOBS.O29.K01,STATOBS(64*5013:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K02,STATOBS(64*5014:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K03,STATOBS(64*5015:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K04,STATOBS(64*5016:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K05,STATOBS(64*5017:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K06,STATOBS(64*5018:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K07,STATOBS(64*5019:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K08,STATOBS(64*5020:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K09,STATOBS(64*5021:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K10,STATOBS(64*5022:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K11,STATOBS(64*5023:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K12,STATOBS(64*5024:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K13,STATOBS(64*5025:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K14,STATOBS(64*5026:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K15,STATOBS(64*5027:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K16,STATOBS(64*5028:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K17,STATOBS(64*5029:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K18,STATOBS(64*5030:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K19,STATOBS(64*5031:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K20,STATOBS(64*5032:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K21,STATOBS(64*5033:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K22,STATOBS(64*5034:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K23,STATOBS(64*5035:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K24,STATOBS(64*5036:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K25,STATOBS(64*5037:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K26,STATOBS(64*5038:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K27,STATOBS(64*5039:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K28,STATOBS(64*5040:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K29,STATOBS(64*5041:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K30,STATOBS(64*5042:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K31,STATOBS(64*5043:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K32,STATOBS(64*5044:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K33,STATOBS(64*5045:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K34,STATOBS(64*5046:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K35,STATOBS(64*5047:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K36,STATOBS(64*5048:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K37,STATOBS(64*5049:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K38,STATOBS(64*5050:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K39,STATOBS(64*5051:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K40,STATOBS(64*5052:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K41,STATOBS(64*5053:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K42,STATOBS(64*5054:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K43,STATOBS(64*5055:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K44,STATOBS(64*5056:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K45,STATOBS(64*5057:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K46,STATOBS(64*5058:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K47,STATOBS(64*5059:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K48,STATOBS(64*5060:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K49,STATOBS(64*5061:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K50,STATOBS(64*5062:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K51,STATOBS(64*5063:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K52,STATOBS(64*5064:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K53,STATOBS(64*5065:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K54,STATOBS(64*5066:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K55,STATOBS(64*5067:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K56,STATOBS(64*5068:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K57,STATOBS(64*5069:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K58,STATOBS(64*5070:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K59,STATOBS(64*5071:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K60,STATOBS(64*5072:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K61,STATOBS(64*5073:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K62,STATOBS(64*5074:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K63,STATOBS(64*5075:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.K64,STATOBS(64*5076:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V01,STATOBS(64*5077:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V02,STATOBS(64*5078:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V03,STATOBS(64*5079:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V04,STATOBS(64*5080:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V05,STATOBS(64*5081:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V06,STATOBS(64*5082:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V07,STATOBS(64*5083:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V08,STATOBS(64*5084:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V09,STATOBS(64*5085:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V10,STATOBS(64*5086:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V11,STATOBS(64*5087:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V12,STATOBS(64*5088:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V13,STATOBS(64*5089:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V14,STATOBS(64*5090:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V15,STATOBS(64*5091:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V16,STATOBS(64*5092:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V17,STATOBS(64*5093:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V18,STATOBS(64*5094:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V19,STATOBS(64*5095:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V20,STATOBS(64*5096:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V21,STATOBS(64*5097:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V22,STATOBS(64*5098:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V23,STATOBS(64*5099:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V24,STATOBS(64*5100:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V25,STATOBS(64*5101:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V26,STATOBS(64*5102:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V27,STATOBS(64*5103:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V28,STATOBS(64*5104:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V29,STATOBS(64*5105:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V30,STATOBS(64*5106:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V31,STATOBS(64*5107:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V32,STATOBS(64*5108:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V33,STATOBS(64*5109:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V34,STATOBS(64*5110:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V35,STATOBS(64*5111:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V36,STATOBS(64*5112:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V37,STATOBS(64*5113:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V38,STATOBS(64*5114:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V39,STATOBS(64*5115:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V40,STATOBS(64*5116:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V41,STATOBS(64*5117:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V42,STATOBS(64*5118:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V43,STATOBS(64*5119:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V44,STATOBS(64*5120:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V45,STATOBS(64*5121:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V46,STATOBS(64*5122:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V47,STATOBS(64*5123:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V48,STATOBS(64*5124:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V49,STATOBS(64*5125:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V50,STATOBS(64*5126:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V51,STATOBS(64*5127:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V52,STATOBS(64*5128:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V53,STATOBS(64*5129:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V54,STATOBS(64*5130:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V55,STATOBS(64*5131:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V56,STATOBS(64*5132:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V57,STATOBS(64*5133:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V58,STATOBS(64*5134:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V59,STATOBS(64*5135:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V60,STATOBS(64*5136:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V61,STATOBS(64*5137:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V62,STATOBS(64*5138:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V63,STATOBS(64*5139:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.V64,STATOBS(64*5140:64:C)         # Extended MEMORY data (O29)
STATOBS.O29.MEMORY,STATOBS(64*5141:64:C)      # Extended MEMORY num O29
# O30
STATOBS.O30.K01,STATOBS(64*5142:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K02,STATOBS(64*5143:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K03,STATOBS(64*5144:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K04,STATOBS(64*5145:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K05,STATOBS(64*5146:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K06,STATOBS(64*5147:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K07,STATOBS(64*5148:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K08,STATOBS(64*5149:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K09,STATOBS(64*5150:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K10,STATOBS(64*5151:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K11,STATOBS(64*5152:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K12,STATOBS(64*5153:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K13,STATOBS(64*5154:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K14,STATOBS(64*5155:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K15,STATOBS(64*5156:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K16,STATOBS(64*5157:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K17,STATOBS(64*5158:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K18,STATOBS(64*5159:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K19,STATOBS(64*5160:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K20,STATOBS(64*5161:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K21,STATOBS(64*5162:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K22,STATOBS(64*5163:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K23,STATOBS(64*5164:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K24,STATOBS(64*5165:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K25,STATOBS(64*5166:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K26,STATOBS(64*5167:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K27,STATOBS(64*5168:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K28,STATOBS(64*5169:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K29,STATOBS(64*5170:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K30,STATOBS(64*5171:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K31,STATOBS(64*5172:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K32,STATOBS(64*5173:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K33,STATOBS(64*5174:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K34,STATOBS(64*5175:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K35,STATOBS(64*5176:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K36,STATOBS(64*5177:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K37,STATOBS(64*5178:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K38,STATOBS(64*5179:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K39,STATOBS(64*5180:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K40,STATOBS(64*5181:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K41,STATOBS(64*5182:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K42,STATOBS(64*5183:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K43,STATOBS(64*5184:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K44,STATOBS(64*5185:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K45,STATOBS(64*5186:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K46,STATOBS(64*5187:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K47,STATOBS(64*5188:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K48,STATOBS(64*5189:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K49,STATOBS(64*5190:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K50,STATOBS(64*5191:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K51,STATOBS(64*5192:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K52,STATOBS(64*5193:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K53,STATOBS(64*5194:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K54,STATOBS(64*5195:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K55,STATOBS(64*5196:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K56,STATOBS(64*5197:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K57,STATOBS(64*5198:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K58,STATOBS(64*5199:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K59,STATOBS(64*5200:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K60,STATOBS(64*5201:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K61,STATOBS(64*5202:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K62,STATOBS(64*5203:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K63,STATOBS(64*5204:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.K64,STATOBS(64*5205:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V01,STATOBS(64*5206:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V02,STATOBS(64*5207:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V03,STATOBS(64*5208:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V04,STATOBS(64*5209:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V05,STATOBS(64*5210:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V06,STATOBS(64*5211:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V07,STATOBS(64*5212:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V08,STATOBS(64*5213:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V09,STATOBS(64*5214:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V10,STATOBS(64*5215:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V11,STATOBS(64*5216:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V12,STATOBS(64*5217:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V13,STATOBS(64*5218:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V14,STATOBS(64*5219:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V15,STATOBS(64*5220:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V16,STATOBS(64*5221:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V17,STATOBS(64*5222:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V18,STATOBS(64*5223:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V19,STATOBS(64*5224:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V20,STATOBS(64*5225:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V21,STATOBS(64*5226:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V22,STATOBS(64*5227:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V23,STATOBS(64*5228:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V24,STATOBS(64*5229:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V25,STATOBS(64*5230:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V26,STATOBS(64*5231:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V27,STATOBS(64*5232:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V28,STATOBS(64*5233:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V29,STATOBS(64*5234:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V30,STATOBS(64*5235:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V31,STATOBS(64*5236:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V32,STATOBS(64*5237:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V33,STATOBS(64*5238:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V34,STATOBS(64*5239:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V35,STATOBS(64*5240:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V36,STATOBS(64*5241:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V37,STATOBS(64*5242:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V38,STATOBS(64*5243:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V39,STATOBS(64*5244:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V40,STATOBS(64*5245:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V41,STATOBS(64*5246:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V42,STATOBS(64*5247:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V43,STATOBS(64*5248:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V44,STATOBS(64*5249:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V45,STATOBS(64*5250:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V46,STATOBS(64*5251:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V47,STATOBS(64*5252:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V48,STATOBS(64*5253:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V49,STATOBS(64*5254:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V50,STATOBS(64*5255:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V51,STATOBS(64*5256:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V52,STATOBS(64*5257:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V53,STATOBS(64*5258:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V54,STATOBS(64*5259:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V55,STATOBS(64*5260:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V56,STATOBS(64*5261:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V57,STATOBS(64*5262:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V58,STATOBS(64*5263:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V59,STATOBS(64*5264:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V60,STATOBS(64*5265:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V61,STATOBS(64*5266:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V62,STATOBS(64*5267:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V63,STATOBS(64*5268:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.V64,STATOBS(64*5269:64:C)         # Extended MEMORY data (O30)
STATOBS.O30.MEMORY,STATOBS(64*5270:64:C)      # Extended MEMORY num O30
# O31
STATOBS.O31.K01,STATOBS(64*5271:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K02,STATOBS(64*5272:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K03,STATOBS(64*5273:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K04,STATOBS(64*5274:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K05,STATOBS(64*5275:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K06,STATOBS(64*5276:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K07,STATOBS(64*5277:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K08,STATOBS(64*5278:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K09,STATOBS(64*5279:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K10,STATOBS(64*5280:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K11,STATOBS(64*5281:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K12,STATOBS(64*5282:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K13,STATOBS(64*5283:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K14,STATOBS(64*5284:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K15,STATOBS(64*5285:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K16,STATOBS(64*5286:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K17,STATOBS(64*5287:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K18,STATOBS(64*5288:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K19,STATOBS(64*5289:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K20,STATOBS(64*5290:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K21,STATOBS(64*5291:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K22,STATOBS(64*5292:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K23,STATOBS(64*5293:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K24,STATOBS(64*5294:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K25,STATOBS(64*5295:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K26,STATOBS(64*5296:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K27,STATOBS(64*5297:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K28,STATOBS(64*5298:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K29,STATOBS(64*5299:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K30,STATOBS(64*5300:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K31,STATOBS(64*5301:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K32,STATOBS(64*5302:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K33,STATOBS(64*5303:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K34,STATOBS(64*5304:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K35,STATOBS(64*5305:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K36,STATOBS(64*5306:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K37,STATOBS(64*5307:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K38,STATOBS(64*5308:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K39,STATOBS(64*5309:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K40,STATOBS(64*5310:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K41,STATOBS(64*5311:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K42,STATOBS(64*5312:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K43,STATOBS(64*5313:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K44,STATOBS(64*5314:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K45,STATOBS(64*5315:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K46,STATOBS(64*5316:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K47,STATOBS(64*5317:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K48,STATOBS(64*5318:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K49,STATOBS(64*5319:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K50,STATOBS(64*5320:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K51,STATOBS(64*5321:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K52,STATOBS(64*5322:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K53,STATOBS(64*5323:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K54,STATOBS(64*5324:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K55,STATOBS(64*5325:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K56,STATOBS(64*5326:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K57,STATOBS(64*5327:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K58,STATOBS(64*5328:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K59,STATOBS(64*5329:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K60,STATOBS(64*5330:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K61,STATOBS(64*5331:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K62,STATOBS(64*5332:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K63,STATOBS(64*5333:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.K64,STATOBS(64*5334:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V01,STATOBS(64*5335:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V02,STATOBS(64*5336:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V03,STATOBS(64*5337:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V04,STATOBS(64*5338:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V05,STATOBS(64*5339:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V06,STATOBS(64*5340:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V07,STATOBS(64*5341:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V08,STATOBS(64*5342:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V09,STATOBS(64*5343:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V10,STATOBS(64*5344:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V11,STATOBS(64*5345:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V12,STATOBS(64*5346:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V13,STATOBS(64*5347:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V14,STATOBS(64*5348:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V15,STATOBS(64*5349:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V16,STATOBS(64*5350:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V17,STATOBS(64*5351:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V18,STATOBS(64*5352:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V19,STATOBS(64*5353:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V20,STATOBS(64*5354:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V21,STATOBS(64*5355:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V22,STATOBS(64*5356:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V23,STATOBS(64*5357:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V24,STATOBS(64*5358:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V25,STATOBS(64*5359:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V26,STATOBS(64*5360:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V27,STATOBS(64*5361:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V28,STATOBS(64*5362:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V29,STATOBS(64*5363:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V30,STATOBS(64*5364:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V31,STATOBS(64*5365:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V32,STATOBS(64*5366:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V33,STATOBS(64*5367:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V34,STATOBS(64*5368:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V35,STATOBS(64*5369:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V36,STATOBS(64*5370:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V37,STATOBS(64*5371:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V38,STATOBS(64*5372:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V39,STATOBS(64*5373:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V40,STATOBS(64*5374:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V41,STATOBS(64*5375:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V42,STATOBS(64*5376:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V43,STATOBS(64*5377:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V44,STATOBS(64*5378:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V45,STATOBS(64*5379:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V46,STATOBS(64*5380:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V47,STATOBS(64*5381:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V48,STATOBS(64*5382:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V49,STATOBS(64*5383:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V50,STATOBS(64*5384:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V51,STATOBS(64*5385:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V52,STATOBS(64*5386:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V53,STATOBS(64*5387:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V54,STATOBS(64*5388:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V55,STATOBS(64*5389:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V56,STATOBS(64*5390:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V57,STATOBS(64*5391:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V58,STATOBS(64*5392:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V59,STATOBS(64*5393:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V60,STATOBS(64*5394:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V61,STATOBS(64*5395:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V62,STATOBS(64*5396:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V63,STATOBS(64*5397:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.V64,STATOBS(64*5398:64:C)         # Extended MEMORY data (O31)
STATOBS.O31.MEMORY,STATOBS(64*5399:64:C)      # Extended MEMORY num O31
# O32
STATOBS.O32.K01,STATOBS(64*5400:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K02,STATOBS(64*5401:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K03,STATOBS(64*5402:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K04,STATOBS(64*5403:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K05,STATOBS(64*5404:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K06,STATOBS(64*5405:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K07,STATOBS(64*5406:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K08,STATOBS(64*5407:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K09,STATOBS(64*5408:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K10,STATOBS(64*5409:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K11,STATOBS(64*5410:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K12,STATOBS(64*5411:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K13,STATOBS(64*5412:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K14,STATOBS(64*5413:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K15,STATOBS(64*5414:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K16,STATOBS(64*5415:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K17,STATOBS(64*5416:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K18,STATOBS(64*5417:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K19,STATOBS(64*5418:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K20,STATOBS(64*5419:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K21,STATOBS(64*5420:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K22,STATOBS(64*5421:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K23,STATOBS(64*5422:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K24,STATOBS(64*5423:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K25,STATOBS(64*5424:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K26,STATOBS(64*5425:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K27,STATOBS(64*5426:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K28,STATOBS(64*5427:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K29,STATOBS(64*5428:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K30,STATOBS(64*5429:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K31,STATOBS(64*5430:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K32,STATOBS(64*5431:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K33,STATOBS(64*5432:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K34,STATOBS(64*5433:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K35,STATOBS(64*5434:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K36,STATOBS(64*5435:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K37,STATOBS(64*5436:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K38,STATOBS(64*5437:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K39,STATOBS(64*5438:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K40,STATOBS(64*5439:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K41,STATOBS(64*5440:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K42,STATOBS(64*5441:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K43,STATOBS(64*5442:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K44,STATOBS(64*5443:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K45,STATOBS(64*5444:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K46,STATOBS(64*5445:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K47,STATOBS(64*5446:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K48,STATOBS(64*5447:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K49,STATOBS(64*5448:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K50,STATOBS(64*5449:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K51,STATOBS(64*5450:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K52,STATOBS(64*5451:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K53,STATOBS(64*5452:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K54,STATOBS(64*5453:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K55,STATOBS(64*5454:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K56,STATOBS(64*5455:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K57,STATOBS(64*5456:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K58,STATOBS(64*5457:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K59,STATOBS(64*5458:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K60,STATOBS(64*5459:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K61,STATOBS(64*5460:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K62,STATOBS(64*5461:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K63,STATOBS(64*5462:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.K64,STATOBS(64*5463:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V01,STATOBS(64*5464:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V02,STATOBS(64*5465:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V03,STATOBS(64*5466:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V04,STATOBS(64*5467:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V05,STATOBS(64*5468:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V06,STATOBS(64*5469:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V07,STATOBS(64*5470:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V08,STATOBS(64*5471:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V09,STATOBS(64*5472:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V10,STATOBS(64*5473:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V11,STATOBS(64*5474:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V12,STATOBS(64*5475:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V13,STATOBS(64*5476:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V14,STATOBS(64*5477:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V15,STATOBS(64*5478:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V16,STATOBS(64*5479:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V17,STATOBS(64*5480:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V18,STATOBS(64*5481:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V19,STATOBS(64*5482:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V20,STATOBS(64*5483:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V21,STATOBS(64*5484:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V22,STATOBS(64*5485:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V23,STATOBS(64*5486:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V24,STATOBS(64*5487:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V25,STATOBS(64*5488:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V26,STATOBS(64*5489:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V27,STATOBS(64*5490:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V28,STATOBS(64*5491:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V29,STATOBS(64*5492:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V30,STATOBS(64*5493:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V31,STATOBS(64*5494:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V32,STATOBS(64*5495:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V33,STATOBS(64*5496:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V34,STATOBS(64*5497:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V35,STATOBS(64*5498:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V36,STATOBS(64*5499:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V37,STATOBS(64*5500:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V38,STATOBS(64*5501:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V39,STATOBS(64*5502:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V40,STATOBS(64*5503:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V41,STATOBS(64*5504:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V42,STATOBS(64*5505:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V43,STATOBS(64*5506:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V44,STATOBS(64*5507:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V45,STATOBS(64*5508:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V46,STATOBS(64*5509:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V47,STATOBS(64*5510:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V48,STATOBS(64*5511:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V49,STATOBS(64*5512:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V50,STATOBS(64*5513:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V51,STATOBS(64*5514:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V52,STATOBS(64*5515:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V53,STATOBS(64*5516:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V54,STATOBS(64*5517:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V55,STATOBS(64*5518:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V56,STATOBS(64*5519:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V57,STATOBS(64*5520:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V58,STATOBS(64*5521:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V59,STATOBS(64*5522:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V60,STATOBS(64*5523:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V61,STATOBS(64*5524:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V62,STATOBS(64*5525:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V63,STATOBS(64*5526:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.V64,STATOBS(64*5527:64:C)         # Extended MEMORY data (O32)
STATOBS.O32.MEMORY,STATOBS(64*5528:64:C)      # Extended MEMORY num O32
# CMN
STATOBS.CMN.K01,STATOBS(64*5529:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K02,STATOBS(64*5530:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K03,STATOBS(64*5531:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K04,STATOBS(64*5532:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K05,STATOBS(64*5533:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K06,STATOBS(64*5534:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K07,STATOBS(64*5535:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K08,STATOBS(64*5536:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K09,STATOBS(64*5537:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K10,STATOBS(64*5538:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K11,STATOBS(64*5539:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K12,STATOBS(64*5540:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K13,STATOBS(64*5541:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K14,STATOBS(64*5542:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K15,STATOBS(64*5543:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K16,STATOBS(64*5544:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K17,STATOBS(64*5545:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K18,STATOBS(64*5546:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K19,STATOBS(64*5547:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K20,STATOBS(64*5548:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K21,STATOBS(64*5549:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K22,STATOBS(64*5550:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K23,STATOBS(64*5551:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K24,STATOBS(64*5552:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K25,STATOBS(64*5553:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K26,STATOBS(64*5554:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K27,STATOBS(64*5555:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K28,STATOBS(64*5556:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K29,STATOBS(64*5557:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K30,STATOBS(64*5558:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K31,STATOBS(64*5559:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K32,STATOBS(64*5560:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K33,STATOBS(64*5561:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K34,STATOBS(64*5562:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K35,STATOBS(64*5563:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K36,STATOBS(64*5564:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K37,STATOBS(64*5565:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K38,STATOBS(64*5566:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K39,STATOBS(64*5567:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K40,STATOBS(64*5568:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K41,STATOBS(64*5569:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K42,STATOBS(64*5570:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K43,STATOBS(64*5571:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K44,STATOBS(64*5572:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K45,STATOBS(64*5573:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K46,STATOBS(64*5574:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K47,STATOBS(64*5575:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K48,STATOBS(64*5576:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K49,STATOBS(64*5577:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K50,STATOBS(64*5578:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K51,STATOBS(64*5579:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K52,STATOBS(64*5580:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K53,STATOBS(64*5581:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K54,STATOBS(64*5582:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K55,STATOBS(64*5583:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K56,STATOBS(64*5584:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K57,STATOBS(64*5585:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K58,STATOBS(64*5586:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K59,STATOBS(64*5587:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K60,STATOBS(64*5588:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K61,STATOBS(64*5589:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K62,STATOBS(64*5590:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K63,STATOBS(64*5591:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.K64,STATOBS(64*5592:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V01,STATOBS(64*5593:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V02,STATOBS(64*5594:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V03,STATOBS(64*5595:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V04,STATOBS(64*5596:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V05,STATOBS(64*5597:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V06,STATOBS(64*5598:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V07,STATOBS(64*5599:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V08,STATOBS(64*5600:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V09,STATOBS(64*5601:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V10,STATOBS(64*5602:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V11,STATOBS(64*5603:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V12,STATOBS(64*5604:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V13,STATOBS(64*5605:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V14,STATOBS(64*5606:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V15,STATOBS(64*5607:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V16,STATOBS(64*5608:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V17,STATOBS(64*5609:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V18,STATOBS(64*5610:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V19,STATOBS(64*5611:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V20,STATOBS(64*5612:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V21,STATOBS(64*5613:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V22,STATOBS(64*5614:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V23,STATOBS(64*5615:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V24,STATOBS(64*5616:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V25,STATOBS(64*5617:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V26,STATOBS(64*5618:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V27,STATOBS(64*5619:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V28,STATOBS(64*5620:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V29,STATOBS(64*5621:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V30,STATOBS(64*5622:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V31,STATOBS(64*5623:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V32,STATOBS(64*5624:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V33,STATOBS(64*5625:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V34,STATOBS(64*5626:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V35,STATOBS(64*5627:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V36,STATOBS(64*5628:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V37,STATOBS(64*5629:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V38,STATOBS(64*5630:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V39,STATOBS(64*5631:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V40,STATOBS(64*5632:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V41,STATOBS(64*5633:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V42,STATOBS(64*5634:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V43,STATOBS(64*5635:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V44,STATOBS(64*5636:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V45,STATOBS(64*5637:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V46,STATOBS(64*5638:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V47,STATOBS(64*5639:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V48,STATOBS(64*5640:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V49,STATOBS(64*5641:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V50,STATOBS(64*5642:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V51,STATOBS(64*5643:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V52,STATOBS(64*5644:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V53,STATOBS(64*5645:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V54,STATOBS(64*5646:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V55,STATOBS(64*5647:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V56,STATOBS(64*5648:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V57,STATOBS(64*5649:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V58,STATOBS(64*5650:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V59,STATOBS(64*5651:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V60,STATOBS(64*5652:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V61,STATOBS(64*5653:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V62,STATOBS(64*5654:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V63,STATOBS(64*5655:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.V64,STATOBS(64*5656:64:C)         # Extended MEMORY data (CMN)
STATOBS.CMN.MEMORY,STATOBS(64*5657:64:C)      # Extended MEMORY num CMN

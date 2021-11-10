#! /bin/sh
#
# ＴＳＣ状変オフセット定義ファイルの作成シェル
# $OSS_SYSTEM/StatusTSCV.def make shell
#
# ＴＳＣ状変オフセット定義ファイルを作成する。
# オフセットに変更がある場合は、本シェルを変更して実行する。
# ＄ＯＳＳ＿ＳＹＳＴＥＭにある以下のｍａｋｅｆｉｌｅで作成する。
# >> cd $OSS_SYSTEM
# >> make -f StatusTSCV.mk
#
# [argments]
#    arg1 : filename ($OSS_SYSTEM/StatusTSCV.def)
#
#  Update : 1999.11.22 chenge TSCV offset.
#  Update : 2000.12.13 Add LogAlias.pro. no chenge TSCV offset.
#
#
LANG=C ; export LANG ;
ORG=$IFS
CR='
'

case $# in
1 )
    ARGFILE=$1
	;;
* )
    echo "usage : $0 filename(\$OSS_SYSTEM/StatusTSCV.def)"
    exit 2
    ;;
esac

case `hostname` in
$OSS_HOSTMASTER )
    ;;
* )
    echo "$0 : my running host is $OSS_HOSTMASTER "
    ;;
esac


#####################################################
# StatusTSCV.def file make
#####################################################
echo ""
echo "StatusTSCV.def file make...."

mv ${ARGFILE} ${ARGFILE}.bak 2>/dev/null

printf "#    create date    : `date` \n" > ${ARGFILE}

printf "#    create program : OSST_StatusTSCV.sh \n" >> ${ARGFILE}

printf "#\n" >> ${ARGFILE}
printf "# TSCS status offset define table\n" >> ${ARGFILE}
printf "#\n" >> ${ARGFILE}
printf "#\n" >> ${ARGFILE}
printf "#table_code         length    offset    comment                <CR>\n" >> ${ARGFILE}
printf "#---+----1----+----2----+----3----+----4----+----5----+----6---<CR>\n" >> ${ARGFILE}
printf "TSCV00A1            %05d     001000    TSC\n"           `echo 1557+19|bc` >> ${ARGFILE}
printf "TSCV00B1            %05d     003000    MLP1\n"          `echo  159+19|bc` >> ${ARGFILE}
printf "TSCV0001            %05d     004000    DRDR\n"          `echo   49+19|bc` >> ${ARGFILE}
printf "TSCV0002            %05d     005000    MTDR\n"          `echo  240+19|bc` >> ${ARGFILE}
printf "TSCV0004            %05d     006000    FRAD\n"          `echo   42+19|bc` >> ${ARGFILE}
printf "TSCV0006            %05d     007000    AG\n"            `echo  120+19|bc` >> ${ARGFILE}
printf "TSCV0007            %05d     008000    SV\n"            `echo  162+19|bc` >> ${ARGFILE}
printf "TSCV0030            %05d     009000    THRM\n"          `echo   78+19|bc` >> ${ARGFILE}
printf "TSCV000D            %05d     010000    FPCI\n"          `echo   30+19|bc` >> ${ARGFILE}
printf "TSCV0027            %05d     011000    BLCU\n"          `echo   54+19|bc` >> ${ARGFILE}
printf "TSCV0008            %05d     012000    AO\n"            `echo   10+19|bc` >> ${ARGFILE}
printf "TSCV0051            %05d     013000    OBE\n"           `echo   10+19|bc` >> ${ARGFILE}
printf "TSCV002E            %05d     014000    CLOCK\n"         `echo    1+19|bc` >> ${ARGFILE}
printf "TSCV00B2            %05d     015000    MLP2\n"          `echo 1100+19|bc` >> ${ARGFILE}
printf "TSCV0009            %05d     017000    SH\n"            `echo  100+19|bc` >> ${ARGFILE}
printf "TSCV0003            %05d     018000    SMCU\n"          `echo   96+19|bc` >> ${ARGFILE}
printf "TSCV00B3            %05d     019000    MLP3\n"          `echo   74+19|bc` >> ${ARGFILE}
printf "TSCV0024            %05d     020000    CVCU\n"          `echo   96+19|bc` >> ${ARGFILE}
printf "TSCV0025            %05d     021000    TMCU\n"          `echo   36+19|bc` >> ${ARGFILE}
printf "TSCV002A            %05d     022000    DOME TEMP\n"     `echo  160+19|bc` >> ${ARGFILE}
printf "TSCV002B            %05d     023000    DOME CT2\n"      `echo   64+19|bc` >> ${ARGFILE}
printf "TSCV002C            %05d     024000    TLSCP TEMP\n"    `echo  180+19|bc` >> ${ARGFILE}
printf "TSCV002D            %05d     025000    TLSCP CT2\n"     `echo   44+19|bc` >> ${ARGFILE}
printf "TSCV0029            %05d     026000    HSBC\n"          `echo    6+19|bc` >> ${ARGFILE}
printf "TSCV000E            %05d     027000    CAL\n"           `echo   76+19|bc` >> ${ARGFILE}
printf "TSCV000A            %05d     028000    MIRROR HT EXE\n" `echo   11+19|bc` >> ${ARGFILE}
printf "TSCV0031            %05d     029000    HT EXE\n"        `echo   10+19|bc` >> ${ARGFILE}
printf "TSCV000B            %05d     030000    MCP1\n"          `echo   50+19|bc` >> ${ARGFILE}
printf "TSCV0010            %05d     032000    MCP2\n"          `echo   33+19|bc` >> ${ARGFILE}
printf "TSCV0032            %05d     033000    BOLT\n"          `echo   33+19|bc` >> ${ARGFILE}
printf "TSCV0033            %05d     034000    SPU4\n"          `echo   53+19|bc` >> ${ARGFILE}
printf "TSCV0034            %05d     035000    SPU5\n"          `echo   23+19|bc` >> ${ARGFILE}
printf "TSCV0035            %05d     036000    SPU6\n"          `echo   22+19|bc` >> ${ARGFILE}
printf "TSCV0028            %05d     037000    TTCU\n"          `echo   53+19|bc` >> ${ARGFILE}
printf "TSCV0036            %05d     038000    FRAD(PF)\n"      `echo   40+19|bc` >> ${ARGFILE}
printf "TSCV0037            %05d     039000    ASCU(PF)\n"      `echo   31+19|bc` >> ${ARGFILE}
printf "TSCV0061            %05d     040000    DOME FLAT\n"     `echo   27+19|bc` >> ${ARGFILE}
printf "TSCV0040            %05d     041000    SH TEST\n"       `echo 1000+19|bc` >> ${ARGFILE}
printf "TSCV003A            %05d     043000    CIAX\n"          `echo   68+19|bc` >> ${ARGFILE}
printf "TSCV0038            %05d     044000    HEAT EXH\n"      `echo    9+19|bc` >> ${ARGFILE}
printf "TSCV0039            %05d     045000    RED EXH\n"       `echo   25+19|bc` >> ${ARGFILE}
printf "TSCV003B            %05d     046000    OBCP(FMOS)\n"    `echo  192+19|bc` >> ${ARGFILE}
printf "TSCV003C            %05d     047000    HYDRST EXH\n"    `echo   35+19|bc` >> ${ARGFILE}

printf "#\n" >> ${ARGFILE}

LIST1="1 2 3 4 5 6 7 8"
LIST2="01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64"

for AA1 in $LIST1
do
    for AA2 in $LIST2
    do
        AAA="0${AA1}${AA2}"
        BBBBB="1${AA1}${AA2}00"
        case "$AAA" in
        08[6-6][1-3] ) printf "TSCV$AAA            %05d     $BBBBB    PMA/PMFXS\n" `echo    4+19|bc` >> ${ARGFILE} ;;
        0860         ) printf "TSCV$AAA            %05d     $BBBBB    PMFXS-3\n"   `echo    2+19|bc` >> ${ARGFILE} ;;
        0859         ) printf "TSCV$AAA            %05d     $BBBBB    PMFXS-2\n"   `echo    2+19|bc` >> ${ARGFILE} ;;
        0858         ) printf "TSCV$AAA            %05d     $BBBBB    PMFXS-1\n"   `echo    2+19|bc` >> ${ARGFILE} ;;
        08[5-5][0-1] ) printf "TSCV$AAA            %05d     $BBBBB    PMA/PMFXS\n" `echo    4+19|bc` >> ${ARGFILE} ;;
        08[0-4][0-9] ) printf "TSCV$AAA            %05d     $BBBBB    PMA/PMFXS\n" `echo    4+19|bc` >> ${ARGFILE} ;;
        07[4-4][0-8] ) printf "TSCV$AAA            %05d     $BBBBB    PMA/PMFXS\n" `echo    4+19|bc` >> ${ARGFILE} ;;
        07[0-3][0-9] ) printf "TSCV$AAA            %05d     $BBBBB    PMA/PMFXS\n" `echo    4+19|bc` >> ${ARGFILE} ;;
        06[4-4][0-2] ) printf "TSCV$AAA            %05d     $BBBBB    PMA/PMFXS\n" `echo    4+19|bc` >> ${ARGFILE} ;;
        06[0-3][0-9] ) printf "TSCV$AAA            %05d     $BBBBB    PMA/PMFXS\n" `echo    4+19|bc` >> ${ARGFILE} ;;
        05[3-3][0-6] ) printf "TSCV$AAA            %05d     $BBBBB    PMA/PMFXS\n" `echo    4+19|bc` >> ${ARGFILE} ;;
        05[0-2][0-9] ) printf "TSCV$AAA            %05d     $BBBBB    PMA/PMFXS\n" `echo    4+19|bc` >> ${ARGFILE} ;;
        04[3-3][0-0] ) printf "TSCV$AAA            %05d     $BBBBB    PMA/PMFXS\n" `echo    4+19|bc` >> ${ARGFILE} ;;
        04[0-2][0-9] ) printf "TSCV$AAA            %05d     $BBBBB    PMA/PMFXS\n" `echo    4+19|bc` >> ${ARGFILE} ;;
        03[2-2][0-4] ) printf "TSCV$AAA            %05d     $BBBBB    PMA/PMFXS\n" `echo    4+19|bc` >> ${ARGFILE} ;;
        03[0-1][0-9] ) printf "TSCV$AAA            %05d     $BBBBB    PMA/PMFXS\n" `echo    4+19|bc` >> ${ARGFILE} ;;
        02[1-1][0-8] ) printf "TSCV$AAA            %05d     $BBBBB    PMA/PMFXS\n" `echo    4+19|bc` >> ${ARGFILE} ;;
        02[0-0][0-9] ) printf "TSCV$AAA            %05d     $BBBBB    PMA/PMFXS\n" `echo    4+19|bc` >> ${ARGFILE} ;;
        01[1-1][0-2] ) printf "TSCV$AAA            %05d     $BBBBB    PMA/PMFXS\n" `echo    4+19|bc` >> ${ARGFILE} ;;
        01[0-0][0-9] ) printf "TSCV$AAA            %05d     $BBBBB    PMA/PMFXS\n" `echo    4+19|bc` >> ${ARGFILE} ;;
        esac
    done
done

echo "create file : ${ARGFILE}"
echo "old file    : ${ARGFILE}.bak"

#####################################################
# StatusAlias.pro LogAlias.pro file make
#####################################################
for PROFILE in StatusAlias.pro StatusDefaultAlias.pro StatusUserAlias.pro LogAlias.pro
do
    echo ""
    echo "$PROFILE file make...."

    TMPFILE=/tmp/OSST_StatusTSCV.tmp

    grep -v "@TSCV" $PROFILE > $TMPFILE

    echo "# @TSCV `date`" >> $TMPFILE
    echo "#-@TSCV--1----+----2----+----3----+----4----+----5----+----6" >> $TMPFILE
    echo "# @TSCV : Offset Define for TSCVxxxx" >> $TMPFILE

    IFS=$CR
    for LIST in `grep "^TSCV" StatusTSCV.def`
    do
        ACODE=`echo $LIST | nawk '{ print $1 }'`
        AOFF=`echo $LIST | nawk '{ print $3 }'`
    	printf "@%8s                     %s+19-1\n" $ACODE $AOFF >> $TMPFILE
    done
    IFS=$ORG

    mv $PROFILE $PROFILE.bak
    mv $TMPFILE $PROFILE

    echo "create file : $PROFILE"
    echo "old file    : $PROFILE.bak"
    echo ""
done

exit 0

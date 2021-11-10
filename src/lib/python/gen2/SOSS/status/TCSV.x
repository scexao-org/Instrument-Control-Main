/*C
C Function-Name
J  TCSV.x : ＴＳＣ状変監視データインタフェース定義ファイル
E  TCSV.x : TCS stat supervision data interface define file
C
C  NOTE:  all "TSC" names have been replaced with "TCS" names.  Other than
C         that and this comment, the file is identical to the SOSS 
C         TSCV.x file.
C
C Abstract
J  ＯＢＳがＴＳＣから受信する状変監視データのＲＰＣに
J  おけるプロトコルインタフェースを定義する．
C
C Attention
J  内容の詳細については，ＪＮＬＴ望遠鏡制御用計算機
J  システム仕様書（インタフェース編）を参照のこと．
C
C Note
C All Rights Reserved, Copyright (C) Fujitsu Limited 1996
C*/

/*------------------------------*/
/* 状変監視データ受信領域定義 */
/*------------------------------*/
typedef opaque  FM_NetForm< >;

/* プログラム定義 */
program  STAT_TRANSMIT_PROG {
    version  STAT_TRANSMIT_VERS {
        bool  STAT_TRANSMIT ( FM_NetForm ) = 1;
    } = 1;
} = 0x99999999;


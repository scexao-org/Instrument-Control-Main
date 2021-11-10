/*C
C Function-Name
J  TCSL.x : ＴＳＣ長周期監視データインタフェース定義ファイル
E  TCSL.x : TCS long supervision data interface define file
C
C  NOTE:  all "TSC" names have been replaced with "TCS" names.  Other than
C         that and this comment, the file is identical to the SOSS 
C         TSCL.x file.
C
C Abstract
J  ＯＢＳがＴＳＣから受信する長周期監視データのＲＰＣに
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
/* 長周期監視データ受信領域定義 */
/*------------------------------*/

/* 配列サイズ値 */
const  default_size = 1292;

/* データ格納領域 */
struct broadcastForm {
    opaque  contents[ default_size ];
};

program LONG_TRANSMIT_PROG {
    version LONG_TRANSMIT_VERS {
        void LONG_TRANSMIT ( broadcastForm ) = 1;
    } = 1;
} = 0x99999999;

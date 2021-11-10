/* C
C  Function-Name
J  OSSS_ClntTSC.x : ＴＳＣ制御インタフェース定義ファイル
E  OSSS_ClntTSC.x : TSC control interface define fail
C
C  Abstract
J  ＯＢＳからＴＳＣに送信する制御要求メッセージのＲＰＣにおける
J  プロトコルインタフェースを定義する．
C
C  Attention
J  内容の詳細については，ＪＮＬＴ望遠鏡制御用計算機システム仕様書
J （インタフェース編）を参照のこと．
C
C  Note
C  All Rights Reserved, Copyright (C) Fujitsu Limited 1996
C */

/* ＴＳＣ送信データ領域定義 */
typedef opaque  FM_NetForm<>;

/* プログラム定義 */
program TOWARD_TSC_PROG {
	version TOWARD_TSC_VERS {
		bool TOWARD_TSC ( FM_NetForm ) = 1;
	} = 1;
} = 0x20000011;

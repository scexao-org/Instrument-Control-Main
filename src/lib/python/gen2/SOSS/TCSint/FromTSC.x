/* C
C  Function-Name
J  OSSS_SvcTSC.x : ＴＳＣ応答メッセージインタフェース定義ファイル
E  OSSS_SvcTSC.x : TSC reply message interface define fail
C
C  Abstract
J  ＯＢＳがＴＳＣから受信する受付応答，終了応答，途中経過通知，
J  予告通知，開始通知，メッセージ通知の各メッセージのＲＰＣにおける
J  プロトコルイタフェースを定義する．
C
C  Attention
J  内容の詳細については，ＪＮＬＴ望遠鏡制御用計算機システム仕様書
J （インタフェース編）を参照のこと．
C
C  Note
C  All Rights Reserved, Copyright (C) Fujitsu Limited 1996
C */

/* ＴＳＣ受信メッセージデータ領域定義 */
typedef opaque  FM_NetForm<>;

/* プログラム定義 */
program FROM_TSC_PROG {
	version FROM_TSC_VERS {
		bool FROM_TSC ( FM_NetForm ) = 1;
	} = 1;
} = 0x20000012;

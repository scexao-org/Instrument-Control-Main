/*C
C Function-Name
J  OSSC_ComCD.x : コミュニケーションマネージャＲＰＣ定義
E  OSSC_ComCD.x : communication manager RPC define.
C
C Abstract
J  コミュニケーションマネージャのコマンドのＲＰＣインタフェース
J  を定義する．
C
C Attention
C  none
C
C Note
C All Rights Reserved, Copyright (C) Fujitsu Limited 1996
C*/

typedef opaque  ComCDarg<>;

program OSSC_COMCD {
    version OSSC_COMCD_VERS {
        bool COMCD ( ComCDarg ) = 1;
    } = 1;
} = 0x99999999;


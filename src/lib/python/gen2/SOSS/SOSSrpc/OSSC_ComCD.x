/*C
C Function-Name
J  OSSC_ComCD.x : ���ߥ�˥��������ޥ͡�����ңУ����
E  OSSC_ComCD.x : communication manager RPC define.
C
C Abstract
J  ���ߥ�˥��������ޥ͡�����Υ��ޥ�ɤΣңУå��󥿥ե�����
J  ��������롥
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


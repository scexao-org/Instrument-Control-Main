/* C
C  Function-Name
J  OSSS_ClntTSC.x : �ԣӣ����楤�󥿥ե���������ե�����
E  OSSS_ClntTSC.x : TSC control interface define fail
C
C  Abstract
J  �ϣ£Ӥ���ԣӣä��������������׵��å������ΣңУäˤ�����
J  �ץ�ȥ��륤�󥿥ե�������������롥
C
C  Attention
J  ���Ƥξܺ٤ˤĤ��Ƥϡ��ʣΣ̣�˾��������ѷ׻��������ƥ���ͽ�
J �ʥ��󥿥ե������ԡˤ򻲾ȤΤ��ȡ�
C
C  Note
C  All Rights Reserved, Copyright (C) Fujitsu Limited 1996
C */

/* �ԣӣ������ǡ����ΰ���� */
typedef opaque  FM_NetForm<>;

/* �ץ������� */
program TOWARD_TSC_PROG {
	version TOWARD_TSC_VERS {
		bool TOWARD_TSC ( FM_NetForm ) = 1;
	} = 1;
} = 0x20000011;

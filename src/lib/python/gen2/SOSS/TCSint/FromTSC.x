/* C
C  Function-Name
J  OSSS_SvcTSC.x : �ԣӣñ�����å��������󥿥ե���������ե�����
E  OSSS_SvcTSC.x : TSC reply message interface define fail
C
C  Abstract
J  �ϣ£Ӥ��ԣӣä������������ձ�������λ����������в����Ρ�
J  ͽ�����Ρ��������Ρ���å��������Τγƥ�å������ΣңУäˤ�����
J  �ץ�ȥ��륤���ե�������������롥
C
C  Attention
J  ���Ƥξܺ٤ˤĤ��Ƥϡ��ʣΣ̣�˾��������ѷ׻��������ƥ���ͽ�
J �ʥ��󥿥ե������ԡˤ򻲾ȤΤ��ȡ�
C
C  Note
C  All Rights Reserved, Copyright (C) Fujitsu Limited 1996
C */

/* �ԣӣü�����å������ǡ����ΰ���� */
typedef opaque  FM_NetForm<>;

/* �ץ������� */
program FROM_TSC_PROG {
	version FROM_TSC_VERS {
		bool FROM_TSC ( FM_NetForm ) = 1;
	} = 1;
} = 0x20000012;

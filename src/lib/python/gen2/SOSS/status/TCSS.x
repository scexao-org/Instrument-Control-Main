/*C
C Function-Name
J  TCSS.x : �ԣӣ�û�����ƻ�ǡ������󥿥ե���������ե�����
E  TCSS.x : TCS short supervision data interface define file
C
C  NOTE:  all "TSC" names have been replaced with "TCS" names.  Other than
C         that and this comment, the file is identical to the SOSS 
C         TSCS.x file.
C
C Abstract
J  �ϣ£Ӥ��ԣӣä����������û�����ƻ�ǡ����ΣңУä�
J  ������ץ�ȥ��륤�󥿥ե�������������롥
C
C Attention
J  ���Ƥξܺ٤ˤĤ��Ƥϡ��ʣΣ̣�˾��������ѷ׻���
J  �����ƥ���ͽ�ʥ��󥿥ե������ԡˤ򻲾ȤΤ��ȡ�
C
C Note
C All Rights Reserved, Copyright (C) Fujitsu Limited 1996
C*/

/*------------------------------*/
/* û�����ƻ�ǡ��������ΰ���� */
/*------------------------------*/

/* ���󥵥����� */
const  default_size = 1292;

/* �ǡ�����Ǽ�ΰ� */
struct broadcastForm {
    opaque  contents[ default_size ];
};

/* �ץ������� */
program SHORT_TRANSMIT_PROG {
    version SHORT_TRANSMIT_VERS {
        void SHORT_TRANSMIT ( broadcastForm ) = 1;
    } = 1;
} = 0x99999999;

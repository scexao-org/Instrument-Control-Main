/*C
C Function-Name
J  TCSL.x : �ԣӣ�Ĺ�����ƻ�ǡ������󥿥ե���������ե�����
E  TCSL.x : TCS long supervision data interface define file
C
C  NOTE:  all "TSC" names have been replaced with "TCS" names.  Other than
C         that and this comment, the file is identical to the SOSS 
C         TSCL.x file.
C
C Abstract
J  �ϣ£Ӥ��ԣӣä����������Ĺ�����ƻ�ǡ����ΣңУä�
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
/* Ĺ�����ƻ�ǡ��������ΰ���� */
/*------------------------------*/

/* ���󥵥����� */
const  default_size = 1292;

/* �ǡ�����Ǽ�ΰ� */
struct broadcastForm {
    opaque  contents[ default_size ];
};

program LONG_TRANSMIT_PROG {
    version LONG_TRANSMIT_VERS {
        void LONG_TRANSMIT ( broadcastForm ) = 1;
    } = 1;
} = 0x99999999;

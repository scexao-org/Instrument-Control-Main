/*C
C Function-Name
J  TCSV.x : �ԣӣþ��Ѵƻ�ǡ������󥿥ե���������ե�����
E  TCSV.x : TCS stat supervision data interface define file
C
C  NOTE:  all "TSC" names have been replaced with "TCS" names.  Other than
C         that and this comment, the file is identical to the SOSS 
C         TSCV.x file.
C
C Abstract
J  �ϣ£Ӥ��ԣӣä������������Ѵƻ�ǡ����ΣңУä�
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
/* ���Ѵƻ�ǡ��������ΰ���� */
/*------------------------------*/
typedef opaque  FM_NetForm< >;

/* �ץ������� */
program  STAT_TRANSMIT_PROG {
    version  STAT_TRANSMIT_VERS {
        bool  STAT_TRANSMIT ( FM_NetForm ) = 1;
    } = 1;
} = 0x99999999;


/****************************************************************/
/* System         :  JNLT�ѥ����ȥ��������������(AG PROC)      */
/* File name      :  ag_vgw.x					*/
/* Function       :  AGPROC-VGW �֤�RPC���ݎ����̎���������̎�����         */
/* Creation       :  1997.05.12                                 */
/* Version        :  $Revision$                                 */
/* Note           :  AGPROC����VGW�ؤν����ѡ�			*/
/*     ���Ƥξܺ٤�"V-LAN���󥿡��ե��������ͽ�"�򻲾ȤΤ���	*/
/* !!                                                           */
/* Revision       :   Ver 1.0 1997.05.12  �޸�                  */
/*                                                              */
/*  COPYRIGHT (c) 1997 MITSUBISHI ELECTRIC CORPORATION          */
/*                ALL RIGHT RESERVED                            */
/****************************************************************/
  
/* ��å��������ܥե����ޥå� */

struct tgVform{
        char    head[60];
	long    tv_sec;
	long    tv_usec;
        unsigned short  data<>;
};


/*   VGW�ؽ��Ϥ��빻���ǡ��� �ץ�������    */
program AGPROC_VGW_PROG {
  version AGPROC_VGW_VERS {
     void AGPROC_VGW_CMD( tgVform ) = 1;
	} = 1;
} = 0x20000021;

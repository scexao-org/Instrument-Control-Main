
/*C-------------------------------------------------------------------
C
C RPCL-Name
J	DAQobcSndStartRcv.x : ��ϼ�ǡ���ž������RPCL�ե�����
E	DAQobcSndStartRcv.x : RPCL file
C
C Abstract
J	OBC���黳ϼ�ؤλ�ϼ�ǡ���ž�����Ϥˤ�����RPC�ץ�ȥ���
J	���󥿥ե�������������롣
C
E Attention
J	�ʤ���
C
C Note
J	�ʤ���
C
-------------------------------------------------------------------C*/

/* �ۥ��ȼ������ */
const HOST_NO = 1;
const SET_PROG_NUM = 0x00000100;

/* ���ޥ�������ΰ���� */
typedef opaque DAQobcRpc< >;

/* �ץ������� */
program DAQOBC_SND_RPC_START_PROG {

	version DAQOBC_SND_RPC_START_VERS {

		bool DAQOBC_SND_RPC_START( DAQobcRpc ) = 1;

    } = 1;

} = 0x22000101;


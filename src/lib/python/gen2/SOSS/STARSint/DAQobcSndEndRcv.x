
/*C-------------------------------------------------------------------
C
C RPCL-Name
J	DAQobcSndEndRcv.x : ��ϼ�ǡ���ž����λRPCL�ե�����
E	DAQobcSndEndRcv.x : RPCL file
C
C Abstract
J	��ϼ����OBC�ؤλ�ϼ�ǡ���ž����λ�ˤ�����RPC�ץ�ȥ���
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
program DAQOBC_SND_RPC_END_PROG {

	version DAQOBC_SND_RPC_END_VERS {

		bool DAQOBC_SND_RPC_END( DAQobcRpc ) = 1;

    } = 1;

} = 0x22000102;


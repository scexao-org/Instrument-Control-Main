
/*C-------------------------------------------------------------------
C
C RPCL-Name
J	DAQobcSndEndRcv.x : 山麓データ転送完了RPCLファイル
E	DAQobcSndEndRcv.x : RPCL file
C
C Abstract
J	山麓からOBCへの山麓データ転送完了におけるRPCプロトコル
J	インタフェースを定義する。
C
E Attention
J	なし．
C
C Note
J	なし．
C
-------------------------------------------------------------------C*/

/* ホスト種別定義 */
const HOST_NO = 1;
const SET_PROG_NUM = 0x00000100;

/* コマンド送信領域定義 */
typedef opaque DAQobcRpc< >;

/* プログラム定義 */
program DAQOBC_SND_RPC_END_PROG {

	version DAQOBC_SND_RPC_END_VERS {

		bool DAQOBC_SND_RPC_END( DAQobcRpc ) = 1;

    } = 1;

} = 0x22000102;


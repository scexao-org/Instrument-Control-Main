
/*C-------------------------------------------------------------------
C
C RPCL-Name
J	DAQobcSndStartRcv.x : 山麓データ転送開始RPCLファイル
E	DAQobcSndStartRcv.x : RPCL file
C
C Abstract
J	OBCから山麓への山麓データ転送開始におけるRPCプロトコル
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
program DAQOBC_SND_RPC_START_PROG {

	version DAQOBC_SND_RPC_START_VERS {

		bool DAQOBC_SND_RPC_START( DAQobcRpc ) = 1;

    } = 1;

} = 0x22000101;


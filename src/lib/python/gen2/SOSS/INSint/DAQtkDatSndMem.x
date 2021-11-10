
/*C-------------------------------------------------------------------
C
C RPCL-Name
J	DAQtkDatSndMem.x : FITSファイル転送RPCLファイル
C
C Abstract
J	OBCPからOBCへのFITSファイル転送におけるRPCプロトコル
J	インタフェースを定義する。
C
E Attention
C
C Note
C
-------------------------------------------------------------------C*/

struct DAQtkRpcFits {
	char	cframe<16>;
	opaque	ph <>;
	opaque	pd <>;
	opaque	ah1 <>;
	opaque	ad1 <>;
	opaque	ah2 <>;
	opaque	ad2 <>;
	opaque	ah3 <>;
	opaque	ad3 <>;
};

program DAQTK_DAT_SND_MEM_PROG {

	version DAQTK_DAT_SND_MEM_VERS {

		bool DAQTK_DAT_SND_MEM( DAQtkRpcFits ) = 1;

    } = 1;

} = 0x21010951;


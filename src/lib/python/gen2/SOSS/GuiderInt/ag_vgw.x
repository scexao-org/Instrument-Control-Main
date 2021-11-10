/****************************************************************/
/* System         :  JNLT用オートガイダ信号処理部(AG PROC)      */
/* File name      :  ag_vgw.x					*/
/* Function       :  AGPROC-VGW 間のRPCｲﾝﾀｰﾌｪｰｽ定義ﾌｧｲﾙ         */
/* Creation       :  1997.05.12                                 */
/* Version        :  $Revision$                                 */
/* Note           :  AGPROCからVGWへの出力用。			*/
/*     内容の詳細は"V-LANインターフェース仕様書"を参照のこと	*/
/* !!                                                           */
/* Revision       :   Ver 1.0 1997.05.12  筑後                  */
/*                                                              */
/*  COPYRIGHT (c) 1997 MITSUBISHI ELECTRIC CORPORATION          */
/*                ALL RIGHT RESERVED                            */
/****************************************************************/
  
/* メッセージ基本フォーマット */

struct tgVform{
        char    head[60];
	long    tv_sec;
	long    tv_usec;
        unsigned short  data<>;
};


/*   VGWへ出力する校正データ プログラム定義    */
program AGPROC_VGW_PROG {
  version AGPROC_VGW_VERS {
     void AGPROC_VGW_CMD( tgVform ) = 1;
	} = 1;
} = 0x20000021;

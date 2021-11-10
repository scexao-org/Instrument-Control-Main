/*C
C Include-Name
C  OSSC_ScreenGet.x : Screen get function RCP define
C
C Abstract
C  Screen get function RPC define
C  
C Note
C  RPC program number  
C      0x21040034 (default)  
C      0x2104003n (environment define)
C               n:5 to f
C
C*/

struct ScreenGetArgs {
	string tabledef<>;      /* table define record */
	string start<>;         /* start byte number   */
	string size<>;          /* byte size           */
};

typedef opaque ScreenGetRet <>;

program OSSC_GETSCREEN {
    version OSSC_GETSCREEN_VERSION {
        ScreenGetRet GET_SCREEN( ScreenGetArgs ) = 1;
    } = 1;
} = 0x21040034;

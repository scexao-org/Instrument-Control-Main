/*C
C Include-Name
C  OSST_Frame.x : frame number server  function RPC define
C
c Abstract
C  frame number server  RPC define
C  
C Note
C  RPC program number  
C      0x21040033
C
C*/

struct GetFnoArgs {
    string unit<>;  /* unit : SUK,O16,OHS,etc */
    string type<>;  /* type : A or Q */
    string dno<>;   /* dispatcher number  : 0,1,2-6 */
    string num<>;   /* number */
};

program OSSS_Frame {
    version OSSS_FrameVersion {
        string OSSs_GET_FNO( GetFnoArgs ) = 1;
        string OSSs_SET_FNO( string     ) = 2;
    } = 1;
} = 0x21040033;


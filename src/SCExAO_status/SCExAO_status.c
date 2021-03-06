#include <string.h>
#include <malloc.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <sys/mman.h>
#include <fcntl.h> // for open
#include <unistd.h> // for close
#include <termios.h>
#include <ncurses.h>

#include "SCExAO_status.h"

#define SHAREDMEMDIR "/tmp"
int SM_fd;
char SM_fname[200];
SCEXAOSTATUS *SCExAO_status;
long cnt;
int wcol, wrow; // window size


int create_status_shm()
{
  
  int result;
  
  
  
  // CREATING SHARED MEMORY
  
  sprintf(SM_fname, "%s/SCExAO_status.shm", SHAREDMEMDIR);
  SM_fd = open(SM_fname, O_RDWR | O_CREAT | O_TRUNC, (mode_t)0600);
  
  if (SM_fd == -1) {
    perror("Error opening file for writing");
    exit(0);
  }
  
  result = lseek(SM_fd, sizeof(SCEXAOSTATUS)-1, SEEK_SET);
  if (result == -1) {
    close(SM_fd);
    perror("Error calling lseek() to 'stretch' the file");
    exit(0);
  }
  
  result = write(SM_fd, "", 1);
  if (result != 1) {
    close(SM_fd);
    perror("Error writing last byte of the file");
    exit(0);
  }
  
  SCExAO_status = (SCEXAOSTATUS*) mmap(0, sizeof(SCEXAOSTATUS), PROT_READ | PROT_WRITE, MAP_SHARED, SM_fd, 0);
  if (SCExAO_status == MAP_FAILED) {
    close(SM_fd);
    perror("Error mmapping the file");
    exit(0);
  }
  
  return 0;
}




int read_status_shm()
{
  
  SM_fd = open(SM_fname, O_RDWR);
  if(SM_fd==-1)
    {
      printf("Cannot import file - continuing\n");
    }
  else
    {
      SCExAO_status = (SCEXAOSTATUS*) mmap(0, sizeof(SCEXAOSTATUS), PROT_READ | PROT_WRITE, MAP_SHARED, SM_fd, 0);
      if (SCExAO_status == MAP_FAILED) {
	close(SM_fd);
	perror("Error mmapping the file");
	exit(0);
      }
    }
  return 0;
  
}


int kbdhit(void)
{
  struct termios oldt, newt;
  int ch;
  int oldf;
  
  tcgetattr(STDIN_FILENO, &oldt);
  newt = oldt;
  newt.c_lflag &= ~(ICANON | ECHO);
  tcsetattr(STDIN_FILENO, TCSANOW, &newt);
  oldf = fcntl(STDIN_FILENO, F_GETFL, 0);
  fcntl(STDIN_FILENO, F_SETFL, oldf | O_NONBLOCK);
  
  ch = getchar();
  
  tcsetattr(STDIN_FILENO, TCSANOW, &oldt);
  fcntl(STDIN_FILENO, F_SETFL, oldf);
  
  if(ch != EOF)
    {
      //     ungetc(ch, stdin);
      return 1;
    }
  
  return 0;
}

int print_header(char *str, char c)
{
  long n;
  long i;
  
  attron(A_BOLD);
  attron(COLOR_PAIR(6));
  n = strlen(str);
  for(i=0; i<(wcol-n)/2; i++)
    printw("%c",c);
  printw("%s", str);
  for(i=0; i<(wcol-n)/2-1; i++)
    printw("%c",c);
  printw("\n");
  attroff(COLOR_PAIR(6));
  attroff(A_BOLD);
  
  return(0);
}


int print_status(char *str, int co)
{
  
  attron(A_BOLD);
  attron(COLOR_PAIR(co+2));
  printw(" %-15s ", str);
  attroff(COLOR_PAIR(co+2));
  attroff(A_BOLD);
  
  return(0);
}


int print_status_f(float fnum, char *unitf, int co)
{
  
  attron(A_BOLD);
  attron(COLOR_PAIR(co+2));
  printw("%12.3f %3s ", fnum, unitf);
  attroff(COLOR_PAIR(co+2));
  attroff(A_BOLD);
  
  return(0);
}


int print_status_i(int inum, char *uniti, int co)
{
  
  attron(A_BOLD);
  attron(COLOR_PAIR(co+2));
  printw("%12d %3s ", inum, uniti);
  attroff(COLOR_PAIR(co+2));
  attroff(A_BOLD);
  
  return(0);
}


int status_display()
{
  initscr();
  getmaxyx(stdscr, wrow, wcol);
  
  // we define colors here
  start_color();
  init_pair(1, COLOR_BLACK, COLOR_WHITE);
  init_pair(2, COLOR_BLACK, COLOR_RED);
  init_pair(3, COLOR_BLACK, COLOR_GREEN);
  init_pair(4, COLOR_BLACK, COLOR_BLUE);
  init_pair(5, COLOR_BLACK, COLOR_CYAN);
  init_pair(6, COLOR_GREEN, COLOR_BLACK);
  
  while( !kbdhit() )
    {
      usleep(500000); // in us
      clear();
      
      print_header(" NETWORK POWER SWTICHES ", '-');
      // NPS1
      printw("NPS1 ports 1-4  : ");
      print_status("SCExAO4 POWER 2", SCExAO_status[0].nps1_1_co);
      printw(" | ");
      print_status("SCExAO2 POWER 1", SCExAO_status[0].nps1_2_co);
      printw(" | ");
      print_status("HIGH-VOLTAGE TT", SCExAO_status[0].nps1_3_co);
      printw(" | ");
      print_status("VAMPIRES CAMERA", SCExAO_status[0].nps1_4_co);
      printw("\n");
      printw("NPS1 ports 5-8  : ");
      print_status("  SOURCE BOX   ", SCExAO_status[0].nps1_5_co);
      printw(" | ");
      print_status("DM ELECTRONICS ", SCExAO_status[0].nps1_6_co);
      printw(" | ");
      print_status("GLINT DOVE PRSM", SCExAO_status[0].nps1_7_co);
      printw(" | ");
      print_status(" FIRST STAGES  ", SCExAO_status[0].nps1_8_co);
      printw("\n");
      // NPS2
      printw("NPS2 ports 1-4  : ");
      print_status("SCExAO4 POWER 1", SCExAO_status[0].nps2_1_co);
      printw(" | ");
      print_status("SCExAO2 POWER 2", SCExAO_status[0].nps2_2_co);
      printw(" | ");
      print_status(" SCExAO3 POWER ", SCExAO_status[0].nps2_3_co);
      printw(" | ");
      print_status("  OCAM POWER   ", SCExAO_status[0].nps2_4_co);
      printw("\n");
      printw("NPS2 ports 5-8  : ");
      print_status(" TT MODULATOR  ", SCExAO_status[0].nps2_5_co);
      printw(" | ");
      print_status("FIRST NEON SRC ", SCExAO_status[0].nps2_6_co);
      printw(" | ");
      print_status("DM VACUUM PUMP ", SCExAO_status[0].nps2_7_co);
      printw(" | ");
      printw("\n");
      // NPS3
      printw("NPS3 ports 1-4  : ");
      print_status(" SAPHIRA POWER ", SCExAO_status[0].nps3_1_co);
      printw(" | ");
      print_status(" VAMPIRES COMP ", SCExAO_status[0].nps3_2_co);
      printw(" | ");
      print_status("   24V POWER   ", SCExAO_status[0].nps3_3_co);
      printw(" | ");
      print_status("   15V POWER   ", SCExAO_status[0].nps3_4_co);
      printw("\n");
      printw("NPS3 ports 5-8  : ");
      print_status("  5/12V POWER  ", SCExAO_status[0].nps3_5_co);
      printw(" | ");
      print_status("C-RED2 CAMERAS ", SCExAO_status[0].nps3_6_co);
      printw(" | ");
      print_status("SAPHIRA TMP CTR", SCExAO_status[0].nps3_7_co);
      printw(" | ");
      print_status("SAPHIRA COOLER ", SCExAO_status[0].nps3_8_co);
      printw("\n");

      print_header(" CALIBRATION SOURCE ", '-');
      // Cal source
      printw("Cal source      : ");
      print_status(SCExAO_status[0].src_fib_st, SCExAO_status[0].src_fib_co);
      printw(" (x: %6.2f mm , y: %6.2f mm )\n", SCExAO_status[0].src_fib_x, SCExAO_status[0].src_fib_y);
      // Source type
      printw("Source type     : ");
      print_status(SCExAO_status[0].src_select_st, SCExAO_status[0].src_select_co);
      printw(" (w: %6.2f deg)\n", SCExAO_status[0].src_select);
      // Source IR ND
      printw("Source IR ND    : ");
      print_status(SCExAO_status[0].src_flux_irnd, -1);
      printw("\n");
      // Source Opt ND
      printw("Source Opt ND   : ");
      print_status(SCExAO_status[0].src_flux_optnd, -1);
      printw("\n");
      // Source Filter
      printw("Source Filter   : ");
      print_status(SCExAO_status[0].src_flux_filter, -1);
      printw("\n");
      // Integrating Sphere
      printw("Integ. Sphere   : ");
      print_status(SCExAO_status[0].intsphere, SCExAO_status[0].intsphere_co);
      printw("\n");
      // Compensating plate
      printw("Comp. plate     : ");
      print_status(SCExAO_status[0].compplate, SCExAO_status[0].compplate_co);
      printw("\n");

      print_header(" FRONT IR BENCH AND CORONAGRAPHS ", '-');
      // OAP1
      printw("OAP1            : ");
      print_status(SCExAO_status[0].oap1_st, SCExAO_status[0].oap1_co);
      printw(" (t: %6.2f deg, p: %6.2f deg, f: %6d stp)\n", SCExAO_status[0].oap1_theta, SCExAO_status[0].oap1_phi, SCExAO_status[0].oap1_f);
      // Dichroic
      printw("Dichroic        : ");
      print_status(SCExAO_status[0].dichroic_st, SCExAO_status[0].dichroic_co);
      printw(" (x: %6.2f mm )\n", SCExAO_status[0].dichroic);
      // Pupil Mask
      printw("Pupil Mask      : ");
      print_status(SCExAO_status[0].pupil_st, SCExAO_status[0].pupil_co);
      printw(" (w: %6.2f deg, x: %6d stp, y: %6d stp)\n", SCExAO_status[0].pupil_wheel, SCExAO_status[0].pupil_x, SCExAO_status[0].pupil_y);
      // PIAA1
      printw("PIAA1           : ");
      print_status(SCExAO_status[0].piaa1_st, SCExAO_status[0].piaa1_co);
      printw(" (w: %6.2f deg, x: %6d stp, y: %6d stp)\n", SCExAO_status[0].piaa1_wheel, SCExAO_status[0].piaa1_x, SCExAO_status[0].piaa1_y);
      // PIAA2
      printw("PIAA2           : ");
      print_status(SCExAO_status[0].piaa2_st, SCExAO_status[0].piaa2_co);
      printw(" (w: %6.2f deg, x: %6d stp, y: %6d stp, f: %6d stp)\n", SCExAO_status[0].piaa2_wheel, SCExAO_status[0].piaa2_x, SCExAO_status[0].piaa2_y, SCExAO_status[0].piaa2_f);
      // Focal Plane Mask
      printw("Focal Plane Mask: ");
      print_status(SCExAO_status[0].fpm_st, SCExAO_status[0].fpm_co);
      printw(" (w: %6.2f deg, x: %6d stp, y: %6d stp, f: %6d stp)\n", SCExAO_status[0].fpm_wheel, SCExAO_status[0].fpm_x, SCExAO_status[0].fpm_y, SCExAO_status[0].fpm_f);
      // Lyot Mask
      printw("Lyot Mask       : ");
      print_status(SCExAO_status[0].lyot_st, SCExAO_status[0].lyot_co);
      printw(" (w: %6.2f deg, x: %6d stp, y: %6d stp)\n", SCExAO_status[0].lyot_wheel, SCExAO_status[0].lyot_x, SCExAO_status[0].lyot_y);
      // Inverse PIAA
      printw("Inverse PIAA    : ");
      print_status(SCExAO_status[0].invpiaa_st, SCExAO_status[0].invpiaa_co);
      printw(" (x: %6.2f mm , y: %6.2f mm , t: %6d stp, p: %6d stp)\n", SCExAO_status[0].invpiaa_x, SCExAO_status[0].invpiaa_y, SCExAO_status[0].invpiaa_theta, SCExAO_status[0].invpiaa_phi);
      // OAP4
      printw("OAP4            : ");
      print_status(SCExAO_status[0].oap4_st, SCExAO_status[0].oap4_co);
      printw(" (t: %6.2f deg, p: %6.2f deg)\n", SCExAO_status[0].oap4_theta, SCExAO_status[0].oap4_phi);
      print_header(" BACK IR BENCH AND IRCAMS ", '-');
      
      // PG1 Pickoff
      printw("PG1 Pickoff     : ");
      print_status(SCExAO_status[0].PG1_pickoff, SCExAO_status[0].PG1_pickoff_co);
      printw("\n");
      // Field stop
      printw("Field Stop      : ");
      print_status(SCExAO_status[0].field_stop_st, SCExAO_status[0].field_stop_co);
      printw(" (x: %6.2f mm , y: %6.2f mm )\n", SCExAO_status[0].field_stop_x, SCExAO_status[0].field_stop_y);
      // Steering Mirror
      printw("Steering mirror : ");
      print_status(SCExAO_status[0].steering_st, SCExAO_status[0].steering_co);
      printw(" (t: %6.2f deg, p: %6.2f deg)\n", SCExAO_status[0].steering_theta, SCExAO_status[0].steering_phi);
      // CHARIS Pickoff
      printw("CHARIS Pickoff  : ");
      print_status(SCExAO_status[0].charis_pickoff_st, SCExAO_status[0].charis_pickoff_co);
      printw(" (w: %6.2f deg, t: %6.2f deg)\n", SCExAO_status[0].charis_pickoff_wheel, SCExAO_status[0].charis_pickoff_theta);
      // MKIDS Pickoff
      printw("MKIDS Pickoff   : ");
      print_status(SCExAO_status[0].mkids_pickoff_st, SCExAO_status[0].mkids_pickoff_co);
      printw(" (w: %6.2f deg, t: %6.2f deg)\n", SCExAO_status[0].mkids_pickoff_wheel, SCExAO_status[0].mkids_pickoff_theta);
      // IR Cams Pupil Masks
      printw("IR Cam Pup Mask : ");
      print_status(SCExAO_status[0].ircam_pupil_st, SCExAO_status[0].ircam_pupil_co);
      printw(" (x: %6.2f mm , y: %6.2f mm )\n", SCExAO_status[0].ircam_pupil_x, SCExAO_status[0].ircam_pupil_y);
      // IR Cams Filter
      printw("IR Cam Filter   : ");
      print_status(SCExAO_status[0].ircam_filter, SCExAO_status[0].ircam_filter_co);
      printw("\n");
      // IR Cams Block
      printw("IR Cams Block   : ");
      print_status(SCExAO_status[0].ircam_block, SCExAO_status[0].ircam_block_co);
      printw("\n");
      // IR Cams Focus
      printw("IR Cams Focus   : ");
      print_status(SCExAO_status[0].ircam_fcs_st, SCExAO_status[0].ircam_fcs_co);
      printw(" (f1:%6d stp, f2:%6.2f mm )\n", SCExAO_status[0].ircam_fcs_f1, SCExAO_status[0].ircam_fcs_f2);
      // SAPHIRA Pickoff
      printw("SAPHIRA Pickoff : ");
      print_status(SCExAO_status[0].saphira_pickoff_st, SCExAO_status[0].saphira_pickoff_co);
      printw(" (x: %6.2f mm )\n", SCExAO_status[0].saphira_pickoff);
      // CHUCKCAM Pupil
      printw("CHUCKCAM Pupil  : ");
      print_status(SCExAO_status[0].chuck_pup, SCExAO_status[0].chuck_pup_co);
      printw("\n");
      // CHUCKCAM Pupil Focus
      printw("CHUCKCAM Pup Fcs: ");
      print_status(SCExAO_status[0].chuck_pup_fcs_st, SCExAO_status[0].chuck_pup_fcs_co);
      printw(" (f: %6.2f mm )\n", SCExAO_status[0].chuck_pup_fcs);
      // SAPHIRA Pupil
      printw("SAPHIRA Pupil   : ");
      print_status(SCExAO_status[0].saphira_pup, SCExAO_status[0].saphira_pup_co);
      printw("\n");
      // LLOWFS Block
      printw("LLOWFS Block    : ");
      print_status(SCExAO_status[0].lowfs_block, SCExAO_status[0].lowfs_block_co);
      printw("\n");
      // LLOWFS Focus
      printw("LLOWFS Focus    : ");
      print_status(" ", -1);
      printw(" (f: %6d stp)\n", SCExAO_status[0].lowfs_fcs);

      print_header(" IR BENCH POLARIZATION ", '-');

      // Polarizer
      printw("Polarizer       : ");
      print_status(SCExAO_status[0].polarizer, SCExAO_status[0].polarizer_co);
      printw(" (t: %6.2f deg )\n", SCExAO_status[0].polarizer_theta);
      // CHARIS Wollaston
      printw("CHARIS Wollaston: ");
      print_status(SCExAO_status[0].ircam_wollaston, SCExAO_status[0].ircam_wollaston_co);
      printw("\n");
      // FLC
      printw("IR Cam FLC      : ");
      print_status(SCExAO_status[0].ircam_flc_st, SCExAO_status[0].ircam_flc_co);
      printw(" (t: %6.2f deg)\n", SCExAO_status[0].ircam_flc);
      // IR Cams QWPs
      printw("IR Cam QWPs     : ");
      print_status(SCExAO_status[0].ircam_qwp, SCExAO_status[0].ircam_qwp_co);
      printw("\n");
      // IR Cams Wollaston
      printw("IR Cam Wollaston: ");
      print_status(SCExAO_status[0].ircam_wollaston, SCExAO_status[0].ircam_wollaston_co);
      printw("\n");

      print_header(" IR BENCH FIBER INJECTIONS ", '-');

      // GLINT PIckoff
      printw("GLINT Pickoff   : ");
      print_status(SCExAO_status[0].nuller_pickoff_st, SCExAO_status[0].nuller_pickoff_co);
      printw(" (x: %6.2f mm )\n", SCExAO_status[0].nuller_pickoff);
      // FIber Injection Pickoff
      printw("Fib Inj Pickoff : ");
      print_status(SCExAO_status[0].fibinj_pickoff_st, SCExAO_status[0].fibinj_pickoff_co);
      printw(" (x: %6.2f mm )\n", SCExAO_status[0].fibinj_pickoff);
      // Fiber Injection Fiber
      printw("Fib Inj Fiber   : ");
      print_status(SCExAO_status[0].fibinj_fib_st, SCExAO_status[0].fibinj_fib_co);
      printw(" (x: %6d stp, y: %6d stp, f: %6d stp)\n", SCExAO_status[0].fibinj_fib_x, SCExAO_status[0].fibinj_fib_y, SCExAO_status[0].fibinj_fib_f);
      // Fiber Injection Cariage
      printw("Fib Inj Cariage : ");
      print_status(" ", -1);
      printw(" ( %8d stp)\n", SCExAO_status[0].fibinj_car);
      // PG2 Pickoff
      printw("PG2 Pickoff     : ");
      print_status(SCExAO_status[0].PG2_pickoff, SCExAO_status[0].PG2_pickoff_co);
      printw("\n");
      // PCFI Pickoff
      printw("PCFI Pickoff    : ");
      print_status(SCExAO_status[0].pcfi_pickoff_st, SCExAO_status[0].pcfi_pickoff_co);
      printw(" (x: %6.2f mm )\n", SCExAO_status[0].pcfi_pickoff);
      // PCFI Lens
      printw("PCFI Lens       : ");
      print_status(SCExAO_status[0].pcfi_len_st, SCExAO_status[0].pcfi_len_co);
      printw(" (x: %6.2f mm )\n", SCExAO_status[0].pcfi_len);
      // PCIF Fiber
      printw("PCFI Fiber      : ");
      print_status(SCExAO_status[0].pcfi_fib_st, SCExAO_status[0].pcfi_fib_co);
      printw(" (x: %6.2f mm , y: %6.2f mm , f: %6.2f mm )\n", SCExAO_status[0].pcfi_fib_x, SCExAO_status[0].pcfi_fib_y, SCExAO_status[0].pcfi_fib_f);

      print_header(" VISIBLE BENCH ", '-');
      
      // PyWFS Pickoff
      printw("PyWFS Pickoff   : ");
      print_status(SCExAO_status[0].pywfs_pickoff_st, SCExAO_status[0].pywfs_pickoff_co);
      printw(" (w: %6.2f deg)\n", SCExAO_status[0].pywfs_pickoff);
      // PyWFS Filter
      printw("PyWFS Filter    : ");
      print_status(SCExAO_status[0].pywfs_filter, SCExAO_status[0].pywfs_filter_co);
      printw("\n");
      // PyWFS Colimating Lens
      printw("PyWFS Col. Lens : ");
      print_status(" ", -1);
      printw(" (f: %6d stp)\n", SCExAO_status[0].pywfs_col);
      // PyWFS Focus
      printw("PyWFS Focus     : ");
      print_status(" ", -1);
      printw(" (f: %6d stp)\n", SCExAO_status[0].pywfs_fcs);
      // PyWFS Pupil Lens
      printw("PyWFS Pupil Lens: ");
      print_status(" ", -1);
      printw(" (x: %6d stp, y: %6d stp)\n", SCExAO_status[0].pywfs_pup_x, SCExAO_status[0].pywfs_pup_y);
      // FIRST PIckoff
      printw("FIRST Pickoff   : ");
      print_status(SCExAO_status[0].first_pickoff_st, SCExAO_status[0].first_pickoff_co);
      printw(" (x: %6.2f mm )\n", SCExAO_status[0].first_pickoff);
      // FIRST Photometry 1
      printw("FIRST Photo. 1  : ");
      print_status(SCExAO_status[0].first_photometry_x1_st, SCExAO_status[0].first_photometry_x1_co);
      printw(" (x: %6.2f mm )\n", SCExAO_status[0].first_photometry_x1);
      // FIRST Photometry 2
      printw("FIRST Photo. 2  : ");
      print_status(SCExAO_status[0].first_photometry_x2_st, SCExAO_status[0].first_photometry_x2_co);
      printw(" (x: %6.2f mm )\n", SCExAO_status[0].first_photometry_x2);
      // RHEA Pickoff
      printw("RHEA Pickoff    : ");
      print_status(SCExAO_status[0].rhea_pickoff_st, SCExAO_status[0].rhea_pickoff_co);
      printw(" (x: %6.2f nm )\n", SCExAO_status[0].rhea_pickoff);

      print_header(" PYWFS LOOP STATUS ", '-');
      
      // pywfs
      printw("PyWFS loop status          : ");
      print_status(SCExAO_status[0].pywfs_loop, SCExAO_status[0].pywfs_loop_co);
      printw(" | ");
      printw("PyWFS loop frequency       : ");
      print_status_i(SCExAO_status[0].pywfs_freq, "Hz ", -1);
      printw("\n");
      printw("PyWFS calibration status   : ");
      print_status(SCExAO_status[0].pywfs_cal, SCExAO_status[0].pywfs_cal_co);
      printw(" | ");
      printw("PyWFS loop gain            : ");
      print_status_f(SCExAO_status[0].pywfs_gain, "", -1);
      printw("\n");
      printw("PyWFS pupil alignment loop : ");
      print_status(SCExAO_status[0].pywfs_puploop, SCExAO_status[0].pywfs_puploop_co);
      printw(" | ");
      printw("PyWFS loop leak            : ");
      print_status_f(SCExAO_status[0].pywfs_leak, "", -1);
      printw("\n");
      printw("PyWFS flux centering loop  : ");
      print_status(SCExAO_status[0].pywfs_cenloop, SCExAO_status[0].pywfs_cenloop_co);
      printw(" | ");
      printw("PyWFS modulation radius    : ");
      print_status_f(SCExAO_status[0].pywfs_rad, "mas", -1);
      printw("\n");
      printw("PyWFS DM offload           : ");
      print_status(SCExAO_status[0].dmoffload, SCExAO_status[0].dmoffload_co);
      printw(" | ");
      printw("\n");

      print_header(" LOWFS LOOP STATUS ", '-');
      
      // lowfs
      printw("LOWFS loop status          : ");
      print_status(SCExAO_status[0].lowfs_loop, SCExAO_status[0].lowfs_loop_co);
      printw(" | ");
      printw("LOWFS loop frequency       : ");
      print_status_i(SCExAO_status[0].lowfs_freq, "Hz ", -1);
      printw("\n");
      printw("LOWFS mode type            : ");
      print_status(SCExAO_status[0].lowfs_mtype, -1);
      printw(" | ");
      printw("LOWFS loop gain            : ");
      print_status_f(SCExAO_status[0].lowfs_gain, "", -1);
      printw("\n");
      printw("LOWFS number of modes      : ");
      print_status_i(SCExAO_status[0].lowfs_nmodes, "", -1);
      printw(" | ");
      printw("LOWFS loop leak            : ");
      print_status_f(SCExAO_status[0].lowfs_leak, "", -1);
      printw("\n");

      print_header(" SPECKLE NULLING LOOP STATUS ", '-');
      
      // speckle nulling
      printw("Speckle Nulling loop status: ");
      print_status(SCExAO_status[0].sn_loop, SCExAO_status[0].sn_loop_co);
      printw(" | ");
      printw("Speckle Nulling loop freq. : ");
      print_status_i(SCExAO_status[0].sn_freq, "Hz ", -1);
      printw("\n");
      printw("Speckle Nulling loop gain  : ");
      print_status_f(SCExAO_status[0].sn_gain, "", -1);
      printw(" | ");
      printw("\n");

      print_header(" ZAP LOOP STATUS ", '-');
      
      // zap
      printw("ZAP loop status            : ");
      print_status(SCExAO_status[0].zap_loop, SCExAO_status[0].zap_loop_co);
      printw(" | ");
      printw("ZAP loop frequency         : ");
      print_status_i(SCExAO_status[0].zap_freq, "Hz ", -1);
      printw("\n");
      printw("ZAP mode type              : ");
      print_status(SCExAO_status[0].zap_mtype, -1);
      printw(" | ");
      printw("ZAP loop gain              : ");
      print_status_f(SCExAO_status[0].zap_gain, "", -1);
      printw("\n");
      printw("ZAP number of modes        : ");
      print_status_i(SCExAO_status[0].zap_nmodes, "", -1);
      printw(" | ");
      printw("\n");
      
      print_header(" ASTROGRID ", '-');
      
      // astrogrid
      printw("ASTROGRID loop status      : ");
      print_status(SCExAO_status[0].grid_st, SCExAO_status[0].grid_st_co);
      printw(" | ");
      printw("ASTROGRID modulation freq. : ");
      print_status_i(SCExAO_status[0].grid_mod, "Hz ", -1);
      printw("\n");
      printw("ASTROGRID separation       : ");
      print_status_f(SCExAO_status[0].grid_sep, "l/D", -1);
      printw(" | ");
      printw("ASTROGRID amplitude        : ");
      print_status_f(SCExAO_status[0].grid_amp, "um ", -1);
      printw("\n");

      print_header(" LOGGING STATUS ", '-');
      
      // Chuck log
      printw("Logging ChuckCam images    : ");
      print_status(SCExAO_status[0].logchuck, SCExAO_status[0].logchuck_co);
      printw(" | ");
      // Chuck dark
      printw("Acquiring Chuckcam darks   : ");
      print_status(SCExAO_status[0].darkchuck, SCExAO_status[0].darkchuck_co);
      printw("\n");
      // Hotspotalign
      printw("Aligning PSF on the hotspot: ");
      print_status(SCExAO_status[0].hotspot, SCExAO_status[0].hotspot_co);
      printw(" | ");
      printw("\n");

      refresh();
    }
  endwin();
  
  return 0;
}




int main(int argc, char **argv)
{
  int cmdOK;
  
  sprintf(SM_fname, "%s/SCExAO_status.shm", SHAREDMEMDIR);
  
  if( argc == 1)
    {
      printf("\n");
      printf("OPTIONS :\n");
      printf("   %s create:\n", argv[0]);
      printf("      create shared memory (run every time the structure has changed)\n");
      printf("   %s set <variable> <value> <color>:\n", argv[0]);
      printf("      Set variable, color is optional \n");
      printf("   %s disp:\n", argv[0]);
      printf("      Display variables\n");
      printf("   Color code (xterm):\n");
      printf("      -1:WHITE 0:RED 1:GREEN 2:BLUE 3:ORANGE 4:BLACK \n");
      printf("\n");
      exit(0);
    }

  
  cmdOK = 0;
  
  if( strcmp(argv[1], "create") == 0)
    {
      printf("create status shared memory structure\n");
      create_status_shm();
      cmdOK = 1;
    }
  
  
  
  if( strcmp(argv[1], "set") == 0)
    {
      read_status_shm();          
      cmdOK = 1;
      // NPS1
      if( strcmp(argv[2], "nps1_1") == 0)
	{
	  SCExAO_status[0].nps1_1_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "nps1_2") == 0)
	{
	  SCExAO_status[0].nps1_2_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "nps1_3") == 0)
	{
	  SCExAO_status[0].nps1_3_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "nps1_4") == 0)
	{
	  SCExAO_status[0].nps1_4_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "nps1_5") == 0)
	{
	  SCExAO_status[0].nps1_5_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "nps1_6") == 0)
	{
	  SCExAO_status[0].nps1_6_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "nps1_7") == 0)
	{
	  SCExAO_status[0].nps1_7_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "nps1_8") == 0)
	{
	  SCExAO_status[0].nps1_8_co = atoi(argv[4]);
	}
      // NPS2
      if( strcmp(argv[2], "nps2_1") == 0)
	{
	  SCExAO_status[0].nps2_1_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "nps2_2") == 0)
	{
	  SCExAO_status[0].nps2_2_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "nps2_3") == 0)
	{
	  SCExAO_status[0].nps2_3_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "nps2_4") == 0)
	{
	  SCExAO_status[0].nps2_4_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "nps2_5") == 0)
	{
	  SCExAO_status[0].nps2_5_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "nps2_6") == 0)
	{
	  SCExAO_status[0].nps2_6_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "nps2_7") == 0)
	{
	  SCExAO_status[0].nps2_7_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "nps2_8") == 0)
	{
	  SCExAO_status[0].nps2_8_co = atoi(argv[4]);
	}
      // NPS3
      if( strcmp(argv[2], "nps3_1") == 0)
	{
	  SCExAO_status[0].nps3_1_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "nps3_2") == 0)
	{
	  SCExAO_status[0].nps3_2_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "nps3_3") == 0)
	{
	  SCExAO_status[0].nps3_3_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "nps3_4") == 0)
	{
	  SCExAO_status[0].nps3_4_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "nps3_5") == 0)
	{
	  SCExAO_status[0].nps3_5_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "nps3_6") == 0)
	{
	  SCExAO_status[0].nps3_6_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "nps3_7") == 0)
	{
	  SCExAO_status[0].nps3_7_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "nps3_8") == 0)
	{
	  SCExAO_status[0].nps3_8_co = atoi(argv[4]);
	}
      // cal source
      if( strcmp(argv[2], "src_fib_st") == 0)
	{
	  strncpy(SCExAO_status[0].src_fib_st, argv[3], 15);
	  SCExAO_status[0].src_fib_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "src_fib_x") == 0)
	{
	  SCExAO_status[0].src_fib_x = atof(argv[3]);
	}
      if( strcmp(argv[2], "src_fib_y") == 0)
	{
	  SCExAO_status[0].src_fib_y = atof(argv[3]);
	}
      if( strcmp(argv[2], "src_select_st") == 0)
	{
	  strncpy(SCExAO_status[0].src_select_st, argv[3], 15);
	  SCExAO_status[0].src_select_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "src_select") == 0)
	{
	  SCExAO_status[0].src_select = atof(argv[3]);
	}
      if( strcmp(argv[2], "src_flux_irnd") == 0)
	{
	  strncpy(SCExAO_status[0].src_flux_irnd, argv[3], 15);
	}
      if( strcmp(argv[2], "src_flux_optnd") == 0)
	{
	  strncpy(SCExAO_status[0].src_flux_optnd, argv[3], 15);
	}
      if( strcmp(argv[2], "src_flux_filter") == 0)
	{
	  strncpy(SCExAO_status[0].src_flux_filter, argv[3], 15);
	}
      // oap1
      if( strcmp(argv[2], "oap1_st") == 0)
	{
	  strncpy(SCExAO_status[0].oap1_st, argv[3], 15);
	  SCExAO_status[0].oap1_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "oap1_theta") == 0)
	{
	  SCExAO_status[0].oap1_theta = atof(argv[3]);
	}
      if( strcmp(argv[2], "oap1_phi") == 0)
	{
	  SCExAO_status[0].oap1_phi = atof(argv[3]);
	}
      if( strcmp(argv[2], "oap1_f") == 0)
	{
	  SCExAO_status[0].oap1_f = atoi(argv[3]);
	}
      // integrating sphere
      if( strcmp(argv[2], "intsphere") == 0)
	{
	  strncpy(SCExAO_status[0].intsphere, argv[3], 15);
	  SCExAO_status[0].intsphere_co = atoi(argv[4]);
	}
      // polarizer
      if( strcmp(argv[2], "polarizer") == 0)
	{
	  strncpy(SCExAO_status[0].polarizer, argv[3], 15);
	  SCExAO_status[0].polarizer_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "polarizer_theta") == 0)
	{
	  SCExAO_status[0].polarizer_theta = atof(argv[3]);
	}
      // dichroic
      if( strcmp(argv[2], "dichroic_st") == 0)
	{
	  strncpy(SCExAO_status[0].dichroic_st, argv[3], 15);
	  SCExAO_status[0].dichroic_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "dichroic") == 0)
	{
	  SCExAO_status[0].dichroic = atof(argv[3]);
	}
      // pupil
      if( strcmp(argv[2], "pupil_st") == 0)
	{
	  strncpy(SCExAO_status[0].pupil_st, argv[3], 15);
	  SCExAO_status[0].pupil_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "pupil_wheel") == 0)
	{
	  SCExAO_status[0].pupil_wheel = atof(argv[3]);
	}
      if( strcmp(argv[2], "pupil_x") == 0)
	{
	  SCExAO_status[0].pupil_x = atoi(argv[3]);
	}
      if( strcmp(argv[2], "pupil_y") == 0)
	{
	  SCExAO_status[0].pupil_y = atoi(argv[3]);
	}
      // Compensating plate
      if( strcmp(argv[2], "compplate") == 0)
	{
	  strncpy(SCExAO_status[0].compplate, argv[3], 15);
	  SCExAO_status[0].compplate_co = atoi(argv[4]);
	}
      // piaa1
      if( strcmp(argv[2], "piaa1_st") == 0)
	{
	  strncpy(SCExAO_status[0].piaa1_st, argv[3], 15);
	  SCExAO_status[0].piaa1_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "piaa1_wheel") == 0)
	{
	  SCExAO_status[0].piaa1_wheel = atof(argv[3]);
	}
      if( strcmp(argv[2], "piaa1_x") == 0)
	{
	  SCExAO_status[0].piaa1_x = atoi(argv[3]);
	}
      if( strcmp(argv[2], "piaa1_y") == 0)
	{
	  SCExAO_status[0].piaa1_y = atoi(argv[3]);
	}
      //piaa2
      if( strcmp(argv[2], "piaa2_st") == 0)
	{
	  strncpy(SCExAO_status[0].piaa2_st, argv[3], 15);
	  SCExAO_status[0].piaa2_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "piaa2_wheel") == 0)
	{
	  SCExAO_status[0].piaa2_wheel = atof(argv[3]);
	}
      if( strcmp(argv[2], "piaa2_x") == 0)
	{
	  SCExAO_status[0].piaa2_x = atoi(argv[3]);
	}
      if( strcmp(argv[2], "piaa2_y") == 0)
	{
	  SCExAO_status[0].piaa2_y = atoi(argv[3]);
	}
      if( strcmp(argv[2], "piaa2_f") == 0)
	{
	  SCExAO_status[0].piaa2_f = atoi(argv[3]);
	}
      //nuller
      if( strcmp(argv[2], "nuller_pickoff_st") == 0)
	{
	  strncpy(SCExAO_status[0].nuller_pickoff_st, argv[3], 15);
	  SCExAO_status[0].nuller_pickoff_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "nuller_pickoff") == 0)
	{
	  SCExAO_status[0].nuller_pickoff = atof(argv[3]);
	}
      // PG1
      if( strcmp(argv[2], "PG1_pickoff") == 0)
	{
	  strncpy(SCExAO_status[0].PG1_pickoff, argv[3], 15);
	  SCExAO_status[0].PG1_pickoff_co = atoi(argv[4]);
	}
      // fpm
      if( strcmp(argv[2], "fpm_st") == 0)
	{
	  strncpy(SCExAO_status[0].fpm_st, argv[3], 15);
	  SCExAO_status[0].fpm_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "fpm_wheel") == 0)
	{
	  SCExAO_status[0].fpm_wheel = atof(argv[3]);
	}
      if( strcmp(argv[2], "fpm_x") == 0)
	{
	  SCExAO_status[0].fpm_x = atoi(argv[3]);
	}
      if( strcmp(argv[2], "fpm_y") == 0)
	{
	  SCExAO_status[0].fpm_y = atoi(argv[3]);
	}
      if( strcmp(argv[2], "fpm_f") == 0)
	{
	  SCExAO_status[0].fpm_f = atoi(argv[3]);
	}
      // lyot
      if( strcmp(argv[2], "lyot_st") == 0)
	{
	  strncpy(SCExAO_status[0].lyot_st, argv[3], 15);
	  SCExAO_status[0].lyot_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "lyot_wheel") == 0)
	{
	  SCExAO_status[0].lyot_wheel = atof(argv[3]);
	}
      if( strcmp(argv[2], "lyot_x") == 0)
	{
	  SCExAO_status[0].lyot_x = atoi(argv[3]);
	}
      if( strcmp(argv[2], "lyot_y") == 0)
	{
	  SCExAO_status[0].lyot_y = atoi(argv[3]);
	}
      // inverse piaa
      if( strcmp(argv[2], "invpiaa_st") == 0)
	{
	  strncpy(SCExAO_status[0].invpiaa_st, argv[3], 15);
	  SCExAO_status[0].invpiaa_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "invpiaa_x") == 0)
	{
	  SCExAO_status[0].invpiaa_x = atof(argv[3]);
	}
      if( strcmp(argv[2], "invpiaa_y") == 0)
	{
	  SCExAO_status[0].invpiaa_y = atof(argv[3]);
	}
      if( strcmp(argv[2], "invpiaa_theta") == 0)
	{
	  SCExAO_status[0].invpiaa_theta = atoi(argv[3]);
	}
      if( strcmp(argv[2], "invpiaa_phi") == 0)
	{
	  SCExAO_status[0].invpiaa_phi = atoi(argv[3]);
	}
      // oap4
      if( strcmp(argv[2], "oap4_st") == 0)
	{
	  strncpy(SCExAO_status[0].oap4_st, argv[3], 15);
	  SCExAO_status[0].oap4_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "oap4_theta") == 0)
	{
	  SCExAO_status[0].oap4_theta = atof(argv[3]);
	}
      if( strcmp(argv[2], "oap4_phi") == 0)
	{
	  SCExAO_status[0].oap4_phi = atof(argv[3]);
	}
      // steering mirror
      if( strcmp(argv[2], "steering_st") == 0)
	{
	  strncpy(SCExAO_status[0].steering_st, argv[3], 15);
	  SCExAO_status[0].steering_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "steering_theta") == 0)
	{
	  SCExAO_status[0].steering_theta = atof(argv[3]);
	}
      if( strcmp(argv[2], "steering_phi") == 0)
	{
	  SCExAO_status[0].steering_phi = atof(argv[3]);
	}
      // charis
      if( strcmp(argv[2], "charis_pickoff_st") == 0)
	{
	  strncpy(SCExAO_status[0].charis_pickoff_st, argv[3], 15);
	  SCExAO_status[0].charis_pickoff_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "charis_pickoff_wheel") == 0)
	{
	  SCExAO_status[0].charis_pickoff_wheel = atof(argv[3]);
	}
      if( strcmp(argv[2], "charis_pickoff_theta") == 0)
	{
	  SCExAO_status[0].charis_pickoff_theta = atof(argv[3]);
	}
      // mkids
      if( strcmp(argv[2], "mkids_pickoff_st") == 0)
	{
	  strncpy(SCExAO_status[0].mkids_pickoff_st, argv[3], 15);
	  SCExAO_status[0].mkids_pickoff_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "mkids_pickoff_wheel") == 0)
	{
	  SCExAO_status[0].mkids_pickoff_wheel = atof(argv[3]);
	}
      if( strcmp(argv[2], "mkids_pickoff_theta") == 0)
	{
	  SCExAO_status[0].mkids_pickoff_theta = atof(argv[3]);
	}
      // ircams common
      if( strcmp(argv[2], "ircam_filter") == 0)
	{
	  strncpy(SCExAO_status[0].ircam_filter, argv[3], 15);
	  SCExAO_status[0].ircam_filter_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "ircam_block") == 0)
	{
	  strncpy(SCExAO_status[0].ircam_block, argv[3], 15);
	  SCExAO_status[0].ircam_block_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "ircam_fcs_st") == 0)
	{
	  strncpy(SCExAO_status[0].ircam_fcs_st, argv[3], 15);
	  SCExAO_status[0].ircam_fcs_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "ircam_fcs_f1") == 0)
	{
	  SCExAO_status[0].ircam_fcs_f1 = atoi(argv[3]);
	}
      if( strcmp(argv[2], "ircam_fcs_f2") == 0)
	{
	  SCExAO_status[0].ircam_fcs_f2 = atof(argv[3]);
	}
      // Polarization
      if( strcmp(argv[2], "field_stop_st") == 0)
	{
	  strncpy(SCExAO_status[0].field_stop_st, argv[3], 15);
	  SCExAO_status[0].field_stop_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "field_stop_x") == 0)
	{
	  SCExAO_status[0].field_stop_x = atof(argv[3]);
	}
      if( strcmp(argv[2], "field_stop_y") == 0)
	{
	  SCExAO_status[0].field_stop_y = atof(argv[3]);
	}
      if( strcmp(argv[2], "charis_wollaston") == 0)
	{
	  strncpy(SCExAO_status[0].charis_wollaston, argv[3], 15);
	  SCExAO_status[0].charis_wollaston_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "ircam_wollaston") == 0)
	{
	  strncpy(SCExAO_status[0].ircam_wollaston, argv[3], 15);
	  SCExAO_status[0].ircam_wollaston_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "ircam_flc_st") == 0)
	{
	  strncpy(SCExAO_status[0].ircam_flc_st, argv[3], 15);
	  SCExAO_status[0].ircam_flc_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "ircam_flc") == 0)
	{
	  SCExAO_status[0].ircam_flc = atof(argv[3]);
	}
      if( strcmp(argv[2], "ircam_pupil_st") == 0)
	{
	  strncpy(SCExAO_status[0].ircam_pupil_st, argv[3], 15);
	  SCExAO_status[0].ircam_pupil_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "ircam_pupil_x") == 0)
	{
	  SCExAO_status[0].ircam_pupil_x = atof(argv[3]);
	}
      if( strcmp(argv[2], "ircam_pupil_y") == 0)
	{
	  SCExAO_status[0].ircam_pupil_y = atof(argv[3]);
	}
      if( strcmp(argv[2], "ircam_qwp") == 0)
	{
	  strncpy(SCExAO_status[0].ircam_qwp, argv[3], 15);
	  SCExAO_status[0].ircam_qwp_co = atoi(argv[4]);
	}
      // PCFI
      if( strcmp(argv[2], "pcfi_pickoff_st") == 0)
	{
	  strncpy(SCExAO_status[0].pcfi_pickoff_st, argv[3], 15);
	  SCExAO_status[0].pcfi_pickoff_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "pcfi_pickoff") == 0)
	{
	  SCExAO_status[0].pcfi_pickoff = atof(argv[3]);
	}
      if( strcmp(argv[2], "pcfi_len_st") == 0)
	{
	  strncpy(SCExAO_status[0].pcfi_len_st, argv[3], 15);
	  SCExAO_status[0].pcfi_len_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "pcfi_len") == 0)
	{
	  SCExAO_status[0].pcfi_len = atof(argv[3]);
	}
      if( strcmp(argv[2], "pcfi_fib_st") == 0)
	{
	  strncpy(SCExAO_status[0].pcfi_fib_st, argv[3], 15);
	  SCExAO_status[0].pcfi_fib_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "pcfi_fib_x") == 0)
	{
	  SCExAO_status[0].pcfi_fib_x = atof(argv[3]);
	}
      if( strcmp(argv[2], "pcfi_fib_y") == 0)
	{
	  SCExAO_status[0].pcfi_fib_y = atof(argv[3]);
	}
      if( strcmp(argv[2], "pcfi_fib_f") == 0)
	{
	  SCExAO_status[0].pcfi_fib_f = atof(argv[3]);
	}
      // saphira/chuck
      if( strcmp(argv[2], "saphira_pickoff_st") == 0)
	{
	  strncpy(SCExAO_status[0].saphira_pickoff_st, argv[3], 15);
	  SCExAO_status[0].saphira_pickoff_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "saphira_pickoff") == 0)
	{
	  SCExAO_status[0].saphira_pickoff = atof(argv[3]);
	}
      if( strcmp(argv[2], "chuck_pup") == 0)
	{
	  strncpy(SCExAO_status[0].chuck_pup, argv[3], 15);
	  SCExAO_status[0].chuck_pup_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "chuck_pup_fcs_st") == 0)
	{
	  strncpy(SCExAO_status[0].chuck_pup_fcs_st, argv[3], 15);
	  SCExAO_status[0].chuck_pup_fcs_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "chuck_pup_fcs") == 0)
	{
	  SCExAO_status[0].chuck_pup_fcs = atof(argv[3]);
	}
      if( strcmp(argv[2], "saphira_pup") == 0)
	{
	  strncpy(SCExAO_status[0].saphira_pup, argv[3], 15);
	  SCExAO_status[0].saphira_pup_co = atoi(argv[4]);
	}
      // rajni
      if( strcmp(argv[2], "lowfs_block") == 0)
	{
	  strncpy(SCExAO_status[0].lowfs_block, argv[3], 15);
	  SCExAO_status[0].lowfs_block_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "lowfs_fcs") == 0)
	{
	  SCExAO_status[0].lowfs_fcs = atoi(argv[3]);
	}
      // fiber injection
      if( strcmp(argv[2], "fibinj_pickoff_st") == 0)
	{
	  strncpy(SCExAO_status[0].fibinj_pickoff_st, argv[3], 15);
	  SCExAO_status[0].fibinj_pickoff_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "fibinj_pickoff") == 0)
	{
	  SCExAO_status[0].fibinj_pickoff = atof(argv[3]);
	}
      if( strcmp(argv[2], "fibinj_fib_st") == 0)
	{
	  strncpy(SCExAO_status[0].fibinj_fib_st, argv[3], 15);
	  SCExAO_status[0].fibinj_fib_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "fibinj_fib_x") == 0)
	{
	  SCExAO_status[0].fibinj_fib_x = atoi(argv[3]);
	}
      if( strcmp(argv[2], "fibinj_fib_y") == 0)
	{
	  SCExAO_status[0].fibinj_fib_y = atoi(argv[3]);
	}
      if( strcmp(argv[2], "fibinj_fib_f") == 0)
	{
	  SCExAO_status[0].fibinj_fib_f = atoi(argv[3]);
	}
      if( strcmp(argv[2], "fibinj_car") == 0)
	{
	  SCExAO_status[0].fibinj_car = atoi(argv[3]);
	}
      // PG2
      if( strcmp(argv[2], "PG2_pickoff") == 0)
	{
	  strncpy(SCExAO_status[0].PG2_pickoff, argv[3], 15);
	  SCExAO_status[0].PG2_pickoff_co = atoi(argv[4]);
	}
      // pywfs
      if( strcmp(argv[2], "pywfs_pickoff_st") == 0)
	{
	  strncpy(SCExAO_status[0].pywfs_pickoff_st, argv[3], 15);
	  SCExAO_status[0].pywfs_pickoff_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "pywfs_pickoff") == 0)
	{
	  SCExAO_status[0].pywfs_pickoff = atof(argv[3]);
	}
      if( strcmp(argv[2], "pywfs_filter") == 0)
	{
	  strncpy(SCExAO_status[0].pywfs_filter, argv[3], 15);
	  SCExAO_status[0].pywfs_filter_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "pywfs_col") == 0)
	{
	  SCExAO_status[0].pywfs_col = atoi(argv[3]);
	}
      if( strcmp(argv[2], "pywfs_fcs") == 0)
	{
	  SCExAO_status[0].pywfs_fcs = atoi(argv[3]);
	}
      if( strcmp(argv[2], "pywfs_pup_x") == 0)
	{
	  SCExAO_status[0].pywfs_pup_x = atoi(argv[3]);
	}
      if( strcmp(argv[2], "pywfs_pup_y") == 0)
	{
	  SCExAO_status[0].pywfs_pup_y = atoi(argv[3]);
	}
      // first
      if( strcmp(argv[2], "first_pickoff_st") == 0)
	{
	  strncpy(SCExAO_status[0].first_pickoff_st, argv[3], 15);
	  SCExAO_status[0].first_pickoff_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "first_pickoff") == 0)
	{
	  SCExAO_status[0].first_pickoff = atof(argv[3]);
	}
      if( strcmp(argv[2], "first_photometry_x1_st") == 0)
	{
	  strncpy(SCExAO_status[0].first_photometry_x1_st, argv[3], 15);
	  SCExAO_status[0].first_photometry_x1_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "first_photometry_x1") == 0)
	{
	  SCExAO_status[0].first_photometry_x1 = atof(argv[3]);
	}
      if( strcmp(argv[2], "first_photometry_x2_st") == 0)
	{
	  strncpy(SCExAO_status[0].first_photometry_x2_st, argv[3], 15);
	  SCExAO_status[0].first_photometry_x2_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "first_photometry_x2") == 0)
	{
	  SCExAO_status[0].first_photometry_x2 = atof(argv[3]);
	}
      // rhea
      if( strcmp(argv[2], "rhea_pickoff_st") == 0)
	{
	  strncpy(SCExAO_status[0].rhea_pickoff_st, argv[3], 15);
	  SCExAO_status[0].rhea_pickoff_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "rhea_pickoff") == 0)
	{
	  SCExAO_status[0].rhea_pickoff = atof(argv[3]);
	}
      // pywfs
      if( strcmp(argv[2], "pywfs_loop") == 0)
	{
	  strncpy(SCExAO_status[0].pywfs_loop, argv[3], 15);
	  SCExAO_status[0].pywfs_loop_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "pywfs_cal") == 0)
	{
	  strncpy(SCExAO_status[0].pywfs_cal, argv[3], 15);
	  SCExAO_status[0].pywfs_cal_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "pywfs_freq") == 0)
	{
	  SCExAO_status[0].pywfs_freq = atoi(argv[3]);
	}
      if( strcmp(argv[2], "pywfs_gain") == 0)
	{
	  SCExAO_status[0].pywfs_gain = atof(argv[3]);
	}
      if( strcmp(argv[2], "pywfs_leak") == 0)
	{
	  SCExAO_status[0].pywfs_leak = atof(argv[3]);
	}
      if( strcmp(argv[2], "pywfs_rad") == 0)
	{
	  SCExAO_status[0].pywfs_rad = atof(argv[3]);
	}
      if( strcmp(argv[2], "pywfs_puploop") == 0)
	{
	  strncpy(SCExAO_status[0].pywfs_puploop, argv[3], 15);
	  SCExAO_status[0].pywfs_puploop_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "pywfs_cenloop") == 0)
	{
	  strncpy(SCExAO_status[0].pywfs_cenloop, argv[3], 15);
	  SCExAO_status[0].pywfs_cenloop_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "dmoffload") == 0)
	{
	  strncpy(SCExAO_status[0].dmoffload, argv[3], 15);
	  SCExAO_status[0].dmoffload_co = atoi(argv[4]);
	}

      // lowfs
      if( strcmp(argv[2], "lowfs_loop") == 0)
	{
	  strncpy(SCExAO_status[0].lowfs_loop, argv[3], 15);
	  SCExAO_status[0].lowfs_loop_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "lowfs_freq") == 0)
	{
	  SCExAO_status[0].lowfs_freq = atoi(argv[3]);
	}
      if( strcmp(argv[2], "lowfs_nmodes") == 0)
	{
	  SCExAO_status[0].lowfs_nmodes = atoi(argv[3]);
	}
      if( strcmp(argv[2], "lowfs_mtype") == 0)
	{
	  strncpy(SCExAO_status[0].lowfs_mtype, argv[3], 15);
	}
      if( strcmp(argv[2], "lowfs_gain") == 0)
	{
	  SCExAO_status[0].lowfs_gain = atof(argv[3]);
	}
      if( strcmp(argv[2], "lowfs_leak") == 0)
	{
	  SCExAO_status[0].lowfs_leak = atof(argv[3]);
	}

      // speckle nulling
      if( strcmp(argv[2], "sn_loop") == 0)
	{
	  strncpy(SCExAO_status[0].sn_loop, argv[3], 15);
	  SCExAO_status[0].sn_loop_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "sn_freq") == 0)
	{
	  SCExAO_status[0].sn_freq = atoi(argv[3]);
	}
      if( strcmp(argv[2], "sn_gain") == 0)
	{
	  SCExAO_status[0].sn_gain = atof(argv[3]);
	}
      
      // zap
      if( strcmp(argv[2], "zap_loop") == 0)
	{
	  strncpy(SCExAO_status[0].zap_loop, argv[3], 15);
	  SCExAO_status[0].zap_loop_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "zap_freq") == 0)
	{
	  SCExAO_status[0].zap_freq = atoi(argv[3]);
	}
      if( strcmp(argv[2], "zap_nmodes") == 0)
	{
	  SCExAO_status[0].zap_nmodes = atoi(argv[3]);
	}
      if( strcmp(argv[2], "zap_mtype") == 0)
	{
	  strncpy(SCExAO_status[0].zap_mtype, argv[3], 15);
	}
      if( strcmp(argv[2], "zap_gain") == 0)
	{
	  SCExAO_status[0].zap_gain = atof(argv[3]);
	}
      
      // astrogrid
      if( strcmp(argv[2], "grid_st") == 0)
	{
	  strncpy(SCExAO_status[0].grid_st, argv[3], 15);
	  SCExAO_status[0].grid_st_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "grid_sep") == 0)
	{
	  SCExAO_status[0].grid_sep = atof(argv[3]);
	}
      if( strcmp(argv[2], "grid_amp") == 0)
	{
	  SCExAO_status[0].grid_amp = atof(argv[3]);
	}
      if( strcmp(argv[2], "grid_mod") == 0)
	{
	  SCExAO_status[0].grid_mod = atoi(argv[3]);
	}

      // logging
      if( strcmp(argv[2], "logchuck") == 0)
	{
	  strncpy(SCExAO_status[0].logchuck, argv[3], 15);
	  SCExAO_status[0].logchuck_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "darkchuck") == 0)
	{
	  strncpy(SCExAO_status[0].darkchuck, argv[3], 15);
	  SCExAO_status[0].darkchuck_co = atoi(argv[4]);
	}
      if( strcmp(argv[2], "hotspot") == 0)
	{
	  strncpy(SCExAO_status[0].hotspot, argv[3], 15);
	  SCExAO_status[0].hotspot_co = atoi(argv[4]);
	}
    }
  
  
  if( strcmp(argv[1], "disp") == 0)
    {
      read_status_shm();
      status_display();
      cmdOK = 1;
    }
  
  
  
  
  if(cmdOK == 0)
    {
      printf("%d  command %s not recognized\n", cmdOK, argv[1]);
    }
  
  return 0;
}









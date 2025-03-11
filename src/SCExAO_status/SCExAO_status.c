#include <string.h>
#include <malloc.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <sys/mman.h>
#include <fcntl.h>  // for open
#include <unistd.h> // for close
#include <termios.h>
#include <ncurses.h>

#include "SCExAO_status.h"

#define SHAREDMEMDIR "/tmp"
int SM_fd;
char SM_fname[200];
SCEXAOSTATUS *SCExAO_status;

int SME_fd;
char SME_fname[200];
SCEXAOSTATUS_EXTENSION *SCExAO_status_ext;
long cnt;
int wcol, wrow; // window size

int create_extended_status_shm(); // Forward

int create_status_shm()
{

  int result;

  // CREATING SHARED MEMORY

  sprintf(SM_fname, "%s/SCExAO_status.shm", SHAREDMEMDIR);
  SM_fd = open(SM_fname, O_RDWR | O_CREAT | O_TRUNC, (mode_t)0600);

  if (SM_fd == -1)
  {
    perror("Error opening file for writing");
    exit(0);
  }

  result = lseek(SM_fd, sizeof(SCEXAOSTATUS) - 1, SEEK_SET);
  if (result == -1)
  {
    close(SM_fd);
    perror("Error calling lseek() to 'stretch' the file");
    exit(0);
  }

  result = write(SM_fd, "", 1);
  if (result != 1)
  {
    close(SM_fd);
    perror("Error writing last byte of the file");
    exit(0);
  }

  SCExAO_status = (SCEXAOSTATUS *)mmap(0, sizeof(SCEXAOSTATUS), PROT_READ | PROT_WRITE, MAP_SHARED, SM_fd, 0);
  if (SCExAO_status == MAP_FAILED)
  {
    close(SM_fd);
    perror("Error mmapping the file");
    exit(0);
  }

  // Create the extended SHM !
  create_extended_status_shm();

  return 0;
}

int create_extended_status_shm()
{

  int result;

  // CREATING SHARED MEMORY

  sprintf(SME_fname, "%s/SCExAO_status_ext.shm", SHAREDMEMDIR);
  SME_fd = open(SME_fname, O_RDWR | O_CREAT | O_TRUNC, (mode_t)0600);

  if (SME_fd == -1)
  {
    perror("Error opening file for writing");
    exit(0);
  }

  result = lseek(SME_fd, sizeof(SCEXAOSTATUS_EXTENSION) - 1, SEEK_SET);
  if (result == -1)
  {
    close(SME_fd);
    perror("Error calling lseek() to 'stretch' the file");
    exit(0);
  }

  result = write(SME_fd, "", 1);
  if (result != 1)
  {
    close(SME_fd);
    perror("Error writing last byte of the file");
    exit(0);
  }

  SCExAO_status_ext = (SCEXAOSTATUS_EXTENSION *)mmap(0, sizeof(SCEXAOSTATUS_EXTENSION), PROT_READ | PROT_WRITE, MAP_SHARED, SME_fd, 0);
  if (SCExAO_status_ext == MAP_FAILED)
  {
    close(SME_fd);
    perror("Error mmapping the file");
    exit(0);
  }

  return 0;
}

int read_status_shm()
{

  SM_fd = open(SM_fname, O_RDWR);
  if (SM_fd == -1)
  {
    printf("Cannot import file - continuing (Orig.)\n");
  }
  else
  {
    SCExAO_status = (SCEXAOSTATUS *)mmap(0, sizeof(SCEXAOSTATUS), PROT_READ | PROT_WRITE, MAP_SHARED, SM_fd, 0);
    if (SCExAO_status == MAP_FAILED)
    {
      close(SM_fd);
      perror("Error mmapping the file");
      exit(0);
    }
  }

  SME_fd = open(SME_fname, O_RDWR);
  if (SME_fd == -1)
  {
    printf("Cannot import file - continuing (Ext.)\n");
  }
  else
  {
    SCExAO_status_ext = (SCEXAOSTATUS_EXTENSION *)mmap(0, sizeof(SCEXAOSTATUS_EXTENSION), PROT_READ | PROT_WRITE, MAP_SHARED, SME_fd, 0);
    if (SCExAO_status_ext == MAP_FAILED)
    {
      close(SME_fd);
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

  if (ch != EOF)
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
  for (i = 0; i < (wcol - n) / 2; i++)
    printw("%c", c);
  printw("%s", str);
  for (i = 0; i < (wcol - n) / 2 - 1; i++)
    printw("%c", c);
  printw("\n");
  attroff(COLOR_PAIR(6));
  attroff(A_BOLD);

  return (0);
}

int print_status(char *str, int co)
{

  attron(A_BOLD);
  attron(COLOR_PAIR(co + 2));
  printw(" %-15s ", str);
  attroff(COLOR_PAIR(co + 2));
  attroff(A_BOLD);

  return (0);
}

int print_status_f(float fnum, char *unitf, int co)
{

  attron(A_BOLD);
  attron(COLOR_PAIR(co + 2));
  printw("%12.3f %3s ", fnum, unitf);
  attroff(COLOR_PAIR(co + 2));
  attroff(A_BOLD);

  return (0);
}

int print_status_i(int inum, char *uniti, int co)
{

  attron(A_BOLD);
  attron(COLOR_PAIR(co + 2));
  printw("%12d %3s ", inum, uniti);
  attroff(COLOR_PAIR(co + 2));
  attroff(A_BOLD);

  return (0);
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

  while (!kbdhit())
  {
    usleep(100000); // in us
    erase();

    print_header(" NETWORK POWER SWITCHES ", '-');
    // NPS1
    printw("NPS1 ports 1-4  : ");
    print_status("               ", SCExAO_status[0].nps1_1_co);
    printw(" | ");
    print_status("SCExAO2 POWER  ", SCExAO_status[0].nps1_2_co);
    printw(" | ");
    print_status("HIGH-VOLTAGE TT", SCExAO_status[0].nps1_3_co);
    printw(" | ");
    print_status("VAMPIRES CAM 1 ", SCExAO_status[0].nps1_4_co);
    printw("\n");
    printw("NPS1 ports 5-8  : ");
    print_status("  SOURCE BOX   ", SCExAO_status[0].nps1_5_co);
    printw(" | ");
    print_status("DM ELECTRONICS ", SCExAO_status[0].nps1_6_co);
    printw(" | ");
    print_status(" VAMPIRES SYNC ", SCExAO_status[0].nps1_7_co);
    printw(" | ");
    print_status("VAMP DIFF WHEEL", SCExAO_status[0].nps1_8_co);
    printw("\n");
    // NPS2
    printw("NPS2 ports 1-4  : ");
    print_status("   FIRST MEMS  ", SCExAO_status[0].nps2_1_co);
    printw(" | ");
    print_status("               ", SCExAO_status[0].nps2_2_co);
    printw(" | ");
    print_status(" IRSPECTRO FIB ", SCExAO_status[0].nps2_3_co);
    printw(" | ");
    print_status("APAPANE C-RED2 ", SCExAO_status[0].nps2_4_co);
    printw("\n");
    printw("NPS2 ports 5-8  : ");
    print_status("               ", SCExAO_status[0].nps2_5_co);
    printw(" | ");
    print_status("  GLINT MEMS   ", SCExAO_status[0].nps2_6_co);
    printw(" | ");
    print_status("FIRST HAMAMATSU", SCExAO_status[0].nps2_7_co);
    printw(" | ");
    print_status("               ", SCExAO_status[0].nps2_8_co);
    printw("\n");
    printw("NPS2 ports 9-12 : ");
    print_status("               ", SCExAO_status_ext[0].nps2_9_co);
    printw(" | ");
    print_status("               ", SCExAO_status_ext[0].nps2_10_co);
    printw(" | ");
    print_status(" FIRST SCI CAM ", SCExAO_status_ext[0].nps2_11_co);
    printw(" | ");
    print_status(" TT MODULATOR  ", SCExAO_status_ext[0].nps2_12_co);
    printw("\n");
    printw("NPS2 ports 13-16: ");
    print_status("  OCAM POWER   ", SCExAO_status_ext[0].nps2_13_co);
    printw(" | ");
    print_status(" KIWIKIU POWER ", SCExAO_status_ext[0].nps2_14_co);
    printw(" | ");
    print_status(" SCExAO2 POWER ", SCExAO_status_ext[0].nps2_15_co);
    printw(" | ");
    print_status("VAMPIRES CAM 2 ", SCExAO_status_ext[0].nps2_16_co);
    printw("\n");
    // NPS3
    printw("NPS3 ports 1-4  : ");
    print_status("FIRST PHOTO CAM", SCExAO_status[0].nps3_1_co);
    printw(" | ");
    print_status("               ", SCExAO_status[0].nps3_2_co);
    printw(" | ");
    print_status("APAPANE C-RED1 ", SCExAO_status[0].nps3_3_co);
    printw(" | ");
    print_status("   15V POWER   ", SCExAO_status[0].nps3_4_co);
    printw("\n");
    printw("NPS3 ports 5-8  : ");
    print_status("  5/12V POWER  ", SCExAO_status[0].nps3_5_co);
    printw(" | ");
    print_status("   24V POWER   ", SCExAO_status[0].nps3_6_co);
    printw(" | ");
    print_status("               ", SCExAO_status[0].nps3_7_co);
    printw(" | ");
    print_status(" PALILA POWER  ", SCExAO_status[0].nps3_8_co);
    printw("\n");

    print_header(" CALIBRATION SOURCE ", '-');
    // Cal source
    printw("Cal source      : ");
    print_status(SCExAO_status[0].src_fib_st, SCExAO_status[0].src_fib_co);
    printw(" (x: %6.2f mm, y: %6.2f mm)\n", SCExAO_status[0].src_fib_x, SCExAO_status[0].src_fib_y);
    // Source type
    printw("Source type     : ");
    print_status(SCExAO_status[0].src_select_st, SCExAO_status[0].src_select_co);
    printw(" (t1: %6.2f deg, t2: %6.2f deg)\n", SCExAO_status[0].src_select_theta1, SCExAO_status[0].src_select_theta2);
    // SuperK status
    printw("Supercontinuum  : ");
    print_status(SCExAO_status[0].src_superk_st, SCExAO_status[0].src_superk_co);
    printw(" (p: %6d %)\n", SCExAO_status[0].src_superk_flux);
    // Source ND1
    printw("Source ND wheel1: ");
    print_status(SCExAO_status[0].src_flux_nd1, -1);
    printw("\n");
    // Source ND2
    printw("Source ND wheel2: ");
    print_status(SCExAO_status[0].src_flux_nd2, -1);
    printw("\n");
    // Source ND3
    printw("Source ND wheel3: ");
    print_status(SCExAO_status[0].src_flux_nd3, -1);
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
    printw(" (x: %6.2f mm)\n", SCExAO_status[0].dichroic);
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

    print_header(" BACK IR BENCH AND IRCAMS ", '-');
    // PG1 Pickoff
    printw("PG1 Pickoff     : ");
    print_status(SCExAO_status[0].PG1_pickoff, SCExAO_status[0].PG1_pickoff_co);
    printw("\n");
    // OAP4
    printw("OAP4            : ");
    print_status(SCExAO_status[0].oap4_st, SCExAO_status[0].oap4_co);
    printw(" (t: %6.2f deg, p: %6.2f deg)\n", SCExAO_status[0].oap4_theta, SCExAO_status[0].oap4_phi);
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
    printw(" (x: %6.2f mm , y: %6.2f mm)\n", SCExAO_status[0].ircam_pupil_x, SCExAO_status[0].ircam_pupil_y);
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
    printw(" (f1:%6d stp, f2:%6.2f mm)\n", SCExAO_status[0].ircam_fcs_f1, SCExAO_status[0].ircam_fcs_f2);
    // PALILA Pupil
    printw("PALILA Pupil    : ");
    print_status(SCExAO_status[0].palila_pup, SCExAO_status[0].palila_pup_co);
    printw("\n");
    // PALILA Pupil Focus
    printw("PALILA Pup Fcs  : ");
    print_status(SCExAO_status[0].palila_pup_fcs_st, SCExAO_status[0].palila_pup_fcs_co);
    printw(" (f: %6.2f mm)\n", SCExAO_status[0].palila_pup_fcs);
    // APAPANE Pickoff
    printw("'APAPANE Pickoff: ");
    print_status(SCExAO_status[0].apapane_pickoff_st, SCExAO_status[0].apapane_pickoff_co);
    printw(" (x: %6.2f mm)\n", SCExAO_status[0].apapane_pickoff);
    // KIWIKIU Block
    printw("KIWIKIU Block   : ");
    print_status(SCExAO_status[0].lowfs_block, SCExAO_status[0].lowfs_block_co);
    printw("\n");
    // KIWIKIU Focus
    printw("KIWIKIU Focus   : ");
    print_status(" ", -1);
    printw(" (f: %6d stp)\n", SCExAO_status[0].lowfs_fcs);

    print_header(" IR BENCH POLARIZATION ", '-');

    // Polarizer
    printw("Polarizer       : ");
    print_status(SCExAO_status[0].polarizer, SCExAO_status[0].polarizer_co);
    printw(" (t: %6.2f deg)\n", SCExAO_status[0].polarizer_theta);
    // Field stop
    printw("Field Stop      : ");
    print_status(SCExAO_status[0].field_stop_st, SCExAO_status[0].field_stop_co);
    printw(" (x: %6.2f mm , y: %6.2f mm)\n", SCExAO_status[0].field_stop_x, SCExAO_status[0].field_stop_y);
    // CHARIS Wollaston
    printw("CHARIS Wollaston: ");
    print_status(SCExAO_status[0].charis_wollaston, SCExAO_status[0].charis_wollaston_co);
    printw("\n");
    // FLC
    printw("IR Cam FLC      : ");
    print_status(SCExAO_status[0].ircam_flc_st, SCExAO_status[0].ircam_flc_co);
    printw(" (t: %6.2f deg)\n", SCExAO_status[0].ircam_flc);
    // IR Cams Wollaston
    printw("IR Cam Wollaston: ");
    print_status(SCExAO_status[0].ircam_wollaston, SCExAO_status[0].ircam_wollaston_co);
    printw("\n");

    print_header(" IR BENCH PHOTONICS ", '-');

    // Photonics Pickoff
    printw("Photonics PO    : ");
    print_status(SCExAO_status[0].photonics_pickoff_st, SCExAO_status[0].photonics_pickoff_co);
    printw(" (x: %6.2f mm)\n", SCExAO_status[0].photonics_pickoff);
    // Photonics Pickoff Type
    printw("Photonics PO typ: ");
    print_status(SCExAO_status[0].photonics_pickoff_type, SCExAO_status[0].photonics_pickoff_type_co);
    printw("\n");
    // Photonics Compensating Plate
    printw("Photonics Comppl: ");
    print_status(SCExAO_status[0].photonics_compplate, SCExAO_status[0].photonics_compplate_co);
    printw("\n");
    // FIber Injection Pickoff
    printw("Fib Inj Pickoff : ");
    print_status(SCExAO_status[0].fibinj_pickoff_st, SCExAO_status[0].fibinj_pickoff_co);
    printw(" (x: %6.2f mm)\n", SCExAO_status[0].fibinj_pickoff);
    // FIber Injection Lens
    printw("Fib Inj Lens    : ");
    print_status(SCExAO_status[0].fibinj_len_st, SCExAO_status[0].fibinj_len_co);
    printw(" (x: %6.2f mm)\n", SCExAO_status[0].fibinj_len);
    // Fiber Injection Fiber
    printw("Fib Inj Fiber   : ");
    print_status(SCExAO_status[0].fibinj_fib_st, SCExAO_status[0].fibinj_fib_co);
    printw(" (x: %6d stp, y: %6d stp, f: %6d stp)\n", SCExAO_status[0].fibinj_fib_x, SCExAO_status[0].fibinj_fib_y, SCExAO_status[0].fibinj_fib_f);
    // Fiber Injection Cariage
    printw("Fib Inj Cariage : ");
    print_status(" ", -1);
    printw(" ( %8d stp)\n", SCExAO_status[0].fibinj_car);
    // REACH Pickoff
    printw("REACH Pickoff   : ");
    print_status(SCExAO_status[0].reach_pickoff_st, SCExAO_status[0].reach_pickoff_co);
    printw(" (x: %6.2f mm)\n", SCExAO_status[0].reach_pickoff);
    // REACH OAP
    printw("REACH OAP       : ");
    print_status(SCExAO_status[0].reach_oap_st, SCExAO_status[0].reach_oap_co);
    printw(" (t: %6.2f deg, p: %6.2f deg)\n", SCExAO_status[0].reach_oap_theta, SCExAO_status[0].reach_oap_phi);
    // REACH Fiber
    printw("REACH Fiber     : ");
    print_status(SCExAO_status[0].reach_fib_st, SCExAO_status[0].reach_fib_co);
    printw(" (x: %6d stp, y: %6d stp, f: %6d stp)\n", SCExAO_status[0].reach_fib_x, SCExAO_status[0].reach_fib_y, SCExAO_status[0].reach_fib_f);
    // IR Spectrometer Mode
    printw("IR Spectro Mode : ");
    print_status(SCExAO_status[0].irspectro_mode_st, SCExAO_status[0].irspectro_mode_co);
    printw(" (x1: %6d stp, x2:%6.2f mm)\n", SCExAO_status[0].irspectro_mode_x1, SCExAO_status[0].irspectro_mode_x2);
    // IR Spectrometer Collimator
    printw("IR Spectro Col  : ");
    print_status(SCExAO_status[0].irspectro_col_st, SCExAO_status[0].irspectro_col_co);
    printw(" (x: %6.2f mm)\n", SCExAO_status[0].irspectro_col);
    // IR Spectrometer Fiber
    printw("IR SPectro Fiber: ");
    print_status(SCExAO_status[0].irspectro_fib_st, SCExAO_status[0].irspectro_fib_co);
    printw(" (x: %6.2f mm, y: %6.2f mm)\n", SCExAO_status[0].irspectro_fib_x, SCExAO_status[0].irspectro_fib_y);
    

    print_header(" VISIBLE BENCH ", '-');

    // PyWFS Pickoff
    printw("PyWFS Pickoff   : ");
    print_status(SCExAO_status[0].pywfs_pickoff_st, SCExAO_status[0].pywfs_pickoff_co);
    printw(" (w: %6.2f deg)\n", SCExAO_status[0].pywfs_pickoff);
    // PyWFS Field stop
    printw("PyWFS Field Stop: ");
    print_status(SCExAO_status[0].pywfs_fieldstop_st, SCExAO_status[0].pywfs_fieldstop_co);
    printw(" (x: %6.2f mm, y: %6.2f mm)\n", SCExAO_status[0].pywfs_fieldstop_x, SCExAO_status[0].pywfs_fieldstop_y);
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
    // PyWFS Focus Pickoff
    printw("PyWFS Fcs pckoff: ");
    print_status(SCExAO_status[0].pywfs_fcs_pickoff, SCExAO_status[0].pywfs_fcs_pickoff_co);
    printw("\n");
    // PyWFS Pupil Lens
    printw("PyWFS Pupil Lens: ");
    print_status(" ", -1);
    printw(" (x: %6d stp, y: %6d stp)\n", SCExAO_status[0].pywfs_pup_x, SCExAO_status[0].pywfs_pup_y);
    // VAMPIRES Field stop
    printw("VAMP Field Stop : ");
    print_status(SCExAO_status[0].vampires_fieldstop_st, SCExAO_status[0].vampires_fieldstop_co);
    printw(" (x: %6.2f mm, y: %6.2f mm, f: %6.2f mm)\n", SCExAO_status[0].vampires_fieldstop_x, SCExAO_status[0].vampires_fieldstop_y, SCExAO_status[0].vampires_fieldstop_f);
    // FIRST PIckoff
    printw("FIRST Pickoff   : ");
    print_status(SCExAO_status[0].first_pickoff_st, SCExAO_status[0].first_pickoff_co);
    printw(" (x: %6.2f mm)\n", SCExAO_status[0].first_pickoff);
    // FIRST PL PIckoff
    printw("VIS PL Pickoff  : ");
    print_status(SCExAO_status[0].firstpl_pickoff_st, SCExAO_status[0].firstpl_pickoff_co);
    printw(" (w: %6.2f deg)\n", SCExAO_status[0].firstpl_pickoff);
    // FIRST injection
    printw("FIRST Injection : ");
    print_status(SCExAO_status[0].first_inj_st, SCExAO_status[0].first_inj_co);
    printw(" (x: %6d stp, y: %6d stp, f: %6.2f mm)\n", SCExAO_status[0].first_inj_x, SCExAO_status[0].first_inj_y, SCExAO_status[0].first_inj_f);
    // FIRST Calibration source
    // printw("FIRST Cal Source: ");
    // print_status(SCExAO_status[0].first_src_st, SCExAO_status[0].first_src_co);
    // printw(" (x: %6.2f mm , y: %6.2f mm )\n", SCExAO_status[0].first_src_x, SCExAO_status[0].first_src_y);
    // FIRST Photometry
    printw("FIRST Photometry: ");
    print_status(SCExAO_status[0].first_photometry_st, SCExAO_status[0].first_photometry_co);
    printw(" (x: %6.2f mm)\n", SCExAO_status[0].first_photometry);

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

    //print_header(" LOWFS LOOP STATUS ", '-');

    // lowfs
    //printw("LOWFS loop status          : ");
    //print_status(SCExAO_status[0].lowfs_loop, SCExAO_status[0].lowfs_loop_co);
    //printw(" | ");
    //printw("LOWFS loop frequency       : ");
    //print_status_i(SCExAO_status[0].lowfs_freq, "Hz ", -1);
    //printw("\n");
    //printw("LOWFS mode type            : ");
    //print_status(SCExAO_status[0].lowfs_mtype, -1);
    //printw(" | ");
    //printw("LOWFS loop gain            : ");
    //print_status_f(SCExAO_status[0].lowfs_gain, "", -1);
    //printw("\n");
    //printw("LOWFS number of modes      : ");
    //print_status_i(SCExAO_status[0].lowfs_nmodes, "", -1);
    //printw(" | ");
    //printw("LOWFS loop leak            : ");
    //print_status_f(SCExAO_status[0].lowfs_leak, "", -1);
    //printw("\n");

    //print_header(" SPECKLE NULLING LOOP STATUS ", '-');

    // speckle nulling
    //printw("Speckle Nulling loop status: ");
    //print_status(SCExAO_status[0].sn_loop, SCExAO_status[0].sn_loop_co);
    //printw(" | ");
    //printw("Speckle Nulling loop freq. : ");
    //print_status_i(SCExAO_status[0].sn_freq, "Hz ", -1);
    //printw("\n");
    //printw("Speckle Nulling loop gain  : ");
    //print_status_f(SCExAO_status[0].sn_gain, "", -1);
    //printw(" | ");
    //printw("\n");
    
    //print_header(" ZAP LOOP STATUS ", '-');

    // zap
    //printw("ZAP loop status            : ");
    //print_status(SCExAO_status[0].zap_loop, SCExAO_status[0].zap_loop_co);
    //printw(" | ");
    //printw("ZAP loop frequency         : ");
    //print_status_i(SCExAO_status[0].zap_freq, "Hz ", -1);
    //printw("\n");
    //printw("ZAP mode type              : ");
    //print_status(SCExAO_status[0].zap_mtype, -1);
    //printw(" | ");
    //printw("ZAP loop gain              : ");
    //print_status_f(SCExAO_status[0].zap_gain, "", -1);
    //printw("\n");
    //printw("ZAP number of modes        : ");
    //print_status_i(SCExAO_status[0].zap_nmodes, "", -1);
    //printw(" | ");
    //printw("\n");

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

    // PALILA log
    printw("Logging PALILA images      : ");
    print_status(SCExAO_status[0].logpalila, SCExAO_status[0].logpalila_co);
    printw(" | ");
    // PALILA dark
    printw("Acquiring PALILA darks     : ");
    print_status(SCExAO_status[0].darkpalila, SCExAO_status[0].darkpalila_co);
    printw("\n");
    // APAPANE log
    printw("Logging 'APAPANE images    : ");
    print_status(SCExAO_status_ext[0].logapapane, SCExAO_status_ext[0].logapapane_co);
    printw(" | ");
    // Hotspotalign
    printw("Aligning PSF on the hotspot: ");
    print_status(SCExAO_status[0].hotspot, SCExAO_status[0].hotspot_co);
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
  sprintf(SME_fname, "%s/SCExAO_status_ext.shm", SHAREDMEMDIR);

  if (argc == 1)
  {
    printf("\n");
    printf("OPTIONS :\n");
    printf("   %s create:\n", argv[0]);
    printf("      create shared memory (run every time the structure has changed)\n");
    printf("   %s set <variable> <value> <value>:\n", argv[0]);
    printf("      Set variable, value is optional \n");
    printf("   %s disp:\n", argv[0]);
    printf("      Display variables\n");
    printf("   value code (xterm):\n");
    printf("      -1:WHITE 0:RED 1:GREEN 2:BLUE 3:ORANGE 4:BLACK \n");
    printf("\n");
    exit(0);
  }

  cmdOK = 0;

  char *command = argv[1];
  char *status_item = argv[2];
  char *value = "0";
  if (argc >= 4)
    value = argv[3];
  char *color = "-1";
  if (argc >= 5)
    color = argv[4];

  if (strcmp(command, "create") == 0)
  {
    printf("create status shared memory structure (legacy and extension)\n");
    create_status_shm();
    cmdOK = 1;
  }
  else if (strcmp(command, "create_ext") == 0)
  {
    printf("create status shared memory structure (extension only)\n");
    create_extended_status_shm();
    cmdOK = 1;
  }
  else if (strcmp(command, "set") == 0)
  {
    read_status_shm();
    cmdOK = 1;
    // NPS1
    if (strcmp(status_item, "nps1_1") == 0)
    {
      SCExAO_status[0].nps1_1_co = atoi(color);
    }
    else if (strcmp(status_item, "nps1_2") == 0)
    {
      SCExAO_status[0].nps1_2_co = atoi(color);
    }
    else if (strcmp(status_item, "nps1_3") == 0)
    {
      SCExAO_status[0].nps1_3_co = atoi(color);
    }
    else if (strcmp(status_item, "nps1_4") == 0)
    {
      SCExAO_status[0].nps1_4_co = atoi(color);
    }
    else if (strcmp(status_item, "nps1_5") == 0)
    {
      SCExAO_status[0].nps1_5_co = atoi(color);
    }
    else if (strcmp(status_item, "nps1_6") == 0)
    {
      SCExAO_status[0].nps1_6_co = atoi(color);
    }
    else if (strcmp(status_item, "nps1_7") == 0)
    {
      SCExAO_status[0].nps1_7_co = atoi(color);
    }
    else if (strcmp(status_item, "nps1_8") == 0)
    {
      SCExAO_status[0].nps1_8_co = atoi(color);
    }
    // NPS2
    else if (strcmp(status_item, "nps2_1") == 0)
    {
      SCExAO_status[0].nps2_1_co = atoi(color);
    }
    else if (strcmp(status_item, "nps2_2") == 0)
    {
      SCExAO_status[0].nps2_2_co = atoi(color);
    }
    else if (strcmp(status_item, "nps2_3") == 0)
    {
      SCExAO_status[0].nps2_3_co = atoi(color);
    }
    else if (strcmp(status_item, "nps2_4") == 0)
    {
      SCExAO_status[0].nps2_4_co = atoi(color);
    }
    else if (strcmp(status_item, "nps2_5") == 0)
    {
      SCExAO_status[0].nps2_5_co = atoi(color);
    }
    else if (strcmp(status_item, "nps2_6") == 0)
    {
      SCExAO_status[0].nps2_6_co = atoi(color);
    }
    else if (strcmp(status_item, "nps2_7") == 0)
    {
      SCExAO_status[0].nps2_7_co = atoi(color);
    }
    else if (strcmp(status_item, "nps2_8") == 0)
    {
      SCExAO_status[0].nps2_8_co = atoi(color);
    }
    // NPS2 EXTENSION (new 16 port)
    else if (strcmp(status_item, "nps2_9") == 0)
    {
      SCExAO_status_ext[0].nps2_9_co = atoi(color);
    }
    else if (strcmp(status_item, "nps2_10") == 0)
    {
      SCExAO_status_ext[0].nps2_10_co = atoi(color);
    }
    else if (strcmp(status_item, "nps2_11") == 0)
    {
      SCExAO_status_ext[0].nps2_11_co = atoi(color);
    }
    else if (strcmp(status_item, "nps2_12") == 0)
    {
      SCExAO_status_ext[0].nps2_12_co = atoi(color);
    }
    else if (strcmp(status_item, "nps2_13") == 0)
    {
      SCExAO_status_ext[0].nps2_13_co = atoi(color);
    }
    else if (strcmp(status_item, "nps2_14") == 0)
    {
      SCExAO_status_ext[0].nps2_14_co = atoi(color);
    }
    else if (strcmp(status_item, "nps2_15") == 0)
    {
      SCExAO_status_ext[0].nps2_15_co = atoi(color);
    }
    else if (strcmp(status_item, "nps2_16") == 0)
    {
      SCExAO_status_ext[0].nps2_16_co = atoi(color);
    }
    // NPS3
    else if (strcmp(status_item, "nps3_1") == 0)
    {
      SCExAO_status[0].nps3_1_co = atoi(color);
    }
    else if (strcmp(status_item, "nps3_2") == 0)
    {
      SCExAO_status[0].nps3_2_co = atoi(color);
    }
    else if (strcmp(status_item, "nps3_3") == 0)
    {
      SCExAO_status[0].nps3_3_co = atoi(color);
    }
    else if (strcmp(status_item, "nps3_4") == 0)
    {
      SCExAO_status[0].nps3_4_co = atoi(color);
    }
    else if (strcmp(status_item, "nps3_5") == 0)
    {
      SCExAO_status[0].nps3_5_co = atoi(color);
    }
    else if (strcmp(status_item, "nps3_6") == 0)
    {
      SCExAO_status[0].nps3_6_co = atoi(color);
    }
    else if (strcmp(status_item, "nps3_7") == 0)
    {
      SCExAO_status[0].nps3_7_co = atoi(color);
    }
    else if (strcmp(status_item, "nps3_8") == 0)
    {
      SCExAO_status[0].nps3_8_co = atoi(color);
    }
    // cal source
    else if (strcmp(status_item, "src_fib_st") == 0)
    {
      strncpy(SCExAO_status[0].src_fib_st, value, 15);
      SCExAO_status[0].src_fib_co = atoi(color);
    }
    else if (strcmp(status_item, "src_fib_x") == 0)
    {
      SCExAO_status[0].src_fib_x = atof(value);
    }
    else if (strcmp(status_item, "src_fib_y") == 0)
    {
      SCExAO_status[0].src_fib_y = atof(value);
    }
    else if (strcmp(status_item, "src_select_st") == 0)
    {
      strncpy(SCExAO_status[0].src_select_st, value, 15);
      SCExAO_status[0].src_select_co = atoi(color);
    }
    else if (strcmp(status_item, "src_select_theta1") == 0)
    {
      SCExAO_status[0].src_select_theta1 = atof(value);
    }
    else if (strcmp(status_item, "src_select_theta2") == 0)
    {
      SCExAO_status[0].src_select_theta2 = atof(value);
    }
    else if (strcmp(status_item, "src_superk_st") == 0)
    {
      strncpy(SCExAO_status[0].src_superk_st, value, 15);
      SCExAO_status[0].src_superk_co = atoi(color);
    }
    else if (strcmp(status_item, "src_superk_flux") == 0)
    {
      SCExAO_status[0].src_superk_flux = atoi(value);
    }
    else if (strcmp(status_item, "src_flux_nd1") == 0)
    {
      strncpy(SCExAO_status[0].src_flux_nd1, value, 15);
    }
    else if (strcmp(status_item, "src_flux_nd2") == 0)
    {
      strncpy(SCExAO_status[0].src_flux_nd2, value, 15);
    }
    else if (strcmp(status_item, "src_flux_nd3") == 0)
    {
      strncpy(SCExAO_status[0].src_flux_nd3, value, 15);
    }
    else if (strcmp(status_item, "src_flux_filter") == 0)
    {
      strncpy(SCExAO_status[0].src_flux_filter, value, 15);
    }
    // oap1
    else if (strcmp(status_item, "oap1_st") == 0)
    {
      strncpy(SCExAO_status[0].oap1_st, value, 15);
      SCExAO_status[0].oap1_co = atoi(color);
    }
    else if (strcmp(status_item, "oap1_theta") == 0)
    {
      SCExAO_status[0].oap1_theta = atof(value);
    }
    else if (strcmp(status_item, "oap1_phi") == 0)
    {
      SCExAO_status[0].oap1_phi = atof(value);
    }
    else if (strcmp(status_item, "oap1_f") == 0)
    {
      SCExAO_status[0].oap1_f = atoi(value);
    }
    // integrating sphere
    else if (strcmp(status_item, "intsphere") == 0)
    {
      strncpy(SCExAO_status[0].intsphere, value, 15);
      SCExAO_status[0].intsphere_co = atoi(color);
    }
    // polarizer
    else if (strcmp(status_item, "polarizer") == 0)
    {
      strncpy(SCExAO_status[0].polarizer, value, 15);
      SCExAO_status[0].polarizer_co = atoi(color);
    }
    else if (strcmp(status_item, "polarizer_theta") == 0)
    {
      SCExAO_status[0].polarizer_theta = atof(value);
    }
    // dichroic
    else if (strcmp(status_item, "dichroic_st") == 0)
    {
      strncpy(SCExAO_status[0].dichroic_st, value, 15);
      SCExAO_status[0].dichroic_co = atoi(color);
    }
    else if (strcmp(status_item, "dichroic") == 0)
    {
      SCExAO_status[0].dichroic = atof(value);
    }
    // pupil
    else if (strcmp(status_item, "pupil_st") == 0)
    {
      strncpy(SCExAO_status[0].pupil_st, value, 15);
      SCExAO_status[0].pupil_co = atoi(color);
    }
    else if (strcmp(status_item, "pupil_wheel") == 0)
    {
      SCExAO_status[0].pupil_wheel = atof(value);
    }
    else if (strcmp(status_item, "pupil_x") == 0)
    {
      SCExAO_status[0].pupil_x = atoi(value);
    }
    else if (strcmp(status_item, "pupil_y") == 0)
    {
      SCExAO_status[0].pupil_y = atoi(value);
    }
    // Compensating plate
    else if (strcmp(status_item, "compplate") == 0)
    {
      strncpy(SCExAO_status[0].compplate, value, 15);
      SCExAO_status[0].compplate_co = atoi(color);
    }
    // piaa1
    else if (strcmp(status_item, "piaa1_st") == 0)
    {
      strncpy(SCExAO_status[0].piaa1_st, value, 15);
      SCExAO_status[0].piaa1_co = atoi(color);
    }
    else if (strcmp(status_item, "piaa1_wheel") == 0)
    {
      SCExAO_status[0].piaa1_wheel = atof(value);
    }
    else if (strcmp(status_item, "piaa1_x") == 0)
    {
      SCExAO_status[0].piaa1_x = atoi(value);
    }
    else if (strcmp(status_item, "piaa1_y") == 0)
    {
      SCExAO_status[0].piaa1_y = atoi(value);
    }
    // piaa2
    else if (strcmp(status_item, "piaa2_st") == 0)
    {
      strncpy(SCExAO_status[0].piaa2_st, value, 15);
      SCExAO_status[0].piaa2_co = atoi(color);
    }
    else if (strcmp(status_item, "piaa2_wheel") == 0)
    {
      SCExAO_status[0].piaa2_wheel = atof(value);
    }
    else if (strcmp(status_item, "piaa2_x") == 0)
    {
      SCExAO_status[0].piaa2_x = atoi(value);
    }
    else if (strcmp(status_item, "piaa2_y") == 0)
    {
      SCExAO_status[0].piaa2_y = atoi(value);
    }
    else if (strcmp(status_item, "piaa2_f") == 0)
    {
      SCExAO_status[0].piaa2_f = atoi(value);
    }
    // Photonics
    else if (strcmp(status_item, "photonics_pickoff_st") == 0)
    {
      strncpy(SCExAO_status[0].photonics_pickoff_st, value, 15);
      SCExAO_status[0].photonics_pickoff_co = atoi(color);
    }
    else if (strcmp(status_item, "photonics_pickoff") == 0)
    {
      SCExAO_status[0].photonics_pickoff = atof(value);
    }
    else if (strcmp(status_item, "photonics_pickoff_type") == 0)
    {
      strncpy(SCExAO_status[0].photonics_pickoff_type, value, 15);
      SCExAO_status[0].photonics_pickoff_type_co = atoi(color);
    }
    else if (strcmp(status_item, "photonics_compplate") == 0)
    {
      strncpy(SCExAO_status[0].photonics_compplate, value, 15);
      SCExAO_status[0].photonics_compplate_co = atoi(color);
    }
    // PG1
    else if (strcmp(status_item, "PG1_pickoff") == 0)
    {
      strncpy(SCExAO_status[0].PG1_pickoff, value, 15);
      SCExAO_status[0].PG1_pickoff_co = atoi(color);
    }
    // fpm
    else if (strcmp(status_item, "fpm_st") == 0)
    {
      strncpy(SCExAO_status[0].fpm_st, value, 15);
      SCExAO_status[0].fpm_co = atoi(color);
    }
    else if (strcmp(status_item, "fpm_wheel") == 0)
    {
      SCExAO_status[0].fpm_wheel = atof(value);
    }
    else if (strcmp(status_item, "fpm_x") == 0)
    {
      SCExAO_status[0].fpm_x = atoi(value);
    }
    else if (strcmp(status_item, "fpm_y") == 0)
    {
      SCExAO_status[0].fpm_y = atoi(value);
    }
    else if (strcmp(status_item, "fpm_f") == 0)
    {
      SCExAO_status[0].fpm_f = atoi(value);
    }
    // lyot
    else if (strcmp(status_item, "lyot_st") == 0)
    {
      strncpy(SCExAO_status[0].lyot_st, value, 15);
      SCExAO_status[0].lyot_co = atoi(color);
    }
    else if (strcmp(status_item, "lyot_wheel") == 0)
    {
      SCExAO_status[0].lyot_wheel = atof(value);
    }
    else if (strcmp(status_item, "lyot_x") == 0)
    {
      SCExAO_status[0].lyot_x = atoi(value);
    }
    else if (strcmp(status_item, "lyot_y") == 0)
    {
      SCExAO_status[0].lyot_y = atoi(value);
    }
    // oap4
    else if (strcmp(status_item, "oap4_st") == 0)
    {
      strncpy(SCExAO_status[0].oap4_st, value, 15);
      SCExAO_status[0].oap4_co = atoi(color);
    }
    else if (strcmp(status_item, "oap4_theta") == 0)
    {
      SCExAO_status[0].oap4_theta = atof(value);
    }
    else if (strcmp(status_item, "oap4_phi") == 0)
    {
      SCExAO_status[0].oap4_phi = atof(value);
    }
    // steering mirror
    else if (strcmp(status_item, "steering_st") == 0)
    {
      strncpy(SCExAO_status[0].steering_st, value, 15);
      SCExAO_status[0].steering_co = atoi(color);
    }
    else if (strcmp(status_item, "steering_theta") == 0)
    {
      SCExAO_status[0].steering_theta = atof(value);
    }
    else if (strcmp(status_item, "steering_phi") == 0)
    {
      SCExAO_status[0].steering_phi = atof(value);
    }
    // charis
    else if (strcmp(status_item, "charis_pickoff_st") == 0)
    {
      strncpy(SCExAO_status[0].charis_pickoff_st, value, 15);
      SCExAO_status[0].charis_pickoff_co = atoi(color);
    }
    else if (strcmp(status_item, "charis_pickoff_wheel") == 0)
    {
      SCExAO_status[0].charis_pickoff_wheel = atof(value);
    }
    else if (strcmp(status_item, "charis_pickoff_theta") == 0)
    {
      SCExAO_status[0].charis_pickoff_theta = atof(value);
    }
    // mkids
    else if (strcmp(status_item, "mkids_pickoff_st") == 0)
    {
      strncpy(SCExAO_status[0].mkids_pickoff_st, value, 15);
      SCExAO_status[0].mkids_pickoff_co = atoi(color);
    }
    else if (strcmp(status_item, "mkids_pickoff_wheel") == 0)
    {
      SCExAO_status[0].mkids_pickoff_wheel = atof(value);
    }
    else if (strcmp(status_item, "mkids_pickoff_theta") == 0)
    {
      SCExAO_status[0].mkids_pickoff_theta = atof(value);
    }
    // ircams common
    else if (strcmp(status_item, "ircam_filter") == 0)
    {
      strncpy(SCExAO_status[0].ircam_filter, value, 15);
      SCExAO_status[0].ircam_filter_co = atoi(color);
    }
    else if (strcmp(status_item, "ircam_block") == 0)
    {
      strncpy(SCExAO_status[0].ircam_block, value, 15);
      SCExAO_status[0].ircam_block_co = atoi(color);
    }
    else if (strcmp(status_item, "ircam_fcs_st") == 0)
    {
      strncpy(SCExAO_status[0].ircam_fcs_st, value, 15);
      SCExAO_status[0].ircam_fcs_co = atoi(color);
    }
    else if (strcmp(status_item, "ircam_fcs_f1") == 0)
    {
      SCExAO_status[0].ircam_fcs_f1 = atoi(value);
    }
    else if (strcmp(status_item, "ircam_fcs_f2") == 0)
    {
      SCExAO_status[0].ircam_fcs_f2 = atof(value);
    }
    // Polarization
    else if (strcmp(status_item, "field_stop_st") == 0)
    {
      strncpy(SCExAO_status[0].field_stop_st, value, 15);
      SCExAO_status[0].field_stop_co = atoi(color);
    }
    else if (strcmp(status_item, "field_stop_x") == 0)
    {
      SCExAO_status[0].field_stop_x = atof(value);
    }
    else if (strcmp(status_item, "field_stop_y") == 0)
    {
      SCExAO_status[0].field_stop_y = atof(value);
    }
    else if (strcmp(status_item, "charis_wollaston") == 0)
    {
      strncpy(SCExAO_status[0].charis_wollaston, value, 15);
      SCExAO_status[0].charis_wollaston_co = atoi(color);
    }
    else if (strcmp(status_item, "ircam_wollaston") == 0)
    {
      strncpy(SCExAO_status[0].ircam_wollaston, value, 15);
      SCExAO_status[0].ircam_wollaston_co = atoi(color);
    }
    else if (strcmp(status_item, "ircam_flc_st") == 0)
    {
      strncpy(SCExAO_status[0].ircam_flc_st, value, 15);
      SCExAO_status[0].ircam_flc_co = atoi(color);
    }
    else if (strcmp(status_item, "ircam_flc") == 0)
    {
      SCExAO_status[0].ircam_flc = atof(value);
    }
    else if (strcmp(status_item, "ircam_pupil_st") == 0)
    {
      strncpy(SCExAO_status[0].ircam_pupil_st, value, 15);
      SCExAO_status[0].ircam_pupil_co = atoi(color);
    }
    else if (strcmp(status_item, "ircam_pupil_x") == 0)
    {
      SCExAO_status[0].ircam_pupil_x = atof(value);
    }
    else if (strcmp(status_item, "ircam_pupil_y") == 0)
    {
      SCExAO_status[0].ircam_pupil_y = atof(value);
    }
    // REACH
    else if (strcmp(status_item, "reach_pickoff_st") == 0)
    {
      strncpy(SCExAO_status[0].reach_pickoff_st, value, 15);
      SCExAO_status[0].reach_pickoff_co = atoi(color);
    }
    else if (strcmp(status_item, "reach_pickoff") == 0)
    {
      SCExAO_status[0].reach_pickoff = atof(value);
    }
    else if (strcmp(status_item, "reach_oap_st") == 0)
    {
      strncpy(SCExAO_status[0].reach_oap_st, value, 15);
      SCExAO_status[0].reach_oap_co = atoi(color);
    }
    else if (strcmp(status_item, "reach_oap_theta") == 0)
    {
      SCExAO_status[0].reach_oap_theta = atof(value);
    }
    else if (strcmp(status_item, "reach_oap_phi") == 0)
    {
      SCExAO_status[0].reach_oap_phi = atof(value);
    }
    else if (strcmp(status_item, "reach_fib_st") == 0)
    {
      strncpy(SCExAO_status[0].reach_fib_st, value, 15);
      SCExAO_status[0].reach_fib_co = atoi(color);
    }
    else if (strcmp(status_item, "reach_fib_x") == 0)
    {
      SCExAO_status[0].reach_fib_x = atoi(value);
    }
    else if (strcmp(status_item, "reach_fib_y") == 0)
    {
      SCExAO_status[0].reach_fib_y = atoi(value);
    }
    else if (strcmp(status_item, "reach_fib_f") == 0)
    {
      SCExAO_status[0].reach_fib_f = atof(value);
    }
    // APAPANE pickoff
    else if (strcmp(status_item, "apapane_pickoff_st") == 0)
    {
      strncpy(SCExAO_status[0].apapane_pickoff_st, value, 15);
      SCExAO_status[0].apapane_pickoff_co = atoi(color);
    }
    else if (strcmp(status_item, "apapane_pickoff") == 0)
    {
      SCExAO_status[0].apapane_pickoff = atof(value);
    }
    else if (strcmp(status_item, "palila_pup") == 0)
    {
      strncpy(SCExAO_status[0].palila_pup, value, 15);
      SCExAO_status[0].palila_pup_co = atoi(color);
    }
    else if (strcmp(status_item, "palila_pup_fcs_st") == 0)
    {
      strncpy(SCExAO_status[0].palila_pup_fcs_st, value, 15);
      SCExAO_status[0].palila_pup_fcs_co = atoi(color);
    }
    else if (strcmp(status_item, "palila_pup_fcs") == 0)
    {
      SCExAO_status[0].palila_pup_fcs = atof(value);
    }
    else if (strcmp(status_item, "irspectro_mode_st") == 0)
    {
      strncpy(SCExAO_status[0].irspectro_mode_st, value, 15);
      SCExAO_status[0].irspectro_mode_co = atoi(color);
    }
    else if (strcmp(status_item, "irspectro_mode_x1") == 0)
    {
      SCExAO_status[0].irspectro_mode_x1 = atoi(value);
    }
    else if (strcmp(status_item, "irspectro_mode_x2") == 0)
    {
      SCExAO_status[0].irspectro_mode_x2 = atof(value);
    }
    else if (strcmp(status_item, "irspectro_col_st") == 0)
    {
      strncpy(SCExAO_status[0].irspectro_col_st, value, 15);
      SCExAO_status[0].irspectro_col_co = atoi(color);
    }
    else if (strcmp(status_item, "irspectro_col") == 0)
    {
      SCExAO_status[0].irspectro_col = atof(value);
    }
    else if (strcmp(status_item, "irspectro_fib_st") == 0)
    {
      strncpy(SCExAO_status[0].irspectro_fib_st, value, 15);
      SCExAO_status[0].irspectro_fib_co = atoi(color);
    }
    else if (strcmp(status_item, "irspectro_fib_x") == 0)
    {
      SCExAO_status[0].irspectro_fib_x = atof(value);
    }
    else if (strcmp(status_item, "irspectro_fib_y") == 0)
    {
      SCExAO_status[0].irspectro_fib_y = atof(value);
    }
    
    // KIWIKIU
    else if (strcmp(status_item, "lowfs_block") == 0)
    {
      strncpy(SCExAO_status[0].lowfs_block, value, 15);
      SCExAO_status[0].lowfs_block_co = atoi(color);
    }
    else if (strcmp(status_item, "lowfs_fcs") == 0)
    {
      SCExAO_status[0].lowfs_fcs = atoi(value);
    }
    // fiber injection
    else if (strcmp(status_item, "fibinj_pickoff_st") == 0)
    {
      strncpy(SCExAO_status[0].fibinj_pickoff_st, value, 15);
      SCExAO_status[0].fibinj_pickoff_co = atoi(color);
    }
    else if (strcmp(status_item, "fibinj_pickoff") == 0)
    {
      SCExAO_status[0].fibinj_pickoff = atof(value);
    }
    else if (strcmp(status_item, "fibinj_len_st") == 0)
    {
      strncpy(SCExAO_status[0].fibinj_len_st, value, 15);
      SCExAO_status[0].fibinj_len_co = atoi(color);
    }
    else if (strcmp(status_item, "fibinj_len") == 0)
    {
      SCExAO_status[0].fibinj_len = atof(value);
    }
    else if (strcmp(status_item, "fibinj_fib_st") == 0)
    {
      strncpy(SCExAO_status[0].fibinj_fib_st, value, 15);
      SCExAO_status[0].fibinj_fib_co = atoi(color);
    }
    else if (strcmp(status_item, "fibinj_fib_x") == 0)
    {
      SCExAO_status[0].fibinj_fib_x = atoi(value);
    }
    else if (strcmp(status_item, "fibinj_fib_y") == 0)
    {
      SCExAO_status[0].fibinj_fib_y = atoi(value);
    }
    else if (strcmp(status_item, "fibinj_fib_f") == 0)
    {
      SCExAO_status[0].fibinj_fib_f = atoi(value);
    }
    else if (strcmp(status_item, "fibinj_car") == 0)
    {
      SCExAO_status[0].fibinj_car = atoi(value);
    }
    // pywfs
    else if (strcmp(status_item, "pywfs_pickoff_st") == 0)
    {
      strncpy(SCExAO_status[0].pywfs_pickoff_st, value, 15);
      SCExAO_status[0].pywfs_pickoff_co = atoi(color);
    }
    else if (strcmp(status_item, "pywfs_pickoff") == 0)
    {
      SCExAO_status[0].pywfs_pickoff = atof(value);
    }
    else if (strcmp(status_item, "pywfs_fieldstop_st") == 0)
    {
      strncpy(SCExAO_status[0].pywfs_fieldstop_st, value, 15);
      SCExAO_status[0].pywfs_fieldstop_co = atoi(color);
    }
    else if (strcmp(status_item, "pywfs_fieldstop_x") == 0)
    {
      SCExAO_status[0].pywfs_fieldstop_x = atof(value);
    }
    else if (strcmp(status_item, "pywfs_fieldstop_y") == 0)
    {
      SCExAO_status[0].pywfs_fieldstop_y = atof(value);
    }
    else if (strcmp(status_item, "pywfs_filter") == 0)
    {
      strncpy(SCExAO_status[0].pywfs_filter, value, 15);
      SCExAO_status[0].pywfs_filter_co = atoi(color);
    }
    else if (strcmp(status_item, "pywfs_col") == 0)
    {
      SCExAO_status[0].pywfs_col = atoi(value);
    }
    else if (strcmp(status_item, "pywfs_fcs") == 0)
    {
      SCExAO_status[0].pywfs_fcs = atoi(value);
    }
    else if (strcmp(status_item, "pywfs_fcs_pickoff") == 0)
    {
      strncpy(SCExAO_status[0].pywfs_fcs_pickoff, value, 15);
      SCExAO_status[0].pywfs_fcs_pickoff_co = atoi(color);
    }
    else if (strcmp(status_item, "pywfs_pup_x") == 0)
    {
      SCExAO_status[0].pywfs_pup_x = atoi(value);
    }
    else if (strcmp(status_item, "pywfs_pup_y") == 0)
    {
      SCExAO_status[0].pywfs_pup_y = atoi(value);
    }
    // vampires
    else if (strcmp(status_item, "vampires_fieldstop_st") == 0)
    {
      strncpy(SCExAO_status[0].vampires_fieldstop_st, value, 15);
      SCExAO_status[0].vampires_fieldstop_co = atoi(color);
    }
    else if (strcmp(status_item, "vampires_fieldstop_x") == 0)
    {
      SCExAO_status[0].vampires_fieldstop_x = atof(value);
    }
    else if (strcmp(status_item, "vampires_fieldstop_y") == 0)
    {
      SCExAO_status[0].vampires_fieldstop_y = atof(value);
    }
    else if (strcmp(status_item, "vampires_fieldstop_f") == 0)
    {
      SCExAO_status[0].vampires_fieldstop_f = atof(value);
    }
    // first
    else if (strcmp(status_item, "first_pickoff_st") == 0)
    {
      strncpy(SCExAO_status[0].first_pickoff_st, value, 15);
      SCExAO_status[0].first_pickoff_co = atoi(color);
    }
    else if (strcmp(status_item, "first_pickoff") == 0)
    {
      SCExAO_status[0].first_pickoff = atof(value);
    }
    else if (strcmp(status_item, "first_inj_st") == 0)
    {
      strncpy(SCExAO_status[0].first_inj_st, value, 15);
      SCExAO_status[0].first_inj_co = atoi(color);
    }
    else if (strcmp(status_item, "first_inj_x") == 0)
    {
      SCExAO_status[0].first_inj_x = atoi(value);
    }
    else if (strcmp(status_item, "first_inj_y") == 0)
    {
      SCExAO_status[0].first_inj_y = atoi(value);
    }
    else if (strcmp(status_item, "first_inj_f") == 0)
    {
      SCExAO_status[0].first_inj_f = atof(value);
    }
    else if (strcmp(status_item, "first_src_st") == 0)
    {
      strncpy(SCExAO_status[0].first_src_st, value, 15);
      SCExAO_status[0].first_src_co = atoi(color);
    }
    else if (strcmp(status_item, "first_src_x") == 0)
    {
      SCExAO_status[0].first_src_x = atof(value);
    }
    else if (strcmp(status_item, "first_src_y") == 0)
    {
      SCExAO_status[0].first_src_y = atof(value);
    }
    else if (strcmp(status_item, "first_photometry_st") == 0)
    {
      strncpy(SCExAO_status[0].first_photometry_st, value, 15);
      SCExAO_status[0].first_photometry_co = atoi(color);
    }
    else if (strcmp(status_item, "first_photometry") == 0)
    {
      SCExAO_status[0].first_photometry = atof(value);
    }
    // pywfs
    else if (strcmp(status_item, "pywfs_loop") == 0)
    {
      strncpy(SCExAO_status[0].pywfs_loop, value, 15);
      SCExAO_status[0].pywfs_loop_co = atoi(color);
    }
    else if (strcmp(status_item, "pywfs_cal") == 0)
    {
      strncpy(SCExAO_status[0].pywfs_cal, value, 15);
      SCExAO_status[0].pywfs_cal_co = atoi(color);
    }
    else if (strcmp(status_item, "pywfs_freq") == 0)
    {
      SCExAO_status[0].pywfs_freq = atoi(value);
    }
    else if (strcmp(status_item, "pywfs_gain") == 0)
    {
      SCExAO_status[0].pywfs_gain = atof(value);
    }
    else if (strcmp(status_item, "pywfs_leak") == 0)
    {
      SCExAO_status[0].pywfs_leak = atof(value);
    }
    else if (strcmp(status_item, "pywfs_rad") == 0)
    {
      SCExAO_status[0].pywfs_rad = atof(value);
    }
    else if (strcmp(status_item, "pywfs_puploop") == 0)
    {
      strncpy(SCExAO_status[0].pywfs_puploop, value, 15);
      SCExAO_status[0].pywfs_puploop_co = atoi(color);
    }
    else if (strcmp(status_item, "pywfs_cenloop") == 0)
    {
      strncpy(SCExAO_status[0].pywfs_cenloop, value, 15);
      SCExAO_status[0].pywfs_cenloop_co = atoi(color);
    }
    else if (strcmp(status_item, "dmoffload") == 0)
    {
      strncpy(SCExAO_status[0].dmoffload, value, 15);
      SCExAO_status[0].dmoffload_co = atoi(color);
    }

    // lowfs
    else if (strcmp(status_item, "lowfs_loop") == 0)
    {
      strncpy(SCExAO_status[0].lowfs_loop, value, 15);
      SCExAO_status[0].lowfs_loop_co = atoi(color);
    }
    else if (strcmp(status_item, "lowfs_freq") == 0)
    {
      SCExAO_status[0].lowfs_freq = atoi(value);
    }
    else if (strcmp(status_item, "lowfs_nmodes") == 0)
    {
      SCExAO_status[0].lowfs_nmodes = atoi(value);
    }
    else if (strcmp(status_item, "lowfs_mtype") == 0)
    {
      strncpy(SCExAO_status[0].lowfs_mtype, value, 15);
    }
    else if (strcmp(status_item, "lowfs_gain") == 0)
    {
      SCExAO_status[0].lowfs_gain = atof(value);
    }
    else if (strcmp(status_item, "lowfs_leak") == 0)
    {
      SCExAO_status[0].lowfs_leak = atof(value);
    }

    // speckle nulling
    else if (strcmp(status_item, "sn_loop") == 0)
    {
      strncpy(SCExAO_status[0].sn_loop, value, 15);
      SCExAO_status[0].sn_loop_co = atoi(color);
    }
    else if (strcmp(status_item, "sn_freq") == 0)
    {
      SCExAO_status[0].sn_freq = atoi(value);
    }
    else if (strcmp(status_item, "sn_gain") == 0)
    {
      SCExAO_status[0].sn_gain = atof(value);
    }

    // zap
    else if (strcmp(status_item, "zap_loop") == 0)
    {
      strncpy(SCExAO_status[0].zap_loop, value, 15);
      SCExAO_status[0].zap_loop_co = atoi(color);
    }
    else if (strcmp(status_item, "zap_freq") == 0)
    {
      SCExAO_status[0].zap_freq = atoi(value);
    }
    else if (strcmp(status_item, "zap_nmodes") == 0)
    {
      SCExAO_status[0].zap_nmodes = atoi(value);
    }
    else if (strcmp(status_item, "zap_mtype") == 0)
    {
      strncpy(SCExAO_status[0].zap_mtype, value, 15);
    }
    else if (strcmp(status_item, "zap_gain") == 0)
    {
      SCExAO_status[0].zap_gain = atof(value);
    }

    // astrogrid
    else if (strcmp(status_item, "grid_st") == 0)
    {
      strncpy(SCExAO_status[0].grid_st, value, 15);
      SCExAO_status[0].grid_st_co = atoi(color);
    }
    else if (strcmp(status_item, "grid_sep") == 0)
    {
      SCExAO_status[0].grid_sep = atof(value);
    }
    else if (strcmp(status_item, "grid_amp") == 0)
    {
      SCExAO_status[0].grid_amp = atof(value);
    }
    else if (strcmp(status_item, "grid_mod") == 0)
    {
      SCExAO_status[0].grid_mod = atoi(value);
    }

    // logging
    else if (strcmp(status_item, "logpalila") == 0)
    {
      strncpy(SCExAO_status[0].logpalila, value, 15);
      SCExAO_status[0].logpalila_co = atoi(color);
    }
    else if (strcmp(status_item, "logapapane") == 0)
    {
      strncpy(SCExAO_status_ext[0].logapapane, value, 15);
      SCExAO_status_ext[0].logapapane_co = atoi(color);
    }
    else if (strcmp(status_item, "darkpalila") == 0)
    {
      strncpy(SCExAO_status[0].darkpalila, value, 15);
      SCExAO_status[0].darkpalila_co = atoi(color);
    }
    else if (strcmp(status_item, "hotspot") == 0)
    {
      strncpy(SCExAO_status[0].hotspot, value, 15);
      SCExAO_status[0].hotspot_co = atoi(color);
    }
  }
  else if (strcmp(command, "disp") == 0)
  {
    read_status_shm();
    status_display();
    cmdOK = 1;
  }

  if (cmdOK == 0)
  {
    printf("%d  command %s not recognized\n", cmdOK, command);
  }

  return 0;
}

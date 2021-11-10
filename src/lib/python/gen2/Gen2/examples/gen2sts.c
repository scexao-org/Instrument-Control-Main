/*
 * Example program to read Gen2 status value feed
 * Eric Jeschke (eric@naoj.org)
 *
 * Example use:
 *  $ mkfifo /tmp/gen2sts.fifo
 *  $ ./gen2sts
 *
 *  (in another terminal)
 *  $ ./gen2sts.py -f gen2sts.yml --loglevel=10 --log=gen2sts.log
 *
 */

#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <time.h>

#define BUFSIZE 1024*1024*4

// this is the FIFO that we will read from
char *input_file = "/tmp/gen2sts.fifo";

// how many seconds of latency before we start getting worried
// if we haven't heard from Gen2
float latency_threshold = 10;

void
nohear_warning(time_t secs)
{
    fprintf(stderr, "I haven't heard from Gen2 for %d sec!\n",
            (int)secs);
}

int
main(int argc, char *argv[])
{
    char buf[BUFSIZE], time_s[50];
    char *ptr1, *ptr2, *ptr3;
    int in_d, num;
    struct tm tval;
    time_t curtime, nonetime;
    
    in_d = open(input_file, O_RDONLY | O_NONBLOCK);

    curtime = time(NULL);
        
    while (1)
    {
        // clear buffer
        (void *)memset((void *)buf, 0, BUFSIZE);

        // read from FIFO
        num = read(in_d, (void *)buf, (size_t)BUFSIZE);
        if (num <= 0)
        {
            nonetime = time(NULL) - curtime;
            if (nonetime >= latency_threshold)
            {
                nohear_warning(nonetime);
                // reset our counter
                curtime = time(NULL);
            }
            sleep(1);
            continue;
        }
        //printf("%d bytes read\n", num);
        //printf("buf:\n%s", buf);

        curtime = time(NULL);
        localtime_r(&curtime, &tval);
        (void *)strftime(time_s, sizeof(time_s), "%Y-%m-%d %H:%M:%S", &tval);
        printf("Received update at %s\n", time_s);
        
        // extract all ALIAS=VALUE combinations
        ptr3 = buf;
        while (1)
        {
            ptr1 = strtok(ptr3, "=");
            ptr3 = (char *)NULL;

            if (ptr1 == NULL)
                break;

            ptr2 = strtok(NULL, "\n");
            if (ptr2 == NULL)
                break;

            printf("alias=%s value=%s\n", ptr1, ptr2);
        }
    }
}

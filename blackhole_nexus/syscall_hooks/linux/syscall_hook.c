#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/ptrace.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/user.h>
#include <sys/syscall.h>
#include <fcntl.h>

#define LOG_FILE "/var/log/syscall_hooks.log"

void log_event(const char* msg) {
    int fd = open(LOG_FILE, O_WRONLY|O_CREAT|O_APPEND, 0644);
    if (fd >= 0) {
        dprintf(fd, "[%ld] %s\n", (long)time(NULL), msg);
        close(fd);
    }
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <command> [args...]\n", argv[0]);
        exit(1);
    }

    pid_t child = fork();
    if (child == 0) {
        ptrace(PTRACE_TRACEME, 0, NULL, NULL);
        execvp(argv[1], argv + 1);
        perror("execvp");
        exit(1);
    } else {
        int status;
        while (1) {
            waitpid(child, &status, 0);
            if (WIFEXITED(status)) break;

            struct user_regs_struct regs;
            ptrace(PTRACE_GETREGS, child, NULL, &regs);

            // Monitor execve (syscall 59 on x86_64)
            if (regs.orig_rax == SYS_execve) {
                char filename[256] = {0};
                char cmdline[1024] = {0};
                
                // Read filename
                for (int i = 0; i < 255; i++) {
                    long word = ptrace(PTRACE_PEEKDATA, child, regs.rdi + i, NULL);
                    if (word == 0 || (word & 0xFF) == 0) break;
                    filename[i] = word & 0xFF;
                    if ((word >> 8) & 0xFF) filename[i+1] = (word >> 8) & 0xFF;
                }

                // Log dangerous executables
                if (strstr(filename, "sh") || strstr(filename, "python")) {
                    char log_msg[2048];
                    snprintf(log_msg, sizeof(log_msg), 
                            "EXECVE DETECTED: %s (PID: %d)", filename, child);
                    log_event(log_msg);
                }
            }

            ptrace(PTRACE_SYSCALL, child, NULL, NULL);
        }
    }
    return 0;
}
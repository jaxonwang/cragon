#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include <pthread.h>
#include <sys/wait.h>

int *consume(int length) {
  int *a = calloc(length, sizeof(int));
  for (int i = 0; i < length; i++) {
    a[i] = i;
  }
  printf("Using %ld MB memory.\n", length * sizeof(int) / 1024 / 1024);
  return a;
}
const int length = 4096 * 10240;

void *thread_run(void *_) {
  consume(length);
  return (void *)0;
}

int main(int argc, const char *argv[]) {
  consume(length);
  const int thread_n = 4;
  const int process_n = 4;
  pthread_t threadId[thread_n];
  pid_t childprocess[process_n];
  for (int i = 0; i < process_n; i++) {
    childprocess[i] = 0;
  }
  for (int i = 0; i < process_n; i++) {
    int pid = fork();
    childprocess[i] = pid;
    if (pid == 0) {
      break;
    }
  }
  for (int i = 0; i < thread_n; i++) {
    pthread_create(&threadId[i], NULL, thread_run, NULL);
  }
  for (int i = 0; i < thread_n; i++) {
     pthread_join(threadId[i], NULL);
  }

  if (childprocess[process_n - 1] != 0) {
    for (int i = 0; i < process_n; i++) {
      waitpid(childprocess[i], NULL, 0);
      printf("asdfasdf%d\n", childprocess[i]);
    }
  }

  /* brk(sbrk(4096*1024)+4096*1024); */
  return 0;
}

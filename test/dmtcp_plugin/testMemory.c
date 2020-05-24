#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include <pthread.h>
#include <sys/mman.h>
#include <sys/wait.h>

int *consume(int length) {
  int *a = calloc(length, sizeof(int));
  for (int i = 0; i < length; i++) {
    a[i] = i;
  }
  printf("Using %ld KB memory.\n", length * sizeof(int) / 1024);
  return a;
}
const int length = 4096;

void *thread_run() {
  consume(length);
  return (void *)0;
}

void multi_process_test() {
  printf("Start multi process test\n");
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
      printf("Waiting child process: %d\n", childprocess[i]);
    }
    printf("Multi process test done.\n");
  }
}

void test_wrapped() {
  const int chunk_size = 4096;
  printf("Start wrapped function test\n");

  printf("Calling mmap.\n");
  char *chunk_mmap = mmap(NULL, chunk_size, PROT_READ | PROT_WRITE,
                          MAP_ANONYMOUS | MAP_PRIVATE, -1, 0);
  printf("Calling mremap.\n");
  chunk_mmap = mremap(chunk_mmap, chunk_size, 2 * chunk_size, MREMAP_MAYMOVE);
  printf("Calling mremap with the variadic argument.\n");
  chunk_mmap = mremap(chunk_mmap, chunk_size, chunk_size, MREMAP_FIXED,
                      chunk_mmap + chunk_size);
  munmap(chunk_mmap, chunk_size * 4);

  printf("Calling malloc.\n");
  int *chunk_malloc = malloc(chunk_size);
  printf("Calling cmalloc.\n");
  int *chunk_calloc = calloc(chunk_size / sizeof(int), sizeof(int));
  printf("Calling realloc.\n");
  chunk_malloc = realloc(chunk_malloc, chunk_size * 2);
  printf("Calling reallocarray.\n");
  chunk_calloc =
      reallocarray(chunk_calloc, chunk_size / sizeof(int), sizeof(int));
  free(chunk_malloc);
  free(chunk_calloc);

  printf("Calling sbrk.\n");
  void *brk_addr = sbrk(chunk_size);
  printf("Calling brk.\n");
  brk((u_int8_t*)brk_addr - chunk_size);

  printf("Wrapped function test done.\n");
}

int main() {
  test_wrapped();
  multi_process_test();

  return 0;
}

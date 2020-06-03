#define _GNU_SOURCE
// define this to enable reallocarray
#if __GLIBC_MINOR__ >= 29
#define _DEFAULT_SOURCE
#endif

#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <unistd.h>

#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/time.h>
#include <sys/wait.h>

void test_wrapped() {
  // 100MB, a test value otherwise: DMTCP(../jalib/jalloc.cpp): _alloc_raw: : Cannot allocate memory
  // VMPeak for this in kernel v4.5.0 is around 94MB, which is similar to the one run without my plugin,
  // But there is no error if dmtcp_launch without my plugin
  // Need to figure out in the future
  const int memory_allowed = 4096 * 1024 * 25;
  const int small_memory = 4096;

  struct rlimit mem_limit;
  mem_limit.rlim_cur = memory_allowed;
  mem_limit.rlim_max = memory_allowed;
  if (-1 == setrlimit(RLIMIT_AS, &mem_limit)) {
    perror("setrlimit");
  }
  printf("Set RLIMIT_DATA to %d bytes.\n", memory_allowed);

  const int chunk_size = memory_allowed * 2;

  char *chunk_mmap = mmap(NULL, chunk_size, PROT_READ | PROT_WRITE,
                          MAP_ANONYMOUS | MAP_PRIVATE, -1, 0);
  printf("mmap,%d,%p,%p,%d,%d,%d,%d,%d\n", errno, chunk_mmap, NULL, chunk_size,
         PROT_READ | PROT_WRITE, MAP_ANONYMOUS | MAP_PRIVATE, -1, 0);

  char *good_mmap = mmap(NULL, small_memory, PROT_READ | PROT_WRITE,
                         MAP_ANONYMOUS | MAP_PRIVATE, -1, 0);

  chunk_mmap = mremap(good_mmap, small_memory, chunk_size, MREMAP_MAYMOVE);
  printf("mremap,%d,%p,%p,%d,%d,%d\n", errno, chunk_mmap, good_mmap,
         small_memory, chunk_size, MREMAP_MAYMOVE);

  chunk_mmap =
      mremap(good_mmap, small_memory, chunk_size, MREMAP_FIXED | MREMAP_MAYMOVE,
             good_mmap + memory_allowed);
  printf("mremap,%d,%p,%p,%d,%d,%d,%p\n", errno, chunk_mmap, good_mmap,
         small_memory, chunk_size, MREMAP_FIXED | MREMAP_MAYMOVE,
         good_mmap + memory_allowed);

  int *chunk_malloc = malloc(chunk_size);
  printf("malloc,%d,%p,%d\n", errno, (void *)chunk_malloc, chunk_size);

  int *chunk_calloc = calloc(chunk_size / sizeof(int), sizeof(int));
  printf("calloc,%d,%p,%ld,%ld\n", errno, (void *)chunk_calloc,
         chunk_size / sizeof(int), sizeof(int));

  char *good_malloc = malloc(small_memory);
  chunk_malloc = realloc(good_malloc, chunk_size);
  printf("realloc,%d,%p,%p,%d\n", errno, (void *)chunk_calloc, good_malloc, chunk_size);

/* reallocarray is introduced in glibc 2.26 */
#if __GLIBC_MINOR__ >= 26
  good_malloc = malloc(small_memory);
  chunk_calloc =
      reallocarray(good_malloc, chunk_size / sizeof(int), sizeof(int));
  printf("reallocarray,%d,%p,%p,%ld,%ld\n", errno, (void *)chunk_calloc, good_malloc,
         chunk_size / sizeof(int), sizeof(int));
#endif

  void *brk_addr = sbrk(chunk_size);
  printf("sbrk,%d,%p,%d\n", errno, brk_addr, chunk_size);

  void *current_brk = sbrk(0);
  void *dest_brk = (uint8_t*)current_brk + chunk_size;
  int brkret = brk(dest_brk);
  printf("brk,%d,%d,%p\n", errno, brkret, dest_brk);
}

int main() {
  test_wrapped();
  return 0;
}

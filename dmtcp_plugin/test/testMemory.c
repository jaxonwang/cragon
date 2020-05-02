#include <stdio.h>
#include <stdlib.h>

int * consume(int length) {
  int *a = calloc(length, sizeof(int));
  for (int i = 0; i < length; i++) {
    a[i] = i;
  }
  printf("Using %ld MB memory.\n", length * sizeof(int) / 1024 / 1024);
  return a;
}

int main(int argc, const char *argv[]) {
  const int length = 4096 * 10240;
  consume(length);
  consume(length);
  consume(length);
  return 0;
}

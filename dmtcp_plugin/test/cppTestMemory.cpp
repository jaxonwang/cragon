#include <iostream>

using namespace std;

int main() {
  cout << "C++ test memroy start." << endl;
  // const int chunk_size = 4096;
  int *c = new int[(long long)1*1024*1024*1024];
  int *d = new int[(long long)1*1024*1024*1024];
  int *e = new int[(long long)1*1024*1024*1024];
  int *f = new int[(long long)1*1024*1024*1024];
  for (int i = 0; i < 4096; i++) {
    c[i] = i;
    d[i] = i;
    e[i] = i;
    f[i] = i;
  }
  cout << "C++ test memroy done." << endl;
  return 0;
}

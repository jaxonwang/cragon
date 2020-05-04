#include <iostream>

using namespace std;

int main() {
  cout << "C++ test memroy start." << endl;
  const int chunk_size = 4096;
  int *c = new int[chunk_size];
  for (int i = 0; i < chunk_size; i++) {
    c[i] = i;
  }
  cout << "C++ test memroy done." << endl;
  return 0;
}

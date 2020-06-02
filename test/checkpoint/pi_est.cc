#include <iostream>
#include <random>
#include <string>

int main(int argc, const char *argv[]) {

  if (argc != 2) {
    std::cout << "Usage: pi_est sample_number" << std::endl;
  }
  const int count = std::stoi(argv[1]);

  std::random_device r;
  std::default_random_engine e1(r());
  std::uniform_real_distribution<double> dis(0, 1.0);

  int inside = 0;
  for (int i = 0; i < count; i++) {
    double a = dis(e1);
    double b = dis(e1);
    if (a * a + b * b <= 1) {
      inside += 1;
    }
  }

  std::cout << (double)inside * 4 / count << std::endl;
  return 0;
}

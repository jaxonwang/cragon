#include <iostream>
#include <fstream>
#include <sstream>
#include <cstdlib>

using namespace std;

string randstring(const size_t length){
    stringstream ss;

    for (size_t i = 0; i < length; i++) {
    ss << char(rand() % 26 + 'a');
    }
    return ss.str();
}

int main(int argc, char *argv[])
{
    if (argc != 2 ){
        cout << "Usage: a.out filename" << endl;
        return -1;
    }

    srand(1234567);
    ofstream of = std::ofstream(argv[1], ios_base::app);

    for (int i = 0; i < 1024 * 100; i++) { // 100mb
        of << randstring(1023) << '\n'; // 1kb
    }
    of.close();
    
    return 0;
}

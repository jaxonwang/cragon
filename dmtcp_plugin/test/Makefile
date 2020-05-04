CFLAGS := -Wall -Wextra -Wno-long-long 

default: all
all: CtestMemory CppTestMemory
CtestMemory: testMemory.c
	gcc -lpthread $(CFLAGS) testMemory.c -o $@
CppTestMemory: cppTestMemory.cpp
	gcc --std=c++11 -lstdc++ -lpthread $(CFLAGS) cppTestMemory.cpp -o $@



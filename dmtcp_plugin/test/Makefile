CFLAGS := -Wall -Wextra -Wno-long-long -Wpedantic
CC := cc
BIN_DIR := bin

default: all
all: CtestMemory CppTestMemory
dirs: $(BIN_DIR)
	mkdir -p $(BIN_DIR)
CtestMemory: testMemory.c dirs
	$(CC) -lpthread $(CFLAGS) testMemory.c -o $(BIN_DIR)/$@
CppTestMemory: cppTestMemory.cpp dirs
	$(CC) --std=c++11 -lstdc++ -lpthread $(CFLAGS) cppTestMemory.cpp -o $(BIN_DIR)/$@



CFLAGS := -Wall -Wextra -Wno-long-long -Wpedantic
CC := cc
BIN_DIR := bin

default: all
all: $(BIN_DIR)/CtestMemory $(BIN_DIR)/CppTestMemory
$(BIN_DIR)/CtestMemory: testMemory.c
	if [ ! -d $(BIN_DIR) ]; then mkdir -p $(BIN_DIR); fi
	$(CC) -lpthread $(CFLAGS) testMemory.c -o $@
$(BIN_DIR)/CppTestMemory: cppTestMemory.cpp
	if [ ! -d $(BIN_DIR) ]; then mkdir -p $(BIN_DIR); fi
	$(CC) --std=c++11 -lstdc++ -lpthread $(CFLAGS) cppTestMemory.cpp -o $@



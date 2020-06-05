CFLAGS := -Wall -Wextra -Wno-long-long -Wpedantic -std=c99
CXXFLAGS := -Wall -Wextra -Wno-long-long -Wpedantic -std=c++11
BIN_DIR := bin

default: all
all: $(BIN_DIR)/CtestMemory $(BIN_DIR)/CppTestMemory $(BIN_DIR)/BadMemoryCall
$(BIN_DIR)/CtestMemory: testMemory.c
	if [ ! -d $(BIN_DIR) ]; then mkdir -p $(BIN_DIR); fi
	$(CC) $(CFLAGS) -pthread $^ -o $@
$(BIN_DIR)/CppTestMemory: cppTestMemory.cpp
	if [ ! -d $(BIN_DIR) ]; then mkdir -p $(BIN_DIR); fi
	$(CXX) $(CXXFLAGS) $^ -o $@
$(BIN_DIR)/BadMemoryCall: badMemoryCall.c
	if [ ! -d $(BIN_DIR) ]; then mkdir -p $(BIN_DIR); fi
	$(CC) $(CFLAGS) $^ -o $@

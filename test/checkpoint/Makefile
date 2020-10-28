CFLAGS := -Wall -Wextra -Wno-long-long -Wpedantic
BIN_DIR := bin


default: all
all: $(BIN_DIR)/PiEst $(BIN_DIR)/SegFault $(BIN_DIR)/HugeAppend
$(BIN_DIR)/PiEst: pi_est.cc
	if [ ! -d $(BIN_DIR) ]; then mkdir -p $(BIN_DIR); fi
	$(CXX) -std=c++11 -lm $(CFLAGS) $^ -o $@

$(BIN_DIR)/SegFault: seg_fault.c
	if [ ! -d $(BIN_DIR) ]; then mkdir -p $(BIN_DIR); fi
	$(CC) $(CFLAGS) $^ -o $@

$(BIN_DIR)/HugeAppend: hugeappend.cc
	if [ ! -d $(BIN_DIR) ]; then mkdir -p $(BIN_DIR); fi
	$(CXX) -std=c++11 $(CFLAGS) $^ -o $@
